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

    # YAML 策略模板（双引擎兼容：local engine + TqSdk）
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
  enabled: true
  conditions:
{market_filter_yaml}

risk:
  daily_loss_limit: {daily_loss_limit}    # 比例（如 0.001 = 0.1%），非金额
  max_drawdown: {max_drawdown}             # 比例（如 0.03 = 3%），非百分数
  force_close_day: "14:55"
  force_close_night: "22:55"
  no_overnight: true
  stop_loss:
    type: "atr"
    atr_multiplier: 1.5
  take_profit:
    type: "atr"
    atr_multiplier: 2.5

position_fraction: {position_fraction}

transaction_costs:
  slippage_per_unit: {slippage}
  commission_per_lot_round_turn: {commission}
"""

    NIGHT_TRADING_COMMODITIES = {
        "rb", "hc", "i", "j", "jm",
        "cu", "al", "zn", "ni", "ss",
        "au", "ag",
        "sc", "fu", "bu", "ru", "sp", "eb", "pg",
        "p", "y", "m", "a", "c", "cs", "l", "v", "pp",
        "ma", "ta", "eg",
    }

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

            yaml_content = self._normalize_generated_yaml(yaml_content)

            # 验证 YAML 格式
            is_valid, reason = self._validate_yaml(yaml_content)

            if not is_valid:
                logger.warning(f"YAML 验证失败，尝试自动修复: {reason}")
                yaml_content = await self._repair_yaml(
                    strategy_design=strategy_design,
                    symbol=symbol,
                    timeframe=timeframe,
                    invalid_yaml=yaml_content,
                    validation_error=reason,
                )
                if not yaml_content:
                    return None

                yaml_content = self._normalize_generated_yaml(yaml_content)

                is_valid, reason = self._validate_yaml(yaml_content)
                if not is_valid:
                    logger.warning(f"自动修复后仍验证失败: {reason}")
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

        recommended_factors = strategy_design.get('recommended_factors', [])
        factors_desc = "\n".join([
            f"- {factor}: 需要配置合理的参数"
            for factor in recommended_factors
        ]) if recommended_factors else "- 根据策略逻辑自行选择合适的技术因子"

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
   - **risk.stop_loss（必须在 risk 块内部）**：
     * type: "atr"
     * atr_multiplier: 1.5（默认值，可根据品种波动率调整为 1.2-2.0）
   - **risk.take_profit（必须在 risk 块内部）**：
     * type: "atr"
     * atr_multiplier: 2.5（默认值，可根据品种波动率调整为 2.0-3.0）
   - risk.force_close_day: 日盘强制平仓时间（如 "14:55"）
   - risk.force_close_night: 夜盘强制平仓时间（如 "22:55"，无夜盘可删除）
   - risk.daily_loss_limit: 比例值（如 0.001），**禁止** 使用 daily_loss_limit_yuan
   - risk.max_drawdown: 比例值（如 0.03），**禁止** 使用 max_drawdown_pct
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

8. **symbol 必须使用 `_main` 通配符格式**（如 `SHFE.rb_main`、`DCE.m_main`、`DCE.p_main`）：
   - 本地回测引擎会自动匹配任意月份合约
   - TqSdk 回测引擎会自动解析为当前主力合约
   - 禁止使用硬编码月份（如 SHFE.rb2505、DCE.p2609 ❌）
   - 禁止使用指数合约（如 SHFE.rb0、DCE.m0 ❌）

9. **因子权重总和应为 1.0**，合理分配各因子的权重

10. **必须包含 transaction_costs**（交易成本），否则无法进入 TqSDK 回测

11. **signal.long_condition 和 signal.short_condition 都必须是非空字符串**：
    - 禁止 `short_condition: ""`
    - 禁止 `short_condition: null`
    - 如果策略偏单边，也必须提供一个明确的反向/退出型做空条件，不能留空

12. **夜盘品种必须包含 risk.force_close_night**：
    - 如 rb、cu、au、sc、p、m、ma、ta 等夜盘品种，必须设置 `risk.force_close_night: "22:55"`
    - 不要省略该字段

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
- **严禁省略 risk.stop_loss 和 risk.take_profit 配置**：必须在 risk 块内部，使用默认值（atr_multiplier: 1.5 / 2.5）
- **严禁 stop_loss/take_profit 出现在根级**：根级不得有独立的 stop_loss/take_profit 键
- **严禁旧字段名**：stop_loss_yuan、take_profit_yuan、daily_loss_limit_yuan、max_drawdown_pct 均被回测引擎拒绝
- **严禁硬编码月份合约**（如 rb2505、p2609、m2507）：必须使用 `_main` 通配格式（如 `SHFE.rb_main`、`DCE.p_main`）
- **严禁输出空的 short_condition**：本地正式引擎会拒绝空字符串
- **夜盘品种严禁省略 risk.force_close_night**：TqSdk 正式回测会拒绝缺失该字段的夜盘策略
"""

    async def _repair_yaml(
        self,
        *,
        strategy_design: dict,
        symbol: str,
        timeframe: int,
        invalid_yaml: str,
        validation_error: str,
    ) -> Optional[str]:
        """在首次生成不符合双引擎约束时，要求 LLM 做一次最小修复。"""
        repair_prompt = f"""你上一次生成的 YAML 未通过 JBT 双引擎兼容校验。

【策略信息】
- 策略名称: {strategy_design['strategy_name']}
- 品种: {symbol}
- 时间周期: {timeframe} 分钟

【校验错误】
{validation_error}

【修复要求】
1. 只做最小必要修改，保留原策略逻辑与字段顺序。
2. 输出仍然必须是纯 YAML，不要加解释。
3. `signal.long_condition` 和 `signal.short_condition` 都必须是非空字符串。
4. 若品种属于夜盘品种，必须补充 `risk.force_close_night: "22:55"`。
5. `risk.stop_loss` / `risk.take_profit` 必须保留在 risk 块内部。
6. symbols 必须继续使用 `_main` 通配格式。

【待修复 YAML】
{invalid_yaml}
"""

        response = await self.online_client.chat(
            self.model,
            [
                {
                    "role": "system",
                    "content": "你是 JBT YAML 修复器。只输出修复后的纯 YAML。",
                },
                {"role": "user", "content": repair_prompt},
            ],
            timeout=120.0,
        )

        if "error" in response:
            logger.warning(f"YAML 自动修复失败: {response['error']}")
            return None

        repaired_yaml = self._extract_yaml(response.get("content", "").strip())
        if not repaired_yaml:
            logger.warning("自动修复未返回有效 YAML")
            return None
        return repaired_yaml

    def _normalize_generated_yaml(self, yaml_content: str) -> str:
        """将模型输出归一化为双引擎可直接消费的 YAML 结构。"""
        try:
            strategy = yaml.safe_load(yaml_content)
        except yaml.YAMLError:
            return yaml_content

        if not isinstance(strategy, dict):
            return yaml_content

        signal = strategy.get("signal") or {}
        if isinstance(signal, dict):
            long_condition = str(signal.get("long_condition") or "").strip()
            short_condition = str(signal.get("short_condition") or "").strip()
            if long_condition and not short_condition:
                signal["short_condition"] = self._mirror_condition(long_condition)
            strategy["signal"] = signal

        risk = strategy.get("risk") or {}
        if not isinstance(risk, dict):
            risk = {}

        # 兼容旧字段名并补齐默认风控
        if "daily_loss_limit" not in risk and "daily_loss_limit_yuan" in risk:
            risk["daily_loss_limit"] = 0.001
        risk.pop("daily_loss_limit_yuan", None)

        if "max_drawdown" not in risk and "max_drawdown_pct" in risk:
            try:
                max_drawdown = float(risk["max_drawdown_pct"])
                risk["max_drawdown"] = max_drawdown / 100.0 if max_drawdown > 1 else max_drawdown
            except (TypeError, ValueError):
                risk["max_drawdown"] = 0.03
        risk.pop("max_drawdown_pct", None)

        if "stop_loss" not in risk and isinstance(strategy.get("stop_loss"), dict):
            risk["stop_loss"] = strategy.pop("stop_loss")
        if "take_profit" not in risk and isinstance(strategy.get("take_profit"), dict):
            risk["take_profit"] = strategy.pop("take_profit")
        risk.pop("stop_loss_yuan", None)
        risk.pop("take_profit_yuan", None)
        strategy.pop("stop_loss_yuan", None)
        strategy.pop("take_profit_yuan", None)

        risk.setdefault("daily_loss_limit", 0.001)
        risk.setdefault("max_drawdown", 0.03)
        risk.setdefault("force_close_day", "14:55")
        risk.setdefault("no_overnight", True)
        risk.setdefault("stop_loss", {"type": "atr", "atr_multiplier": 1.5})
        risk.setdefault("take_profit", {"type": "atr", "atr_multiplier": 2.5})

        symbols = strategy.get("symbols") or []
        for sym in symbols:
            base = str(sym).split(".")[-1].lower()
            commodity = re.sub(r"(_main|\d+)$", "", base)
            if commodity in self.NIGHT_TRADING_COMMODITIES:
                risk.setdefault("force_close_night", "22:55")
                break

        strategy["risk"] = risk

        return yaml.safe_dump(
            strategy,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )

    @staticmethod
    def _mirror_condition(condition: str) -> str:
        """为单边 long 条件生成一个保守的镜像 short 条件。"""
        mirrored = str(condition)
        replacements = [
            (">=", "__LE__"),
            ("<=", "__GE__"),
            (">", "<"),
            ("<", ">"),
            ("__LE__", "<="),
            ("__GE__", ">="),
        ]
        for old, new in replacements:
            mirrored = mirrored.replace(old, new)
        return mirrored

    def _get_fallback_template(self) -> str:
        """获取内置的后备模板（本地引擎 + TqSdk 双引擎兼容格式）"""
        return """name: "FC-XXX_strategy_name"
description: "策略描述"
version: "1.0"
category: "trend_following"

# symbols 使用 _main 通配符：本地引擎匹配任意月份，TqSdk 自动解析为主力合约
symbols:
  - "SHFE.rb_main"

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

transaction_costs:
  slippage_per_unit: 1
  commission_per_lot_round_turn: 5

# risk 块：stop_loss 和 take_profit 必须在 risk 内部（本地引擎从此读取 atr_multiplier）
risk:
  daily_loss_limit: 0.001      # 比例（0.1%），非金额
  max_drawdown: 0.03            # 比例（3%），非百分数
  force_close_day: "14:55"
  force_close_night: "22:55"
  no_overnight: true
  stop_loss:
    type: "atr"
    atr_multiplier: 1.5
  take_profit:
    type: "atr"
    atr_multiplier: 2.5

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
        """验证 YAML 格式（双引擎兼容性校验）

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
                "transaction_costs",
            ]

            for field in required_fields:
                if field not in strategy:
                    return False, f"缺少必填字段: {field}"

            # 检查 position_fraction 或 position_size（本地引擎必须有）
            if "position_fraction" not in strategy and "position_size" not in strategy:
                return False, "缺少仓位配置（position_fraction 或 position_size）"

            # 检查 signal 字段
            signal = strategy.get("signal", {})
            if "long_condition" not in signal or "short_condition" not in signal:
                return False, "signal 缺少 long_condition 或 short_condition"
            if not str(signal.get("long_condition") or "").strip():
                return False, "signal.long_condition 必须是非空字符串"
            if not str(signal.get("short_condition") or "").strip():
                return False, "signal.short_condition 必须是非空字符串"

            # 检查 factors
            factors = strategy.get("factors", [])
            if not factors:
                return False, "factors 不能为空"

            for factor in factors:
                if "factor_name" not in factor:
                    return False, "factor 缺少 factor_name"

            # 检查 symbols 格式（必须含 . 且使用 _main 通配符格式）
            symbols = strategy.get("symbols", [])
            for sym in symbols:
                if "." not in str(sym):
                    return False, f"symbol 格式错误（缺少交易所前缀）: {sym}"
                base = str(sym).split(".")[-1].lower()
                # 禁止硬编码月份合约（字母+4位数字，如 rb2505）
                import re
                if re.match(r'^[a-z]+\d{4}$', base):
                    return False, (
                        f"symbol '{sym}' 使用了硬编码月份合约，"
                        "请改用 _main 通配符（如 SHFE.rb_main）"
                    )

            # 检查 risk 字段
            risk = strategy.get("risk", {})

            # 禁止旧格式字段
            forbidden_risk_fields = [
                "stop_loss_yuan", "take_profit_yuan",
                "daily_loss_limit_yuan", "max_drawdown_pct",
            ]
            for bad_field in forbidden_risk_fields:
                if bad_field in risk:
                    return False, (
                        f"risk 使用了废弃字段 '{bad_field}'，"
                        "请使用 daily_loss_limit（比例）/ max_drawdown（比例）/ "
                        "stop_loss.atr_multiplier"
                    )

            # 检查 stop_loss 在 risk 内（本地引擎从 risk.stop_loss 读取）
            stop_loss = risk.get("stop_loss")
            if stop_loss is None:
                return False, "risk 缺少 stop_loss 配置（需放在 risk 内部）"
            if not isinstance(stop_loss, dict):
                return False, "risk.stop_loss 必须是映射类型（包含 type 和 atr_multiplier）"

            # 检查 force_close_day（防止 TqSdk 收盘前未平仓）
            if "force_close_day" not in risk:
                return False, "risk 缺少 force_close_day（如 '14:55'）"

            # 夜盘品种必须包含 force_close_night
            for sym in symbols:
                base = str(sym).split(".")[-1].lower()
                commodity = re.sub(r"(_main|\d+)$", "", base)
                if commodity in self.NIGHT_TRADING_COMMODITIES and "force_close_night" not in risk:
                    return False, f"夜盘品种 {commodity} 缺少 risk.force_close_night（如 '22:55'）"

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
