#!/usr/bin/env python3
"""LLM 流水线：棕榈油(p) 策略批量生成

策略矩阵（7个）：
1. p_trend_following_60m_v1 — 低频趋势跟踪 (EMA + ADX + ATR)
2. p_trend_following_15m_v1 — 中频趋势跟踪 (MACD + ADX + ATR)
3. p_breakout_30m_v1 — 中频突破 (Bollinger + VolumeRatio + ATR)
4. p_mean_reversion_15m_v1 — 中频均值回归 (Bollinger + RSI + ATR)
5. p_intraday_momentum_5m_v1 — 日内动量 (ATR + RSI + VolumeRatio)
6. p_intraday_oscillation_5m_v1 — 日内震荡 (KDJ + Bollinger + ATR)
7. p_multi_factor_30m_v1 — 中频多因子 (MACD + CCI + ATR + VolumeRatio)

硬约束：
- 日盘 14:55 强制平仓
- 夜盘 22:55 强制平仓
- 禁止隔夜持仓

用法：
    cd /Users/jayshao/JBT/services/decision
    source ../../.venv/bin/activate
    python scripts/generate_llm_strategies_palm.py
"""
import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from typing import Optional

import yaml

# 项目路径
_BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BASE))

# 加载 decision 服务 .env（包含 NewCoin API 配置）
from dotenv import load_dotenv
load_dotenv(_BASE / ".env")

from src.research.symbol_profiler import SymbolProfiler
from src.research.code_generator import CodeGenerator
from src.llm.openai_client import OpenAICompatibleClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("llm_pipeline_palm")

# ── 配置 ──────────────────────────────────────────────
SYMBOL = "KQ_m_DCE_p"  # Mini data API 主力连续合约格式
SYMBOL_NAME = "p"
SYMBOL_CN = "棕榈油"
DATA_URL = "http://192.168.31.76:8105"

# 输出目录
OUTPUT_DIR = _BASE / "strategies" / "llm_generated" / SYMBOL_NAME
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 策略矩阵 ─────────────────────────────────────────
STRATEGY_SPECS = [
    {
        "name": "p_trend_following_60m_v1",
        "category": "trend_following",
        "timeframe": 60,
        "frequency": "低频",
        "factors": ["EMA", "ADX", "ATR"],
        "description": "60分钟EMA交叉+ADX趋势确认+ATR波动率过滤的低频趋势跟踪策略",
        "guidance": "使用双EMA(快线12/慢线26)交叉判断趋势方向, ADX>22确认趋势有效, ATR做动态止损",
    },
    {
        "name": "p_trend_following_15m_v1",
        "category": "trend_following",
        "timeframe": 15,
        "frequency": "中频",
        "factors": ["MACD", "ADX", "ATR"],
        "description": "15分钟MACD动量+ADX趋势过滤+ATR风控的中频趋势跟踪策略",
        "guidance": "MACD柱状图(macd_hist)判断动量方向和力度, ADX>20过滤震荡行情, ATR动态止损止盈",
    },
    {
        "name": "p_breakout_30m_v1",
        "category": "breakout",
        "timeframe": 30,
        "frequency": "中频",
        "factors": ["Bollinger", "VolumeRatio", "ATR"],
        "description": "30分钟布林带收窄后放量突破的中频突破策略",
        "guidance": "布林带bandwidth收窄表示蓄势, VolumeRatio>1.3确认放量突破, 突破方向跟随, ATR止损",
    },
    {
        "name": "p_mean_reversion_15m_v1",
        "category": "mean_reversion",
        "timeframe": 15,
        "frequency": "中频",
        "factors": ["Bollinger", "RSI", "ATR"],
        "description": "15分钟布林带+RSI超买超卖的中频均值回归策略",
        "guidance": "价格接近布林带上下轨(middle±0.2*bandwidth)且RSI进入超买(>65)或超卖(<35)区间时反向开仓, ATR止损",
    },
    {
        "name": "p_intraday_momentum_5m_v1",
        "category": "intraday_momentum",
        "timeframe": 5,
        "frequency": "日内",
        "factors": ["ATR", "RSI", "VolumeRatio"],
        "description": "5分钟ATR波动脉冲+RSI动量+成交量确认的日内动量策略",
        "guidance": "ATR突然放大(>0.004*close)表示波动脉冲, RSI方向确认(>55做多/<45做空), VolumeRatio>1.3放量确认",
    },
    {
        "name": "p_intraday_oscillation_5m_v1",
        "category": "intraday_oscillation",
        "timeframe": 5,
        "frequency": "日内",
        "factors": ["KDJ", "Bollinger", "ATR"],
        "description": "5分钟KDJ+布林带震荡区间交易的日内震荡策略",
        "guidance": "KDJ的K值在20-80区间配合布林带中轨判断支撑阻力, K<30且close>bb_lower做多, K>70且close<bb_upper做空, ATR控制止损",
    },
    {
        "name": "p_multi_factor_30m_v1",
        "category": "multi_factor",
        "timeframe": 30,
        "frequency": "中频",
        "factors": ["MACD", "CCI", "ATR", "VolumeRatio"],
        "description": "30分钟MACD+CCI+ATR+成交量四因子复合的多因子策略",
        "guidance": "MACD趋势方向(macd_hist>0) + CCI极端值(>100做多/<-100做空) + ATR波动确认(>0.003*close) + VolumeRatio放量(>1.2), 多因子共振时开仓",
    },
]


