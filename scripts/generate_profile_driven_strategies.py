#!/usr/bin/env python3
"""
Profile 驱动的策略批量生成器 (v1)

读取 runtime/symbol_profiles/{interval}m/{EXCHANGE_PRODUCT}.json
根据 profile 特征（volatility / trend_strength / autocorr）选择策略族
生成 YAML 到 services/decision/strategy_library/{EXCHANGE.product}/{family}/

关键约定：
  - symbols 字段写 KQ.m@EXCHANGE.product（本地回测 + tqsdk 双兼容）
  - 夜盘品种加 force_close_night: '22:55'
  - 高波动品种限制最小时间框架
  - 输出: services/decision/strategy_library/{EXCHANGE.product}/{family}/
           STRAT_{exchange}_{product}_{family}_{interval}m.yaml

用法:
  python scripts/generate_profile_driven_strategies.py
  python scripts/generate_profile_driven_strategies.py --intervals 60 120
  python scripts/generate_profile_driven_strategies.py --symbols SHFE.rb DCE.i
  python scripts/generate_profile_driven_strategies.py --overwrite
"""

import argparse
import json
import re
from pathlib import Path
from typing import Optional

import yaml

# ─── 路径 ─────────────────────────────────────────────────────────
WORKSPACE_ROOT = Path(__file__).parent.parent
PROFILE_ROOT = WORKSPACE_ROOT / "runtime/symbol_profiles"
STRATEGY_LIBRARY_ROOT = WORKSPACE_ROOT / "services/decision/strategy_library"

# ─── 42个品种 ─────────────────────────────────────────────────────
ALL_42_SYMBOLS = [
    "CZCE.AP", "CZCE.CF", "CZCE.FG", "CZCE.MA", "CZCE.OI",
    "CZCE.PF", "CZCE.RM", "CZCE.SA", "CZCE.SR", "CZCE.TA", "CZCE.UR",
    "DCE.a",  "DCE.c",  "DCE.cs", "DCE.eb", "DCE.eg",
    "DCE.i",  "DCE.j",  "DCE.jd", "DCE.jm", "DCE.l",
    "DCE.lh", "DCE.m",  "DCE.p",  "DCE.pg", "DCE.pp",
    "DCE.v",  "DCE.y",
    "INE.sc",
    "SHFE.ag", "SHFE.al", "SHFE.au", "SHFE.bu", "SHFE.cu",
    "SHFE.fu", "SHFE.hc", "SHFE.ni", "SHFE.rb", "SHFE.ru",
    "SHFE.sp", "SHFE.ss", "SHFE.zn",
]

# ─── 时间框架 ─────────────────────────────────────────────────────
ALL_TIMEFRAMES = [5, 15, 30, 60, 120, 240]

# ─── 夜盘品种 ─────────────────────────────────────────────────────
NIGHT_TRADING_PRODUCTS = {
    "rb", "hc", "cu", "al", "zn", "ni", "ss", "au", "ag",
    "fu", "bu", "ru", "sp", "sc",
    "i",  "j",  "jm", "p",  "y",  "m",  "a",  "c",  "cs",
    "l",  "v",  "pp", "eg", "eb", "pg",
    "ma", "ta", "MA", "TA",
}

