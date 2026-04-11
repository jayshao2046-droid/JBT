"""邮件+看板 YAML 策略导入 — TASK-0063 CF2
支持从邮件正文提取 YAML 策略块、或看板直传 YAML 文件导入策略。
"""
from __future__ import annotations

import re
import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from .yaml_importer import parse_yaml_strategy
from .strategy_importer import import_strategy, get_import_repository

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))

_YAML_BLOCK_RE = re.compile(
    r"```yaml\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)


@dataclass
class ImportResult:
    import_id: str
    channel: str  # email / dashboard
    status: str  # success / failed / partial
    created_at: str
    strategy_ids: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    raw_yaml_count: int = 0


class EmailImporter:
    """邮件 / 看板通道策略导入器。"""

    def __init__(self) -> None:
        self._results: dict[str, ImportResult] = {}

    # ------------------------------------------------------------------
    # public
    # ------------------------------------------------------------------

    def import_from_email(
        self, subject: str, body: str, sender: str
    ) -> ImportResult:
        """从邮件 body 中提取 ```yaml``` 代码块并逐个导入。"""
        blocks = self._extract_yaml_blocks(body)
        result = self._make_result("email", len(blocks))

        if not blocks:
            result.status = "failed"
            result.errors.append("邮件正文中未找到 YAML 代码块")
            self._results[result.import_id] = result
            return result

        for idx, blk in enumerate(blocks, 1):
            sid, err = self._safe_import_one(blk)
            if sid:
                result.strategy_ids.append(sid)
            if err:
                result.errors.append(f"块#{idx}: {err}")

        result.status = self._resolve_status(result)
        self._results[result.import_id] = result
        logger.info(
            "email import %s from=%s subject=%s status=%s ids=%s",
            result.import_id, sender, subject,
            result.status, result.strategy_ids,
        )
        return result

    def import_from_dashboard(self, yaml_content: str) -> ImportResult:
        """看板直传 YAML 内容导入。"""
        result = self._make_result("dashboard", 1)

        if not yaml_content or not yaml_content.strip():
            result.status = "failed"
            result.raw_yaml_count = 0
            result.errors.append("YAML 内容为空")
            self._results[result.import_id] = result
            return result

        sid, err = self._safe_import_one(yaml_content)
        if sid:
            result.strategy_ids.append(sid)
        if err:
            result.errors.append(err)

        result.status = self._resolve_status(result)
        self._results[result.import_id] = result
        return result

    def get_result(self, import_id: str) -> Optional[ImportResult]:
        return self._results.get(import_id)

    def list_results(self, channel: Optional[str] = None) -> list[ImportResult]:
        if channel is None:
            return list(self._results.values())
        return [r for r in self._results.values() if r.channel == channel]

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_yaml_blocks(text: str) -> list[str]:
        """用 regex 提取 ```yaml ... ``` 块。"""
        return [m.group(1).strip() for m in _YAML_BLOCK_RE.finditer(text)]

    def _safe_import_one(
        self, yaml_str: str
    ) -> tuple[Optional[str], Optional[str]]:
        """返回 (strategy_id, None) 或 (None, error_msg)。"""
        try:
            data = parse_yaml_strategy(yaml_str)
        except (ValueError, ImportError) as exc:
            return None, str(exc)

        result = import_strategy(data, repo=get_import_repository())
        if result["status"] in ("imported", "validated", "duplicate"):
            return result["strategy_id"], None
        # validation_failed or other
        errs = result.get("validation_errors") or [result.get("message", "导入失败")]
        return None, "; ".join(errs)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_result(channel: str, raw_count: int) -> ImportResult:
        return ImportResult(
            import_id=str(uuid.uuid4()),
            channel=channel,
            status="pending",
            created_at=datetime.now(_TZ_CST).isoformat(),
            raw_yaml_count=raw_count,
        )

    @staticmethod
    def _resolve_status(r: ImportResult) -> str:
        if r.strategy_ids and not r.errors:
            return "success"
        if r.strategy_ids and r.errors:
            return "partial"
        return "failed"
