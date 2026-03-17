"""ZIM-RAG 本地知识库问答系统

基于 ZIM 文件和本地大语言模型 (Ollama) 的检索增强生成 (RAG) 系统。
"""

__version__ = "1.0.0"
__author__ = "ZIM-RAG Team"
__license__ = "GPL-3.0"

from .api import ZIMRAGAPI, ToolResult
from .core import ZIMParser, ContentIndex, RAGEngine, OllamaClient

__all__ = [
    "ZIMRAGAPI",
    "ToolResult",
    "ZIMParser",
    "ContentIndex",
    "RAGEngine",
    "OllamaClient",
]