# ─── 交易成本 ──────────────────────────────────────────────────────
_TC = {
    "SHFE_ferrous":     {"slippage_per_unit": 1.0,   "commission_per_lot_round_turn": 3.0},
    "SHFE_industrial":  {"slippage_per_unit": 10.0,  "commission_per_lot_round_turn": 3.0},
    "SHFE_precious_ag": {"slippage_per_unit": 1.0,   "commission_per_lot_round_turn": 2.0},
    "SHFE_precious_au": {"slippage_per_unit": 0.02,  "commission_per_lot_round_turn": 2.0},
    "SHFE_energy":      {"slippage_per_unit": 1.0,   "commission_per_lot_round_turn": 3.0},
    "INE_crude":        {"slippage_per_unit": 0.1,   "commission_per_lot_round_turn": 5.0},
    "DCE_ferrous":      {"slippage_per_unit": 0.5,   "commission_per_lot_round_turn": 3.0},
    "DCE_agri":         {"slippage_per_unit": 1.0,   "commission_per_lot_round_turn": 2.0},
    "DCE_chemical":     {"slippage_per_unit": 1.0,   "commission_per_lot_round_turn": 2.0},
    "CZCE_agri":        {"slippage_per_unit": 1.0,   "commission_per_lot_round_turn": 2.0},
    "CZCE_chemical":    {"slippage_per_unit": 1.0,   "commission_per_lot_round_turn": 2.0},
    "default":          {"slippage_per_unit": 1.0,   "commission_per_lot_round_turn": 3.0},
}
_PRODUCT_TC_MAP = {
    "rb": "SHFE_ferrous",   "hc": "SHFE_ferrous",
    "cu": "SHFE_industrial","al": "SHFE_industrial","zn": "SHFE_industrial",
    "ni": "SHFE_industrial","ss": "SHFE_industrial",
    "ag": "SHFE_precious_ag","au": "SHFE_precious_au",
    "fu": "SHFE_energy",    "bu": "SHFE_energy",
    "ru": "SHFE_energy",    "sp": "SHFE_energy",
    "sc": "INE_crude",
    "i":  "DCE_ferrous",    "j":  "DCE_ferrous",   "jm": "DCE_ferrous",
    "a":  "DCE_agri",       "c":  "DCE_agri",      "cs": "DCE_agri",
    "jd": "DCE_agri",       "m":  "DCE_agri",      "y":  "DCE_agri",
    "p":  "DCE_agri",       "lh": "DCE_agri",
    "l":  "DCE_chemical",   "v":  "DCE_chemical",  "pp": "DCE_chemical",
    "eg": "DCE_chemical",   "eb": "DCE_chemical",  "pg": "DCE_chemical",
    "AP": "CZCE_agri",      "CF": "CZCE_agri",     "SR": "CZCE_agri",
    "OI": "CZCE_agri",      "RM": "CZCE_agri",     "SA": "CZCE_agri",
    "UR": "CZCE_agri",
    "MA": "CZCE_chemical",  "TA": "CZCE_chemical", "FG": "CZCE_chemical",
    "PF": "CZCE_chemical",
}


def _get_tc(product: str) -> dict:
    return _TC.get(_PRODUCT_TC_MAP.get(product, "default"), _TC["default"])


def _is_night(product: str) -> bool:
    return product in NIGHT_TRADING_PRODUCTS or product.lower() in NIGHT_TRADING_PRODUCTS


# ─── 时间框架参数缩放 ──────────────────────────────────────────────
def _tf_scale(tf: int) -> dict:
    if tf <= 15:
        return {"adx_t": 18, "adx_low": 15, "stop_scale": 1.0, "take_scale": 1.0, "confirm": 1}
    elif tf <= 60:
        return {"adx_t": 20, "adx_low": 17, "stop_scale": 1.1, "take_scale": 1.1, "confirm": 1}
    else:
        return {"adx_t": 23, "adx_low": 18, "stop_scale": 1.3, "take_scale": 1.2, "confirm": 2}


