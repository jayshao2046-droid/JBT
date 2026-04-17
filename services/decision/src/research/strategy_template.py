"""
策略YAML标准模板

用于指导V3和Coder生成符合规范的策略文件
"""

STRATEGY_YAML_TEMPLATE = """
name: {strategy_name}
description: {description}

symbols:
  - {symbol}

timeframe_minutes: {timeframe}

factors:
{factors}

signal:
  long_condition: "{long_condition}"
  short_condition: "{short_condition}"
  confirm_bars: {confirm_bars}

market_filter:
  conditions:
{market_filter_conditions}

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

# 因子配置示例
FACTOR_EXAMPLES = {
    "ATR": {"period": 14},
    "ADX": {"period": 14},
    "RSI": {"period": 14},
    "MACD": {"fast": 12, "slow": 26, "signal": 9},
    "Bollinger": {"period": 20, "multiplier": 2},
    "EMA": {"period": 20},
    "SMA": {"period": 20},
    "Volume": {},
    "OBV": {},
    "CCI": {"period": 20},
    "Williams_R": {"period": 14},
    "KDJ": {"n_period": 9, "m1": 3, "m2": 3},
}

# 策略类型模板
STRATEGY_TYPE_TEMPLATES = {
    "volatility_breakout": {
        "description": "基于波动率突破的趋势跟踪策略",
        "recommended_factors": ["ATR", "ADX", "Volume"],
        "entry_logic": "当ATR突破均值且ADX>25时，根据价格突破方向入场",
        "exit_logic": "固定止损或反向信号",
        "risk_params": {
            "stop_loss_yuan": 1000,
            "position_fraction": 0.1,
        }
    },
    "trend_momentum": {
        "description": "基于趋势和动量的跟踪策略",
        "recommended_factors": ["EMA", "MACD", "ADX"],
        "entry_logic": "EMA金叉/死叉 + MACD确认 + ADX>25",
        "exit_logic": "反向信号或止损",
        "risk_params": {
            "stop_loss_yuan": 1200,
            "position_fraction": 0.12,
        }
    },
    "mean_reversion": {
        "description": "基于均值回归的反转策略",
        "recommended_factors": ["Bollinger", "RSI", "ATR"],
        "entry_logic": "价格触及布林带上下轨 + RSI超买超卖",
        "exit_logic": "回归中轨或止损",
        "risk_params": {
            "stop_loss_yuan": 800,
            "position_fraction": 0.08,
        }
    },
}

# 生产标准
PRODUCTION_STANDARDS = {
    "sharpe_ratio": 1.5,
    "trades_count": 20,
    "win_rate": 0.5,
    "max_drawdown": 0.03,
    "annualized_return": 0.15,
}

# 合约映射（主力合约）
MAIN_CONTRACT_MAPPING = {
    "SHFE.ru": "SHFE.ru2505",  # 橡胶
    "SHFE.rb": "SHFE.rb2505",  # 螺纹钢
    "DCE.p": "DCE.p2505",      # 棕榈油
    "DCE.i": "DCE.i2505",      # 铁矿石
    "DCE.jm": "DCE.jm2505",    # 焦煤
    "SHFE.cu": "SHFE.cu2505",  # 铜
    "SHFE.au": "SHFE.au2506",  # 黄金
}
