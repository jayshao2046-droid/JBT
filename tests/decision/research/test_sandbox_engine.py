"""
沙箱回测引擎测试 — TASK-0056 CA2'
用 mock httpx 响应，不实际调 data 服务。
"""
from __future__ import annotations

import json
import math
import pytest
import httpx
import respx

from services.decision.src.research.sandbox_engine import SandboxEngine, SandboxResult


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

def _make_bars(n: int, base_price: float = 100.0, trend: float = 0.5) -> list[dict]:
    """生成 n 条 bars，带简单上升趋势以产生交叉信号。"""
    bars = []
    for i in range(n):
        price = base_price + trend * i + (2.0 if i % 7 < 3 else -1.5)
        bars.append({
            "datetime": f"2025-01-{1 + i:02d}T09:30:00",
            "open": round(price - 0.3, 2),
            "high": round(price + 1.0, 2),
            "low": round(price - 1.0, 2),
            "close": round(price, 2),
            "volume": 1000 + i * 10,
            "open_interest": 5000 + i,
        })
    return bars


def _make_flat_bars(n: int, price: float = 100.0) -> list[dict]:
    """生成 n 条无趋势 bars（不产生交叉信号）。"""
    return [
        {
            "datetime": f"2025-01-{1 + i:02d}T09:30:00",
            "open": price,
            "high": price + 0.1,
            "low": price - 0.1,
            "close": price,
            "volume": 1000,
            "open_interest": 5000,
        }
        for i in range(n)
    ]


DATA_URL = "http://test-data:8105"
BARS_50 = _make_bars(50)
FLAT_BARS_50 = _make_flat_bars(50)


@pytest.fixture
def engine() -> SandboxEngine:
    return SandboxEngine(data_service_url=DATA_URL)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_backtest_completed_futures(engine: SandboxEngine) -> None:
    """正常期货回测应返回 completed 状态与合理指标。"""
    respx.get(f"{DATA_URL}/api/v1/bars").mock(
        return_value=httpx.Response(200, json=BARS_50)
    )
    result = await engine.run_backtest(
        strategy_config={"short_window": 3, "long_window": 10, "symbol": "KQ_m_CFFEX_IF"},
        start_time="2025-01-01",
        end_time="2025-02-20",
        asset_type="futures",
        initial_capital=1_000_000,
    )
    assert isinstance(result, SandboxResult)
    assert result.status == "completed"
    assert result.backtest_id.startswith("sandbox-")
    assert result.initial_capital == 1_000_000
    assert isinstance(result.total_return, float)
    assert isinstance(result.sharpe_ratio, float)
    assert 0.0 <= result.max_drawdown <= 1.0
    assert 0.0 <= result.win_rate <= 1.0
    assert result.trades_count >= 0


@pytest.mark.asyncio
@respx.mock
async def test_backtest_completed_stock(engine: SandboxEngine) -> None:
    """股票回测走 /api/v1/stocks/bars 端点。"""
    respx.get(f"{DATA_URL}/api/v1/stocks/bars").mock(
        return_value=httpx.Response(200, json=BARS_50)
    )
    result = await engine.run_backtest(
        strategy_config={"short_window": 3, "long_window": 10, "symbol": "SH_600000"},
        start_time="2025-01-01",
        end_time="2025-02-20",
        asset_type="stock",
        initial_capital=500_000,
    )
    assert result.status == "completed"
    assert result.initial_capital == 500_000


@pytest.mark.asyncio
@respx.mock
async def test_backtest_unsupported_asset_type(engine: SandboxEngine) -> None:
    """不支持的 asset_type 应返回 failed。"""
    result = await engine.run_backtest(
        strategy_config={"symbol": "X"},
        start_time="2025-01-01",
        end_time="2025-01-31",
        asset_type="crypto",
    )
    assert result.status == "failed"
    assert "unsupported" in result.performance_metrics.get("error", "")


@pytest.mark.asyncio
@respx.mock
async def test_backtest_data_service_error(engine: SandboxEngine) -> None:
    """data 服务返回 500 时回测应 fail。"""
    respx.get(f"{DATA_URL}/api/v1/bars").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    result = await engine.run_backtest(
        strategy_config={"symbol": "KQ_m_CFFEX_IF"},
        start_time="2025-01-01",
        end_time="2025-01-31",
        asset_type="futures",
    )
    assert result.status == "failed"
    assert result.trades_count == 0


