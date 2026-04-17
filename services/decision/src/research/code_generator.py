"""代码生成器 — TASK-U0-20260417-004

混合双驱模式第三层：代码生成器

将策略架构师（第二层）输出的伪代码转化为标准的 YAML/Python 策略文件。

核心功能:
1. 接收策略设计（逻辑描述 + 推荐因子）
2. 调用 Qwen Coder 生成 YAML 策略文件
3. 验证生成的 YAML 格式
4. 保存到 strategies/ 目录

工作流程:
第一层：SymbolProfiler → 品种特征
  ↓
第二层：StrategyArchitect → 策略逻辑伪代码
  ↓
第三层：CodeGenerator → YAML/Python 策略文件
  ↓
自动化：回测验证

输入示例:
{
  "strategy_name": "rb_volatility_breakout_001",
  "logic_description": "基于波动率突破 + 持仓量异动的趋势跟踪策略",
  "recommended_factors": ["ATR", "ADX", "OBV"],
  "entry_logic": "当 ATR 突破20日高点 且 OBV 放量 且 ADX > 25 时开仓",
  "exit_logic": "ATR 回落至10日均线以下 或 ADX < 20 时平仓",
  "risk_management": "动态止损：ATR * 2.5"
}

输出示例:
YAML 策略文件（符合 JBT 规范）
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

import yaml

from ..llm.openai_client import OpenAICompatibleClient

logger = logging.getLogger(__name__)


class CodeGenerator:
    """代码生成器

    将策略逻辑伪代码转化为标准的 YAML 策略文件。
    """

    # YAML 策略模板
    YAML_TEMPLATE = """name: {strategy_name}
description: {description}

symbols:
  - {symbol}

timeframe_minutes: {timeframe}

factors:
{factors_yaml}

signal:
  long_condition: "{long_condition}"
  short_condition: "{short_condition}"
  confirm_bars: {confirm_bars}

market_filter:
  conditions:
{market_filter_yaml}

risk:
  stop_loss_yuan: {stop_loss}
  daily_loss_limit_yuan: {daily_loss_limit}
  max_drawdown_pct: {max_drawdown}

position_fraction: {position_fraction}

transaction_costs:
  slippage_per_unit: {slippage}
  commission_per_lot_round_turn: {commission}

no_overnight: true
"""

    def __init__(
        self,
        online_client: OpenAICompatibleClient,
        model: str = "qwen-coder-plus",
        output_dir: str = "./strategies",
    ):
        self.online_client = online_client
        self.model = model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"🔧 代码生成器已启动（模型: {self.model}）")

    async def generate_yaml_strategy(
        self,
        strategy_design: dict,
        symbol: str,
        timeframe: int = 120,
    ) -> Optional[Path]:
        """生成 YAML 策略文件

        Args:
            strategy_design: 策略设计字典（来自 StrategyArchitect）
            symbol: 品种代码（如 DCE.rb0）
            timeframe: 时间周期（分钟）

        Returns:
            生成的 YAML 文件路径
        """
        logger.info(f"🔧 生成 YAML 策略: {strategy_design['strategy_name']}")

        # 构建 Prompt
        prompt = self._build_generation_prompt(strategy_design, symbol, timeframe)

        messages = [
            {
                "role": "system",
                "content": "你是 JBT 高级工程师，负责将策略逻辑转化为标准 YAML 配置文件。只输出纯 YAML。"
            },
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.online_client.chat(self.model, messages, timeout=120.0)

            if "error" in response:
                logger.warning(f"代码生成失败: {response['error']}")
                return None

            content = response.get("content", "").strip()

            # 提取 YAML
            yaml_content = self._extract_yaml(content)

            if not yaml_content:
                logger.warning("未能提取有效的 YAML 内容")
                return None

            # 验证 YAML 格式
            is_valid, reason = self._validate_yaml(yaml_content)

            if not is_valid:
                logger.warning(f"YAML 验证失败: {reason}")
                return None

            # 保存文件
            file_path = self._save_yaml(strategy_design['strategy_name'], yaml_content)

            logger.info(f"✅ YAML 策略已生成: {file_path}")

            return file_path

        except Exception as e:
            logger.error(f"代码生成异常: {e}", exc_info=True)
            return None

    def _build_generation_prompt(
        self,
        strategy_design: dict,
        symbol: str,
        timeframe: int,
    ) -> str:
        """构建代码生成 Prompt"""

        factors_desc = "\n".join([
            f"- {factor}: 需要配置合理的参数"
            for factor in strategy_design['recommended_factors']
        ])

        return f"""将以下策略逻辑转化为 JBT 标准 YAML 配置文件。

