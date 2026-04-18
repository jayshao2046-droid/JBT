"""策略绩效监控器 — 滑窗 Sharpe 衰减检测 + 策略池枯竭触发

职责：
1. 定期扫描 in_production 策略的近 N 日 Sharpe
2. Sharpe 低于阈值自动标记 degraded
3. 候选池低于最小阈值时触发策略补充信号
4. 归档时记录失败归因
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# 默认配置
DEFAULT_SHARPE_THRESHOLD = 0.3       # 低于此值标记 degraded
DEFAULT_SHARPE_WINDOW_DAYS = 30      # 滑窗天数
DEFAULT_MIN_CANDIDATE_POOL = 5       # 候选池最低策略数
DEFAULT_MAX_PRODUCTION = 20          # 最大在产策略数


class StrategyMonitor:
    """策略绩效监控器"""

    def __init__(
        self,
        sharpe_threshold: float = DEFAULT_SHARPE_THRESHOLD,
        window_days: int = DEFAULT_SHARPE_WINDOW_DAYS,
        min_candidate_pool: int = DEFAULT_MIN_CANDIDATE_POOL,
        max_production: int = DEFAULT_MAX_PRODUCTION,
        attribution_dir: str = "runtime/strategy_attribution",
    ):
        self.sharpe_threshold = sharpe_threshold
        self.window_days = window_days
        self.min_candidate_pool = min_candidate_pool
        self.max_production = max_production
        self.attribution_dir = Path(attribution_dir)
        self.attribution_dir.mkdir(parents=True, exist_ok=True)

    def check_strategy_health(
        self,
        strategy_id: str,
        recent_returns: list[float],
    ) -> dict[str, Any]:
        """检查单个策略健康状态

        Args:
            strategy_id: 策略 ID
            recent_returns: 近 N 日收益率列表

        Returns:
            {healthy, sharpe, action, reason}
        """
        if not recent_returns or len(recent_returns) < 5:
            return {
                "healthy": True,
                "sharpe": None,
                "action": "insufficient_data",
                "reason": f"数据不足（{len(recent_returns)}天），暂不评估",
            }

        import statistics
        mean_ret = statistics.mean(recent_returns)
        std_ret = statistics.stdev(recent_returns) if len(recent_returns) > 1 else 1e-9

        # 年化 Sharpe（假设日频）
        sharpe = (mean_ret / max(std_ret, 1e-9)) * (252 ** 0.5)

        if sharpe < self.sharpe_threshold:
            return {
                "healthy": False,
                "sharpe": round(sharpe, 4),
                "action": "degrade",
                "reason": f"滑窗 Sharpe={sharpe:.4f} < 阈值 {self.sharpe_threshold}",
            }

        return {
            "healthy": True,
            "sharpe": round(sharpe, 4),
            "action": "none",
            "reason": f"Sharpe={sharpe:.4f} 正常",
        }

    def check_pool_capacity(
        self,
        production_count: int,
        candidate_count: int,
    ) -> dict[str, Any]:
        """检查策略池容量

        Args:
            production_count: 当前在产策略数
            candidate_count: 当前候选策略数（backtest_confirmed 及以上）

        Returns:
            {needs_replenishment, production_count, candidate_count, reason}
        """
        needs = candidate_count < self.min_candidate_pool
        return {
            "needs_replenishment": needs,
            "production_count": production_count,
            "candidate_count": candidate_count,
            "max_production": self.max_production,
            "min_candidate_pool": self.min_candidate_pool,
            "reason": (
                f"候选池枯竭: {candidate_count} < 最小阈值 {self.min_candidate_pool}，需要触发新策略生成"
                if needs else
                f"候选池充足: {candidate_count} 个候选策略"
            ),
        }

    def record_archive_attribution(
        self,
        strategy_id: str,
        symbol: str,
        reason: str,
        final_sharpe: Optional[float] = None,
        max_drawdown: Optional[float] = None,
        days_in_production: Optional[int] = None,
        market_context: Optional[str] = None,
    ) -> Path:
        """记录策略归档归因

        Args:
            strategy_id: 策略 ID
            symbol: 品种代码
            reason: 归档原因（sharpe_decay / max_drawdown / market_mismatch / manual）
            final_sharpe: 最终 Sharpe
            max_drawdown: 最大回撤
            days_in_production: 在产天数
            market_context: 市场环境描述

        Returns:
            归因记录文件路径
        """
        attribution = {
            "strategy_id": strategy_id,
            "symbol": symbol,
            "reason": reason,
            "final_sharpe": final_sharpe,
            "max_drawdown": max_drawdown,
            "days_in_production": days_in_production,
            "market_context": market_context,
            "archived_at": datetime.now().isoformat(),
        }

        fp = self.attribution_dir / f"{strategy_id}.json"
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(attribution, f, ensure_ascii=False, indent=2)

        logger.info("策略归档归因已记录: %s → %s (原因: %s)", strategy_id, fp, reason)
        return fp

    def get_attribution(self, strategy_id: str) -> Optional[dict[str, Any]]:
        """查询策略归档归因"""
        fp = self.attribution_dir / f"{strategy_id}.json"
        if not fp.exists():
            return None
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)

    def scan_all_strategies(
        self,
        strategies: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """批量扫描所有在产策略健康状态

        Args:
            strategies: 策略列表，每个元素需包含 strategy_id 和 recent_returns

        Returns:
            {total, healthy, degraded, actions: [...]}
        """
        healthy_count = 0
        degraded_list = []
        actions = []

        for s in strategies:
            sid = s.get("strategy_id", "unknown")
            returns = s.get("recent_returns", [])
            result = self.check_strategy_health(sid, returns)

            if result["healthy"]:
                healthy_count += 1
            else:
                degraded_list.append(sid)
                actions.append({
                    "strategy_id": sid,
                    "symbol": s.get("symbol", ""),
                    "action": result["action"],
                    "sharpe": result["sharpe"],
                    "reason": result["reason"],
                })

        return {
            "scanned_at": datetime.now().isoformat(),
            "total": len(strategies),
            "healthy": healthy_count,
            "degraded": len(degraded_list),
            "degraded_ids": degraded_list,
            "actions": actions,
        }
