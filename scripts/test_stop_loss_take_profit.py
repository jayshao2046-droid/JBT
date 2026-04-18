#!/usr/bin/env python3
"""测试 YamlSignalExecutor 的止盈止损功能"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.decision.src.research.yaml_signal_executor import YAMLSignalExecutor


def test_atr_calculation():
    """测试 ATR 计算"""
    bars = [
        {"high": 100, "low": 95, "close": 98},
        {"high": 102, "low": 97, "close": 100},
        {"high": 105, "low": 99, "close": 103},
        {"high": 104, "low": 100, "close": 102},
        {"high": 106, "low": 101, "close": 105},
    ]

    atr_values = YAMLSignalExecutor._calculate_atr(bars, period=3)

    print("✅ ATR 计算测试:")
    for i, atr in atr_values.items():
        print(f"   Bar {i}: ATR = {atr:.2f}")

    assert len(atr_values) > 0, "ATR 应该有值"
    print()


def test_stop_loss_logic():
    """测试止损逻辑"""
    stop_loss_config = {
        "type": "atr",
        "atr_multiplier": 1.5,
        "atr_period": 14
    }

    # 测试多头止损
    should_stop = YAMLSignalExecutor._should_stop_loss(
        position=1,
        entry_price=100.0,
        current_price=95.0,  # 下跌 5 元
        stop_loss_config=stop_loss_config,
        atr=3.0  # ATR = 3, 止损距离 = 3 * 1.5 = 4.5
    )

    print("✅ 止损逻辑测试:")
    print(f"   多头止损 (入场100, 当前95, ATR=3, 倍数=1.5): {should_stop}")
    assert should_stop == True, "应该触发多头止损"

    # 测试空头止损
    should_stop = YAMLSignalExecutor._should_stop_loss(
        position=-1,
        entry_price=100.0,
        current_price=105.0,  # 上涨 5 元
        stop_loss_config=stop_loss_config,
        atr=3.0
    )

    print(f"   空头止损 (入场100, 当前105, ATR=3, 倍数=1.5): {should_stop}")
    assert should_stop == True, "应该触发空头止损"
    print()


def test_take_profit_logic():
    """测试止盈逻辑"""
    take_profit_config = {
        "type": "atr",
        "atr_multiplier": 2.5,
        "atr_period": 14
    }

    # 测试多头止盈
    should_profit = YAMLSignalExecutor._should_take_profit(
        position=1,
        entry_price=100.0,
        current_price=108.0,  # 上涨 8 元
        take_profit_config=take_profit_config,
        atr=3.0  # ATR = 3, 止盈距离 = 3 * 2.5 = 7.5
    )

    print("✅ 止盈逻辑测试:")
    print(f"   多头止盈 (入场100, 当前108, ATR=3, 倍数=2.5): {should_profit}")
    assert should_profit == True, "应该触发多头止盈"

    # 测试空头止盈
    should_profit = YAMLSignalExecutor._should_take_profit(
        position=-1,
        entry_price=100.0,
        current_price=92.0,  # 下跌 8 元
        take_profit_config=take_profit_config,
        atr=3.0
    )

    print(f"   空头止盈 (入场100, 当前92, ATR=3, 倍数=2.5): {should_profit}")
    assert should_profit == True, "应该触发空头止盈"
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("测试 YamlSignalExecutor 止盈止损功能")
    print("=" * 60)
    print()

    try:
        test_atr_calculation()
        test_stop_loss_logic()
        test_take_profit_logic()

        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    except AssertionError as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