# ─── 策略族定义 ───────────────────────────────────────────────────
# 每个 family: factors, long_tpl, short_tpl, position_fraction,
#              stop_atr_base, take_atr_base, category, description
# 信号条件模板支持 {adx_t} / {adx_low} 占位符
_FAMILIES = {
    # ── 趋势跟随 ────────────────────────────────────────────────────
    "trend": {
        "description": "趋势跟随：MACD + EMA + ADX",
        "category": "trend_following",
        "position_fraction": 0.08,
        "stop_atr_base": 2.0,
        "take_atr_base": 3.0,
        "factors": [
            {"factor_name": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}},
            {"factor_name": "EMA",  "params": {"period": 20}},
            {"factor_name": "ADX",  "params": {"period": 14}},
            {"factor_name": "ATR",  "params": {"period": 14}},
        ],
        "long_tpl":  "macd_hist > 0 and close > ema and adx > {adx_t}",
        "short_tpl": "macd_hist < 0 and close < ema and adx > {adx_t}",
    },
    "ema_cross": {
        "description": "均线交叉趋势：EMA(9) 金叉/死叉 SMA(21)",
        "category": "trend_following",
        "position_fraction": 0.08,
        "stop_atr_base": 1.8,
        "take_atr_base": 2.8,
        "factors": [
            {"factor_name": "EMA", "params": {"period": 9}},
            {"factor_name": "SMA", "params": {"period": 21}},
            {"factor_name": "ATR", "params": {"period": 14}},
        ],
        "long_tpl":  "ema > sma and close > ema",
        "short_tpl": "ema < sma and close < ema",
    },
    "macd_adx": {
        "description": "MACD + ADX 强趋势确认",
        "category": "trend_following",
        "position_fraction": 0.08,
        "stop_atr_base": 2.0,
        "take_atr_base": 3.5,
        "factors": [
            {"factor_name": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}},
            {"factor_name": "ADX",  "params": {"period": 14}},
            {"factor_name": "ATR",  "params": {"period": 14}},
        ],
        "long_tpl":  "macd_hist > 0 and macd_line > 0 and adx > {adx_t}",
        "short_tpl": "macd_hist < 0 and macd_line < 0 and adx > {adx_t}",
    },
    "bollinger_trend": {
        "description": "布林带中轨方向趋势：价格站上/下中轨 + EMA方向 + ADX",
        "category": "trend_following",
        "position_fraction": 0.07,
        "stop_atr_base": 2.0,
        "take_atr_base": 3.0,
        "factors": [
            {"factor_name": "BollingerBands", "params": {"period": 20, "std_dev": 2}},
            {"factor_name": "EMA",            "params": {"period": 10}},
            {"factor_name": "ADX",            "params": {"period": 14}},
            {"factor_name": "ATR",            "params": {"period": 14}},
        ],
        "long_tpl":  "close > bollinger_mid and ema > bollinger_mid and adx > {adx_low}",
        "short_tpl": "close < bollinger_mid and ema < bollinger_mid and adx > {adx_low}",
    },
    "volume_trend": {
        "description": "量价趋势：MACD + 均线 + 成交量放大确认",
        "category": "trend_following",
        "position_fraction": 0.08,
        "stop_atr_base": 2.0,
        "take_atr_base": 3.0,
        "factors": [
            {"factor_name": "VolumeRatio", "params": {"period": 10}},
            {"factor_name": "EMA",         "params": {"period": 20}},
            {"factor_name": "SMA",         "params": {"period": 20}},
            {"factor_name": "MACD",        "params": {"fast": 12, "slow": 26, "signal": 9}},
            {"factor_name": "ATR",         "params": {"period": 14}},
        ],
        "long_tpl":  "macd_hist > 0 and ema > sma and volume_ratio > 1.0",
        "short_tpl": "macd_hist < 0 and ema < sma and volume_ratio > 1.0",
    },
    "multi_confirm": {
        "description": "多重确认趋势：MACD + RSI + ADX + EMA 四重过滤",
        "category": "trend_following",
        "position_fraction": 0.08,
        "stop_atr_base": 2.0,
        "take_atr_base": 3.0,
        "factors": [
            {"factor_name": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}},
            {"factor_name": "RSI",  "params": {"period": 14}},
            {"factor_name": "ADX",  "params": {"period": 14}},
            {"factor_name": "EMA",  "params": {"period": 20}},
            {"factor_name": "ATR",  "params": {"period": 14}},
        ],
        "long_tpl":  "macd_hist > 0 and rsi > 50 and adx > {adx_t} and close > ema",
        "short_tpl": "macd_hist < 0 and rsi < 50 and adx > {adx_t} and close < ema",
    },
    "supertrend_follow": {
        "description": "超趋势跟踪：Supertrend方向 + ADX强度过滤",
        "category": "trend_following",
        "position_fraction": 0.09,
        "stop_atr_base": 2.0,
        "take_atr_base": 3.5,
        "factors": [
            {"factor_name": "Supertrend", "params": {"period": 10, "multiplier": 3.0}},
            {"factor_name": "ADX",        "params": {"period": 14}},
            {"factor_name": "ATR",        "params": {"period": 14}},
        ],
        "long_tpl":  "supertrend_direction > 0 and adx > {adx_t}",
        "short_tpl": "supertrend_direction < 0 and adx > {adx_t}",
    },
    "donchian_breakout": {
        "description": "唐奇安通道突破：价格突破N期高低轨 + ADX趋势确认",
        "category": "breakout",
        "position_fraction": 0.09,
        "stop_atr_base": 2.0,
        "take_atr_base": 4.0,
        "factors": [
            {"factor_name": "DonchianBreakout", "params": {"period": 20}},
            {"factor_name": "ADX",              "params": {"period": 14}},
            {"factor_name": "ATR",              "params": {"period": 14}},
        ],
        "long_tpl":  "close > donchian_high and adx > {adx_t}",
        "short_tpl": "close < donchian_low and adx > {adx_t}",
    },
    "ema_cross_signal": {
        "description": "EMA快慢线交叉信号差值正负 + ADX趋势过滤",
        "category": "trend_following",
        "position_fraction": 0.08,
        "stop_atr_base": 2.0,
        "take_atr_base": 3.0,
        "factors": [
            {"factor_name": "EMA_Cross", "params": {"fast_period": 10, "slow_period": 20}},
            {"factor_name": "ADX",       "params": {"period": 14}},
            {"factor_name": "ATR",       "params": {"period": 14}},
        ],
        "long_tpl":  "ema_cross > 0 and adx > {adx_low}",
        "short_tpl": "ema_cross < 0 and adx > {adx_low}",
    },
    "parabolicsar_trend": {
        "description": "抛物线SAR趋势跟踪：SAR方向 + EMA方向 + ADX确认",
        "category": "trend_following",
        "position_fraction": 0.08,
        "stop_atr_base": 2.0,
        "take_atr_base": 3.0,
        "factors": [
            {"factor_name": "ParabolicSAR", "params": {"af_start": 0.02, "af_max": 0.2}},
            {"factor_name": "EMA",          "params": {"period": 20}},
            {"factor_name": "ADX",          "params": {"period": 14}},
            {"factor_name": "ATR",          "params": {"period": 14}},
        ],
        "long_tpl":  "psar_direction > 0 and close > ema and adx > {adx_low}",
        "short_tpl": "psar_direction < 0 and close < ema and adx > {adx_low}",
    },
    "aroon_trend": {
        "description": "Aroon趋势方向：Aroon上线强势 + 振荡子方向 + ADX确认",
        "category": "trend_following",
        "position_fraction": 0.07,
        "stop_atr_base": 1.8,
        "take_atr_base": 3.0,
        "factors": [
            {"factor_name": "Aroon", "params": {"period": 25}},
            {"factor_name": "ADX",   "params": {"period": 14}},
            {"factor_name": "ATR",   "params": {"period": 14}},
        ],
        "long_tpl":  "aroon_up > 70 and aroon_oscillator > 0 and adx > {adx_low}",
        "short_tpl": "aroon_up < 30 and aroon_oscillator < 0 and adx > {adx_low}",
    },

    # ── 均值回归 ────────────────────────────────────────────────────
    "mean_reversion": {
        "description": "布林带均值回归：价格触碰上下轨 + RSI超买超卖",
        "category": "mean_reversion",
        "position_fraction": 0.06,
        "stop_atr_base": 1.5,
        "take_atr_base": 2.0,
        "factors": [
            {"factor_name": "BollingerBands", "params": {"period": 20, "std_dev": 2}},
            {"factor_name": "RSI",            "params": {"period": 14}},
            {"factor_name": "ATR",            "params": {"period": 14}},
        ],
        "long_tpl":  "close < bollinger_lower and rsi < 35",
        "short_tpl": "close > bollinger_upper and rsi > 65",
    },
    "kdj_reversion": {
        "description": "KDJ超买超卖均值回归：KD双线极值 + RSI确认",
        "category": "mean_reversion",
        "position_fraction": 0.06,
        "stop_atr_base": 1.5,
        "take_atr_base": 2.0,
        "factors": [
            {"factor_name": "KDJ", "params": {"k_period": 9, "d_period": 3, "j_smooth": 3}},
            {"factor_name": "RSI", "params": {"period": 14}},
            {"factor_name": "ATR", "params": {"period": 14}},
        ],
        "long_tpl":  "kdj_k < 20 and kdj_d < 20 and rsi < 45",
        "short_tpl": "kdj_k > 80 and kdj_d > 80 and rsi > 55",
    },
    "bb_rsi_arb": {
        "description": "布林带+RSI统计套利：价格偏离均值2σ + RSI确认",
        "category": "mean_reversion",
        "position_fraction": 0.07,
        "stop_atr_base": 1.5,
        "take_atr_base": 2.2,
        "factors": [
            {"factor_name": "BollingerBands", "params": {"period": 20, "std_dev": 2}},
            {"factor_name": "RSI",            "params": {"period": 14}},
            {"factor_name": "ATR",            "params": {"period": 14}},
        ],
        "long_tpl":  "close < bollinger_lower and rsi < 40",
        "short_tpl": "close > bollinger_upper and rsi > 60",
    },
    "rsi_extreme": {
        "description": "RSI极值套利：RSI深度超卖/超买纯反转",
        "category": "mean_reversion",
        "position_fraction": 0.05,
        "stop_atr_base": 1.3,
        "take_atr_base": 1.8,
        "factors": [
            {"factor_name": "RSI", "params": {"period": 14}},
            {"factor_name": "ATR", "params": {"period": 14}},
        ],
        "long_tpl":  "rsi < 25",
        "short_tpl": "rsi > 75",
    },
    "wr_reversion": {
        "description": "Williams %R 极值均值回归：WR超买超卖反转",
        "category": "mean_reversion",
        "position_fraction": 0.06,
        "stop_atr_base": 1.5,
        "take_atr_base": 2.0,
        "factors": [
            {"factor_name": "WilliamsR", "params": {"period": 14}},
            {"factor_name": "EMA",       "params": {"period": 20}},
            {"factor_name": "ATR",       "params": {"period": 14}},
        ],
        "long_tpl":  "williams_r < -80 and close > ema",
        "short_tpl": "williams_r > -20 and close < ema",
    },

    # ── 突破 ─────────────────────────────────────────────────────────
    "breakout": {
        "description": "布林带放量突破：价格突破上下轨 + 成交量放大 + ADX趋势",
        "category": "breakout",
        "position_fraction": 0.10,
        "stop_atr_base": 2.0,
        "take_atr_base": 4.0,
        "factors": [
            {"factor_name": "BollingerBands", "params": {"period": 20, "std_dev": 2}},
            {"factor_name": "VolumeRatio",    "params": {"period": 10}},
            {"factor_name": "ADX",            "params": {"period": 14}},
            {"factor_name": "ATR",            "params": {"period": 14}},
        ],
        "long_tpl":  "close > bollinger_upper and volume_ratio > 1.3 and adx > {adx_t}",
        "short_tpl": "close < bollinger_lower and volume_ratio > 1.3 and adx > {adx_t}",
    },
    "volume_breakout": {
        "description": "量能突破：成交量大幅放量 + MACD方向确认",
        "category": "breakout",
        "position_fraction": 0.10,
        "stop_atr_base": 2.0,
        "take_atr_base": 3.5,
        "factors": [
            {"factor_name": "VolumeRatio", "params": {"period": 10}},
            {"factor_name": "MACD",        "params": {"fast": 12, "slow": 26, "signal": 9}},
            {"factor_name": "ATR",         "params": {"period": 14}},
        ],
        "long_tpl":  "volume_ratio > 1.5 and macd_hist > 0",
        "short_tpl": "volume_ratio > 1.5 and macd_hist < 0",
    },

    # ── 动量/震荡 ─────────────────────────────────────────────────────
    "momentum": {
        "description": "多因子动量：MACD + RSI + 成交量放大三重动量",
        "category": "momentum",
        "position_fraction": 0.10,
        "stop_atr_base": 2.0,
        "take_atr_base": 3.0,
        "factors": [
            {"factor_name": "MACD",        "params": {"fast": 12, "slow": 26, "signal": 9}},
            {"factor_name": "RSI",         "params": {"period": 14}},
            {"factor_name": "VolumeRatio", "params": {"period": 10}},
            {"factor_name": "ATR",         "params": {"period": 14}},
        ],
        "long_tpl":  "macd_hist > 0 and rsi > 50 and volume_ratio > 1.2",
        "short_tpl": "macd_hist < 0 and rsi < 50 and volume_ratio > 1.2",
    },
    "oscillation": {
        "description": "震荡策略：KDJ超卖/超买转折 + RSI方向确认",
        "category": "oscillator",
        "position_fraction": 0.06,
        "stop_atr_base": 1.5,
        "take_atr_base": 2.5,
        "factors": [
            {"factor_name": "KDJ", "params": {"k_period": 9, "d_period": 3, "j_smooth": 3}},
            {"factor_name": "RSI", "params": {"period": 14}},
            {"factor_name": "ATR", "params": {"period": 14}},
        ],
        "long_tpl":  "kdj_k < 30 and kdj_k > kdj_d and rsi < 45",
        "short_tpl": "kdj_k > 70 and kdj_k < kdj_d and rsi > 55",
    },
}


