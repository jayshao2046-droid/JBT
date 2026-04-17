"""参数映射规则应用器 — TASK-U0-20260417-004

根据品种特征动态生成参数搜索空间。

核心功能:
1. 读取 param_mapping_rules.yaml
2. 根据品种特征查找对应的参数范围
3. 生成 Optuna 搜索空间或 LLM Prompt
4. 防止"棕榈油跑出螺纹钢参数"的荒谬情况

使用流程:
1. SymbolProfiler 计算品种特征
2. ParamMappingApplicator 生成搜索空间
3. 传递给 Optuna 或 LLM
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import yaml

from .symbol_profiler import SymbolFeatures

logger = logging.getLogger(__name__)


class ParamMappingApplicator:
    """参数映射规则应用器

    根据品种特征动态生成参数搜索空间。
    """

    def __init__(self, rules_path: str = "./runtime/param_mapping_rules.yaml"):
        self.rules_path = Path(rules_path)
        self.rules = self._load_rules()

        logger.info(f"📋 参数映射规则应用器已启动（规则: {self.rules_path}）")

    def _load_rules(self) -> dict:
        """加载参数映射规则"""
        if not self.rules_path.exists():
            logger.warning(f"规则文件不存在: {self.rules_path}，使用默认规则")
            return self._get_default_rules()

        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                rules = yaml.safe_load(f)

            logger.info(f"✅ 已加载参数映射规则: {self.rules_path}")
            return rules

        except Exception as e:
            logger.error(f"加载规则失败: {e}，使用默认规则")
            return self._get_default_rules()

    def _get_default_rules(self) -> dict:
        """获取默认规则"""
        return {
            "volatility": {
                "High": {
                    "atr_multiplier": [1.5, 3.0],
                    "entry_threshold": [0.5, 1.0],
                },
                "Medium": {
                    "atr_multiplier": [1.0, 2.0],
                    "entry_threshold": [0.8, 1.5],
                },
                "Low": {
                    "atr_multiplier": [0.5, 1.5],
                    "entry_threshold": [1.0, 2.0],
                },
            },
            "trend_strength": {
                "Strong": {
                    "adx_threshold": [20, 30],
                },
                "Weak": {
                    "adx_threshold": [15, 25],
                },
            },
        }

    def generate_search_space(self, features: SymbolFeatures) -> dict:
        """生成参数搜索空间

        Args:
            features: 品种特征

        Returns:
            参数搜索空间字典
        """
        search_space = {}

        # 1. 根据波动率生成搜索空间
        if "volatility" in self.rules:
            vol_level = features.volatility_weighted
            if vol_level in self.rules["volatility"]:
                vol_params = self.rules["volatility"][vol_level]
                search_space.update(vol_params)
                logger.debug(f"波动率 {vol_level}: {vol_params}")

        # 2. 根据趋势强度生成搜索空间
        if "trend_strength" in self.rules:
            trend_level = features.trend_strength_weighted
            if trend_level in self.rules["trend_strength"]:
                trend_params = self.rules["trend_strength"][trend_level]
                search_space.update(trend_params)
                logger.debug(f"趋势强度 {trend_level}: {trend_params}")

        # 3. 根据流动性生成搜索空间
        if "liquidity" in self.rules:
            liquidity_level = features.liquidity
            if liquidity_level in self.rules["liquidity"]:
                liquidity_params = self.rules["liquidity"][liquidity_level]
                search_space.update(liquidity_params)
                logger.debug(f"流动性 {liquidity_level}: {liquidity_params}")

        # 4. 品种特定规则（优先级最高）
        if "symbol_specific" in self.rules:
            if features.symbol in self.rules["symbol_specific"]:
                symbol_params = self.rules["symbol_specific"][features.symbol].get("recommended_params", {})
                search_space.update(symbol_params)
                logger.debug(f"品种特定 {features.symbol}: {symbol_params}")

        logger.info(f"✅ 已生成搜索空间: {features.symbol} → {len(search_space)} 个参数")

        return search_space

    def generate_optuna_space(self, features: SymbolFeatures, trial: Any) -> dict:
        """生成 Optuna 搜索空间

        Args:
            features: 品种特征
            trial: Optuna Trial 对象

        Returns:
            参数字典
        """
        search_space = self.generate_search_space(features)
        params = {}

        for param_name, param_range in search_space.items():
            if isinstance(param_range, list) and len(param_range) == 2:
                # 数值范围
                low, high = param_range
                if isinstance(low, int) and isinstance(high, int):
                    params[param_name] = trial.suggest_int(param_name, low, high)
                else:
                    params[param_name] = trial.suggest_float(param_name, low, high)
            elif isinstance(param_range, bool):
                # 布尔值
                params[param_name] = trial.suggest_categorical(param_name, [True, False])
            else:
                # 直接使用值
                params[param_name] = param_range

        return params

    def generate_llm_prompt(self, features: SymbolFeatures) -> str:
        """生成 LLM Prompt（用于策略设计）

        Args:
            features: 品种特征

        Returns:
            Prompt 文本
        """
        search_space = self.generate_search_space(features)

        # 构建特征描述
        feature_desc = f"""品种: {features.symbol}

特征画像:
- 波动率: {features.volatility_weighted} (3个月: {features.volatility_3m:.4f}, 1年: {features.volatility_1y:.4f})
- 趋势强度: {features.trend_strength_weighted} (3个月: {features.trend_strength_3m:.4f}, 1年: {features.trend_strength_1y:.4f})
- 流动性: {features.liquidity}
- 自相关性: {features.autocorr_3m:.4f}
- 偏度: {features.skewness:.4f}
- 峰度: {features.kurtosis:.4f}
"""

        # 构建参数建议
        param_suggestions = []
        for param_name, param_range in search_space.items():
            if isinstance(param_range, list) and len(param_range) == 2:
                param_suggestions.append(f"- {param_name}: 建议范围 {param_range}")
            else:
                param_suggestions.append(f"- {param_name}: 建议值 {param_range}")

        param_desc = "\n".join(param_suggestions)

        prompt = f"""{feature_desc}

推荐参数范围:
{param_desc}

请基于以上品种特征和参数建议，设计一个适合该品种的交易策略。
"""

        return prompt

    def validate_params(self, features: SymbolFeatures, params: dict) -> tuple[bool, str]:
        """验证参数是否合理

        Args:
            features: 品种特征
            params: 参数字典

        Returns:
            (是否合理, 原因)
        """
        search_space = self.generate_search_space(features)

        for param_name, param_value in params.items():
            if param_name not in search_space:
                continue

            expected_range = search_space[param_name]

            if isinstance(expected_range, list) and len(expected_range) == 2:
                low, high = expected_range

                if not (low <= param_value <= high):
                    return False, f"{param_name}={param_value} 超出建议范围 [{low}, {high}]"

        return True, "参数合理"

    def get_feature_description(self, features: SymbolFeatures) -> str:
        """获取品种特征描述（用于日志）

        Args:
            features: 品种特征

        Returns:
            描述文本
        """
        return (
            f"{features.symbol}: "
            f"波动率={features.volatility_weighted}, "
            f"趋势={features.trend_strength_weighted}, "
            f"流动性={features.liquidity}"
        )
