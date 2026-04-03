# account 契约

状态: ACTIVE
作者: 项目架构师
登记时间: 2026-04-03
来源草稿: `shared/contracts/drafts/sim-trading/account.md`

## 1. 用途

本契约定义 sim-trading 的账户与资金快照模型，用于：

1. 看板展示账户权益、可用资金与风险占比。
2. 风控或上游查询资金口径时使用统一字段。
3. 为后续账本与健康检查接口提供稳定响应模型。

## 2. 账户模型

| 字段 | 类型 | 必填 | 说明 | 约束 |
|---|---|---|---|---|
| account_id | string | 是 | 账户标识 | 由 sim-trading 维护 |
| currency | string | 是 | 计价货币 | 当前默认 `CNY` |
| balance | number | 是 | 当前账户权益 | 大于等于 0 |
| pre_balance | number | 是 | 上一交易日权益 | 大于等于 0 |
| available | number | 是 | 当前可用资金 | 大于等于 0 |
| margin | number | 是 | 已占用保证金 | 大于等于 0 |
| frozen_margin | number | 是 | 冻结保证金 | 大于等于 0 |
| unrealized_pnl | number | 是 | 浮动盈亏 | 可正可负 |
| realized_pnl | number | 是 | 已实现盈亏 | 可正可负 |
| commission | number | 是 | 当日手续费累计 | 大于等于 0 |
| risk_ratio | number | 是 | 风险度 | 范围 0 到 1，或返回保留两位小数比例值 |
| updated_at | string | 是 | 最近更新时间 | ISO 8601 |

## 3. 字段归一说明

1. legacy 中的 `float_profit` 在本契约统一命名为 `unrealized_pnl`。
2. legacy 中的 `close_profit` 在本契约统一命名为 `realized_pnl`。
3. legacy 中的 `pre_balance` 保留，用于计算日内损益。

## 4. 明确排除字段

以下字段暂不进入跨服务契约：

- `static_balance`
- `deposit` / `withdraw`
- 任意券商原始回包字段
- 清算或结算内部过程字段

若后续 dashboard 明确需要，可在后续契约版本中增补。

## 5. 示例

```json
{
	"account_id": "simnow-main",
	"currency": "CNY",
	"balance": 201560.0,
	"pre_balance": 200800.0,
	"available": 183200.0,
	"margin": 12800.0,
	"frozen_margin": 1200.0,
	"unrealized_pnl": 480.0,
	"realized_pnl": 320.0,
	"commission": 46.0,
	"risk_ratio": 0.07,
	"updated_at": "2026-04-03T21:22:00+08:00"
}
```