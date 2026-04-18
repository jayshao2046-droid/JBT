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

        # 读取 TqSDK 标准模板
        template_path = Path(__file__).parent / "templates" / "strategy_template.yaml"
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
        except FileNotFoundError:
            logger.warning(f"模板文件不存在: {template_path}，使用内置示例")
            template_content = self._get_fallback_template()

        return f"""将以下策略逻辑转化为 JBT 标准 YAML 配置文件（符合 TqSDK 回测格式）。

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

【关键要求】
1. **严格按照下方的 TqSDK 标准模板格式输出**
2. **必须包含的字段**：
   - version: 版本号（如 "1.0"）
   - category: 策略分类（trend_following / mean_reversion / breakout / arbitrage / intraday_momentum）
   - factors[].weight: 因子权重（0-1，总和为1.0）
   - market_filter.enabled: 市场过滤开关（true/false）
   - position_adjustment: 动态仓位调整配置
   - **stop_loss: 止损配置（必须包含，使用 ATR 动态止损）**
     * type: "atr"
     * atr_multiplier: 1.5（默认值，可根据品种波动率调整为 1.2-2.0）
     * atr_period: 14（默认值）
   - **take_profit: 止盈配置（必须包含，使用 ATR 动态止盈）**
     * type: "atr"
     * atr_multiplier: 2.5（默认值，可根据品种波动率调整为 2.0-3.0）
     * atr_period: 14（默认值）
   - risk.force_close_day: 日盘强制平仓时间（如 "14:55"）
   - risk.force_close_night: 夜盘强制平仓时间（如 "22:55"，无夜盘可删除）
   - tags: 标签列表（如 ["v1", "trend", "5m"]）

3. **信号条件语法规则**：
   - 因子名称自动转为小写变量（ATR → atr, ADX → adx, MACD → macd_hist）
   - 只能使用简单的比较表达式，不支持函数调用
   - 可用的内置变量：close, open, high, low, volume
   - 可用的运算符：>, <, >=, <=, ==, and, or
   - 正确示例：
     * "macd_hist > 0 and rsi > 50 and rsi_slope > 0"
     * "atr > 0.005 * close and adx > 20"
     * "close > open and volume_ratio > 1.2"
   - 错误示例（不要使用）：
     * "atr > high(-20)" ❌ 不支持函数调用
     * "obv > obv(-1)" ❌ 不支持历史值引用
     * "atr < sma(atr, 10)" ❌ 不支持函数调用

4. **市场过滤条件必须比入场条件更宽松**：
   - 市场过滤是全局前置条件，应该比开仓条件阈值更低
   - 如果入场条件是 "atr > 0.008 * close"，市场过滤应该是 "atr > 0.005 * close"（更低）
   - 如果入场条件是 "adx > 25"，市场过滤应该是 "adx > 20"（更低）

5. **止损止盈使用 ATR 倍数，不是固定金额**：
   - 正确：stop_loss.atr_multiplier: 1.5
   - 错误：stop_loss_yuan: 1000 ❌（TqSDK 不支持）

6. **强制平仓时间使用具体时间点**：
   - 正确：risk.force_close_day: "14:55"
   - 错误：risk.time_to_exit_bars: 12 ❌（TqSDK 不支持）

7. **所有数值必须是具体的数字**，不要使用模板语法如 {{{{ }}}}

8. **使用主力合约代码**（如 SHFE.rb2505），不要使用指数合约（如 SHFE.rb0）

9. **因子权重总和应为 1.0**，合理分配各因子的权重

10. **必须包含 transaction_costs**（交易成本），否则无法进入 TqSDK 回测

【TqSDK 标准 YAML 模板】
{template_content}

【严禁】
- 不要输出任何解释或注释（模板中的注释可以保留）
- 不要使用 markdown 代码块标记
- 只输出纯 YAML
- **严禁在signal条件中创造新变量**：
  * 禁止：atr_20_high, atr_10_sma, obv_prev, rsi_ma, macd_prev 等
  * 只能使用：因子输出字段（见模板中的因子字段名列表）+ 内置变量（close, open, high, low, volume）+ 数值常量
  * 正确示例：macd_hist > 0, rsi > 50, atr > 0.005 * close, volume_ratio > 1.2
- **严禁使用固定金额的止损止盈**（stop_loss_yuan, take_profit_yuan），必须使用 ATR 倍数
- **严禁省略 stop_loss 和 take_profit 配置**：每个策略必须包含这两个字段，即使策略设计中未明确提及，也要使用默认值（stop_loss.atr_multiplier: 1.5, take_profit.atr_multiplier: 2.5）
"""

    def _get_fallback_template(self) -> str:
        """获取内置的后备模板（TqSDK 格式）"""
        return """name: "FC-XXX_strategy_name"
description: "策略描述"
version: "1.0"
category: "trend_following"

symbols:
  - "SHFE.rb2505"

timeframe_minutes: 120

factors:
  - factor_name: "MACD"
    weight: 0.4
    params:
      fast: 12
      slow: 26
      signal: 9
  - factor_name: "RSI"
    weight: 0.3
    params:
      period: 14
  - factor_name: "ATR"
    weight: 0.3
    params:
      period: 14

market_filter:
  enabled: true
  conditions:
    - "atr > 0.005 * close"
    - "adx > 20"

signal:
  long_condition: "macd_hist > 0 and rsi > 50 and rsi_slope > 0"
  short_condition: "macd_hist < 0 and rsi < 50 and rsi_slope < 0"
  confirm_bars: 1

position_fraction: 0.08
position_adjustment:
  method: "atr_scaling"
  base_position: 0.08
  atr_period: 14
  atr_multiplier: 1.0

transaction_costs:
  slippage_per_unit: 1
  commission_per_lot_round_turn: 5

risk:
  daily_loss_limit_yuan: 2000
  per_symbol_fuse_yuan: 160
  max_drawdown_pct: 0.008
  force_close_day: "14:55"
  force_close_night: "22:55"
  no_overnight: true

stop_loss:
  atr_multiplier: 1.5
  type: "atr"

take_profit:
  atr_multiplier: 2.5
  type: "atr"

tags: ["v1", "trend", "120m"]
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
