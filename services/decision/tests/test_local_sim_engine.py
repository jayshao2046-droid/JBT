"""本地 Sim 容灾引擎测试 — TASK-0076 CS1"""
from __future__ import annotations

import pytest

from src.research.local_sim_engine import LocalSimEngine, LocalSimOrder


# ------------------------------------------------------------------
# 测试 LocalSimEngine 初始化
# ------------------------------------------------------------------


def test_local_sim_engine_init():
    """测试 LocalSimEngine 初始化。"""
    engine = LocalSimEngine()
    assert engine.capital == 1_000_000.0
    assert len(engine.orders) == 0
    assert len(engine.positions) == 0


def test_local_sim_engine_custom_data_url():
    """测试自定义 data_service_url。"""
    engine = LocalSimEngine(data_service_url="http://192.168.31.76:8105")
    assert engine.sandbox.data_service_url == "http://192.168.31.76:8105"


# ------------------------------------------------------------------
# 测试下单功能
# ------------------------------------------------------------------


def test_place_order_buy():
    """测试买入订单。"""
    engine = LocalSimEngine()
    order = engine.place_order(
        symbol="KQ_m_CFFEX_IF2504",
        direction="buy",
        quantity=1,
        price=5000.0,
    )

    assert order.symbol == "KQ_m_CFFEX_IF2504"
    assert order.direction == "buy"
    assert order.quantity == 1
    assert order.price == 5000.0
    assert order.status == "filled"
    assert order.filled_at is not None

    # 检查持仓和资金
    assert engine.positions["KQ_m_CFFEX_IF2504"] == 1
    assert engine.capital == 1_000_000.0 - 5000.0


def test_place_order_sell():
    """测试卖出订单。"""
    engine = LocalSimEngine()

    # 先买入
    engine.place_order("KQ_m_CFFEX_IF2504", "buy", 2, 5000.0)

    # 再卖出
    order = engine.place_order("KQ_m_CFFEX_IF2504", "sell", 1, 5100.0)

    assert order.direction == "sell"
    assert order.status == "filled"

    # 检查持仓和资金
    assert engine.positions["KQ_m_CFFEX_IF2504"] == 1
    assert engine.capital == 1_000_000.0 - 5000.0 * 2 + 5100.0


def test_place_order_multiple_symbols():
    """测试多个合约下单。"""
    engine = LocalSimEngine()

    engine.place_order("IF2504", "buy", 1, 5000.0)
    engine.place_order("IC2504", "buy", 2, 6000.0)

    assert engine.positions["IF2504"] == 1
    assert engine.positions["IC2504"] == 2
    assert engine.capital == 1_000_000.0 - 5000.0 - 6000.0 * 2


# ------------------------------------------------------------------
# 测试订单查询
# ------------------------------------------------------------------


def test_get_order_exists():
    """测试查询存在的订单。"""
    engine = LocalSimEngine()
    order = engine.place_order("IF2504", "buy", 1, 5000.0)

    retrieved = engine.get_order(order.order_id)
    assert retrieved is not None
    assert retrieved.order_id == order.order_id
    assert retrieved.symbol == "IF2504"


def test_get_order_not_exists():
    """测试查询不存在的订单。"""
    engine = LocalSimEngine()
    retrieved = engine.get_order("non-existent-id")
    assert retrieved is None


# ------------------------------------------------------------------
# 测试持仓和资金查询
# ------------------------------------------------------------------


def test_get_positions_empty():
    """测试空持仓。"""
    engine = LocalSimEngine()
    positions = engine.get_positions()
    assert len(positions) == 0


def test_get_positions_with_orders():
    """测试有持仓时的查询。"""
    engine = LocalSimEngine()
    engine.place_order("IF2504", "buy", 1, 5000.0)
    engine.place_order("IC2504", "buy", 2, 6000.0)

    positions = engine.get_positions()
    assert positions["IF2504"] == 1
    assert positions["IC2504"] == 2


def test_get_capital():
    """测试资金查询。"""
    engine = LocalSimEngine()
    assert engine.get_capital() == 1_000_000.0

    engine.place_order("IF2504", "buy", 1, 5000.0)
    assert engine.get_capital() == 1_000_000.0 - 5000.0


# ------------------------------------------------------------------
# 测试重置功能
# ------------------------------------------------------------------


def test_reset_engine():
    """测试重置引擎。"""
    engine = LocalSimEngine()

    # 下单
    engine.place_order("IF2504", "buy", 1, 5000.0)
    assert len(engine.orders) > 0
    assert len(engine.positions) > 0
    assert engine.capital != 1_000_000.0

    # 重置
    engine.reset()
    assert len(engine.orders) == 0
    assert len(engine.positions) == 0
    assert engine.capital == 1_000_000.0


# ------------------------------------------------------------------
# 测试回测功能（集成测试，需要 data 服务）
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_strategy_backtest():
    """测试策略回测（需要 data 服务运行）。"""
    engine = LocalSimEngine(data_service_url="http://localhost:8105")

    strategy_config = {
        "symbol": "KQ_m_CFFEX_IF",
        "fast_period": 5,
        "slow_period": 20,
    }

    result = await engine.run_strategy_backtest(
        strategy_config=strategy_config,
        start_time="2024-01-01T00:00:00Z",
        end_time="2024-01-31T23:59:59Z",
        asset_type="futures",
        initial_capital=1_000_000,
    )

    assert result.backtest_id.startswith("sandbox-")
    assert result.status in ("completed", "failed")
    assert result.initial_capital == 1_000_000
