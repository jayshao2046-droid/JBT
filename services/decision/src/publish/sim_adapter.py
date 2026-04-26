"""
SimTradingAdapter — TASK-0021 G batch
向 sim-trading 服务发送策略发布请求（HTTP POST）。
"""
from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict

from ..core.settings import get_settings

logger = logging.getLogger(__name__)


class SimTradingAdapter:
    """
    向 sim-trading 服务 POST 策略包。
    URL: {SIM_TRADING_SERVICE_URL}/api/v1/strategy/publish
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
    ) -> None:
        settings = get_settings()
        resolved_base_url = base_url or settings.sim_trading_url
        resolved_api_key = settings.sim_trading_api_key if api_key is None else api_key

        self._base_url = resolved_base_url.rstrip("/")
        self._api_key = (resolved_api_key or "").strip()
        self._timeout = settings.publish_http_timeout if timeout is None else timeout

    def _publish_url(self) -> str:
        return f"{self._base_url}/api/v1/strategy/publish"

    def _request_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        return headers

    def health_check(self) -> bool:
        """
        健康检查 sim-trading 服务。

        Returns:
            True if healthy, False otherwise
        """
        url = f"{self._base_url}/health"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.getcode() == 200
        except (urllib.error.HTTPError, urllib.error.URLError, Exception) as exc:
            logger.debug(f"Health check failed: {exc}")
            return False

    @staticmethod
    def _decode_payload(payload: bytes) -> dict[str, Any]:
        raw = payload.decode("utf-8", errors="replace")
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return {"raw": raw}

    def publish(self, strategy_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送策略包到 sim-trading。
        返回 {"success": bool, "status_code": int, "response": dict | str}
        """
        url = self._publish_url()
        body = json.dumps(strategy_payload, ensure_ascii=False).encode("utf-8")

        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers=self._request_headers(),
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                status_code = resp.getcode()
                resp_json = self._decode_payload(resp.read())

                success = status_code in (200, 201, 202, 204)
                logger.info(
                    "SimTradingAdapter.publish strategy=%s status=%d success=%s",
                    strategy_payload.get("strategy_id"), status_code, success,
                )
                return {"success": success, "status_code": status_code, "response": resp_json}

        except urllib.error.HTTPError as exc:
            response = self._decode_payload(exc.read()) or {"raw": str(exc)}
            logger.error(
                "SimTradingAdapter HTTPError %d for strategy=%s: %s",
                exc.code, strategy_payload.get("strategy_id"), exc,
            )
            return {"success": False, "status_code": exc.code, "response": response}

        except urllib.error.URLError as exc:
            logger.error(
                "SimTradingAdapter URLError for strategy=%s: %s",
                strategy_payload.get("strategy_id"), exc,
            )
            return {"success": False, "status_code": 0, "response": str(exc)}

        except Exception as exc:
            logger.error(
                "SimTradingAdapter unexpected error for strategy=%s: %s",
                strategy_payload.get("strategy_id"), exc,
            )
            return {"success": False, "status_code": 0, "response": str(exc)}