@pytest.mark.asyncio
@respx.mock
async def test_backtest_empty_bars(engine: SandboxEngine) -> None:
    """空 bars 应完成但无交易。"""
    respx.get(f"{DATA_URL}/api/v1/bars").mock(
        return_value=httpx.Response(200, json=[])
    )
    result = await engine.run_backtest(
        strategy_config={"symbol": "KQ_m_CFFEX_IF"},
        start_time="2025-01-01",
        end_time="2025-01-31",
    )
    assert result.status == "completed"
    assert result.trades_count == 0
    assert result.final_capital == result.initial_capital


@pytest.mark.asyncio
@respx.mock
async def test_cache_hit(engine: SandboxEngine) -> None:
    """第二次相同请求应命中缓存，不再发 HTTP。"""
    route = respx.get(f"{DATA_URL}/api/v1/bars").mock(
        return_value=httpx.Response(200, json=BARS_50)
    )
    await engine.run_backtest(
        strategy_config={"short_window": 3, "long_window": 10, "symbol": "KQ_m_CFFEX_IF"},
        start_time="2025-01-01",
        end_time="2025-02-20",
    )
    await engine.run_backtest(
        strategy_config={"short_window": 3, "long_window": 10, "symbol": "KQ_m_CFFEX_IF"},
        start_time="2025-01-01",
        end_time="2025-02-20",
    )
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_multiple_symbols(engine: SandboxEngine) -> None:
    """多 symbol 回测应合并 trades。"""
    respx.get(f"{DATA_URL}/api/v1/bars").mock(
        return_value=httpx.Response(200, json=BARS_50)
    )
    result = await engine.run_backtest(
        strategy_config={"short_window": 3, "long_window": 10},
        start_time="2025-01-01",
        end_time="2025-02-20",
        symbols=["KQ_m_CFFEX_IF", "KQ_m_CFFEX_IC"],
    )
    assert result.status == "completed"


@pytest.mark.asyncio
@respx.mock
async def test_flat_bars_no_trades(engine: SandboxEngine) -> None:
    """纯平价 bars 不应产生交叉信号（均线值相等不触发）。"""
    respx.get(f"{DATA_URL}/api/v1/bars").mock(
        return_value=httpx.Response(200, json=FLAT_BARS_50)
    )
    result = await engine.run_backtest(
        strategy_config={"short_window": 3, "long_window": 10, "symbol": "KQ_m_CFFEX_IF"},
        start_time="2025-01-01",
        end_time="2025-02-20",
    )
    assert result.status == "completed"
    assert result.trades_count == 0
    assert result.total_return == 0.0


@pytest.mark.asyncio
@respx.mock
async def test_sandbox_result_to_dict(engine: SandboxEngine) -> None:
    """SandboxResult.to_dict() 应返回可 JSON 序列化的 dict。"""
    respx.get(f"{DATA_URL}/api/v1/bars").mock(
        return_value=httpx.Response(200, json=BARS_50)
    )
    result = await engine.run_backtest(
        strategy_config={"short_window": 3, "long_window": 10, "symbol": "KQ_m_CFFEX_IF"},
        start_time="2025-01-01",
        end_time="2025-02-20",
    )
    d = result.to_dict()
    assert isinstance(d, dict)
    assert "backtest_id" in d
    json.dumps(d)  # 确保可序列化


@pytest.mark.asyncio
@respx.mock
async def test_bars_wrapped_in_data_key(engine: SandboxEngine) -> None:
    """data 服务返回 {"data": [...]} 格式时应正常解析。"""
    respx.get(f"{DATA_URL}/api/v1/bars").mock(
        return_value=httpx.Response(200, json={"data": BARS_50})
    )
    result = await engine.run_backtest(
        strategy_config={"short_window": 3, "long_window": 10, "symbol": "KQ_m_CFFEX_IF"},
        start_time="2025-01-01",
        end_time="2025-02-20",
    )
    assert result.status == "completed"
    assert result.trades_count > 0
