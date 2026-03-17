"""ZIM-RAG 核心模块测试"""

import pytest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestOllamaClient:
    """Ollama 客户端测试"""

    def test_init_default(self):
        """测试默认初始化"""
        from zimrag.core.llm_client import OllamaClient

        client = OllamaClient()
        assert client.model == "llama3"
        assert client.host == "http://localhost:11434"

    def test_init_custom(self):
        """测试自定义参数初始化"""
        from zimrag.core.llm_client import OllamaClient

        client = OllamaClient(model="mistral", host="http://remote:11434")
        assert client.model == "mistral"
        assert client.host == "http://remote:11434"


class TestZIMParser:
    """ZIM 解析器测试"""

    def test_init_empty(self):
        """测试空初始化"""
        from zimrag.core.zim_parser import ZIMParser

        parser = ZIMParser()
        assert parser.zim_paths == []
        assert parser.files == {}

    def test_init_with_paths(self):
        """测试带路径初始化"""
        from zimrag.core.zim_parser import ZIMParser

        paths = ["/path/to/file.zim"]
        parser = ZIMParser(paths)
        assert parser.zim_paths == paths

    def test_load_nonexistent_zim(self):
        """测试加载不存在的 ZIM 文件"""
        from zimrag.core.zim_parser import ZIMParser

        parser = ZIMParser()
        result = parser.load_zim("/nonexistent/file.zim")
        assert result is False

    def test_get_stats_empty(self):
        """测试空统计信息"""
        from zimrag.core.zim_parser import ZIMParser

        parser = ZIMParser()
        stats = parser.get_stats()

        assert stats["loaded_files"] == 0
        assert stats["total_articles"] == 0


class TestContentIndex:
    """内容索引测试"""

    def test_init_default(self):
        """测试默认初始化"""
        from zimrag.core.content_index import ContentIndex

        index = ContentIndex()
        assert index.collection_name == "zim_content"

    def test_add_empty_document(self):
        """测试添加空文档"""
        from zimrag.core.content_index import ContentIndex

        index = ContentIndex()
        result = index.add_document("test_id", "", {})
        assert result is False

    def test_add_document(self):
        """测试添加文档"""
        from zimrag.core.content_index import ContentIndex

        index = ContentIndex()
        result = index.add_document("test_id", "This is test content", {"title": "Test"})
        assert result is True


class TestRAGResponse:
    """RAG 响应测试"""

    def test_to_dict(self):
        """测试转换为字典"""
        from zimrag.core.rag_engine import RAGResponse, RAGContext

        context = RAGContext(
            question="Test question?", contexts=["context1"], sources=[{"title": "Test"}]
        )

        response = RAGResponse(
            answer="Test answer", context=context, model="llama3", generation_time=1.5
        )

        result = response.to_dict()

        assert result["answer"] == "Test answer"
        assert result["model"] == "llama3"
        assert result["generation_time"] == 1.5
        assert result["context_count"] == 1


class TestToolResult:
    """工具结果测试"""

    def test_success(self):
        """测试成功结果"""
        from zimrag.api import ToolResult

        result = ToolResult(success=True, data={"key": "value"})

        assert result.success is True
        assert result.error is None
        assert result.data["key"] == "value"

    def test_failure(self):
        """测试失败结果"""
        from zimrag.api import ToolResult

        result = ToolResult(success=False, error="Test error")

        assert result.success is False
        assert result.error == "Test error"
        assert result.data is None

    def test_to_dict(self):
        """测试转换为字典"""
        from zimrag.api import ToolResult

        result = ToolResult(success=True, data={"answer": "test"}, metadata={"time": 1.0})

        d = result.to_dict()

        assert d["success"] is True
        assert d["data"]["answer"] == "test"
        assert d["metadata"]["time"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