# ─── profile 驱动的族选择逻辑 ─────────────────────────────────────
def select_families_for_profile(profile: dict, interval: int) -> list:
    """
    根据 profile 特征和时间框架返回合适的策略族名列表。

    时间框架约束（波动率过高→短周期噪声太多）：
      vol > 0.30 (极高)：只用 60/120/240m
      vol > 0.15 (高)：只用 30/60/120/240m
      vol > 0.08 (中)：只用 15/30/60/120/240m
      vol <= 0.08 (低)：所有周期均可

    策略族选择：
      trend_strength 强(>=50) + autocorr 不负 → 趋势族优先
      autocorr < -0.1 + trend_strength 弱(<40) → 均值回归族优先
      混合情况 → 两类都选，各取代表
      突破族始终保留
    """
    vol = profile.get("volatility_1y", 0.10)
    trend = profile.get("trend_strength_1y", 50.0)
    autocorr = profile.get("autocorr_1y", 0.0)

    # ── 时间框架过滤（波动率太高，短周期意义不大）──────────────────
    if vol > 0.30 and interval < 60:
        return []
    if vol > 0.15 and interval < 30:
        return []
    if vol > 0.08 and interval < 15:
        return []

    families = []

    # ── 趋势跟随族 ─────────────────────────────────────────────────
    trend_families = [
        "trend", "ema_cross", "macd_adx", "bollinger_trend",
        "multi_confirm", "supertrend_follow", "donchian_breakout",
        "ema_cross_signal", "parabolicsar_trend", "aroon_trend",
        "volume_trend",
    ]
    # ── 均值回归族 ─────────────────────────────────────────────────
    reversion_families = [
        "mean_reversion", "kdj_reversion", "bb_rsi_arb",
        "rsi_extreme", "wr_reversion",
    ]
    # ── 突破族 ─────────────────────────────────────────────────────
    breakout_families = ["breakout", "volume_breakout"]
    # ── 动量族 ─────────────────────────────────────────────────────
    momentum_families = ["momentum", "oscillation"]

    # 强趋势市场（ADX高，autocorr 非负）
    is_trending = trend >= 50 and autocorr > -0.05
    # 均值回归市场（autocorr 负且趋势弱）
    is_mean_reverting = autocorr < -0.10 and trend < 45
    # 震荡市（低波动，弱趋势）
    is_oscillating = vol < 0.08 and trend < 45

    if is_trending:
        families.extend(trend_families)
        families.extend(breakout_families)
        families.extend(momentum_families[:1])  # momentum
    elif is_mean_reverting:
        families.extend(reversion_families)
        families.extend(breakout_families)
        families.extend(trend_families[:3])  # 少量趋势策略作对冲
    elif is_oscillating:
        families.extend(reversion_families)
        families.extend(momentum_families)
        families.extend(trend_families[:3])
    else:
        # 混合市场：全量
        families.extend(trend_families)
        families.extend(reversion_families)
        families.extend(breakout_families)
        families.extend(momentum_families)

    return list(dict.fromkeys(families))  # 去重保序


