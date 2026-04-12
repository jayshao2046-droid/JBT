"""股票策略模板路由 — TASK-0069 CB1

GET /api/v1/stock/templates → 获取所有模板信息
POST /api/v1/stock/templates/{name}/backtest → 执行模板回测
"""
from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...core.settings import get_settings
from ...research.sandbox_engine import SandboxEngine
from ...research.stock_data_client import StockDataClient, StockDataError
from ...research.stock_templates import get_all_templates

router = APIRouter(prefix="/api/v1/stock", tags=["stock_template"])


class BacktestRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 1_000_000


class BacktestResponse(BaseModel):
    template_name: str
    symbol: str
    status: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trades_count: int
    trades: list[dict[str, Any]]


@router.get("/templates")
def list_templates() -> list[dict[str, Any]]:
    """获取所有股票策略模板信息。"""
    templates = get_all_templates()
    return [t.to_dict() for t in templates]


@router.post("/templates/{name}/backtest")
async def backtest_template(name: str, req: BacktestRequest) -> BacktestResponse:
    """执行指定模板的回测。

    Args:
        name: 模板名称（short_term / mid_term / long_term）
        req: 回测请求参数

    Returns:
        回测结果
    """
    # 查找模板
    templates = get_all_templates()
    template = next((t for t in templates if t.name == name), None)
    if template is None:
        raise HTTPException(status_code=404, detail=f"Template '{name}' not found")

    # 获取股票数据
    settings = get_settings()
    client = StockDataClient()
    try:
        bars = client.fetch_bars(
            symbol=req.symbol,
            start_date=req.start_date,
            end_date=req.end_date,
            timeframe_minutes=1440,  # 日线
        )
    except StockDataError as exc:
        raise HTTPException(
            status_code=400, detail=f"Failed to fetch stock data: {exc}"
        ) from exc

    if len(bars) < template.holding_days:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data: need at least {template.holding_days} bars, got {len(bars)}",
        )

    # 执行回测
    result = _run_template_backtest(
        template=template,
        bars=bars,
        initial_capital=req.initial_capital,
    )

    return BacktestResponse(
        template_name=name,
        symbol=req.symbol,
        status=result["status"],
        total_return=result["total_return"],
        sharpe_ratio=result["sharpe_ratio"],
        max_drawdown=result["max_drawdown"],
        win_rate=result["win_rate"],
        trades_count=result["trades_count"],
        trades=result["trades"],
    )


def _run_template_backtest(
    template: Any,
    bars: list[dict],
    initial_capital: float,
) -> dict[str, Any]:
    """使用模板信号执行回测。"""
    capital = initial_capital
    position = 0.0
    entry_price = 0.0
    trades: list[dict] = []

    df = pd.DataFrame(bars)
    if "close" not in df.columns:
        return {
            "status": "failed",
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "trades_count": 0,
            "trades": [],
        }

    for i in range(len(df)):
        current_df = df.iloc[: i + 1]
        current_price = float(current_df["close"].iloc[-1])

        # 无持仓时检查入场信号
        if position == 0.0:
            if template.entry_signal(current_df):
                qty = (capital * 0.1) / current_price if current_price > 0 else 0
                if qty > 0:
                    position = qty
                    entry_price = current_price
                    trades.append({
                        "type": "buy",
                        "price": current_price,
                        "qty": round(qty, 4),
                        "bar_index": i,
                    })

        # 有持仓时检查离场信号
        elif position > 0:
            if template.exit_signal(current_df, entry_price):
                pnl = (current_price - entry_price) * position
                capital += pnl
                trades.append({
                    "type": "sell",
                    "price": current_price,
                    "qty": round(position, 4),
                    "pnl": round(pnl, 2),
                    "bar_index": i,
                })
                position = 0.0
                entry_price = 0.0

    # 收盘时平仓
    if position > 0 and not df.empty:
        last_price = float(df["close"].iloc[-1])
        pnl = (last_price - entry_price) * position
        capital += pnl
        trades.append({
            "type": "sell",
            "price": last_price,
            "qty": round(position, 4),
            "pnl": round(pnl, 2),
            "bar_index": len(df) - 1,
        })

    # 计算指标
    total_return = (capital - initial_capital) / initial_capital if initial_capital else 0.0
    sell_trades = [t for t in trades if t.get("type") == "sell"]
    pnls = [t.get("pnl", 0.0) for t in sell_trades]

    win_count = sum(1 for p in pnls if p > 0)
    win_rate = win_count / len(pnls) if pnls else 0.0

    # Sharpe ratio
    sharpe_ratio = 0.0
    if len(pnls) >= 2:
        returns = [p / initial_capital for p in pnls]
        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
        std_ret = (variance ** 0.5) if variance > 0 else 0.0
        if std_ret > 0:
            sharpe_ratio = (mean_ret / std_ret) * (252 ** 0.5)

    # Max drawdown
    max_drawdown = 0.0
    if pnls:
        equity = initial_capital
        peak = equity
        for p in pnls:
            equity += p
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0.0
            if dd > max_drawdown:
                max_drawdown = dd

    return {
        "status": "completed",
        "total_return": round(total_return, 6),
        "sharpe_ratio": round(sharpe_ratio, 4),
        "max_drawdown": round(max_drawdown, 6),
        "win_rate": round(win_rate, 4),
        "trades_count": len(sell_trades),
        "trades": trades,
    }
