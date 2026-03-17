"""本地 Ollama 大模型客户端"""

import requests
import json
from typing import Optional, List, Dict, Generator, Any
from dataclasses import dataclass


@dataclass
class ModelInfo:
    """模型信息"""

    name: str
    size: int
    digest: str
    modified_at: str


@dataclass
class GenerateResponse:
    """生成响应"""

    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None


class OllamaClient:
    """
    Ollama API 客户端

    提供与大模型的交互接口，支持文本生成、流式输出、模型管理等功能。
    """

    def __init__(
        self,
        model: str = "llama3",
        host: str = "http://localhost:11434",
        timeout: int = 120,
    ):
        """
        初始化 Ollama 客户端

        Args:
            model: 默认使用的模型名称
            host: Ollama 服务地址
            timeout: 请求超时时间（秒）
        """
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
        options: Optional[Dict] = None,
    ) -> str | Generator[str, None, None]:
        """
        生成文本响应

        Args:
            prompt: 提示词
            model: 使用的模型，None 表示使用默认模型
            stream: 是否流式输出
            options: 生成选项（temperature, top_p, num_predict 等）

        Returns:
            生成的文本或生成器
        """
        url = f"{self.host}/api/generate"

        payload = {"model": model or self.model, "prompt": prompt, "stream": stream}

        if options:
            payload["options"] = options

        if stream:
            return self._stream_generate(url, payload)

        try:
            response = self._session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"无法连接到 Ollama 服务 ({self.host})。请确保 Ollama 正在运行。"
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(f"请求超时 ({self.timeout}秒)")
        except Exception as e:
            raise RuntimeError(f"生成失败：{e}")

    def _stream_generate(self, url: str, payload: dict) -> Generator[str, None, None]:
        """流式生成"""
        try:
            response = self._session.post(
                url, json=payload, timeout=self.timeout, stream=True
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("response"):
                            yield data["response"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"无法连接到 Ollama 服务 ({self.host})")
        except Exception as e:
            raise RuntimeError(f"流式生成失败：{e}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        options: Optional[Dict] = None,
    ) -> str | Generator[str, None, None]:
        """
        聊天模式生成

        Args:
            messages: 消息列表，每项包含 {"role": "user/assistant", "content": "..."}
            model: 使用的模型
            stream: 是否流式输出
            options: 生成选项

        Returns:
            生成的回复或生成器
        """
        url = f"{self.host}/api/chat"

        payload = {"model": model or self.model, "messages": messages, "stream": stream}

        if options:
            payload["options"] = options

        if stream:
            return self._stream_chat(url, payload)

        try:
            response = self._session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            raise RuntimeError(f"聊天生成失败：{e}")

    def _stream_chat(self, url: str, payload: dict) -> Generator[str, None, None]:
        """流式聊天"""
        try:
            response = self._session.post(
                url, json=payload, timeout=self.timeout, stream=True
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("message", {}).get("content"):
                            yield data["message"]["content"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            raise RuntimeError(f"流式聊天失败：{e}")

    def list_models(self) -> List[ModelInfo]:
        """
        列出可用模型

        Returns:
            模型信息列表
        """
        url = f"{self.host}/api/tags"

        try:
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            models = []
            for m in data.get("models", []):
                models.append(
                    ModelInfo(
                        name=m.get("name", ""),
                        size=m.get("size", 0),
                        digest=m.get("digest", ""),
                        modified_at=m.get("modified_at", ""),
                    )
                )
            return models
        except Exception as e:
            raise RuntimeError(f"获取模型列表失败：{e}")

    def check_health(self) -> bool:
        """
        检查 Ollama 服务是否可用

        Returns:
            是否可用
        """
        try:
            response = self._session.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def pull_model(self, name: str) -> Generator[Dict, None, None]:
        """
        拉取模型

        Args:
            name: 模型名称

        Yields:
            下载进度信息
        """
        url = f"{self.host}/api/pull"
        payload = {"name": name, "stream": True}

        try:
            response = self._session.post(url, json=payload, timeout=None, stream=True)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            raise RuntimeError(f"拉取模型失败：{e}")

    def delete_model(self, name: str) -> bool:
        """
        删除模型

        Args:
            name: 模型名称

        Returns:
            是否成功删除
        """
        url = f"{self.host}/api/delete"
        payload = {"name": name}

        try:
            response = self._session.delete(url, json=payload, timeout=30)
            return response.status_code == 200
        except Exception:
            return False

    def embed(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        生成文本嵌入向量

        Args:
            text: 输入文本
            model: 嵌入模型，None 表示使用默认模型

        Returns:
            嵌入向量
        """
        url = f"{self.host}/api/embeddings"
        payload = {"model": model or self.model, "prompt": text}

        try:
            response = self._session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", [])
        except Exception as e:
            raise RuntimeError(f"生成嵌入失败：{e}")

    def get_model_info(self, name: str) -> Dict[str, Any]:
        """
        获取模型详细信息

        Args:
            name: 模型名称

        Returns:
            模型信息字典
        """
        url = f"{self.host}/api/show"
        payload = {"name": name}

        try:
            response = self._session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"获取模型信息失败：{e}")
