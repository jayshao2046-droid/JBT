"""优化数据收集器 — TASK-U0-20260417-004

自动保存每次迭代记录，为 LoRA 微调和 MetaOptimizer 提供数据源。

功能:
1. 自动保存每次迭代记录到 runtime/optimization_history/
2. 支持人工标注 actual_improvement
3. 集成 StabilityFilter 自动过滤
4. 生成训练数据（Alpaca 格式）

数据格式:
{
  "strategy_id": "STRAT_p_trend_120m_001",
  "iteration": 5,
  "timestamp": "2026-04-17T10:30:00",
  "is_sharpe": 1.2,
  "is_trades": 25,
  "is_win_rate": 0.52,
  "is_max_dd": 0.03,
  "oos_sharpe": 0.85,
  "oos_trades": 18,
  "oos_win_rate": 0.48,
  "oos_max_dd": 0.04,
  "actual_improvement": true,  # 人工标注
  "parameter_changes": {...},
  "diagnosis": {...}
}
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .stability_filter import StabilityFilter, OptimizationRecord

logger = logging.getLogger(__name__)


class OptimizationDataCollector:
    """优化数据收集器

    自动保存每次迭代记录，为 LoRA 微调和 MetaOptimizer 提供数据源。
    """

    def __init__(
        self,
        history_dir: str = "./runtime/optimization_history",
        enable_auto_filter: bool = True,
    ):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # 稳定性过滤器
        self.stability_filter = StabilityFilter() if enable_auto_filter else None

        logger.info(f"📊 优化数据收集器已启动（目录: {self.history_dir}）")

    def save_iteration(
        self,
        strategy_id: str,
        iteration: int,
        is_result: Any,  # 样本内回测结果
        oos_result: Any,  # 样本外回测结果
        parameter_changes: dict,
        diagnosis: Optional[dict] = None,
        actual_improvement: Optional[bool] = None,
    ) -> Path:
        """保存单次迭代记录

        Args:
            strategy_id: 策略ID
            iteration: 迭代次数
            is_result: 样本内回测结果
            oos_result: 样本外回测结果
            parameter_changes: 参数变化
            diagnosis: 诊断信息
            actual_improvement: 人工标注（是否真正改进）

        Returns:
            保存路径
        """
        # 构建记录
        record_data = {
            "strategy_id": strategy_id,
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            # 样本内指标
            "is_sharpe": is_result.sharpe_ratio,
            "is_trades": is_result.trades_count,
            "is_win_rate": is_result.win_rate,
            "is_max_dd": is_result.max_drawdown,
            # 样本外指标
            "oos_sharpe": oos_result.sharpe_ratio,
            "oos_trades": oos_result.trades_count,
            "oos_win_rate": oos_result.win_rate,
            "oos_max_dd": oos_result.max_drawdown,
            # 其他信息
            "parameter_changes": parameter_changes,
            "diagnosis": diagnosis,
            "actual_improvement": actual_improvement,  # 人工标注
        }

        # 自动过滤检查
        if self.stability_filter and actual_improvement is None:
            record = OptimizationRecord(
                strategy_id=strategy_id,
                iteration=iteration,
                is_sharpe=is_result.sharpe_ratio,
                is_trades=is_result.trades_count,
                is_win_rate=is_result.win_rate,
                is_max_dd=is_result.max_drawdown,
                oos_sharpe=oos_result.sharpe_ratio,
                oos_trades=oos_result.trades_count,
                oos_win_rate=oos_result.win_rate,
                oos_max_dd=oos_result.max_drawdown,
                actual_improvement=False,  # 默认 False，需要人工标注
                parameter_changes=parameter_changes,
                diagnosis=diagnosis,
            )

            is_high_quality = self.stability_filter.is_high_quality(record)
            record_data["auto_filter_passed"] = is_high_quality

            if is_high_quality:
                logger.info(f"✅ 记录通过自动过滤: {strategy_id} 迭代{iteration}")
            else:
                logger.debug(f"⚠️ 记录未通过自动过滤: {strategy_id} 迭代{iteration}")

        # 保存到文件
        filename = f"{strategy_id}_iter{iteration:03d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = self.history_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(record_data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 已保存迭代记录: {file_path}")

        return file_path

    def annotate_improvement(self, file_path: Path, actual_improvement: bool):
        """人工标注是否真正改进

        Args:
            file_path: 记录文件路径
            actual_improvement: 是否真正改进
        """
        if not file_path.exists():
            logger.error(f"记录文件不存在: {file_path}")
            return

        # 读取记录
        with open(file_path, "r", encoding="utf-8") as f:
            record_data = json.load(f)

        # 更新标注
        record_data["actual_improvement"] = actual_improvement
        record_data["annotated_at"] = datetime.now().isoformat()

        # 保存
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(record_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ 已标注: {file_path} → {actual_improvement}")

    def export_training_data(
        self,
        output_path: str = "./runtime/training_data/critic_training.jsonl",
        only_high_quality: bool = True,
    ) -> int:
        """导出训练数据（Alpaca 格式）

        Args:
            output_path: 输出路径
            only_high_quality: 只导出高质量记录

        Returns:
            导出记录数
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 收集所有记录
        records = []
        for file_path in self.history_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    record_data = json.load(f)

                # 过滤条件
                if only_high_quality:
                    if not record_data.get("actual_improvement"):
                        continue
                    if not record_data.get("auto_filter_passed", True):
                        continue

                records.append(record_data)

            except Exception as e:
                logger.warning(f"读取记录失败 {file_path}: {e}")
                continue

        # 转换为 Alpaca 格式
        training_data = []
        for record in records:
            # 构建输入
            input_text = f"""策略配置：
- 策略ID: {record['strategy_id']}
- 迭代: {record['iteration']}

回测结果：
- 样本内 Sharpe: {record['is_sharpe']:.4f}
- 样本内交易次数: {record['is_trades']}
- 样本内胜率: {record['is_win_rate']:.2%}
- 样本外 Sharpe: {record['oos_sharpe']:.4f}
- 样本外交易次数: {record['oos_trades']}
- 样本外胜率: {record['oos_win_rate']:.2%}

参数变化：
{json.dumps(record['parameter_changes'], ensure_ascii=False, indent=2)}
"""

            # 构建输出
            diagnosis = record.get('diagnosis', {})
            output_text = f"""根本原因：
{json.dumps(diagnosis.get('root_causes', []), ensure_ascii=False, indent=2)}

最佳方案：
{json.dumps(diagnosis.get('best_solution', {}), ensure_ascii=False, indent=2)}
"""

            # Alpaca 格式
            alpaca_item = {
                "instruction": "作为 JBT 策略调优专家，分析以下回测结果并给出调整建议",
                "input": input_text,
                "output": output_text,
            }

            training_data.append(alpaca_item)

        # 保存为 JSONL
        with open(output_file, "w", encoding="utf-8") as f:
            for item in training_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        logger.info(f"✅ 已导出 {len(training_data)} 条训练数据到: {output_file}")

        return len(training_data)

    def get_statistics(self) -> dict:
        """获取收集统计"""
        total_count = 0
        annotated_count = 0
        high_quality_count = 0

        for file_path in self.history_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    record_data = json.load(f)

                total_count += 1

                if record_data.get("actual_improvement") is not None:
                    annotated_count += 1

                if record_data.get("actual_improvement") and record_data.get("auto_filter_passed", True):
                    high_quality_count += 1

            except Exception:
                continue

        return {
            "total_count": total_count,
            "annotated_count": annotated_count,
            "high_quality_count": high_quality_count,
            "annotation_rate": annotated_count / total_count if total_count > 0 else 0.0,
        }
