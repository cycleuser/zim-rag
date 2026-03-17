"""RAG (检索增强生成) 核心引擎"""

import hashlib
from typing import List, Optional, Dict, Any, Generator
from dataclasses import dataclass, field
from pathlib import Path

from .zim_parser import ZIMParser, ZIMArticle
from .content_index import ContentIndex, IndexedDocument
from .llm_client import OllamaClient


@dataclass
class RAGContext:
    """RAG 上下文信息"""

    question: str
    contexts: List[str]
    sources: List[Dict[str, Any]]
    retrieval_time: float = 0.0


@dataclass
class RAGResponse:
    """RAG 响应"""

    answer: str
    context: RAGContext
    model: str
    generation_time: float = 0.0
    stream: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "question": self.context.question,
            "sources": self.context.sources,
            "model": self.model,
            "generation_time": self.generation_time,
            "context_count": len(self.context.contexts),
        }


class RAGEngine:
    """
    RAG (检索增强生成) 引擎

    整合 ZIM 解析、内容索引和大模型，实现基于本地知识库的问答系统。
    """

    def __init__(
        self,
        zim_paths: Optional[List[str]] = None,
        model: str = "llama3",
        ollama_host: str = "http://localhost:11434",
        index_dir: str = "./zimrag_index",
    ):
        """
        初始化 RAG 引擎

        Args:
            zim_paths: ZIM 文件路径列表
            model: Ollama 模型名称
            ollama_host: Ollama 服务地址
            index_dir: 索引存储目录
        """
        self.zim_paths = list(zim_paths) if zim_paths else []
        self.model = model
        self.index_dir = index_dir

        # 初始化组件
        self.parser = ZIMParser(self.zim_paths)
        self.index = ContentIndex(index_dir=index_dir)
        self.llm = OllamaClient(model=model, host=ollama_host)

        # 加载 ZIM 文件
        if self.zim_paths:
            self.parser.load_zims(self.zim_paths)

    def load_zim(self, zim_path: str) -> bool:
        """
        加载 ZIM 文件

        Args:
            zim_path: ZIM 文件路径

        Returns:
            是否加载成功
        """
        success = self.parser.load_zim(zim_path)
        if success and zim_path not in self.zim_paths:
            self.zim_paths.append(zim_path)
        return success

    def unload_zim(self, zim_path: str) -> bool:
        """卸载 ZIM 文件"""
        return self.parser.unload_zim(zim_path)

    def build_index(
        self,
        max_articles: int = 10000,
        chunk_size: int = 500,
        zim_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        构建内容索引

        Args:
            max_articles: 最大索引文章数
            chunk_size: 分块大小（字符数）
            zim_paths: 指定要索引的 ZIM 文件，None 表示所有

        Returns:
            索引构建统计信息
        """
        target_paths = zim_paths if zim_paths else self.zim_paths

        if not target_paths:
            return {"error": "没有已加载的 ZIM 文件"}

        # 确保 ZIM 文件已加载
        for path in target_paths:
            if path not in self.parser.files:
                self.parser.load_zim(path)

        stats = {
            "total_processed": 0,
            "total_indexed": 0,
            "total_chunks": 0,
            "errors": 0,
            "by_file": {},
        }

        documents = []

        for zim_path in target_paths:
            file_stats = {"processed": 0, "indexed": 0, "chunks": 0, "errors": 0}

            try:
                for i, article in enumerate(
                    self.parser.iter_articles(zim_path, limit=max_articles)
                ):
                    if stats["total_processed"] >= max_articles:
                        break

                    file_stats["processed"] += 1
                    stats["total_processed"] += 1

                    # 跳过太短的文章
                    if len(article.content) < 100:
                        continue

                    # 分块处理长文章
                    chunks = self._chunk_text(article.content, chunk_size)

                    for j, chunk in enumerate(chunks):
                        # 生成唯一 ID
                        doc_id = hashlib.md5(f"{zim_path}:{article.url}:{j}".encode()).hexdigest()

                        metadata = {
                            "title": article.title,
                            "url": article.url,
                            "zim_path": zim_path,
                            "chunk": j,
                            "total_chunks": len(chunks),
                        }

                        documents.append(
                            IndexedDocument(doc_id=doc_id, content=chunk, metadata=metadata)
                        )

                        file_stats["indexed"] += 1
                        file_stats["chunks"] += 1
                        stats["total_indexed"] += 1
                        stats["total_chunks"] += 1

                    # 每 1000 篇文章打印进度
                    if stats["total_processed"] % 1000 == 0:
                        print(f"已处理 {stats['total_processed']:,} 篇文章...")

            except Exception as e:
                file_stats["errors"] += 1
                stats["errors"] += 1
                print(f"索引 ZIM 文件 {zim_path} 时出错：{e}")

            stats["by_file"][Path(zim_path).name] = file_stats

        # 批量添加到索引
        if documents:
            print(f"正在添加 {len(documents):,} 个文档到索引...")
            results = self.index.add_documents(documents)
            successful = sum(1 for v in results.values() if v)
            print(f"成功添加 {successful:,} 个文档")

        return stats

    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        将文本分块

        Args:
            text: 输入文本
            chunk_size: 每块大小（字符数）

        Returns:
            文本块列表
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        current_chunk = []
        current_length = 0

        # 按句子分块
        sentences = text.replace("\n", " ").split(". ")

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_len = len(sentence) + 2  # +2 for ". "

            if current_length + sentence_len > chunk_size:
                if current_chunk:
                    chunks.append(". ".join(current_chunk) + ".")
                current_chunk = [sentence]
                current_length = sentence_len
            else:
                current_chunk.append(sentence)
                current_length += sentence_len

        if current_chunk:
            chunks.append(". ".join(current_chunk) + ".")

        return chunks

    def query(
        self,
        question: str,
        context_limit: int = 5,
        zim_paths: Optional[List[str]] = None,
        model: Optional[str] = None,
        stream: bool = False,
    ) -> RAGResponse | Generator[str, None, None]:
        """
        回答问题

        Args:
            question: 问题
            context_limit: 上下文数量限制
            zim_paths: 指定搜索的 ZIM 文件
            model: 使用的模型
            stream: 是否流式输出

        Returns:
            RAGResponse 或流式生成器
        """
        import time

        start_time = time.time()

        # 检索相关上下文
        results = self.index.search(
            query=question,
            n_results=context_limit * 2,  # 多检索一些用于过滤
            filter_zim=zim_paths,
        )

        contexts = []
        sources = []

        # 处理搜索结果
        if results.get("documents") and results["documents"][0]:
            seen_titles = set()

            for i, doc in enumerate(results["documents"][0]):
                if len(contexts) >= context_limit:
                    break

                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                title = metadata.get("title", "未知")

                # 去重（相同标题）
                if title not in seen_titles:
                    contexts.append(doc)
                    sources.append(
                        {
                            "title": title,
                            "zim_path": metadata.get("zim_path", ""),
                            "url": metadata.get("url", ""),
                        }
                    )
                    seen_titles.add(title)

        retrieval_time = time.time() - start_time

        # 构建上下文
        rag_context = RAGContext(
            question=question,
            contexts=contexts,
            sources=sources,
            retrieval_time=retrieval_time,
        )

        # 构建提示词
        prompt = self._build_prompt(question, contexts)

        # 生成回答
        gen_start = time.time()

        if stream:
            return self._stream_query(prompt, rag_context, model)

        answer = self.llm.generate(prompt, model=model)
        generation_time = time.time() - gen_start

        return RAGResponse(
            answer=answer,
            context=rag_context,
            model=model or self.model,
            generation_time=generation_time,
        )

    def _stream_query(
        self, prompt: str, context: RAGContext, model: Optional[str] = None
    ) -> Generator[str, None, None]:
        """流式查询"""
        for chunk in self.llm.generate(prompt, model=model, stream=True):
            yield chunk

    def _build_prompt(self, question: str, contexts: List[str]) -> str:
        """
        构建 RAG 提示词

        Args:
            question: 问题
            contexts: 上下文列表

        Returns:
            完整的提示词
        """
        if not contexts:
            return f"""请回答以下问题。如果你不知道答案，请诚实地说明。

问题：{question}

回答："""

        context_text = "\n\n".join([f"[相关资料 {i + 1}]\n{ctx}" for i, ctx in enumerate(contexts)])

        prompt = f"""基于以下知识资料回答问题。如果资料中不包含答案，请说明你不知道。
请引用相关资料来支持你的回答。

知识资料：
{context_text}

问题：{question}

请提供详细、准确的回答："""

        return prompt

    def chat(
        self,
        messages: List[Dict[str, str]],
        context_limit: int = 3,
        zim_paths: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> str:
        """
        聊天模式（带历史上下文）

        Args:
            messages: 消息历史
            context_limit: 上下文数量
            zim_paths: 指定 ZIM 文件
            model: 使用的模型

        Returns:
            回复内容
        """
        # 获取最后一条用户消息
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg["content"]
                break

        if not last_user_msg:
            return "请提供问题。"

        # 检索相关上下文
        results = self.index.search(
            query=last_user_msg, n_results=context_limit, filter_zim=zim_paths
        )

        contexts = []
        if results.get("documents") and results["documents"][0]:
            contexts = results["documents"][0][:context_limit]

        # 构建系统提示
        system_prompt = """你是一个基于本地知识库的智能助手。
请根据提供的知识资料回答用户问题。
如果资料中没有相关信息，请诚实地说明。
回答要准确、详细、有条理。"""

        # 构建用户消息
        if contexts:
            context_text = "\n\n".join([f"[资料 {i + 1}]\n{ctx}" for i, ctx in enumerate(contexts)])
            user_content = f"""基于以下知识资料：

{context_text}

请回答：{last_user_msg}"""
        else:
            user_content = last_user_msg

        # 构建消息列表
        chat_messages = [{"role": "system", "content": system_prompt}]

        # 添加历史消息（限制长度）
        for msg in messages[-6:]:  # 最近 6 条
            chat_messages.append(msg)

        chat_messages.append({"role": "user", "content": user_content})

        return self.llm.chat(chat_messages, model=model)

    def generate_document(
        self,
        topic: str,
        outline: Optional[List[str]] = None,
        context_limit: int = 10,
        zim_paths: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> str:
        """
        根据主题生成文档

        Args:
            topic: 文档主题
            outline: 大纲列表，None 表示自动生成
            context_limit: 上下文数量
            zim_paths: 指定 ZIM 文件
            model: 使用的模型

        Returns:
            生成的文档内容
        """
        # 如果没有大纲，先生成大纲
        if not outline:
            outline_prompt = f"""请为以下主题生成一个详细的文档大纲：

主题：{topic}

请提供包含主要章节和子章节的大纲，使用 Markdown 格式。"""

            outline_text = self.llm.generate(outline_prompt, model=model)
            # 简单解析大纲
            outline = [
                line.strip().lstrip("#").strip()
                for line in outline_text.split("\n")
                if line.strip() and not line.strip().startswith("```")
            ]

        # 检索相关上下文
        results = self.index.search(
            query=f"{topic} " + " ".join(outline),
            n_results=context_limit,
            filter_zim=zim_paths,
        )

        contexts = []
        if results.get("documents") and results["documents"][0]:
            contexts = results["documents"][0]

        # 生成文档
        doc_prompt = f"""请根据以下知识资料和大纲，撰写一篇完整的文档。

主题：{topic}

大纲：
{chr(10).join(outline)}

知识资料：
{chr(10).join(contexts[:5])}  # 限制上下文长度

要求：
1. 按照大纲结构组织内容
2. 内容准确、详细
3. 使用 Markdown 格式
4. 适当引用资料

请生成完整的文档："""

        return self.llm.generate(doc_prompt, model=model)

    def get_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        zim_stats = self.parser.get_stats()
        index_stats = self.index.get_stats()

        return {
            "zim_files": zim_stats,
            "index": index_stats,
            "model": self.model,
            "ollama_host": self.llm.host,
            "ollama_healthy": self.llm.check_health(),
        }