【策略信息】
- 策略名称: {strategy_design['strategy_name']}
- 逻辑描述: {strategy_design['logic_description']}
- 品种: {symbol}
- 时间周期: {timeframe} 分钟

【推荐因子】
{factors_desc}

【入场逻辑】
{strategy_design['entry_logic']}

【出场逻辑】
{strategy_design['exit_logic']}

【风险管理】
{strategy_design['risk_management']}

【要求】
1. 严格按照 JBT YAML 格式输出
2. 为每个因子配置合理的参数（基于因子特性）
3. 将入场/出场逻辑转化为 long_condition 和 short_condition
4. 配置合理的风险参数（止损、日内止损、最大回撤）
5. 添加必要的市场过滤条件（ATR、ADX、成交量等）

【YAML 格式示例】
```yaml
name: rb_volatility_breakout_001
description: 基于波动率突破 + 持仓量异动的趋势跟踪策略

symbols:
  - DCE.rb0

timeframe_minutes: 120

factors:
  - factor_name: ATR
    params:
      period: 14
  - factor_name: ADX
    params:
      period: 14
  - factor_name: OBV
    params: {{}}

signal:
  long_condition: "atr > atr_ma_20 and obv > obv_prev and adx > 25"
  short_condition: "atr > atr_ma_20 and obv < obv_prev and adx > 25"
  confirm_bars: 2

market_filter:
  conditions:
    - "atr > 0.006 * close"
    - "adx > 20"
    - "volume_ratio > 1.0"

risk:
  stop_loss_yuan: 1000
  daily_loss_limit_yuan: 2000
  max_drawdown_pct: 0.015

position_fraction: 0.1

transaction_costs:
  slippage_per_unit: 1
  commission_per_lot_round_turn: 5

no_overnight: true
```

【严禁】
- 不要输出任何解释
- 不要使用 markdown 代码块标记
- 只输出纯 YAML
"""

    def _extract_yaml(self, content: str) -> Optional[str]:
        """从 LLM 回复中提取 YAML"""
        # 去除 markdown 代码块标记
        content = content.replace("```yaml", "").replace("```", "").strip()

        # 检查是否包含 YAML 关键字
        if "name:" in content and "factors:" in content:
            return content

        return None

    def _validate_yaml(self, yaml_content: str) -> tuple[bool, str]:
        """验证 YAML 格式

        Args:
            yaml_content: YAML 内容

        Returns:
            (是否有效, 原因)
        """
        try:
            # 解析 YAML
            strategy = yaml.safe_load(yaml_content)

            # 检查必填字段
            required_fields = [
                "name",
                "symbols",
                "timeframe_minutes",
                "factors",
                "signal",
                "risk",
            ]

            for field in required_fields:
                if field not in strategy:
                    return False, f"缺少必填字段: {field}"

            # 检查 signal 字段
            signal = strategy.get("signal", {})
            if "long_condition" not in signal or "short_condition" not in signal:
                return False, "signal 缺少 long_condition 或 short_condition"

            # 检查 factors
            factors = strategy.get("factors", [])
            if not factors:
                return False, "factors 不能为空"

            for factor in factors:
                if "factor_name" not in factor:
                    return False, "factor 缺少 factor_name"

            return True, "YAML 格式正确"

        except yaml.YAMLError as e:
            return False, f"YAML 解析错误: {e}"
        except Exception as e:
            return False, f"验证异常: {e}"

    def _save_yaml(self, strategy_name: str, yaml_content: str) -> Path:
        """保存 YAML 文件

        Args:
            strategy_name: 策略名称
            yaml_content: YAML 内容

        Returns:
            文件路径
        """
        # 清理策略名称（移除特殊字符）
        clean_name = re.sub(r'[^\w\-]', '_', strategy_name)
        file_path = self.output_dir / f"{clean_name}.yaml"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        logger.info(f"💾 已保存 YAML 策略: {file_path}")

        return file_path

    def generate_batch(
        self,
        strategy_designs: list[dict],
        symbol: str,
        timeframe: int = 120,
    ) -> list[Path]:
        """批量生成 YAML 策略文件

        Args:
            strategy_designs: 策略设计列表
            symbol: 品种代码
            timeframe: 时间周期

        Returns:
            生成的文件路径列表
        """
        import asyncio

        async def _generate_all():
            tasks = [
                self.generate_yaml_strategy(design, symbol, timeframe)
                for design in strategy_designs
            ]
            return await asyncio.gather(*tasks)

        results = asyncio.run(_generate_all())

        # 过滤掉 None
        file_paths = [path for path in results if path is not None]

        logger.info(f"✅ 批量生成完成: {len(file_paths)}/{len(strategy_designs)} 个策略")

        return file_paths
