#!/usr/bin/env python3
"""
ZIM-RAG 多 ZIM 文件答案生成测试脚本

从多个 ZIM 文件中检索并生成答案，输出为 Markdown 文档。

使用方法:
    python tests/generate_zim_answers.py

输出:
    - output/zim_answers_YYYYMMDD_HHMMSS.md
    - output/zim_comparison_YYYYMMDD_HHMMSS.md
"""

import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from zimrag.api import ZIMRAGAPI, ToolResult


# 测试问题列表（中英双语）
TEST_QUESTIONS = [
    {"zh": "什么是量子力学？", "en": "What is quantum mechanics?", "category": "physics"},
    {
        "zh": "Python 编程语言有什么特点？",
        "en": "What are the characteristics of Python programming language?",
        "category": "programming",
    },
    {
        "zh": "第一次世界大战发生在什么时候？",
        "en": "When did World War I take place?",
        "category": "history",
    },
    {
        "zh": "人工智能的发展历程是什么？",
        "en": "What is the development history of artificial intelligence?",
        "category": "technology",
    },
    {
        "zh": "光合作用的过程是怎样的？",
        "en": "What is the process of photosynthesis?",
        "category": "biology",
    },
]


def format_markdown_header() -> str:
    """生成 Markdown 文档头部"""
    return f"""# ZIM-RAG 多 ZIM 文件答案生成测试报告

**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**系统**: ZIM-RAG v1.0.0
**许可证**: GPL-3.0

---

## 项目信息

- **GitHub**: https://github.com/cycleuser/zim-rag
- **PyPI**: https://pypi.org/project/zim-rag/

---

"""


def format_question_section(question: Dict, answers: List[Dict], zim_files: List[str]) -> str:
    """格式化单个问题的答案部分"""
    md = f"""### {question["category"].title()}: {question["zh"]}

**英文**: {question["en"]}

"""

    for i, answer in enumerate(answers):
        zim_name = Path(zim_files[i]).name if i < len(zim_files) else f"ZIM-{i + 1}"
        md += f"""#### 答案来源：{zim_name}

**回答**:
{answer["answer"]}

**检索时间**: {answer.get("retrieval_time", "N/A"):.2f} 秒
**生成时间**: {answer.get("generation_time", "N/A"):.2f} 秒
**模型**: {answer.get("model", "N/A")}

**参考来源**:
"""
        for j, source in enumerate(answer.get("sources", []), 1):
            title = source.get("title", "Unknown")
            url = source.get("url", "")
            md += f"{j}. [{title}]({url})\n" if url else f"{j}. {title}\n"

        md += "\n---\n\n"

    return md


def generate_comparison_table(questions: List[Dict], all_answers: List[List[Dict]]) -> str:
    """生成答案对比表格"""
    md = """## 答案对比摘要

| 问题 | 类别 | 答案长度 (字符) | 来源数量 | 平均生成时间 |
|------|------|----------------|----------|-------------|
"""
    for i, question in enumerate(questions):
        answers = all_answers[i]
        if answers:
            avg_length = sum(len(a["answer"]) for a in answers) // len(answers)
            avg_sources = sum(len(a.get("sources", [])) for a in answers) // len(answers)
            avg_time = sum(a.get("generation_time", 0) for a in answers) / len(answers)

            md += f"| {question['zh'][:30]}... | {question['category']} | {avg_length} | {avg_sources} | {avg_time:.2f}s |\n"

    md += "\n---\n\n"
    return md


