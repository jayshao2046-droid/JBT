# backtest_certificate 契约

状态: ACTIVE
作者: 决策 Agent
登记时间: 2026-04-07
来源冻结口径: `TASK-0021` 批次 A

## 1. 用途

本契约定义策略“回测合格证明”的最小正式字段，用于：

1. 为 decision 执行资格门禁提供回测通过凭证。
2. 复用 backtest 已冻结的 `requested_symbol` / `executed_data_symbol` 分离口径。
3. 为策略仓库、通知和看板提供统一的回测资格索引。

## 2. 字段定义

| 字段 | 类型 | 必填 | 说明 | 约束 |
|---|---|---|---|---|
| certificate_id | string | 是 | 回测证明 ID | 全局唯一 |
| strategy_id | string | 是 | 关联策略 ID | 对齐 `strategy_package.md` |
| strategy_version | string | 是 | 策略版本 | 与回测输入一致 |
| backtest_job_id | string | 是 | 回测任务 ID | FK → `shared/contracts/backtest/backtest_job.md` |
| backtest_result_id | string | 是 | 回测结果 ID | FK → `shared/contracts/backtest/backtest_result.md` |
| metrics_ref | string | 是 | 绩效指标引用 | FK 语义对齐 `performance_metrics.md` |
| formal_report_ref | string | 是 | 正式报告引用 | 指向统一报告对象，不写绝对路径 |
| requested_symbol | string | 是 | 用户请求标的 | 保留原始请求口径 |
| executed_data_symbol | string | 是 | 实际执行数据标的 | 必须与回测实际数据来源一致 |
| backtest_window | object | 是 | 回测区间 | 见第 3 节 |
| factor_version_hash | string | 是 | 回测时使用的因子版本哈希 | 与策略包和研究快照对齐 |
| review_status | enum | 是 | 审阅状态 | `pending` / `approved` / `rejected` / `expired` |
| approved_at | string | 否 | 审阅通过时间 | ISO 8601 |
| expires_at | string | 是 | 证明失效时间 | ISO 8601 |

## 3. backtest_window 对象

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| start_date | string | 是 | 回测开始日期，`YYYY-MM-DD` |
| end_date | string | 是 | 回测结束日期，`YYYY-MM-DD` |

## 4. 合格证明约束

1. `requested_symbol` 与 `executed_data_symbol` 必须显式区分，不得把连续主力执行口径伪装成单一合约完整回放。
2. 若 `expires_at` 已过期，或 `factor_version_hash` 与当前策略包不一致，则该证明不再有效。
3. `review_status=approved` 只是“回测合格证明有效”，不等于“允许直接下单”。
4. 本契约只保存资格证明索引，不复制 backtest 原始结果全文。

## 5. 示例

```json
{
  "certificate_id": "bc-20260407-0001",
  "strategy_id": "alpha-trend-001",
  "strategy_version": "2026.04.07",
  "backtest_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "backtest_result_id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
  "metrics_ref": "metrics-b2c3d4e5-f6a7-8901-bcde-f23456789012",
  "formal_report_ref": "formal-report-b2c3d4e5-f6a7-8901-bcde-f23456789012",
  "requested_symbol": "DCE.p2605",
  "executed_data_symbol": "KQ_m_DCE_p",
  "backtest_window": {
    "start_date": "2023-04-03",
    "end_date": "2026-04-03"
  },
  "factor_version_hash": "fac-5511c0f3",
  "review_status": "approved",
  "approved_at": "2026-04-07T13:50:00+08:00",
  "expires_at": "2026-05-07T00:00:00+08:00"
}
```

## 6. 明确排除项

以下内容不进入本契约：

- 原始成交明细、逐 bar 序列、完整权益曲线数据
- 报告文件绝对路径、运行时缓存路径
- prompt 原文、思维链、旧系统内部回测细节
- SQLite 行号与内部审计表结构