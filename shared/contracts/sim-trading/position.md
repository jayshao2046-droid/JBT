# position 契约

状态: ACTIVE
作者: 项目架构师
登记时间: 2026-04-03
来源草稿: `shared/contracts/drafts/sim-trading/position.md`

## 1. 用途

本契约定义 sim-trading 对外暴露的持仓快照模型，用于：

1. 看板查询当前账户持仓。
2. 决策服务在必要时读取当前仓位方向与可平数量。
3. 为后续 close / close_today 语义提供明确字段边界。

## 2. 持仓模型

| 字段 | 类型 | 必填 | 说明 | 约束 |
|---|---|---|---|---|
| position_id | string | 是 | 持仓记录唯一标识 | 由 sim-trading 生成 |
| account_id | string | 是 | 所属账户标识 | 对应账户契约中的 `account_id` |
| symbol | string | 是 | 合约代码 | 与订单模型一致 |
| direction | enum | 是 | 持仓方向 | `long` / `short` |
| volume | integer | 是 | 当前总持仓手数 | 大于等于 0 |
| today_volume | integer | 是 | 今仓手数 | 大于等于 0 |
| yesterday_volume | integer | 是 | 昨仓手数 | 大于等于 0 |
| available_volume | integer | 是 | 当前可平手数 | 大于等于 0，且不大于 `volume` |
| open_price | number | 是 | 持仓均价 | 大于等于 0 |
| last_price | number | 是 | 最新价格 | 大于等于 0 |
| unrealized_pnl | number | 是 | 浮动盈亏 | 可正可负 |
| margin | number | 是 | 当前占用保证金 | 大于等于 0 |
| updated_at | string | 是 | 最近更新时间 | ISO 8601 |

## 3. 设计说明

1. `today_volume` / `yesterday_volume` 是 futures 场景的必要字段，用于后续 `close_today` 处理。
2. 不在本契约中定义成交明细或逐笔开仓记录；这些属于交易服务内部账本。
3. `available_volume` 面向查询方，避免上游自行推导可平量。

## 4. 明确排除字段

以下字段暂不进入跨服务契约：

- 逐笔成交明细
- 持仓成本拆解明细
- 风控阈值状态
- 内部账本分录 ID
- 任意网关原始持仓对象字段

## 5. 示例

```json
{
	"position_id": "POS-20260403-rb2410-long",
	"account_id": "simnow-main",
	"symbol": "SHFE.rb2410",
	"direction": "long",
	"volume": 3,
	"today_volume": 1,
	"yesterday_volume": 2,
	"available_volume": 3,
	"open_price": 3562.0,
	"last_price": 3578.0,
	"unrealized_pnl": 480.0,
	"margin": 12800.0,
	"updated_at": "2026-04-03T21:20:00+08:00"
}
```