# ─── 波动率驱动的参数调整 ─────────────────────────────────────────
def _vol_adjust(profile: dict, base_stop: float, base_take: float, base_pos: float):
    vol = profile.get("volatility_1y", 0.10)
    if vol > 0.30:
        return round(base_stop * 1.6, 2), round(base_take * 1.4, 2), round(base_pos * 0.45, 3)
    elif vol > 0.20:
        return round(base_stop * 1.35, 2), round(base_take * 1.25, 2), round(base_pos * 0.65, 3)
    elif vol > 0.12:
        return round(base_stop * 1.15, 2), round(base_take * 1.15, 2), round(base_pos * 0.85, 3)
    elif vol < 0.04:
        return round(base_stop * 0.8, 2), round(base_take * 0.9, 2), round(min(base_pos * 1.2, 0.15), 3)
    else:
        return round(base_stop, 2), round(base_take, 2), round(base_pos, 3)


# ─── profile 文件路径 ─────────────────────────────────────────────
def _profile_path(symbol: str, interval: int) -> Path:
    exchange, product = symbol.split(".", 1)
    filename = f"{exchange}_{product}.json"
    return PROFILE_ROOT / f"{interval}m" / filename


def _load_profile(symbol: str, interval: int) -> Optional[dict]:
    path = _profile_path(symbol, interval)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ─── YAML 文件名 / 策略名生成 ─────────────────────────────────────
