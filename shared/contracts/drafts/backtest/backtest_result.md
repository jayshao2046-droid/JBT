# 回测结果模型草稿（BacktestResult）

【归属服务】services/backtest
【目标正式路径】shared/contracts/backtest/backtest_result.md
【草稿状态】已完成；等待 P0 Token 后迁入正式目录
【审核人】项目架构师
【最后更新】2026-04-03

---

## 字段定义

| 字段 | 类型 | 说明 |
|---|---|---|
| result_id | string (UUID) | 结果唯一 ID，由服务生成 |
| job_id | string (UUID) | 关联的回测任务 ID（FK → BacktestJob.job_id） |
| symbol | string | 合约代码（冗余自 Job，方便查询） |
| strategy_id | string | 策略标识（冗余自 Job，方便查询） |
| final_equity | float | 最终资产净值（CNY） |
| max_drawdown | float | 最大回撤（浮点，[0, 1]；0.12 表示 12%） |
| total_trades | int | 总交易笔数 |
| equity_curve_path | string | 权益曲线 Parquet 文件路径（相对 BACKTEST_STORAGE_PATH） |
| completed_at | string (ISO8601 datetime) | 回测完成时间 |

## 明确排除字段

| 排除字段 | 排除原因 |
|---|---|
| `trade_pnls` 原始列表 | 数据量大，消费方应通过 `equity_curve_path` 解析 Parquet 文件获取 |
| `per_bar_records` 逐 K 线状态 | 同上，体积大，不适合 API 传输 |
| `internal_id`、`archive_version`、`session_key` | 内部归档实现字段，不暴露于契约 |
| `tqsdk_context`、`tqsdk_position` | TqSdk 运行时状态，内部字段 |

## 响应示例

```json
{
  "result_id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "symbol": "SHFE.rb2405",
  "strategy_id": "sma_cross_v1",
  "final_equity": 1153200.0,
  "max_drawdown": 0.087,
  "total_trades": 43,
  "equity_curve_path": "a1b2c3d4/equity_curve.parquet",
  "completed_at": "2026-04-03T10:05:32+08:00"
}
```

## 权益曲线 Parquet 结构（参考，非 API 字段）

权益曲线文件保存在 `${BACKTEST_STORAGE_PATH}/{job_id}/equity_curve.parquet`，列定义如下：

| 列名 | 类型 | 说明 |
|---|---|---|
| timestamp | datetime | K 线时间戳 |
| equity | float | 当 K 线末累计净值（CNY） |
| drawdown | float | 当 K 线末回撤（[0, 1]） |
| position | int8 | 仓位方向（1=多，-1=空，0=空仓） |
| pnl | float | 当 K 线盈亏（CNY） |
| cum_pnl | float | 累计盈亏（CNY） |
