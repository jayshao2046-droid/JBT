# decision_request 契约

状态: ACTIVE
作者: 决策 Agent
登记时间: 2026-04-07
来源冻结口径: `TASK-0021` 批次 A

## 1. 用途

本契约定义 decision 服务统一的决策分析请求模型，用于：

1. 承接标准化信号、因子快照与市场上下文。
2. 把研究快照、回测证明与目标发布服务纳入同一请求边界。
3. 为审批结果、通知事件与后续发布编排提供稳定输入。

## 2. 字段定义

| 字段 | 类型 | 必填 | 说明 | 约束 |
|---|---|---|---|---|
| request_id | string | 是 | 请求唯一 ID | 全局唯一 |
| trace_id | string | 是 | 跨链路追踪 ID | 用于通知与审计关联 |
| strategy_id | string | 是 | 策略 ID | 对齐 `strategy_package.md` |
| strategy_version | string | 是 | 策略版本 | 与研究/回测证明一致 |
| symbol | string | 是 | 标的代码 | 当前决策目标 |
| requested_target | enum | 是 | 请求发布目标 | `sim-trading` / `live-trading` |
| signal | integer | 是 | 标准化信号方向 | 允许值 `-1`、`0`、`1` |
| signal_strength | number | 是 | 信号强度 | 范围 `[0, 1]` |
| factors | object[] | 是 | 因子快照数组 | 见第 3 节 |
| factor_version_hash | string | 是 | 因子版本哈希 | 与研究/回测证明对齐 |
| market_context | object | 是 | 市场上下文摘要 | 见第 4 节 |
| research_snapshot_id | string | 是 | 关联研究快照 ID | FK → `research_snapshot.md` |
| backtest_certificate_id | string | 是 | 关联回测证明 ID | FK → `backtest_certificate.md` |
| submitted_at | string | 是 | 提交时间 | ISO 8601 |

## 3. factors 对象字段

每个因子对象最少包含：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 因子名称 |
| value | number | 是 | 因子值 |
| version | string | 是 | 因子版本 |
| updated_at | string | 是 | 该因子快照时间，ISO 8601 |

## 4. market_context 对象字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| market_session | string | 是 | 交易时段标识 |
| volatility_regime | string | 是 | 波动环境摘要 |
| liquidity_regime | string | 是 | 流动性环境摘要 |
| headline_risk_level | string | 是 | 资讯或事件风险等级摘要 |

## 5. 请求约束

1. `requested_target` 第一阶段允许提交 `sim-trading` 或 `live-trading`，但若为 `live-trading`，结果必须保留“锁定可见”语义，不得推进执行。
2. `signal=0` 表示观望或无方向信号，decision 可以据此返回 `hold`。
3. 若 `research_snapshot_id`、`backtest_certificate_id` 或 `factor_version_hash` 失配，服务不得跳过门禁继续分析。
4. 请求只传递标准化摘要，不传递 prompt 原文、思维链或原始 K 线序列。

## 6. 示例

```json
{
  "request_id": "dr-20260407-0001",
  "trace_id": "tr-20260407-0001",
  "strategy_id": "alpha-trend-001",
  "strategy_version": "2026.04.07",
  "symbol": "DCE.p2605",
  "requested_target": "sim-trading",
  "signal": 1,
  "signal_strength": 0.82,
  "factors": [
    {
      "name": "momentum_score",
      "value": 0.71,
      "version": "v3",
      "updated_at": "2026-04-07T13:58:00+08:00"
    },
    {
      "name": "volatility_score",
      "value": 0.44,
      "version": "v2",
      "updated_at": "2026-04-07T13:58:00+08:00"
    }
  ],
  "factor_version_hash": "fac-5511c0f3",
  "market_context": {
    "market_session": "day",
    "volatility_regime": "normal",
    "liquidity_regime": "stable",
    "headline_risk_level": "low"
  },
  "research_snapshot_id": "rs-20260407-0001",
  "backtest_certificate_id": "bc-20260407-0001",
  "submitted_at": "2026-04-07T14:00:00+08:00"
}
```

## 7. 明确排除项

以下内容不进入本契约：

- API Key、模型 Secret、prompt 原文
- 思维链、完整推理上下文、原始行情序列
- 绝对路径、SQLite 行号、旧系统内部字段