def _strat_name(exchange: str, product: str, family: str, interval: int) -> str:
    """
    生成符合 backtest runner 命名规范的策略名。
    示例: STRAT_shfe_rb_trend_60m
    """
    return f"STRAT_{exchange.lower()}_{product.lower()}_{family}_{interval}m"


def _yaml_filename(exchange: str, product: str, family: str, interval: int) -> str:
    return _strat_name(exchange, product, family, interval) + ".yaml"


# ─── YAML 构建 ────────────────────────────────────────────────────
def build_yaml(symbol: str, profile: dict, family_name: str, interval: int) -> dict:
    """
    构建一个完整的策略 YAML 字典。
    symbols 字段写 KQ.m@EXCHANGE.product，兼容本地回测和 tqsdk。
    """
    exchange, product = symbol.split(".", 1)
    fam = _FAMILIES[family_name]
    scale = _tf_scale(interval)
    stop, take, pos = _vol_adjust(
        profile,
        fam["stop_atr_base"],
        fam["take_atr_base"],
        fam["position_fraction"],
    )
    stop = round(stop * scale["stop_scale"], 2)
    take = round(take * scale["take_scale"], 2)
    pos = round(pos, 3)

    tc = _get_tc(product)
    is_night = _is_night(product)

    long_cond  = fam["long_tpl"].format(**scale)
    short_cond = fam["short_tpl"].format(**scale)

    strat_name = _strat_name(exchange, product, family_name, interval)

    doc = {
        "name": strat_name,
        "description": f"{symbol} {fam['description']} {interval}m",
        "version": "1.0",
        "category": fam["category"],
        "factors": fam["factors"],
        "signal": {
            "long_condition":  long_cond,
            "short_condition": short_cond,
            "confirm_bars": scale["confirm"],
        },
        "timeframe_minutes": interval,
        "position_fraction": pos,
        "symbols": [f"KQ.m@{symbol}"],
        "transaction_costs": {
            "slippage_per_unit": tc["slippage_per_unit"],
            "commission_per_lot_round_turn": tc["commission_per_lot_round_turn"],
        },
        "risk": {
            "force_close_day": "14:55",
            "no_overnight": True,
            "stop_loss": {
                "type": "atr",
                "atr_multiplier": stop,
            },
            "take_profit": {
                "type": "atr",
                "atr_multiplier": take,
            },
        },
        "tags": [exchange, product, family_name, fam["category"], f"{interval}m"],
    }
    if is_night:
        doc["risk"]["force_close_night"] = "22:55"

    return doc