def _build_single_design_prompt(spec: dict, features_desc: str) -> str:
    """为单个策略构建 LLM 设计提示词"""
    factors_str = "、".join(spec["factors"])
    factors_json = json.dumps(spec["factors"])
    return f"""你是 JBT 首席策略架构师。请为棕榈油(DCE.p)设计一个 **{spec['category']}** 类型的交易策略。

【品种特征】
{features_desc}

【策略要求】
- 策略名称: {spec['name']}
- 策略分类: {spec['category']}
- 时间周期: {spec['timeframe']} 分钟
- 交易频率: {spec['frequency']}
- 核心因子: {factors_str}
- 设计方向: {spec['guidance']}

【硬约束 — 日内交易】
- 日盘 14:55 强制平仓
- 夜盘 22:55 强制平仓
- 禁止隔夜持仓 (no_overnight: true)
- 所有持仓在上述时点必须全部清零

【可用因子库】
只能使用以下因子，不要创造新因子：
- ATR: 平均真实波幅 (params: period)
- ADX: 平均趋向指标 (params: period)
- RSI: 相对强弱指标 (params: period)
- MACD: 指数平滑异同移动平均线 (params: fast, slow, signal)
- SMA: 简单移动平均 (params: period)
- EMA: 指数移动平均 (params: period)
- Bollinger: 布林带 (params: period, std_dev)
- VolumeRatio: 成交量比率 (params: period)
- CCI: 商品通道指标 (params: period)
- KDJ: 随机指标 (params: k_period, d_period, j_period)

【参数建议】
- ATR阈值: 0.002-0.005 * close（初始建议 0.003）
- VolumeRatio: 1.2-1.5（初始建议 1.3）
- ADX: 20-25（初始建议 22）
- RSI: 30-70 区间（不要使用极端值 <20 或 >80）
- Bollinger std_dev: 2.0（标准值）

【入场/出场规则语法】
- 必须是简单的阈值比较
- 因子名自动转小写变量: ATR → atr, ADX → adx, MACD → macd_hist, RSI → rsi
- KDJ 输出: kdj_k, kdj_d, kdj_j
- Bollinger 输出: bb_upper, bb_middle, bb_lower, bb_bandwidth
- 可用内置变量: close, open, high, low, volume
- 可用运算符: >, <, >=, <=, ==, and, or
- 正确示例: "atr > 0.003 * close and adx > 22 and rsi > 50"
- 禁止: 函数调用、历史值引用、创造新变量

【风险管理】
- 棕榈油交易单位: 10吨/手
- 最小变动价位: 2元/吨 (1 tick = 20元/手)
- 手续费: 约 2.5 元/手（单边）
- 止损使用 ATR 倍数: atr_multiplier 1.2~2.0
- 止盈使用 ATR 倍数: atr_multiplier 2.0~3.0
- position_fraction: 0.08

【输出格式】
严格按照以下 JSON 格式输出（只输出1个策略）：

{{
  "strategy_name": "{spec['name']}",
  "logic_description": "策略逻辑的详细描述",
  "recommended_factors": {factors_json},
  "entry_logic": "做多入场条件（简单阈值比较）",
  "exit_logic": "做多出场条件（简单阈值比较）",
  "short_entry_logic": "做空入场条件",
  "short_exit_logic": "做空出场条件",
  "risk_management": "日盘14:55强制平仓 + 夜盘22:55强制平仓 + ATR动态止损 atr_multiplier=1.5",
  "innovation_points": ["创新点1", "创新点2"],
  "expected_advantage": "预期优势描述"
}}

【严禁】
- 不要输出任何解释文字
- 不要使用 markdown 代码块标记
- 只输出纯 JSON
"""