def generate_zim_answers(
    zim_paths: List[str],
    questions: List[Dict],
    output_dir: str = "output",
    model: str = "llama3",
    context_limit: int = 5,
) -> Dict:
    """
    从多个 ZIM 文件生成答案

    Args:
        zim_paths: ZIM 文件路径列表
        questions: 问题列表
        output_dir: 输出目录
        model: Ollama 模型名称
        context_limit: 上下文数量限制

    Returns:
        测试结果字典
    """
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 初始化 API
    api = ZIMRAGAPI(model=model, index_dir=str(output_path / "zimrag_index"))

    # 添加 ZIM 文件
    print("=" * 60)
    print("ZIM-RAG 多 ZIM 文件答案生成测试")
    print("=" * 60)
    print(f"\n📦 ZIM 文件：{len(zim_paths)}")
    for zim in zim_paths:
        print(f"   - {zim}")
    print(f"\n🤖 模型：{model}")
    print(f"📝 问题数量：{len(questions)}")
    print(f"📂 输出目录：{output_path}\n")

    # 为每个 ZIM 文件构建索引并生成答案
    results = {
        "timestamp": datetime.now().isoformat(),
        "zim_files": zim_paths,
        "model": model,
        "questions": questions,
        "answers": [],
    }

    all_answers = []

    for zim_idx, zim_path in enumerate(zim_paths):
        print(f"\n{'=' * 60}")
        print(f"处理 ZIM 文件 {zim_idx + 1}/{len(zim_paths)}: {Path(zim_path).name}")
        print(f"{'=' * 60}")

        # 重置索引
        api.engine.index = None

        # 添加 ZIM 文件
        print(f"📖 加载 ZIM 文件...")
        result = api.add_zim(zim_path)
        if not result.success:
            print(f"❌ 加载失败：{result.error}")
            continue

        # 构建索引
        print(f"🔨 构建索引...")
        result = api.build_index(max_articles=1000, chunk_size=500)
        if not result.success:
            print(f"❌ 索引构建失败：{result.error}")
            continue

        zim_answers = []

        # 对每个问题生成答案
        for q_idx, question in enumerate(questions, 1):
            print(f"\n  问题 {q_idx}/{len(questions)}: {question['zh']}")

            # 提问
            result = api.ask(question=question["zh"], context_limit=context_limit, model=model)

            if result.success:
                answer_data = result.data
                answer_entry = {
                    "question_zh": question["zh"],
                    "question_en": question["en"],
                    "category": question["category"],
                    "answer": answer_data.get("answer", "N/A"),
                    "sources": answer_data.get("sources", []),
                    "retrieval_time": answer_data.get("retrieval_time", 0),
                    "generation_time": answer_data.get("generation_time", 0),
                    "model": answer_data.get("model", model),
                    "zim_file": zim_path,
                }
                zim_answers.append(answer_entry)
                print(f"  ✅ 答案生成完成 ({len(answer_data.get('sources', []))} 个来源)")
            else:
                print(f"  ❌ 失败：{result.error}")
                zim_answers.append(
                    {
                        "question_zh": question["zh"],
                        "question_en": question["en"],
                        "category": question["category"],
                        "answer": f"Error: {result.error}",
                        "sources": [],
                        "error": result.error,
                        "zim_file": zim_path,
                    }
                )

        results["answers"].extend(zim_answers)
        all_answers.append(zim_answers)

    # 生成 Markdown 报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 完整答案文档
    md_content = format_markdown_header()
    md_content += f"""## 测试配置

- **ZIM 文件数量**: {len(zim_paths)}
- **问题数量**: {len(questions)}
- **模型**: {model}
- **上下文限制**: {context_limit}

## ZIM 文件列表

"""
    for i, zim in enumerate(zim_paths, 1):
        zim_size = Path(zim).stat().st_size / (1024 * 1024) if Path(zim).exists() else 0
        md_content += f"{i}. `{Path(zim).name}` ({zim_size:.1f} MB)\n"

    md_content += "\n---\n\n## 详细答案\n\n"

    for i, question in enumerate(questions):
        question_answers = [a for a in results["answers"] if a["question_zh"] == question["zh"]]
        md_content += format_question_section(question, question_answers, zim_paths)

    # 对比表格
    md_content += generate_comparison_table(questions, all_answers)

    # 统计信息
    md_content += f"""## 统计信息

- **总问题数**: {len(questions)}
- **总 ZIM 文件数**: {len(zim_paths)}
- **成功回答数**: {len([a for a in results["answers"] if "error" not in a])}
- **失败回答数**: {len([a for a in results["answers"] if "error" in a])}
- **平均答案长度**: {sum(len(a["answer"]) for a in results["answers"] if "error" not in a) // max(1, len([a for a in results["answers"] if "error" not in a]))} 字符
- **平均来源数**: {sum(len(a.get("sources", [])) for a in results["answers"] if "error" not in a) / max(1, len([a for a in results["answers"] if "error" not in a])):.1f}

---

*Generated by ZIM-RAG v1.0.0 | https://github.com/cycleuser/zim-rag*
"""

    # 保存文件
    output_file = output_path / f"zim_answers_{timestamp}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n{'=' * 60}")
    print(f"✅ 报告已保存：{output_file}")
    print(f"{'=' * 60}\n")

    return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ZIM-RAG 多 ZIM 文件答案生成测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tests/generate_zim_answers.py /path/to/wiki.zim
  python tests/generate_zim_answers.py /path/to/wiki1.zim /path/to/wiki2.zim -m mistral -o my_output
        """,
    )

    parser.add_argument("zims", nargs="+", help="ZIM 文件路径")
    parser.add_argument("-o", "--output-dir", default="output", help="输出目录 (默认：output)")
    parser.add_argument("-m", "--model", default="llama3", help="Ollama 模型名称 (默认：llama3)")
    parser.add_argument(
        "-n", "--context-limit", type=int, default=5, help="上下文数量限制 (默认：5)"
    )
    parser.add_argument(
        "-q", "--questions", type=str, help="自定义问题文件 (JSON 格式，每行一个问题)"
    )

    args = parser.parse_args()

    # 验证 ZIM 文件
    valid_zims = []
    for zim in args.zims:
        if Path(zim).exists():
            valid_zims.append(zim)
        else:
            print(f"⚠️  警告：ZIM 文件不存在：{zim}")

    if not valid_zims:
        print("❌ 错误：没有有效的 ZIM 文件")
        sys.exit(1)

    # 加载自定义问题（如果有）
    questions = TEST_QUESTIONS
    if args.questions:
        try:
            import json

            with open(args.questions, "r", encoding="utf-8") as f:
                questions = json.load(f)
            print(f"📝 已加载 {len(questions)} 个自定义问题")
        except Exception as e:
            print(f"⚠️  加载问题文件失败，使用默认问题：{e}")

    # 生成答案
    results = generate_zim_answers(
        zim_paths=valid_zims,
        questions=questions,
        output_dir=args.output_dir,
        model=args.model,
        context_limit=args.context_limit,
    )

    # 输出摘要
    print("\n📊 测试摘要:")
    print(f"   总问题数：{len(questions)}")
    print(f"   总 ZIM 文件：{len(valid_zims)}")
    print(f"   生成答案：{len(results['answers'])}")
    print(f"   输出文件：{args.output_dir}/zim_answers_*.md")


if __name__ == "__main__":
    main()