# ─── 主生成函数 ───────────────────────────────────────────────────
def generate(
    symbols: list,
    intervals: list,
    overwrite: bool = False,
    dry_run: bool = False,
) -> dict:
    stats = {"generated": 0, "skipped": 0, "no_profile": 0, "no_family": 0}

    for symbol in symbols:
        exchange, product = symbol.split(".", 1)

        for interval in intervals:
            profile = _load_profile(symbol, interval)
            if profile is None:
                print(f"  ⚠️  缺少 profile: {symbol} {interval}m → 跳过")
                stats["no_profile"] += 1
                continue

            families = select_families_for_profile(profile, interval)
            if not families:
                stats["no_family"] += 1
                continue

            for family_name in families:
                if family_name not in _FAMILIES:
                    continue

                out_dir = STRATEGY_LIBRARY_ROOT / symbol / family_name
                filename = _yaml_filename(exchange, product, family_name, interval)
                out_path = out_dir / filename

                if out_path.exists() and not overwrite:
                    stats["skipped"] += 1
                    continue

                doc = build_yaml(symbol, profile, family_name, interval)

                if not dry_run:
                    out_dir.mkdir(parents=True, exist_ok=True)
                    with open(out_path, "w", encoding="utf-8") as f:
                        yaml.dump(
                            doc, f,
                            allow_unicode=True,
                            default_flow_style=False,
                            sort_keys=False,
                        )
                stats["generated"] += 1

    return stats


