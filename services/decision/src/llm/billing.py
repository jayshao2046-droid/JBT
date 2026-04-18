"""LLM 计费追踪器 — 记录所有模型调用的 Token 用量与费用。

单例模式，供 OpenAICompatibleClient / OllamaClient / HybridClient 自动上报。
支持按小时/天聚合，为看板和飞书通知提供数据源。

价格数据来源: MODEL_PRICES 环境变量（¥/1M tokens 人民币）
"""

import atexit
import json
import logging
import os
import threading
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_TZ_CST = timezone(timedelta(hours=8))


class LLMBillingRecord:
    """单次 LLM 调用记录。"""

    __slots__ = (
        "timestamp", "model", "component", "tier",
        "input_tokens", "output_tokens",
        "input_cost", "output_cost", "total_cost",
        "is_local", "fallback_from",
    )

    def __init__(
        self,
        model: str,
        component: str,
        input_tokens: int,
        output_tokens: int,
        input_cost: float,
        output_cost: float,
        tier: str = "主力",
        is_local: bool = False,
        fallback_from: str = "",
    ):
        self.timestamp = datetime.now(_TZ_CST)
        self.model = model
        self.component = component
        self.tier = tier
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.input_cost = input_cost
        self.output_cost = output_cost
        self.total_cost = input_cost + output_cost
        self.is_local = is_local
        self.fallback_from = fallback_from

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
            "component": self.component,
            "tier": self.tier,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "input_cost": round(self.input_cost, 6),
            "output_cost": round(self.output_cost, 6),
            "total_cost": round(self.total_cost, 6),
            "is_local": self.is_local,
            "fallback_from": self.fallback_from,
        }


