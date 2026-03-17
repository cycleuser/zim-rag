"""ZIM-RAG 统一 Python API"""

from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict, Generator

from .core.rag_engine import RAGEngine, RAGResponse


@dataclass
class ToolResult:
    """统一工具结果"""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }


class ZIMRAGAPI:
    """
    ZIM-RAG 统一 API

    提供完整的 Python 接口用于 ZIM 知识库问答系统。
    """

    def __init__(
        self,
        zim_paths: Optional[List[str]] = None,
        model: str = "llama3",
        ollama_host: str = "http://localhost:11434",
        index_dir: str = "./zimrag_index",
    ):
        """
        初始化 API

        Args:
            zim_paths: ZIM 文件路径列表
            model: Ollama 模型名称
            ollama_host: Ollama 服务地址
            index_dir: 索引存储目录
        """
        self.engine = RAGEngine(
            zim_paths=zim_paths,
            model=model,
            ollama_host=ollama_host,
            index_dir=index_dir,
        )

    def ask(
        self,
        question: str,
        context_limit: int = 5,
        zim_paths: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> ToolResult:
        """
        提问接口

        Args:
            question: 问题内容
            context_limit: 上下文数量
            zim_paths: 指定 ZIM 文件
            model: 使用的模型

        Returns:
            ToolResult 包含回答
        """
        try:
            response = self.engine.query(
                question=question,
                context_limit=context_limit,
                zim_paths=zim_paths,
                model=model,
            )
            return ToolResult(
                success=True,
                data=response.to_dict(),
                metadata={
                    "sources": response.context.sources,
                    "retrieval_time": response.context.retrieval_time,
                    "generation_time": response.generation_time,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def ask_stream(
        self,
        question: str,
        context_limit: int = 5,
        zim_paths: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """
        流式提问接口

        Yields:
            回答文本块
        """
        try:
            for chunk in self.engine.query(
                question=question,
                context_limit=context_limit,
                zim_paths=zim_paths,
                model=model,
                stream=True,
            ):
                yield chunk
        except Exception as e:
            yield f"[错误：{e}]"

    def chat(
        self,
        messages: List[Dict[str, str]],
        context_limit: int = 3,
        zim_paths: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> ToolResult:
        """
        聊天接口

        Args:
            messages: 消息历史 [{"role": "user/assistant", "content": "..."}]
            context_limit: 上下文数量
            zim_paths: 指定 ZIM 文件
            model: 使用的模型

        Returns:
            ToolResult 包含回复
        """
        try:
            response = self.engine.chat(
                messages=messages,
                context_limit=context_limit,
                zim_paths=zim_paths,
                model=model,
            )
            return ToolResult(
                success=True,
                data={"response": response},
                metadata={"message_count": len(messages)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def build_index(
        self,
        max_articles: int = 10000,
        chunk_size: int = 500,
        zim_paths: Optional[List[str]] = None,
    ) -> ToolResult:
        """
        构建索引接口

        Args:
            max_articles: 最大文章数
            chunk_size: 分块大小
            zim_paths: 指定 ZIM 文件

        Returns:
            ToolResult 包含统计信息
        """
        try:
            stats = self.engine.build_index(
                max_articles=max_articles, chunk_size=chunk_size, zim_paths=zim_paths
            )
            return ToolResult(success=True, data=stats, metadata={"indexed": True})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def add_zim(self, zim_path: str) -> ToolResult:
        """添加 ZIM 文件"""
        try:
            success = self.engine.load_zim(zim_path)
            if success:
                return ToolResult(success=True, data={"path": zim_path}, metadata={"added": True})
            return ToolResult(success=False, error="无法加载 ZIM 文件")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def remove_zim(self, zim_path: str) -> ToolResult:
        """移除 ZIM 文件"""
        try:
            success = self.engine.unload_zim(zim_path)
            return ToolResult(
                success=success, data={"path": zim_path}, metadata={"removed": success}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def list_zims(self) -> ToolResult:
        """列出已加载的 ZIM 文件"""
        try:
            stats = self.engine.parser.get_stats()
            return ToolResult(
                success=True,
                data=stats["files"],
                metadata={
                    "total_files": stats["loaded_files"],
                    "total_articles": stats["total_articles"],
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def get_stats(self) -> ToolResult:
        """获取系统统计信息"""
        try:
            stats = self.engine.get_stats()
            return ToolResult(success=True, data=stats)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def check_health(self) -> ToolResult:
        """检查系统健康状态"""
        try:
            ollama_healthy = self.engine.llm.check_health()
            models = self.engine.llm.list_models()

            return ToolResult(
                success=ollama_healthy,
                data={
                    "ollama": ollama_healthy,
                    "models": [m.name for m in models],
                    "model": self.engine.model,
                },
                metadata={
                    "zim_files": len(self.engine.zim_paths),
                    "index_dir": self.engine.index_dir,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def generate_document(
        self,
        topic: str,
        outline: Optional[List[str]] = None,
        context_limit: int = 10,
        zim_paths: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> ToolResult:
        """生成文档"""
        try:
            content = self.engine.generate_document(
                topic=topic,
                outline=outline,
                context_limit=context_limit,
                zim_paths=zim_paths,
                model=model,
            )
            return ToolResult(
                success=True,
                data={"content": content, "topic": topic},
                metadata={"generated": True},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def reset_index(self) -> ToolResult:
        """重置索引"""
        try:
            success = self.engine.index.reset()
            return ToolResult(
                success=success,
                data={"reset": success},
                metadata={"index_dir": self.engine.index_dir},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def export_index(self, output_path: str) -> ToolResult:
        """导出索引"""
        try:
            success = self.engine.index.export_index(output_path)
            return ToolResult(
                success=success,
                data={"path": output_path},
                metadata={"exported": success},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