def _features_to_desc(features) -> str:
    """将 SymbolFeatures 转为文本描述"""
    return f"""品种: DCE.p (大商所棕榈油)
- 波动率: {features.volatility_weighted} (3个月: {features.volatility_3m:.4f}, 1年: {features.volatility_1y:.4f})
- 趋势强度: {features.trend_strength_weighted} (3个月: {features.trend_strength_3m:.4f}, 1年: {features.trend_strength_1y:.4f})
- 流动性: {features.liquidity}
- 自相关性: {features.autocorr_3m:.4f}
- 偏度: {features.skewness:.4f}
- 峰度: {features.kurtosis:.4f}"""


# 棕榈油默认特征（数据不可达时的降级方案）
DEFAULT_FEATURES_DESC = """品种: DCE.p (大商所棕榈油)
- 波动率: Medium (3个月: 0.0180, 1年: 0.0160)
- 趋势强度: Strong (3个月: 0.4200, 1年: 0.3800)
- 流动性: High
- 自相关性: 0.1200
- 偏度: -0.2500
- 峰度: 3.5000
- 油脂板块龙头，日均成交量大，夜盘21:00-23:00
- 波动受马来西亚棕榈油期货(BMD CPO)和豆油、菜油联动影响
- 季节性明显（东南亚产量周期）"""


