"""元优化器 — TASK-U0-20260417-004

每月自动更新参数映射规则，让规则库具备自我进化能力。

核心功能:
1. 收集过去30天的调优记录
2. 分析"哪些参数组合在哪些特征下表现最好"
3. 调用 DeepSeek V3 生成新规则
4. 人工审核 + 自动部署

触发方式:
- Cron 任务，每月1号凌晨自动运行
- 手动触发（用于测试）

输出:
- param_mapping_rules.yaml（新规则）
- meta_optimization_report.json（分析报告）
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import yaml

from llm.openai_client import OpenAICompatibleClient
from .stability_filter import StabilityFilter, OptimizationRecord

logger = logging.getLogger(__name__)


class MetaOptimizer:
    """元优化器

    每月自动更新参数映射规则，让规则库具备自我进化能力。
    """

    def __init__(
        self,
        online_client: OpenAICompatibleClient,
        rules_path: str = "./runtime/param_mapping_rules.yaml",
        history_dir: str = "./runtime/optimization_history",
    ):
        self.online_client = online_client
        self.rules_path = Path(rules_path)
        self.history_dir = Path(history_dir)

        # 确保目录存在
        self.rules_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # 稳定性过滤器
        self.stability_filter = StabilityFilter()

        # 模型配置
        self.v3_model = os.getenv("DEEPSEEK_V3_MODEL", "deepseek-chat")

    async def evolve_rules(self, days: int = 30) -> dict:
        """进化参数映射规则

        Args:
            days: 回溯天数（默认30天）

        Returns:
            进化报告
        """
        logger.info(f"🧬 启动参数规则自我进化（回溯 {days} 天）")

        # 1. 收集优化记录
        records = self._load_optimization_history(days=days)
        logger.info(f"📊 收集到 {len(records)} 条优化记录")

        if len(records) < 10:
            logger.warning("优化记录不足10条，跳过规则进化")
            return {
                "success": False,
                "reason": "优化记录不足",
                "records_count": len(records),
            }

        # 2. 稳定性过滤
        high_quality_records = self.stability_filter.filter_batch(records)
        logger.info(f"✅ 高质量记录: {len(high_quality_records)} 条")

        if len(high_quality_records) < 5:
            logger.warning("高质量记录不足5条，跳过规则进化")
            return {
                "success": False,
                "reason": "高质量记录不足",
                "records_count": len(records),
                "high_quality_count": len(high_quality_records),
            }

        # 3. 分析参数表现
        analysis = self._analyze_param_performance(high_quality_records)
        logger.info(f"📈 参数表现分析完成")

        # 4. 调用 DeepSeek V3 生成新规则
        new_rules = await self._generate_new_rules(analysis)

        if not new_rules:
            logger.error("❌ 规则生成失败")
            return {
                "success": False,
                "reason": "规则生成失败",
                "records_count": len(records),
                "high_quality_count": len(high_quality_records),
            }

        # 5. 保存新规则（待人工审核）
        review_path = self._save_rules_for_review(new_rules)
        logger.info(f"📝 新规则已保存到: {review_path}")

        # 6. 生成进化报告
        report = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "days": days,
            "records_count": len(records),
            "high_quality_count": len(high_quality_records),
            "filter_stats": self.stability_filter.get_filter_stats(),
            "analysis": analysis,
            "new_rules_path": str(review_path),
        }

        # 保存报告
        report_path = self.history_dir / f"meta_optimization_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ 进化报告已保存到: {report_path}")

        return report

    def _load_optimization_history(self, days: int) -> list[OptimizationRecord]:
        """加载优化历史记录

        Args:
            days: 回溯天数

        Returns:
            优化记录列表
        """
        records = []
        cutoff_date = datetime.now() - timedelta(days=days)

        # 遍历历史目录
        for file_path in self.history_dir.glob("*.json"):
            try:
                # 检查文件修改时间
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff_date:
                    continue

                # 加载记录
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 转换为 OptimizationRecord
                if isinstance(data, list):
                    for item in data:
                        record = self._parse_record(item)
                        if record:
                            records.append(record)
                else:
                    record = self._parse_record(data)
                    if record:
                        records.append(record)

            except Exception as e:
                logger.warning(f"加载记录失败 {file_path}: {e}")
                continue

        return records

    def _parse_record(self, data: dict) -> Optional[OptimizationRecord]:
        """解析优化记录"""
        try:
            return OptimizationRecord(
                strategy_id=data.get("strategy_id", "unknown"),
                iteration=data.get("iteration", 0),
                is_sharpe=data.get("is_sharpe", 0.0),
                is_trades=data.get("is_trades", 0),
                is_win_rate=data.get("is_win_rate", 0.0),
                is_max_dd=data.get("is_max_dd", 0.0),
                oos_sharpe=data.get("oos_sharpe", 0.0),
                oos_trades=data.get("oos_trades", 0),
                oos_win_rate=data.get("oos_win_rate", 0.0),
                oos_max_dd=data.get("oos_max_dd", 0.0),
                actual_improvement=data.get("actual_improvement", False),
                parameter_changes=data.get("parameter_changes", {}),
                diagnosis=data.get("diagnosis"),
            )
        except Exception as e:
            logger.warning(f"解析记录失败: {e}")
            return None

    def _analyze_param_performance(self, records: list[OptimizationRecord]) -> dict:
        """分析参数表现

        Args:
            records: 高质量优化记录

        Returns:
            分析结果
        """
        # 按品种分组
        by_symbol: dict[str, list[OptimizationRecord]] = {}
        for record in records:
            # 从 strategy_id 提取品种（如 STRAT_p_trend_120m_001 → p）
            parts = record.strategy_id.split("_")
            symbol = parts[1] if len(parts) > 1 else "unknown"

            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(record)

        # 统计每个品种的最佳参数
        best_params_by_symbol = {}
        for symbol, symbol_records in by_symbol.items():
            # 按 OOS Sharpe 排序
            sorted_records = sorted(symbol_records, key=lambda r: r.oos_sharpe, reverse=True)
            top_records = sorted_records[:3]  # 取前3名

            # 提取参数变化
            param_changes = []
            for record in top_records:
                param_changes.append({
                    "oos_sharpe": record.oos_sharpe,
                    "oos_trades": record.oos_trades,
                    "oos_win_rate": record.oos_win_rate,
                    "parameter_changes": record.parameter_changes,
                })

            best_params_by_symbol[symbol] = {
                "records_count": len(symbol_records),
                "top_performers": param_changes,
            }

        return {
            "total_records": len(records),
            "symbols_count": len(by_symbol),
            "best_params_by_symbol": best_params_by_symbol,
        }

    async def _generate_new_rules(self, analysis: dict) -> Optional[dict]:
        """调用 DeepSeek V3 生成新规则

        Args:
            analysis: 参数表现分析结果

        Returns:
            新规则字典
        """
        prompt = self._build_rule_generation_prompt(analysis)

        messages = [
            {
                "role": "system",
                "content": "你是 JBT 参数映射规则专家。基于历史调优数据，生成新的参数映射规则。只输出纯 YAML。"
            },
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.online_client.chat(self.v3_model, messages, timeout=120.0)

            if "error" in response:
                logger.warning(f"V3 调用失败: {response['error']}")
                return None

            content = response.get("content", "").strip()

            # 提取 YAML
            yaml_match = self._extract_yaml(content)
            if yaml_match:
                try:
                    rules = yaml.safe_load(yaml_match)
                    return rules
                except yaml.YAMLError as e:
                    logger.error(f"YAML 解析失败: {e}")
                    return None

            return None

        except Exception as e:
            logger.error(f"规则生成异常: {e}", exc_info=True)
            return None

    def _build_rule_generation_prompt(self, analysis: dict) -> str:
        """构建规则生成 Prompt"""
        return f"""基于以下 {analysis['total_records']} 条高质量调优数据，更新参数映射规则。

