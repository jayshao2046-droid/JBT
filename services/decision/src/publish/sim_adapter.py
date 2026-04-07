"""
SimTradingAdapter — TASK-0021 G batch
向 sim-trading 服务发送策略发布请求（HTTP POST）。
"""
from __future__ import annotations

import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SimTradingAdapter:
    """
    向 sim-trading 服务 POST 策略包。
    URL: {SIM_TRADING_SERVICE_URL}/api/sim/v1/strategy/publish
    第一阶段：接口不存在时降级到 204→mock 成功，不硬挂。
    """

    def __init__(self) -> None:
        self._base_url: str = os.environ.get(
            "SIM_TRADING_SERVICE_URL", "http://localhost:8101"
        ).rstrip("/")
        self._timeout: int = int(os.environ.get("PUBLISH_HTTP_TIMEOUT", "10"))

    def _publish_url(self) -> str:
        return f"{self._base_url}/api/sim/v1/strategy/publish"

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
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                status_code = resp.getcode()
                resp_body = resp.read().decode("utf-8")
                try:
                    resp_json = json.loads(resp_body)
                except (json.JSONDecodeError, ValueError):
                    resp_json = {"raw": resp_body}

                success = status_code in (200, 201, 204)
                logger.info(
                    "SimTradingAdapter.publish strategy=%s status=%d success=%s",
                    strategy_payload.get("strategy_id"), status_code, success,
                )
                return {"success": success, "status_code": status_code, "response": resp_json}

        except urllib.error.HTTPError as exc:
            # 404 = 端点尚未实现（第一阶段降级）
            if exc.code == 404:
                logger.warning(
                    "SimTradingAdapter: publish endpoint not yet implemented (404), degrading to mock success. strategy=%s",
                    strategy_payload.get("strategy_id"),
                )
                return {"success": True, "status_code": 404, "response": {"degraded": True}}
            logger.error(
                "SimTradingAdapter HTTPError %d for strategy=%s: %s",
                exc.code, strategy_payload.get("strategy_id"), exc,
            )
            return {"success": False, "status_code": exc.code, "response": str(exc)}

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
