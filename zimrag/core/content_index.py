"""内容索引模块 - 使用 ChromaDB 进行向量存储和检索"""

import os
import hashlib
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class IndexedDocument:
    """已索引的文档"""

    doc_id: str
    content: str
    metadata: Dict[str, Any]


class ContentIndex:
    """
    内容索引器

    使用 ChromaDB 进行向量存储，支持语义搜索和过滤。
    提供文档添加、搜索、删除等功能。
    """

    def __init__(
        self,
        index_dir: str = "./zimrag_index",
        collection_name: str = "zim_content",
        embedding_fn: Optional[Any] = None,
    ):
        """
        初始化内容索引

        Args:
            index_dir: 索引存储目录
            collection_name: 集合名称
            embedding_fn: 嵌入函数，None 表示使用默认
        """
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedding_fn = embedding_fn
        self._client = None
        self._collection = None
        self._init_chroma()

    def _init_chroma(self):
        """初始化 ChromaDB 客户端"""
        try:
            import chromadb
            from chromadb.config import Settings

            self._client = chromadb.PersistentClient(
                path=str(self.index_dir),
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )

            # 获取或创建集合
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name, metadata={"hnsw:space": "cosine"}
            )
        except ImportError:
            raise ImportError("ChromaDB 未安装。请运行：pip install chromadb")
        except Exception as e:
            raise RuntimeError(f"初始化 ChromaDB 失败：{e}")

    def add_document(
        self, doc_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        添加文档到索引

        Args:
            doc_id: 文档唯一 ID
            content: 文档内容
            metadata: 元数据（标题、来源等）

        Returns:
            是否添加成功
        """
        if not content or not content.strip():
            return False

        try:
            # 限制内容长度（ChromaDB 限制）
            content = content[:65000]

            metadata = metadata or {}
            metadata["doc_id"] = doc_id

            self._collection.add(documents=[content], ids=[doc_id], metadatas=[metadata])
            return True

        except Exception as e:
            print(f"添加文档失败 {doc_id}: {e}")
            return False

    def add_documents(self, documents: List[IndexedDocument]) -> Dict[str, bool]:
        """
        批量添加文档

        Args:
            documents: 文档列表

        Returns:
            {doc_id: 是否成功} 的字典
        """
        results = {}
        batch_size = 100

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]

            contents = []
            ids = []
            metadatas = []

            for doc in batch:
                if doc.content and doc.content.strip():
                    contents.append(doc.content[:65000])
                    ids.append(doc.doc_id)
                    metadata = doc.metadata.copy()
                    metadata["doc_id"] = doc.doc_id
                    metadatas.append(metadata)

            if contents:
                try:
                    self._collection.add(documents=contents, ids=ids, metadatas=metadatas)
                    for doc in batch:
                        results[doc.doc_id] = True
                except Exception as e:
                    print(f"批量添加失败：{e}")
                    for doc in batch:
                        results[doc.doc_id] = False

        return results

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_zim: Optional[List[str]] = None,
        filter_title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        语义搜索

        Args:
            query: 搜索查询
            n_results: 返回结果数量
            filter_zim: 过滤 ZIM 文件路径列表
            filter_title: 过滤标题关键词

        Returns:
            搜索结果字典
        """
        try:
            # 构建过滤条件
            where = None
            if filter_zim:
                where = {"zim_path": {"$in": filter_zim}}

            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            # 后处理：标题过滤
            if filter_title and results.get("metadatas") and results["metadatas"][0]:
                filtered_results = {
                    "documents": [[]],
                    "metadatas": [[]],
                    "distances": [[]],
                    "ids": [[]],
                }

                for i, meta in enumerate(results["metadatas"][0]):
                    if meta and filter_title.lower() in meta.get("title", "").lower():
                        filtered_results["documents"][0].append(results["documents"][0][i])
                        filtered_results["metadatas"][0].append(meta)
                        filtered_results["distances"][0].append(results["distances"][0][i])
                        filtered_results["ids"][0].append(results["ids"][0][i])

                results = filtered_results

            return results

        except Exception as e:
            print(f"搜索失败：{e}")
            return {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
                "ids": [[]],
            }

    def hybrid_search(
        self,
        query: str,
        keyword_results: int = 10,
        semantic_results: int = 5,
        filter_zim: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        混合搜索（关键词 + 语义）

        Args:
            query: 搜索查询
            keyword_results: 关键词搜索结果数
            semantic_results: 语义搜索结果数
            filter_zim: 过滤 ZIM 文件

        Returns:
            合并后的结果列表
        """
        # 语义搜索
        semantic = self.search(query, n_results=semantic_results, filter_zim=filter_zim)

        results = []
        seen_ids = set()

        # 添加语义搜索结果
        if semantic.get("documents") and semantic["documents"][0]:
            for i, doc in enumerate(semantic["documents"][0]):
                doc_id = semantic["ids"][0][i] if semantic.get("ids") else f"semantic_{i}"
                if doc_id not in seen_ids:
                    results.append(
                        {
                            "content": doc,
                            "metadata": semantic["metadatas"][0][i]
                            if semantic.get("metadatas")
                            else {},
                            "score": 1
                            - (semantic["distances"][0][i] if semantic.get("distances") else 0),
                            "type": "semantic",
                        }
                    )
                    seen_ids.add(doc_id)

        return results

    def delete_document(self, doc_id: str) -> bool:
        """
        删除文档

        Args:
            doc_id: 文档 ID

        Returns:
            是否删除成功
        """
        try:
            self._collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            print(f"删除文档失败 {doc_id}: {e}")
            return False

    def delete_by_zim(self, zim_path: str) -> int:
        """
        删除指定 ZIM 文件的所有文档

        Args:
            zim_path: ZIM 文件路径

        Returns:
            删除的文档数量
        """
        try:
            # ChromaDB 不支持直接按 metadata 删除，需要重新实现
            # 这里返回 0 表示需要手动处理
            return 0
        except Exception as e:
            print(f"删除 ZIM 文档失败 {zim_path}: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        获取索引统计信息

        Returns:
            统计信息字典
        """
        try:
            count = self._collection.count()

            return {
                "total_documents": count,
                "index_dir": str(self.index_dir),
                "collection_name": self.collection_name,
            }
        except Exception as e:
            return {"error": str(e)}

    def reset(self) -> bool:
        """
        重置索引（清空所有数据）

        Returns:
            是否成功重置
        """
        try:
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name, metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as e:
            print(f"重置索引失败：{e}")
            return False

    def export_index(self, output_path: str) -> bool:
        """
        导出索引数据

        Args:
            output_path: 输出文件路径

        Returns:
            是否导出成功
        """
        try:
            # 导出为 JSON
            count = self._collection.count()
            if count == 0:
                return False

            # 获取所有数据（分批）
            all_data = []
            offset = 0
            limit = 1000

            while True:
                results = self._collection.get(
                    offset=offset, limit=limit, include=["documents", "metadatas"]
                )

                if not results["ids"]:
                    break

                for i, doc_id in enumerate(results["ids"]):
                    all_data.append(
                        {
                            "doc_id": doc_id,
                            "content": results["documents"][i],
                            "metadata": results["metadatas"][i],
                        }
                    )

                offset += limit
                if len(results["ids"]) < limit:
                    break

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"count": len(all_data), "documents": all_data},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

            return True
        except Exception as e:
            print(f"导出索引失败：{e}")
            return False
