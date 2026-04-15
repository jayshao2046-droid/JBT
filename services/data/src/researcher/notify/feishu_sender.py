"""研究员独立飞书发送器 — 使用 RESEARCHER_FEISHU_WEBHOOK_URL"""

import os
import json
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from ..config import ResearcherConfig


class ResearcherFeishuSender:
    """研究员独立飞书发送器"""

    def __init__(self):
        self.webhook_url = os.getenv("RESEARCHER_FEISHU_WEBHOOK_URL", "")
        self.failure_log_path = Path("runtime/researcher/logs/notify_failures.jsonl")
        self.failure_log_path.parent.mkdir(parents=True, exist_ok=True)

    async def send_card(self, card: Dict[str, Any]) -> bool:
        """
        发送飞书卡片

        Args:
            card: 飞书卡片 JSON

        Returns:
            True 表示发送成功，False 表示失败
        """
        if not self.webhook_url:
            self._log_failure("飞书 webhook 未配置", card)
            return False

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self.webhook_url,
                    json=card,
                    timeout=ResearcherConfig.HTTP_TIMEOUT_MEDIUM
                )

                if resp.status_code == 200:
                    result = resp.json()
                    if result.get("code") == 0:
                        return True
                    else:
                        self._log_failure(f"飞书返回错误: {result}", card)
                        return False
                else:
                    self._log_failure(f"HTTP {resp.status_code}", card)
                    return False

        except Exception as e:
            self._log_failure(str(e), card)
            return False

    def _log_failure(self, error: str, card: Dict[str, Any]):
        """记录发送失败到本地日志"""
        failure_record = {
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "card_title": card.get("card", {}).get("header", {}).get("title", {}).get("content", "Unknown"),
            "card": card
        }

        with open(self.failure_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(failure_record, ensure_ascii=False) + "\n")