【分析结果】
{json.dumps(analysis, indent=2, ensure_ascii=False)}

【任务】
1. 分析每个品种的最佳参数组合
2. 提取共性规律（如"高波动品种适合更宽的止损"）
3. 生成新的参数映射规则

【输出格式】
严格按照以下 YAML 格式输出：

```yaml
# 参数映射规则 - 自动生成于 {datetime.now().strftime('%Y-%m-%d')}

volatility:
  High:
    atr_multiplier: [1.5, 3.0]  # 放宽止损
    entry_threshold: [0.5, 1.0]  # 降低入场门槛
    description: "高波动品种适合更宽的止损和更低的入场门槛"
  Medium:
    atr_multiplier: [1.0, 2.0]
    entry_threshold: [0.8, 1.5]
    description: "中等波动品种使用标准参数"
  Low:
    atr_multiplier: [0.5, 1.5]
    entry_threshold: [1.0, 2.0]
    description: "低波动品种适合更紧的止损和更高的入场门槛"

trend_strength:
  Strong:
    enable_mean_reversion: false
    breakout_filter: true
    adx_threshold: [20, 30]
    description: "强趋势品种关闭均值回归，启用突破过滤"
  Weak:
    enable_mean_reversion: true
    breakout_filter: false
    adx_threshold: [15, 25]
    description: "弱趋势品种启用均值回归，关闭突破过滤"

liquidity:
  High:
    volume_ratio_threshold: [0.8, 1.2]
    description: "高流动性品种可以放宽成交量过滤"
  Low:
    volume_ratio_threshold: [1.2, 2.0]
    description: "低流动性品种需要更严格的成交量过滤"
```

【要求】
1. 只输出纯 YAML，不要任何解释
2. 不要使用 markdown 代码块标记
3. 确保 YAML 格式正确
4. 每个规则必须包含 description 字段
"""

    def _extract_yaml(self, content: str) -> Optional[str]:
        """从 LLM 回复中提取 YAML"""
        # 去除 markdown 代码块标记
        content = content.replace("```yaml", "").replace("```", "").strip()

        # 检查是否包含 YAML 关键字
        if "volatility:" in content or "trend_strength:" in content:
            return content

        return None

    def _save_rules_for_review(self, rules: dict) -> Path:
        """保存规则供人工审核

        Args:
            rules: 新规则字典

        Returns:
            保存路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        review_path = self.rules_path.parent / f"param_mapping_rules_review_{timestamp}.yaml"

        with open(review_path, "w", encoding="utf-8") as f:
            yaml.dump(rules, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        logger.info(f"📝 新规则已保存到: {review_path}")
        logger.info("⚠️ 请人工审核后，手动替换 param_mapping_rules.yaml")

        return review_path

    def approve_rules(self, review_path: str) -> bool:
        """批准新规则（人工审核后调用）

        Args:
            review_path: 待审核规则路径

        Returns:
            是否成功
        """
        review_file = Path(review_path)

        if not review_file.exists():
            logger.error(f"规则文件不存在: {review_path}")
            return False

        try:
            # 备份旧规则
            if self.rules_path.exists():
                backup_path = self.rules_path.parent / f"param_mapping_rules_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
                self.rules_path.rename(backup_path)
                logger.info(f"📦 旧规则已备份到: {backup_path}")

            # 部署新规则
            review_file.rename(self.rules_path)
            logger.info(f"✅ 新规则已部署到: {self.rules_path}")

            return True

        except Exception as e:
            logger.error(f"规则部署失败: {e}", exc_info=True)
            return False