# ─── CLI ──────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Profile 驱动策略批量生成器")
    parser.add_argument(
        "--intervals", nargs="+", type=int,
        default=ALL_TIMEFRAMES,
        choices=ALL_TIMEFRAMES,
        help="要生成的时间框架（分钟），默认全部: 5 15 30 60 120 240",
    )
    parser.add_argument(
        "--symbols", nargs="+", type=str,
        default=None,
        help="指定品种（如 SHFE.rb DCE.i），默认全部42个",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="覆盖已存在的 YAML 文件",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="仅统计数量，不写文件",
    )
    args = parser.parse_args()

    symbols = args.symbols or ALL_42_SYMBOLS
    intervals = sorted(set(args.intervals))
    overwrite = args.overwrite
    dry_run = args.dry_run

    print(f"\n{'='*72}")
    print(f"Profile 驱动策略生成器")
    print(f"{'='*72}")
    print(f"品种数:   {len(symbols)}")
    print(f"时间框架: {intervals}")
    print(f"策略族数: {len(_FAMILIES)} 个")
    print(f"输出目录: {STRATEGY_LIBRARY_ROOT}")
    print(f"覆盖模式: {'是' if overwrite else '否（跳过已存在）'}")
    print(f"Dry-run:  {'是' if dry_run else '否'}")
    print(f"{'='*72}\n")

    stats = generate(symbols, intervals, overwrite=overwrite, dry_run=dry_run)

    total_possible = len(symbols) * len(intervals) * len(_FAMILIES)
    print(f"\n{'='*72}")
    print(f"生成完成")
    print(f"{'='*72}")
    print(f"  ✅ 生成: {stats['generated']} 个")
    print(f"  ⏭️  跳过: {stats['skipped']} 个（已存在）")
    print(f"  ❌ 缺 profile: {stats['no_profile']} 次")
    print(f"  ⚡ 波动率/族为空: {stats['no_family']} 次")
    print(f"  理论最大: {total_possible} 个（42品种×{len(intervals)}周期×{len(_FAMILIES)}族）")
    if not dry_run and stats["generated"] > 0:
        print(f"\n  输出路径: {STRATEGY_LIBRARY_ROOT}")
    print(f"{'='*72}\n")


if __name__ == "__main__":
    main()
