"""OpenAI-compatible API client for online models (Qwen, DeepSeek, etc).

支持通义千问（DashScope）、DeepSeek 等兼容 OpenAI API 的在线模型。
"""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class OpenAICompatibleClient:
    """OpenAI-compatible API client for online models."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize OpenAI-compatible client.

        Args:
            base_url: API base URL. Defaults to ONLINE_MODEL_BASE_URL env var
            api_key: API key. Defaults to ONLINE_MODEL_API_KEY env var
        """
        self.base_url = (
            base_url or os.getenv("ONLINE_MODEL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        ).rstrip("/")
        self.api_key = api_key or os.getenv("ONLINE_MODEL_API_KEY", "")

        if not self.api_key:
            raise ValueError("API key is required. Set ONLINE_MODEL_API_KEY environment variable.")

        self._client = httpx.AsyncClient(timeout=httpx.Timeout(300.0))

    async def chat(
        self, model: str, messages: List[Dict[str, str]], timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Call OpenAI-compatible /chat/completions endpoint.

        Args:
            model: Model name (e.g., "qwen-coder-plus", "qwen-max")
            messages: List of message dicts with "role" and "content"
            timeout: Request timeout in seconds

        Returns:
            Dict containing:
                - content: Response text
                - model: Model name
                - total_duration: Total time in nanoseconds (estimated)
                - eval_count: Number of tokens evaluated
                - eval_duration: Evaluation time in nanoseconds (estimated)
                - error: Error message if request failed
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }

        try:
            self._client.timeout = httpx.Timeout(timeout)
            response = await self._client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Extract response content
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Extract usage info
            usage = data.get("usage", {})
            completion_tokens = usage.get("completion_tokens", 0)

            # Estimate durations (OpenAI API doesn't provide these)
            # Assume ~50 tokens/sec for estimation
            estimated_duration_ns = int(completion_tokens * 20_000_000)  # 20ms per token

            return {
                "content": content,
                "model": data.get("model", model),
                "total_duration": estimated_duration_ns,
                "eval_count": completion_tokens,
                "eval_duration": estimated_duration_ns,
            }

        except httpx.TimeoutException as exc:
            logger.warning(f"Online API request timeout for model {model}: {exc}")
            return {
                "error": f"Request timeout after {timeout}s",
                "model": model,
                "content": "",
            }

        except httpx.HTTPStatusError as exc:
            logger.error(f"Online API HTTP error for model {model}: {exc}")
            return {
                "error": f"HTTP {exc.response.status_code}: {exc.response.text}",
                "model": model,
                "content": "",
            }

        except httpx.RequestError as exc:
            logger.error(f"Online API request error for model {model}: {exc}")
            return {
                "error": f"Request failed: {str(exc)}",
                "model": model,
                "content": "",
            }

        except Exception as exc:
            logger.error(f"Unexpected error calling online API: {exc}", exc_info=True)
            return {
                "error": f"Unexpected error: {str(exc)}",
                "model": model,
                "content": "",
            }

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
