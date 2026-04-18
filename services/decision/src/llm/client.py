"""Ollama HTTP client for model inference.

TASK-0083: 必要时增加 data 拉取辅助方法（当前无需修改）。
"""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class OllamaClient:
    """HTTP client for Ollama API."""

    def __init__(self, base_url: Optional[str] = None, component: str = "unknown"):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama server URL. Defaults to OLLAMA_BASE_URL env var
                     or http://192.168.31.142:11434
            component: Component name for billing tracking
        """
        self.base_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL", "http://192.168.31.142:11434")
        ).rstrip("/")
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(300.0))
        self._component = component

    async def chat(
        self, model: str, messages: List[Dict[str, str]], timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Call Ollama /api/chat endpoint.

        Args:
            model: Model name (e.g., "qwen3:14b")
            messages: List of message dicts with "role" and "content"
            timeout: Request timeout in seconds

        Returns:
            Dict containing:
                - content: Response text
                - model: Model name
                - total_duration: Total time in nanoseconds
                - eval_count: Number of tokens evaluated
                - eval_duration: Evaluation time in nanoseconds
                - error: Error message if request failed
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": 0,  # Unload model immediately after response
        }

        try:
            self._client.timeout = httpx.Timeout(timeout)
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            result = {
                "content": data.get("message", {}).get("content", ""),
                "model": data.get("model", model),
                "prompt_eval_count": data.get("prompt_eval_count", 0),
                "total_duration": data.get("total_duration", 0),
                "eval_count": data.get("eval_count", 0),
                "eval_duration": data.get("eval_duration", 0),
            }

            # 记录计费（本地调用，费用=0）
            from .billing import get_billing_tracker
            get_billing_tracker().record(
                model=model,
                input_tokens=result["prompt_eval_count"],
                output_tokens=result["eval_count"],
                component=self._component,
                is_local=True,
            )

            return result

        except httpx.TimeoutException as exc:
            logger.warning(f"Ollama request timeout for model {model}: {exc}")
            return {
                "error": f"Request timeout after {timeout}s",
                "model": model,
                "content": "",
            }

        except httpx.HTTPStatusError as exc:
            logger.error(f"Ollama HTTP error for model {model}: {exc}")
            return {
                "error": f"HTTP {exc.response.status_code}: {exc.response.text}",
                "model": model,
                "content": "",
            }

        except httpx.RequestError as exc:
            logger.error(f"Ollama request error for model {model}: {exc}")
            return {
                "error": f"Request failed: {str(exc)}",
                "model": model,
                "content": "",
            }

        except Exception as exc:
            logger.error(f"Unexpected error calling Ollama: {exc}", exc_info=True)
            return {
                "error": f"Unexpected error: {str(exc)}",
                "model": model,
                "content": "",
            }

    async def list_models(self) -> Dict[str, Any]:
        """
        List available models from Ollama.

        Returns:
            Dict containing:
                - models: List of model dicts
                - error: Error message if request failed
        """
        url = f"{self.base_url}/api/tags"

        try:
            response = await self._client.get(url)
            response.raise_for_status()
            data = response.json()
            return {"models": data.get("models", [])}

        except Exception as exc:
            logger.error(f"Failed to list models: {exc}")
            return {"error": str(exc), "models": []}

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "OllamaClient":
        """P1-4 修复：支持上下文管理器（async with OllamaClient() as c）。"""
        return self

    async def __aexit__(self, *_: object) -> None:
        """P1-4 修复：退出时自动关闭 HTTP 客户端。"""
        await self.close()


class HybridClient:
    """Ollama 优先，超时/错误自动降级到在线 API（省钱又可靠）。

    正常情况走本地 Ollama（免费），Ollama 超时或宕机时自动透明切换
    到在线 API，调用方无感知。在线客户端 lazy-init，不用就不初始化。
    """

    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        fallback_model: Optional[str] = None,
        component: str = "unknown",
    ):
        self._component = component
        self.ollama = ollama_client or OllamaClient(component=component)
        # 确保内部 Ollama 客户端继承组件名
        self.ollama._component = component
        self._online = None  # lazy init
        self.fallback_model = (
            fallback_model
            or os.getenv("ONLINE_FALLBACK_MODEL", "gpt-5.4")
        )

    @property
    def online(self):
        if self._online is None:
            from .openai_client import OpenAICompatibleClient
            self._online = OpenAICompatibleClient(component=self._component)
            logger.info(f"HybridClient: 在线降级客户端已初始化 → {self.fallback_model}")
        return self._online

    async def chat(
        self, model: str, messages: List[Dict[str, str]], timeout: float = 300.0
    ) -> Dict[str, Any]:
        result = await self.ollama.chat(model, messages, timeout=timeout)
        if not result.get("error"):
            return result

        ollama_error = result["error"]
        logger.warning(
            f"Ollama 失败 ({ollama_error})，自动降级到在线 API: {self.fallback_model}"
        )
        online_result = await self.online.chat(
            self.fallback_model, messages, timeout=timeout
        )
        online_result["_ollama_fallback"] = True
        online_result["_ollama_error"] = ollama_error
        return online_result

    async def close(self):
        await self.ollama.close()
        if self._online is not None:
            await self._online.close()

    async def __aenter__(self) -> "HybridClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
