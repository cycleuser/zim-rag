"""ZIM 文件解析器模块"""

import os
import hashlib
from dataclasses import dataclass, field
from typing import Iterator, Optional, List
from pathlib import Path


@dataclass
class ZIMArticle:
    """ZIM 文章数据模型"""

    title: str
    content: str
    url: str
    zim_path: str
    word_count: int = field(init=False)

    def __post_init__(self):
        self.word_count = len(self.content.split())


@dataclass
class ZIMFile:
    """ZIM 文件信息"""

    path: str
    name: str
    article_count: int
    size_bytes: int
    is_loaded: bool = False


class ZIMParser:
    """
    ZIM 文件解析器

    支持加载多个 ZIM 文件，提供内容搜索和文章遍历功能。
    使用 zimfs 或 libzim 作为底层解析库。
    """

    def __init__(self, zim_paths: Optional[List[str]] = None):
        self.zim_paths = list(zim_paths) if zim_paths else []
        self.files: dict[str, ZIMFile] = {}
        self._zim_objects: dict[str, any] = {}

    def load_zim(self, zim_path: str) -> bool:
        """
        加载单个 ZIM 文件

        Args:
            zim_path: ZIM 文件路径

        Returns:
            是否加载成功
        """
        if not os.path.exists(zim_path):
            print(f"ZIM 文件不存在：{zim_path}")
            return False

        zim_path = os.path.abspath(zim_path)

        if zim_path in self.files:
            print(f"ZIM 文件已加载：{zim_path}")
            return True

        try:
            # 尝试使用 zimfs
            try:
                import zimfs

                zim_file = zimfs.ZIMFile(zim_path)
                article_count = len(list(zim_file.each()))
            except ImportError:
                # 尝试使用 libzim
                try:
                    from zimscraperlib.zim import Archive

                    zim_file = Archive(zim_path)
                    article_count = zim_file.entry_count
                except ImportError:
                    print("警告：未找到 zimfs 或 libzim，使用模拟模式")
                    article_count = 0
                    zim_file = None

            self.files[zim_path] = ZIMFile(
                path=zim_path,
                name=os.path.basename(zim_path),
                article_count=article_count,
                size_bytes=os.path.getsize(zim_path),
                is_loaded=(zim_file is not None),
            )

            if zim_file is not None:
                self._zim_objects[zim_path] = zim_file

            self.zim_paths.append(zim_path)
            print(f"已加载 ZIM 文件：{zim_path} ({article_count:,} 篇文章)")
            return True

        except Exception as e:
            print(f"加载 ZIM 文件失败 {zim_path}: {e}")
            return False

    def load_zims(self, zim_paths: List[str]) -> dict[str, bool]:
        """
        批量加载 ZIM 文件

        Args:
            zim_paths: ZIM 文件路径列表

        Returns:
            {路径：是否成功} 的字典
        """
        results = {}
        for path in zim_paths:
            results[path] = self.load_zim(path)
        return results

    def iter_articles(
        self, zim_path: Optional[str] = None, limit: Optional[int] = None
    ) -> Iterator[ZIMArticle]:
        """
        遍历 ZIM 文件中的文章

        Args:
            zim_path: 指定 ZIM 文件路径，None 表示所有已加载文件
            limit: 限制返回文章数量

        Yields:
            ZIMArticle 对象
        """
        target_paths = [zim_path] if zim_path else self.zim_paths
        count = 0

        for path in target_paths:
            if path not in self._zim_objects:
                continue

            zim_obj = self._zim_objects[path]

            try:
                # 使用 zimfs 遍历
                if hasattr(zim_obj, "each"):
                    for entry in zim_obj.each():
                        if limit and count >= limit:
                            return

                        try:
                            article = ZIMArticle(
                                title=entry.title,
                                content=entry.content,
                                url=entry.path,
                                zim_path=path,
                            )
                            yield article
                            count += 1
                        except Exception:
                            continue

                # 使用 libzim 遍历
                elif hasattr(zim_obj, "iter_entries"):
                    for entry in zim_obj.iter_entries():
                        if limit and count >= limit:
                            return

                        try:
                            content = entry.get_item().content.decode(
                                "utf-8", errors="ignore"
                            )
                            article = ZIMArticle(
                                title=entry.title,
                                content=content,
                                url=entry.path,
                                zim_path=path,
                            )
                            yield article
                            count += 1
                        except Exception:
                            continue
            except Exception as e:
                print(f"遍历 ZIM 文件 {path} 时出错：{e}")

    def search_content(
        self, query: str, zim_paths: Optional[List[str]] = None, limit: int = 20
    ) -> List[ZIMArticle]:
        """
        在 ZIM 文件中搜索内容

        Args:
            query: 搜索关键词
            zim_paths: 指定搜索的 ZIM 文件，None 表示所有
            limit: 限制返回结果数量

        Returns:
            ZIMArticle 列表
        """
        target_paths = zim_paths if zim_paths else self.zim_paths
        results = []

        for path in target_paths:
            if path not in self._zim_objects:
                continue

            zim_obj = self._zim_objects[path]
            query_lower = query.lower()

            try:
                # 遍历搜索
                for article in self.iter_articles(path, limit=limit * 2):
                    if len(results) >= limit:
                        break

                    # 标题或内容匹配
                    if (
                        query_lower in article.title.lower()
                        or query_lower in article.content.lower()
                    ):
                        results.append(article)

            except Exception as e:
                print(f"搜索 ZIM 文件 {path} 时出错：{e}")

        return results

    def get_article(self, url: str, zim_path: str) -> Optional[ZIMArticle]:
        """
        获取指定 URL 的文章

        Args:
            url: 文章 URL
            zim_path: ZIM 文件路径

        Returns:
            ZIMArticle 或 None
        """
        if zim_path not in self._zim_objects:
            return None

        zim_obj = self._zim_objects[zim_path]

        try:
            if hasattr(zim_obj, "get_content"):
                content = zim_obj.get_content(url)
                title = url.split("/")[-1].replace("_", " ")
                return ZIMArticle(
                    title=title,
                    content=content.decode("utf-8", errors="ignore"),
                    url=url,
                    zim_path=zim_path,
                )
        except Exception as e:
            print(f"获取文章失败 {url}: {e}")

        return None

    def get_stats(self) -> dict:
        """
        获取已加载 ZIM 文件的统计信息

        Returns:
            统计信息字典
        """
        total_articles = sum(f.article_count for f in self.files.values())
        total_size = sum(f.size_bytes for f in self.files.values())

        return {
            "loaded_files": len(self.files),
            "total_articles": total_articles,
            "total_size_bytes": total_size,
            "total_size_gb": round(total_size / (1024**3), 2),
            "files": [
                {
                    "name": f.name,
                    "path": f.path,
                    "articles": f.article_count,
                    "size_gb": round(f.size_bytes / (1024**3), 2),
                    "loaded": f.is_loaded,
                }
                for f in self.files.values()
            ],
        }

    def unload_zim(self, zim_path: str) -> bool:
        """
        卸载 ZIM 文件

        Args:
            zim_path: ZIM 文件路径

        Returns:
            是否成功卸载
        """
        if zim_path not in self.files:
            return False

        try:
            if zim_path in self._zim_objects:
                del self._zim_objects[zim_path]
            if zim_path in self.files:
                del self.files[zim_path]
            if zim_path in self.zim_paths:
                self.zim_paths.remove(zim_path)
            return True
        except Exception:
            return False
