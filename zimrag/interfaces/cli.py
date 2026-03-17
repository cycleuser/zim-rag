"""ZIM-RAG 命令行接口"""

import argparse
import sys
import json
from typing import Optional

from ..api import ZIMRAGAPI, ToolResult


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="zim-rag",
        description="ZIM 本地知识库 RAG 问答系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  zim-rag index /path/to/wiki.zim          # 构建索引
  zim-rag ask "量子力学是什么？"              # 提问
  zim-rag gui                               # 启动图形界面
  zim-rag web --port 5000                   # 启动 Web 服务
  zim-rag chat                              # 交互聊天模式
        """,
    )

    # 统一标志
    parser.add_argument("-V", "--version", action="version", version="zim-rag 1.0.0")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("-o", "--output", type=str, help="输出文件路径")
    parser.add_argument("--json", action="store_true", dest="json_output", help="JSON 格式输出")
    parser.add_argument("-q", "--quiet", action="store_true", help="安静模式")
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="llama3",
        help="Ollama 模型名称 (默认：llama3)",
    )
    parser.add_argument(
        "--host", type=str, default="http://localhost:11434", help="Ollama 服务地址"
    )
    parser.add_argument("--index-dir", type=str, default="./zimrag_index", help="索引存储目录")

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # index 命令
    index_parser = subparsers.add_parser("index", help="构建 ZIM 索引")
    index_parser.add_argument("zims", nargs="+", help="ZIM 文件路径")
    index_parser.add_argument("--max-articles", type=int, default=10000, help="最大索引文章数")
    index_parser.add_argument("--chunk-size", type=int, default=500, help="文本分块大小")

    # ask 命令
    ask_parser = subparsers.add_parser("ask", help="提问并获取答案")
    ask_parser.add_argument("question", type=str, help="问题内容")
    ask_parser.add_argument("-z", "--zims", nargs="+", help="指定 ZIM 文件")
    ask_parser.add_argument("-n", "--context-limit", type=int, default=5, help="上下文数量限制")
    ask_parser.add_argument("--stream", action="store_true", help="流式输出")

    # chat 命令
    chat_parser = subparsers.add_parser("chat", help="交互聊天模式")
    chat_parser.add_argument("-n", "--context-limit", type=int, default=3, help="上下文数量限制")

    # gui 命令
    gui_parser = subparsers.add_parser("gui", help="启动图形界面")
    gui_parser.add_argument("--no-web", action="store_true", help="禁用嵌入的 Web 服务器")

    # web 命令
    web_parser = subparsers.add_parser("web", help="启动 Web 服务")
    web_parser.add_argument("--host", type=str, default="127.0.0.1", help="Web 服务监听地址")
    web_parser.add_argument("-p", "--port", type=int, default=5000, help="Web 服务端口")

    # stats 命令
    stats_parser = subparsers.add_parser("stats", help="显示系统统计")

    # health 命令
    health_parser = subparsers.add_parser("health", help="检查系统健康状态")

    # doc 命令
    doc_parser = subparsers.add_parser("doc", help="生成文档")
    doc_parser.add_argument("topic", type=str, help="文档主题")
    doc_parser.add_argument("--outline", nargs="+", help="文档大纲")
    doc_parser.add_argument("-n", "--context-limit", type=int, default=10, help="上下文数量限制")

    return parser


def print_result(
    result: ToolResult,
    json_output: bool = False,
    verbose: bool = False,
    quiet: bool = False,
):
    """打印结果"""
    if quiet and result.success:
        return

    if json_output:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        if result.success:
            if isinstance(result.data, dict):
                for key, value in result.data.items():
                    if not quiet or key in ["answer", "response", "content"]:
                        print(f"{key}: {value}")
            else:
                print(result.data)

            if verbose and result.metadata:
                print("\n元数据:")
                for key, value in result.metadata.items():
                    print(f"  {key}: {value}")
        else:
            print(f"错误：{result.error}", file=sys.stderr)


def cmd_index(api: ZIMRAGAPI, args, **kwargs) -> ToolResult:
    """构建索引命令"""
    print(f"开始构建索引...")
    print(f"ZIM 文件：{', '.join(args.zims)}")
    print(f"最大文章数：{args.max_articles:,}")

    # 先添加 ZIM 文件
    for zim_path in args.zims:
        result = api.add_zim(zim_path)
        if not result.success:
            return result

    # 构建索引
    return api.build_index(max_articles=args.max_articles, chunk_size=args.chunk_size)


def cmd_ask(api: ZIMRAGAPI, args, **kwargs) -> ToolResult | None:
    """提问命令"""
    if args.stream:
        print("回答：", end="", flush=True)
        try:
            for chunk in api.ask_stream(
                question=args.question,
                context_limit=args.context_limit,
                zim_paths=args.zims,
                model=args.model,
            ):
                print(chunk, end="", flush=True)
            print()
            return None
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    else:
        return api.ask(
            question=args.question,
            context_limit=args.context_limit,
            zim_paths=args.zims,
            model=args.model,
        )


def cmd_chat(api: ZIMRAGAPI, args, **kwargs):
    """聊天命令"""
    print("ZIM-RAG 聊天模式 (输入 'quit' 退出)")
    print("=" * 40)

    messages = []

    while True:
        try:
            user_input = input("\n你：").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                print("再见！")
                break

            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})

            result = api.chat(messages=messages, context_limit=args.context_limit, model=args.model)

            if result.success:
                response = result.data.get("response", "")
                print(f"\n助手：{response}")
                messages.append({"role": "assistant", "content": response})
            else:
                print(f"\n错误：{result.error}")

        except KeyboardInterrupt:
            print("\n再见！")
            break
        except EOFError:
            break


def cmd_stats(api: ZIMRAGAPI, args, **kwargs) -> ToolResult:
    """统计命令"""
    return api.get_stats()


def cmd_health(api: ZIMRAGAPI, args, **kwargs) -> ToolResult:
    """健康检查命令"""
    return api.check_health()


def cmd_doc(api: ZIMRAGAPI, args, **kwargs) -> ToolResult:
    """生成文档命令"""
    return api.generate_document(
        topic=args.topic,
        outline=args.outline,
        context_limit=args.context_limit,
        model=args.model,
    )


def cmd_gui(api: ZIMRAGAPI, args, **kwargs):
    """启动 GUI"""
    from .interfaces.gui import launch_gui

    launch_gui(api, no_web=args.no_web)


def cmd_web(api: ZIMRAGAPI, args, **kwargs):
    """启动 Web 服务"""
    from .interfaces.web import launch_web

    launch_web(api, host=args.host, port=args.port)


def main():
    """主入口"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # 初始化 API
    api = ZIMRAGAPI(model=args.model, ollama_host=args.host, index_dir=args.index_dir)

    # 命令映射
    commands = {
        "index": cmd_index,
        "ask": cmd_ask,
        "chat": cmd_chat,
        "stats": cmd_stats,
        "health": cmd_health,
        "doc": cmd_doc,
        "gui": cmd_gui,
        "web": cmd_web,
    }

    if args.command in commands:
        result = commands[args.command](api, args)

        # 打印结果（chat、gui、web 命令不打印）
        if result is not None and args.command not in ["chat", "gui", "web"]:
            print_result(
                result,
                json_output=args.json_output,
                verbose=args.verbose,
                quiet=args.quiet,
            )

            # 保存到文件
            if args.output and result:
                try:
                    with open(args.output, "w", encoding="utf-8") as f:
                        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
                    print(f"\n结果已保存到：{args.output}")
                except Exception as e:
                    print(f"保存失败：{e}", file=sys.stderr)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
