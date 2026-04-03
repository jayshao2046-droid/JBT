# 绩效指标模型草稿（PerformanceMetrics）

【归属服务】services/backtest
【目标正式路径】shared/contracts/backtest/performance_metrics.md
【草稿状态】已完成；等待 P0 Token 后迁入正式目录
【审核人】项目架构师
【最后更新】2026-04-03

---

## 字段定义

| 字段 | 类型 | 说明 |
|---|---|---|
| result_id | string (UUID) | 关联的回测结果 ID（FK → BacktestResult.result_id） |
| total_return | float | 总收益率（0.25 表示 25%） |
| annualized_return | float | 年化收益率（按 252 交易日折算） |
| sharpe_ratio | float | 夏普比率（无风险利率 3%，年化） |
| max_drawdown | float | 最大回撤（[0, 1]；与 BacktestResult.max_drawdown 一致） |
| win_rate | float | 胜率（[0, 1]；盈利笔数 / 总笔数） |
| profit_factor | float | 盈亏比（gross_profit / gross_loss；亏损为零时为 Inf） |
| total_trades | int | 总交易笔数（与 BacktestResult.total_trades 一致） |
| avg_trade_pnl | float | 平均单笔盈亏（CNY） |
| max_consecutive_wins | int | 最大连续盈利次数 |
| max_consecutive_losses | int | 最大连续亏损次数 |

## 明确排除字段

| 排除字段 | 排除原因 |
|---|---|
| `risk_free_rate` | 计算配置参数，不作为结果字段（固定为 3%） |
| 原始 `trade_pnls` 列表 | 同 BacktestResult，体积大，通过 equity_curve_path 获取 |
| `daily_pnl` 序列 | 可从权益曲线 Parquet 推导，不需独立字段 |
| `overfitting_score` | Walk-forward 与过拟合检测属于进阶分析，MVP 不纳入 |
| `walk_forward_ratio` | 同上 |
| `calmar_ratio`、`sortino_ratio` | 进阶风险指标，MVP 不纳入 |
| `benchmark_comparison` | 基准对比结果，MVP 不纳入 |

## 响应示例

```json
{
  "result_id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
  "total_return": 0.1532,
  "annualized_return": 0.1532,
  "sharpe_ratio": 1.47,
  "max_drawdown": 0.087,
  "win_rate": 0.558,
  "profit_factor": 1.83,
  "total_trades": 43,
  "avg_trade_pnl": 3565.12,
  "max_consecutive_wins": 7,
  "max_consecutive_losses": 4
}
```

## 计算说明（参考，非契约约束）

- `annualized_return`：`(1 + total_return) ^ (252 / n_bars) - 1`（对齐 legacy `performance.py`）
- `sharpe_ratio`：`(annualized_return - 0.03) / (daily_std * sqrt(252))`
- `profit_factor`：`sum(win_pnls) / abs(sum(loss_pnls))`

实际计算逻辑由 `services/backtest/src/backtest/result_builder.py` 实现，字段口径须与本草稿保持一致。