class LLMBillingTracker:
    """LLM 计费追踪器（线程安全单例）。"""

    _instance: Optional["LLMBillingTracker"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "LLMBillingTracker":
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._initialized = False
                cls._instance = inst
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._records: List[LLMBillingRecord] = []
        self._data_lock = threading.Lock()
        self._prices = self._load_prices()
        self._daily_budget = float(os.getenv("DAILY_API_BUDGET", "10.0"))
        self._persist_dir = Path(
            os.getenv(
                "BILLING_DATA_DIR",
                os.path.join(os.path.dirname(__file__), "..", "..", "runtime", "billing"),
            )
        )
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        # JSONL 实时流水文件路径 — 每条记录立即追加
        self._records_jsonl = self._persist_dir / "billing_records.jsonl"
        # 注册进程退出时自动 flush
        atexit.register(self._atexit_flush)
        logger.info(
            "LLMBillingTracker 初始化完成，已加载 %d 个模型价格，日预算 ¥%.2f",
            len(self._prices), self._daily_budget,
        )

    # ------------------------------------------------------------------
    # 价格
    # ------------------------------------------------------------------

    def _load_prices(self) -> Dict[str, Dict[str, float]]:
        """从 MODEL_PRICES 环境变量加载价格表（¥/1M tokens）。"""
        raw = os.getenv("MODEL_PRICES", "")
        if not raw:
            logger.warning("MODEL_PRICES 未设置，计费将使用默认估算价格")
            return {}
        try:
            prices = json.loads(raw)
            if isinstance(prices, dict):
                return prices
        except json.JSONDecodeError:
            logger.error("MODEL_PRICES JSON 解析失败")
        return {}

    def get_price(self, model: str) -> Dict[str, float]:
        """获取模型单价（¥/1M tokens）。未知模型使用保守估算。"""
        if model in self._prices:
            return self._prices[model]
        # 未知在线模型给一个保守默认值
        return {"input": 1.0, "output": 3.0}

    def calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> tuple:
        """计算一次调用的费用。返回 (input_cost, output_cost)。"""
        price = self.get_price(model)
        input_cost = input_tokens * price["input"] / 1_000_000
        output_cost = output_tokens * price["output"] / 1_000_000
        return input_cost, output_cost

    # ------------------------------------------------------------------
    # 记录
    # ------------------------------------------------------------------

    def record(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        component: str = "unknown",
        tier: str = "主力",
        is_local: bool = False,
        fallback_from: str = "",
    ) -> LLMBillingRecord:
        """记录一次 LLM 调用。自动计算费用。"""
        if is_local:
            input_cost, output_cost = 0.0, 0.0
        else:
            input_cost, output_cost = self.calculate_cost(
                model, input_tokens, output_tokens
            )

        rec = LLMBillingRecord(
            model=model,
            component=component,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            tier=tier,
            is_local=is_local,
            fallback_from=fallback_from,
        )

        with self._data_lock:
            self._records.append(rec)

        # 实时持久化 — 每条记录立即追加到 JSONL 文件
        self._append_record_jsonl(rec)

        if not is_local and rec.total_cost > 0:
            logger.info(
                "💰 计费: %s [%s] in=%d out=%d ¥%.6f",
                model, component, input_tokens, output_tokens, rec.total_cost,
            )

        return rec

    def _append_record_jsonl(self, rec: LLMBillingRecord) -> None:
        """将单条记录追加写入 JSONL 流水文件（实时持久化）。"""
        try:
            with open(self._records_jsonl, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.error("JSONL 流水写入失败: %s", exc)

    def _atexit_flush(self) -> None:
        """进程退出时自动 flush 当前小时汇总。"""
        try:
            result = self.flush_hourly()
            if result:
                logger.info("进程退出前已自动 flush 计费数据: %s", result)
        except Exception as exc:
            logger.error("进程退出 flush 失败: %s", exc)

    # ------------------------------------------------------------------
    # 聚合查询
    # ------------------------------------------------------------------

    def get_hourly_summary(self, hour: Optional[datetime] = None) -> Dict[str, Any]:
        """获取指定小时的聚合统计。默认当前小时。"""
        now = hour or datetime.now(_TZ_CST)
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)

        with self._data_lock:
            records = [
                r for r in self._records
                if hour_start <= r.timestamp < hour_end
            ]

        return self._aggregate(records, hour_start, hour_end)

    def get_daily_summary(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """获取指定日的聚合统计。默认今天。"""
        now = date or datetime.now(_TZ_CST)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        with self._data_lock:
            records = [
                r for r in self._records
                if day_start <= r.timestamp < day_end
            ]

        summary = self._aggregate(records, day_start, day_end)
        summary["budget"] = self._daily_budget
        summary["budget_remaining"] = round(
            max(0, self._daily_budget - summary["total_cost"]), 6
        )
        summary["budget_usage_pct"] = round(
            summary["total_cost"] / self._daily_budget * 100
            if self._daily_budget > 0 else 0,
            2,
        )
        return summary

    def _aggregate(
        self,
        records: List[LLMBillingRecord],
        start: datetime,
        end: datetime,
    ) -> Dict[str, Any]:
        """对一批记录做聚合统计。"""
        by_model: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0,
            }
        )
        by_component: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"calls": 0, "total_cost": 0.0}
        )

        total_calls = 0
        total_input = 0
        total_output = 0
        total_cost = 0.0
        local_calls = 0

        for r in records:
            m = by_model[r.model]
            m["calls"] += 1
            m["input_tokens"] += r.input_tokens
            m["output_tokens"] += r.output_tokens
            m["input_cost"] += r.input_cost
            m["output_cost"] += r.output_cost
            m["total_cost"] += r.total_cost

            c = by_component[r.component]
            c["calls"] += 1
            c["total_cost"] += r.total_cost

            total_calls += 1
            total_input += r.input_tokens
            total_output += r.output_tokens
            total_cost += r.total_cost
            if r.is_local:
                local_calls += 1

        # 对浮点数做 round
        for v in by_model.values():
            for k in ("input_cost", "output_cost", "total_cost"):
                v[k] = round(v[k], 6)
        for v in by_component.values():
            v["total_cost"] = round(v["total_cost"], 6)

        return {
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "total_calls": total_calls,
            "local_calls": local_calls,
            "online_calls": total_calls - local_calls,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost": round(total_cost, 6),
            "by_model": dict(by_model),
            "by_component": dict(by_component),
        }

    # ------------------------------------------------------------------
    # 持久化
    # ------------------------------------------------------------------

    def flush_hourly(self, hour: Optional[datetime] = None) -> Optional[str]:
        """将指定小时的汇总写入 JSON 文件，返回文件路径。"""
        target = hour or datetime.now(_TZ_CST)
        summary = self.get_hourly_summary(target)
        if summary["total_calls"] == 0:
            return None

        filename = f"billing_{target.strftime('%Y%m%d_%H')}00.json"
        filepath = self._persist_dir / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            logger.info("计费数据已写入: %s", filepath)
            return str(filepath)
        except Exception as exc:
            logger.error("计费数据写入失败: %s", exc)
            return None

    def get_records_json(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近 N 条原始记录（用于 API / 看板）。"""
        with self._data_lock:
            recent = self._records[-limit:]
        return [r.to_dict() for r in recent]

    def cleanup_old_records(self, keep_hours: int = 48) -> int:
        """清理超过 N 小时的内存记录（保留磁盘文件）。"""
        cutoff = datetime.now(_TZ_CST) - timedelta(hours=keep_hours)
        with self._data_lock:
            before = len(self._records)
            self._records = [r for r in self._records if r.timestamp >= cutoff]
            removed = before - len(self._records)
        if removed > 0:
            logger.info("清理了 %d 条过期计费记录", removed)
        return removed


def get_billing_tracker() -> LLMBillingTracker:
    """获取全局计费追踪器实例。"""
    return LLMBillingTracker()
