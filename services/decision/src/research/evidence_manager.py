"""证据管理器 — TASK-0127

管理策略的完整证据链：生成、调优、本地回测、TqSdk回测、评分报告。
负责策略的评分分桶迁移与证据文件归档。

证据目录结构：
{score_bucket}/{symbol}/{strategy_name}/
├── strategy.yaml
└── reports/
    ├── generation_report.json
    ├── optimization_report.json
    ├── local_backtest_report.json
    ├── tqsdk_backtest_report.json
    └── evaluator_report.json
"""
from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EvidenceManager:
    """证据管理器"""

    # 评分分桶映射
    SCORE_BUCKETS = {
        "fused": "熔断",
        "below_60": "小于60分",
        "60_69": "60-69",
        "70_79": "70-79",
        "80_89": "80-89",
        "90_100": "90-100",
    }

    def __init__(self, ranked_root: str | Path):
        """初始化证据管理器

        Args:
            ranked_root: 评分归档根目录（如 services/decision/strategies/llm_ranked）
        """
        self.ranked_root = Path(ranked_root)
        if not self.ranked_root.exists():
            raise ValueError(f"评分归档根目录不存在: {self.ranked_root}")

    def save_generation_report(
        self,
        symbol: str,
        strategy_name: str,
        report: dict[str, Any],
    ) -> Path:
        """保存生成报告

        Args:
            symbol: 品种代码
            strategy_name: 策略名称
            report: 生成报告内容

        Returns:
            报告文件路径
        """
        return self._save_report(
            symbol=symbol,
            strategy_name=strategy_name,
            report_type="generation",
            report=report,
        )

    def save_optimization_report(
        self,
        symbol: str,
        strategy_name: str,
        report: dict[str, Any],
    ) -> Path:
        """保存调优报告"""
        return self._save_report(
            symbol=symbol,
            strategy_name=strategy_name,
            report_type="optimization",
            report=report,
        )

    def save_local_backtest_report(
        self,
        symbol: str,
        strategy_name: str,
        report: dict[str, Any],
    ) -> Path:
        """保存本地回测报告"""
        return self._save_report(
            symbol=symbol,
            strategy_name=strategy_name,
            report_type="local_backtest",
            report=report,
        )

    def save_tqsdk_backtest_report(
        self,
        symbol: str,
        strategy_name: str,
        report: dict[str, Any],
    ) -> Path:
        """保存 TqSdk 回测报告"""
        return self._save_report(
            symbol=symbol,
            strategy_name=strategy_name,
            report_type="tqsdk_backtest",
            report=report,
        )

    def save_evaluator_report(
        self,
        symbol: str,
        strategy_name: str,
        report: dict[str, Any],
    ) -> Path:
        """保存评分报告"""
        return self._save_report(
            symbol=symbol,
            strategy_name=strategy_name,
            report_type="evaluator",
            report=report,
        )

    def move_to_bucket(
        self,
        yaml_path: str | Path,
        symbol: str,
        strategy_name: str,
        score: int,
        is_fused: bool = False,
    ) -> Path:
        """将策略迁移到对应评分目录

        Args:
            yaml_path: 策略 YAML 文件路径
            symbol: 品种代码
            strategy_name: 策略名称
            score: 评分（0-100）
            is_fused: 是否熔断

        Returns:
            最终存储路径
        """
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"策略 YAML 不存在: {yaml_path}")

        # 确定目标分桶
        bucket_name = self._get_bucket_name(score, is_fused)
        target_dir = self.ranked_root / bucket_name / symbol / strategy_name
        target_dir.mkdir(parents=True, exist_ok=True)

        # 复制 YAML 文件
        target_yaml = target_dir / "strategy.yaml"
        shutil.copy2(yaml_path, target_yaml)
        logger.info(f"策略 YAML 已复制: {target_yaml}")

        # 创建 reports 目录（如果不存在）
        reports_dir = target_dir / "reports"
        reports_dir.mkdir(exist_ok=True)

        logger.info(f"✅ 策略已迁移到评分目录: {target_dir}")
        return target_dir

    def get_evidence_summary(
        self,
        symbol: str,
        strategy_name: str,
        score: int,
        is_fused: bool = False,
    ) -> dict[str, Any]:
        """获取策略的完整证据摘要

        Args:
            symbol: 品种代码
            strategy_name: 策略名称
            score: 评分
            is_fused: 是否熔断

        Returns:
            证据摘要字典
        """
        bucket_name = self._get_bucket_name(score, is_fused)
        strategy_dir = self.ranked_root / bucket_name / symbol / strategy_name
        reports_dir = strategy_dir / "reports"

        summary = {
            "symbol": symbol,
            "strategy_name": strategy_name,
            "score": score,
            "is_fused": is_fused,
            "bucket": bucket_name,
            "storage_path": str(strategy_dir),
            "reports": {},
        }

        # 检查各报告文件是否存在
        report_types = [
            "generation",
            "optimization",
            "local_backtest",
            "tqsdk_backtest",
            "evaluator",
        ]

        for report_type in report_types:
            report_file = reports_dir / f"{report_type}_report.json"
            if report_file.exists():
                try:
                    with open(report_file, "r", encoding="utf-8") as f:
                        summary["reports"][report_type] = json.load(f)
                except Exception as e:
                    logger.warning(f"读取报告失败 {report_file}: {e}")
                    summary["reports"][report_type] = {"error": str(e)}
            else:
                summary["reports"][report_type] = None

        return summary

    def _save_report(
        self,
        symbol: str,
        strategy_name: str,
        report_type: str,
        report: dict[str, Any],
    ) -> Path:
        """保存报告到临时目录（后续通过 move_to_bucket 迁移）

        Args:
            symbol: 品种代码
            strategy_name: 策略名称
            report_type: 报告类型
            report: 报告内容

        Returns:
            报告文件路径
        """
        # 临时存储在 llm_generated 目录下
        temp_dir = self.ranked_root.parent / "llm_generated" / symbol / strategy_name / "reports"
        temp_dir.mkdir(parents=True, exist_ok=True)

        report_file = temp_dir / f"{report_type}_report.json"

        # 添加时间戳
        report_with_meta = {
            **report,
            "saved_at": datetime.now().isoformat(),
            "report_type": report_type,
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_with_meta, f, ensure_ascii=False, indent=2)

        logger.debug(f"报告已保存: {report_file}")
        return report_file

    def _get_bucket_name(self, score: int, is_fused: bool) -> str:
        """根据评分确定分桶名称

        Args:
            score: 评分（0-100）
            is_fused: 是否熔断

        Returns:
            分桶名称
        """
        if is_fused:
            return self.SCORE_BUCKETS["fused"]

        if score < 60:
            return self.SCORE_BUCKETS["below_60"]
        elif score < 70:
            return self.SCORE_BUCKETS["60_69"]
        elif score < 80:
            return self.SCORE_BUCKETS["70_79"]
        elif score < 90:
            return self.SCORE_BUCKETS["80_89"]
        else:
            return self.SCORE_BUCKETS["90_100"]

    def copy_reports_to_bucket(
        self,
        symbol: str,
        strategy_name: str,
        score: int,
        is_fused: bool = False,
    ) -> None:
        """将临时报告复制到评分目录

        Args:
            symbol: 品种代码
            strategy_name: 策略名称
            score: 评分
            is_fused: 是否熔断
        """
        # 源目录（临时）
        temp_reports_dir = (
            self.ranked_root.parent / "llm_generated" / symbol / strategy_name / "reports"
        )

        # 目标目录（评分归档）
        bucket_name = self._get_bucket_name(score, is_fused)
        target_reports_dir = (
            self.ranked_root / bucket_name / symbol / strategy_name / "reports"
        )
        target_reports_dir.mkdir(parents=True, exist_ok=True)

        # 复制所有报告文件
        if temp_reports_dir.exists():
            for report_file in temp_reports_dir.glob("*.json"):
                target_file = target_reports_dir / report_file.name
                shutil.copy2(report_file, target_file)
                logger.debug(f"报告已复制: {target_file}")

            logger.info(f"✅ 所有报告已复制到评分目录: {target_reports_dir}")
        else:
            logger.warning(f"临时报告目录不存在: {temp_reports_dir}")
