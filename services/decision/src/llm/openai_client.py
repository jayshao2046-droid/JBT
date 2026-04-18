"""OpenAI-compatible API client with automatic 3-tier model fallback.

支持通义千问、DeepSeek、GPT、Claude 等兼容 OpenAI API 的在线模型。
内置三级降级链：主力 → 备选 → 降级，自动处理上游通道故障。
"""

import json as _json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_TIER_NAMES = ["主力", "备选", "降级"]


class OpenAICompatibleClient:
    """OpenAI-compatible API client with automatic model fallback."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        component: str = "unknown",
    ):
        self.base_url = (
            base_url or os.getenv("ONLINE_MODEL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        ).rstrip("/")
        self.api_key = api_key or os.getenv("ONLINE_MODEL_API_KEY", "")
        self._component = component

        if not self.api_key:
            raise ValueError("API key is required. Set ONLINE_MODEL_API_KEY environment variable.")

        self._client = httpx.AsyncClient(timeout=httpx.Timeout(300.0))
        self._fallback_map = self._load_fallback_map()

    def _load_fallback_map(self) -> Dict[str, List[str]]:
        """从 MODEL_FALLBACK_MAP 环境变量加载降级链 (JSON 格式)。"""
        raw = os.getenv("MODEL_FALLBACK_MAP", "")
        if not raw:
            return {}
        try:
            parsed = _json.loads(raw)
            if isinstance(parsed, dict):
                return {k: v for k, v in parsed.items() if isinstance(v, list)}
        except _json.JSONDecodeError:
            logger.warning("MODEL_FALLBACK_MAP JSON 解析失败，降级链未加载")
        return {}

    async def chat(
        self, model: str, messages: List[Dict[str, str]], timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Call /chat/completions with automatic fallback chain.

        Tries primary model first, then up to 2 fallbacks from MODEL_FALLBACK_MAP.
        Detects gateway errors disguised as HTTP 200 (e.g. NewCoin status "439").

        Returns:
            Dict with content/model/error etc. On fallback success, includes
            _fallback_from (original model) and _fallback_tier (tier name).
        """
        chain = [model] + self._fallback_map.get(model, [])
        last_error = None

        for i, current_model in enumerate(chain):
            tier = _TIER_NAMES[min(i, 2)]
            if i > 0:
                logger.warning(f"🔄 [{tier}] 切换到备选模型: {current_model}")

            result = await self._chat_single(current_model, messages, timeout)

            if "error" not in result and result.get("content"):
                if i > 0:
                    logger.info(f"✅ [{tier}] {current_model} 调用成功")
                    result["_fallback_from"] = model
                    result["_fallback_tier"] = tier

                # 记录计费（用请求模型名匹配价格表，非 API 返回的内部版本号）
                from .billing import get_billing_tracker
                get_billing_tracker().record(
                    model=current_model,
                    input_tokens=result.get("prompt_tokens", 0),
                    output_tokens=result.get("completion_tokens", 0),
                    component=self._component,
                    tier=tier,
                    fallback_from=model if i > 0 else "",
                )

                return result

            last_error = result.get("error", "empty response")
            logger.warning(f"❌ [{tier}] {current_model} 失败: {last_error}")

        logger.error(f"🚫 模型 {model} 及其全部备选链均失败")
        return {
            "error": f"All models failed. Last: {last_error}",
            "model": model,
            "content": "",
        }

    async def _chat_single(
        self, model: str, messages: List[Dict[str, str]], timeout: float
    ) -> Dict[str, Any]:
        """单次模型调用，不含降级逻辑。"""
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

            # 检测网关伪 200 错误 (NewCoin 返回 HTTP 200 + status "439" 等)
            gw_status = data.get("status")
            if gw_status and str(gw_status) != "200":
                error_msg = data.get("msg", f"upstream error {gw_status}")
                return {
                    "error": f"Gateway [{gw_status}]: {error_msg[:200]}",
                    "model": model,
                    "content": "",
                }

            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                return {
                    "error": "Empty response content",
                    "model": model,
                    "content": "",
                }

            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            estimated_duration_ns = int(completion_tokens * 20_000_000)

            return {
                "content": content,
                "model": data.get("model", model),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_duration": estimated_duration_ns,
                "eval_count": completion_tokens,
                "eval_duration": estimated_duration_ns,
            }

        except httpx.TimeoutException as exc:
            return {
                "error": f"Request timeout after {timeout}s",
                "model": model,
                "content": "",
            }

        except httpx.HTTPStatusError as exc:
            return {
                "error": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}",
                "model": model,
                "content": "",
            }

        except httpx.RequestError as exc:
            return {
                "error": f"Request failed: {str(exc)}",
                "model": model,
                "content": "",
            }

        except Exception as exc:
            logger.error(f"Unexpected error calling {model}: {exc}", exc_info=True)
            return {
                "error": f"Unexpected error: {str(exc)}",
                "model": model,
                "content": "",
            }

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