def _extract_json(content: str) -> Optional[dict]:
    """从 LLM 回复中提取 JSON"""
    content = content.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', content, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _ensure_force_close(yaml_path: Path) -> bool:
    """后处理: 确保 YAML 包含强制平仓约束和完整风控字段"""
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            strategy = yaml.safe_load(f)

        if not isinstance(strategy, dict):
            logger.warning(f"   ⚠️ YAML 内容不是字典类型")
            return False

        modified = False
        risk = strategy.setdefault("risk", {})

        # 强制平仓时间
        if risk.get("force_close_day") != "14:55":
            risk["force_close_day"] = "14:55"
            modified = True
        if risk.get("force_close_night") != "22:55":
            risk["force_close_night"] = "22:55"
            modified = True
        if not risk.get("no_overnight"):
            risk["no_overnight"] = True
            modified = True

        # 确保止损止盈用 ATR
        if "stop_loss" not in strategy:
            strategy["stop_loss"] = {"type": "atr", "atr_multiplier": 1.5, "atr_period": 14}
            modified = True
        if "take_profit" not in strategy:
            strategy["take_profit"] = {"type": "atr", "atr_multiplier": 2.5, "atr_period": 14}
            modified = True

        # 确保交易成本
        if "transaction_costs" not in strategy:
            strategy["transaction_costs"] = {
                "slippage_per_unit": 2,
                "commission_per_lot_round_turn": 5,
            }
            modified = True

        if modified:
            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(strategy, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            logger.info(f"   🔧 后处理: 已注入强制平仓 + 风控约束")

        return True
    except Exception as e:
        logger.error(f"   ❌ 后处理失败: {e}")
        return False


async def main():
    start_time = datetime.now()

    logger.info("=" * 80)
    logger.info(f"LLM 流水线 — {SYMBOL_CN}({SYMBOL_NAME}) 策略批量生成")
    logger.info(f"策略数量: {len(STRATEGY_SPECS)}")
    logger.info(f"输出目录: {OUTPUT_DIR}")
    logger.info(f"硬约束: 14:55 日盘平仓 / 22:55 夜盘平仓 / 禁止隔夜")
    logger.info("=" * 80)

    # ── 初始化客户端 ──
    client = OpenAICompatibleClient(component="llm_pipeline_palm")
    designer_model = "gpt-5.4"
    coder_model = "deepseek-v3.2"  # Coder 角色，降级链: deepseek-v3 → qwen3.6-plus

    logger.info(f"📡 设计师模型: {designer_model} (via NewCoin)")
    logger.info(f"📡 编码器模型: {coder_model} (via NewCoin)")
    logger.info(f"📡 数据服务: {DATA_URL}")

    # ── 第一步: 品种特征分析 ──
    logger.info("")
    logger.info("━" * 60)
    logger.info("第一步：品种特征分析 (SymbolProfiler)")
    logger.info("━" * 60)

    features_desc = DEFAULT_FEATURES_DESC
    try:
        profiler = SymbolProfiler(data_service_url=DATA_URL)
        features = await profiler.calculate_features(symbol=SYMBOL)

        if features:
            features_desc = _features_to_desc(features)
            logger.info(f"✅ 特征分析完成")

            # 保存特征
            profile_path = OUTPUT_DIR / f"{SYMBOL_NAME}_profile.json"
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump({
                    "symbol": SYMBOL,
                    "volatility_weighted": features.volatility_weighted,
                    "trend_strength_weighted": features.trend_strength_weighted,
                    "liquidity": features.liquidity,
                    "volatility_3m": features.volatility_3m,
                    "volatility_1y": features.volatility_1y,
                    "trend_strength_3m": features.trend_strength_3m,
                    "trend_strength_1y": features.trend_strength_1y,
                    "autocorr_3m": features.autocorr_3m,
                    "skewness": features.skewness,
                    "kurtosis": features.kurtosis,
                    "calculated_at": datetime.now().isoformat(),
                }, f, ensure_ascii=False, indent=2)
        else:
            logger.warning("⚠️ 品种特征计算返回空，使用默认特征")
    except Exception as e:
        logger.warning(f"⚠️ 品种特征分析失败({e})，使用默认特征继续")

    logger.info(f"品种特征:\n{features_desc}")

    # ── 第二步: 策略设计 + YAML 生成 ──
    logger.info("")
    logger.info("━" * 60)
    logger.info("第二步：策略设计 + YAML 生成 (逐个生成)")
    logger.info("━" * 60)

    generator = CodeGenerator(
        online_client=client,
        model=coder_model,
        output_dir=str(OUTPUT_DIR),
    )

    results = []

    for i, spec in enumerate(STRATEGY_SPECS, 1):
        logger.info(f"\n{'─' * 50}")
        logger.info(f"[{i}/{len(STRATEGY_SPECS)}] {spec['name']}")
        logger.info(f"  分类: {spec['category']} | 周期: {spec['timeframe']}m | 频率: {spec['frequency']}")
        logger.info(f"  因子: {', '.join(spec['factors'])}")

        # 2a: LLM 策略设计
        logger.info(f"  → 调用设计师模型 ({designer_model})...")
        prompt = _build_single_design_prompt(spec, features_desc)
        messages = [
            {
                "role": "system",
                "content": "你是 JBT 首席策略架构师，擅长设计日内期货交易策略。只输出纯 JSON，不要任何解释。",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = await client.chat(designer_model, messages, timeout=120.0)
            if "error" in response:
                logger.error(f"  ❌ 设计失败: {response['error']}")
                results.append({"spec": spec, "status": "design_failed", "error": response["error"]})
                continue

            content = response.get("content", "")
            design = _extract_json(content)
            if not design:
                logger.error(f"  ❌ 无法解析设计 JSON, 原始内容前200字: {content[:200]}")
                results.append({"spec": spec, "status": "parse_failed"})
                continue

            # 确保关键字段
            design["strategy_name"] = spec["name"]
            if "recommended_factors" not in design:
                design["recommended_factors"] = spec["factors"]
            if "risk_management" not in design:
                design["risk_management"] = "日盘14:55强制平仓 + 夜盘22:55强制平仓 + ATR动态止损 atr_multiplier=1.5"

            desc_short = design.get("logic_description", "")[:80]
            logger.info(f"  ✅ 设计完成: {desc_short}")
            logger.info(f"     入场: {design.get('entry_logic', 'N/A')[:80]}")

        except Exception as e:
            logger.error(f"  ❌ 设计异常: {e}")
            results.append({"spec": spec, "status": "design_error", "error": str(e)})
            continue

        # 2b: YAML 代码生成
        logger.info(f"  → 调用编码器模型 ({coder_model})...")
        try:
            yaml_path = await generator.generate_yaml_strategy(
                strategy_design=design,
                symbol=SYMBOL,
                timeframe=spec["timeframe"],
            )

            if not yaml_path:
                logger.error(f"  ❌ YAML 生成失败")
                results.append({"spec": spec, "status": "yaml_failed", "design": design})
                continue

            # 2c: 后处理 — 注入强制平仓
            _ensure_force_close(yaml_path)

            logger.info(f"  ✅ 策略文件: {yaml_path}")
            results.append({"spec": spec, "status": "success", "yaml_path": str(yaml_path)})

        except Exception as e:
            logger.error(f"  ❌ YAML 生成异常: {e}")
            results.append({"spec": spec, "status": "yaml_error", "error": str(e)})

    # ── 汇总 ──
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"生成结果汇总 (耗时 {elapsed:.1f}s)")
    logger.info("=" * 80)

    success_count = sum(1 for r in results if r["status"] == "success")
    fail_count = len(results) - success_count

    for r in results:
        icon = "✅" if r["status"] == "success" else "❌"
        name = r["spec"]["name"]
        if r["status"] == "success":
            logger.info(f"  {icon} {name} → {r['yaml_path']}")
        else:
            logger.info(f"  {icon} {name} → {r['status']}: {r.get('error', 'N/A')}")

    logger.info(f"\n成功: {success_count}/{len(STRATEGY_SPECS)} | 失败: {fail_count}/{len(STRATEGY_SPECS)}")
    logger.info(f"输出目录: {OUTPUT_DIR}")

    # 保存运行报告
    report_path = OUTPUT_DIR / f"generation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "symbol": SYMBOL,
            "symbol_name": SYMBOL_NAME,
            "symbol_cn": SYMBOL_CN,
            "generated_at": datetime.now().isoformat(),
            "elapsed_seconds": round(elapsed, 1),
            "designer_model": designer_model,
            "coder_model": coder_model,
            "total": len(STRATEGY_SPECS),
            "success": success_count,
            "failed": fail_count,
            "constraints": {
                "force_close_day": "14:55",
                "force_close_night": "22:55",
                "no_overnight": True,
            },
            "results": [
                {
                    "name": r["spec"]["name"],
                    "category": r["spec"]["category"],
                    "timeframe": r["spec"]["timeframe"],
                    "status": r["status"],
                    "yaml_path": r.get("yaml_path"),
                    "error": r.get("error"),
                }
                for r in results
            ],
        }, f, ensure_ascii=False, indent=2)
    logger.info(f"运行报告: {report_path}")

    # ── 计费统计 ──
    from src.llm.billing import get_billing_tracker
    tracker = get_billing_tracker()
    summary = tracker.get_hourly_summary()
    logger.info("")
    logger.info("━" * 60)
    logger.info("LLM 计费统计")
    logger.info("━" * 60)
    logger.info(f"  总调用: {summary['total_calls']} 次")
    logger.info(f"  输入 Token: {summary['total_input_tokens']:,}")
    logger.info(f"  输出 Token: {summary['total_output_tokens']:,}")
    logger.info(f"  总费用: ¥{summary['total_cost']:.6f}")
    if summary.get("by_model"):
        for model_name, stats in summary["by_model"].items():
            logger.info(
                f"    {model_name}: {stats['calls']}次 "
                f"in={stats['input_tokens']:,} out={stats['output_tokens']:,} "
                f"¥{stats['total_cost']:.6f}"
            )
    # 显式 flush 计费数据到磁盘
    flush_path = tracker.flush_hourly()
    if flush_path:
        logger.info(f"  计费数据已持久化: {flush_path}")
    else:
        logger.info("  本小时无计费数据需要 flush")

    # 关闭客户端
    try:
        await client._client.aclose()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
