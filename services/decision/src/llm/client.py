"""Ollama HTTP client for model inference."""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class OllamaClient:
    """HTTP client for Ollama API."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama server URL. Defaults to OLLAMA_BASE_URL env var
                     or http://192.168.31.142:11434
        """
        self.base_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL", "http://192.168.31.142:11434")
        ).rstrip("/")
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(300.0))

    async def chat(
        self, model: str, messages: List[Dict[str, str]], timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Call Ollama /api/chat endpoint.

        Args:
            model: Model name (e.g., "deepcoder:14b")
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

            return {
                "content": data.get("message", {}).get("content", ""),
                "model": data.get("model", model),
                "total_duration": data.get("total_duration", 0),
                "eval_count": data.get("eval_count", 0),
                "eval_duration": data.get("eval_duration", 0),
            }

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
