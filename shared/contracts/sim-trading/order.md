# order 契约

状态: ACTIVE
作者: 项目架构师
登记时间: 2026-04-03
来源草稿: `shared/contracts/drafts/sim-trading/order.md`

## 1. 用途

本契约定义 sim-trading 对外暴露的订单模型最小必要字段，用于：

1. 决策服务提交下单请求。
2. 看板或上游调用方查询订单状态。
3. 为后续服务骨架设计提供稳定字段边界。

本契约不包含任何网关原始字段、不绑定 TqSdk/CTP 内部对象、不承载账本实现细节。

## 2. 订单模型

| 字段 | 类型 | 必填 | 说明 | 约束 |
|---|---|---|---|---|
| order_id | string | 是 | sim-trading 生成的全局唯一订单 ID | 不暴露网关内部 ID |
| account_id | string | 是 | 下单账户标识 | 由 sim-trading 维护的账户标识 |
| symbol | string | 是 | 交易合约代码 | 采用交易服务统一代码口径 |
| side | enum | 是 | 买卖方向 | `buy` / `sell` |
| offset | enum | 是 | 开平标志 | `open` / `close` / `close_today` |
| volume | integer | 是 | 报单手数 | 必须大于 0 |
| price | number | 否 | 委托价格 | 限价单必填，市价单可为空 |
| order_type | enum | 是 | 订单类型 | `limit` / `market` |
| status | enum | 是 | 订单当前状态 | 见状态归一化定义 |
| filled_volume | integer | 是 | 已成交手数 | 范围 0 到 `volume` |
| avg_fill_price | number | 否 | 平均成交价 | 未成交时可为空 |
| submitted_at | string | 是 | 提交时间 | ISO 8601 |
| updated_at | string | 是 | 最近状态更新时间 | ISO 8601 |
| error_message | string | 否 | 失败或拒单说明 | 仅 `rejected` / `error` 场景返回 |

## 3. 状态归一化

对外契约不直接暴露 legacy/TqSdk 的内部状态，而统一为以下状态：

| 状态 | 含义 |
|---|---|
| pending | 已接收，尚未被交易通道确认 |
| accepted | 已被交易通道接受，等待成交或撤销 |
| partially_filled | 部分成交 |
| filled | 全部成交 |
| cancelled | 已撤销 |
| rejected | 下单前置检查或交易通道拒绝 |
| error | 系统错误，需人工或系统介入 |

说明：

1. legacy 中的 `ALIVE` 应归一到 `accepted`。
2. legacy 中的 `FINISHED` 需根据成交量映射为 `filled` 或 `cancelled`，不直接暴露原值。

## 4. 明确排除字段

以下字段故意不进入跨服务契约：

- `internal_id`
- 网关原始 `order_ref` / `front_id` / `session_id`
- `broker_id` / `investor_id`
- `risk_check_passed`
- 任意风控引擎内部对象或执行链上下文

这些字段如有需要，应保留在 sim-trading 服务内部模型，不进入 shared 契约。

## 5. 示例

```json
{
	"order_id": "SIM-20260403-000001",
	"account_id": "simnow-main",
	"symbol": "SHFE.rb2410",
	"side": "buy",
	"offset": "open",
	"volume": 2,
	"price": 3568.0,
	"order_type": "limit",
	"status": "accepted",
	"filled_volume": 0,
	"avg_fill_price": null,
	"submitted_at": "2026-04-03T21:15:00+08:00",
	"updated_at": "2026-04-03T21:15:01+08:00",
	"error_message": null
}
```