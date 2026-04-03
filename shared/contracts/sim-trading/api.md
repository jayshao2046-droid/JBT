# sim-trading API 契约

状态: ACTIVE
作者: 项目架构师
登记时间: 2026-04-03
来源草稿: `shared/contracts/drafts/sim-trading/api.md`

## 1. 用途

本契约定义 sim-trading 第一批最小 API 边界，服务对象为：

1. decision：提交订单、查询订单状态。
2. dashboard：查询账户与持仓快照。
3. 运维探活：查询健康状态。

统一采用 `/api/v1` 前缀，避免后续版本化时破坏路径稳定性。

## 2. API 清单

| 方法 | 路径 | 用途 | 请求模型 | 响应模型 |
|---|---|---|---|---|
| GET | `/api/v1/health` | 健康检查 | 无 | 服务状态对象 |
| POST | `/api/v1/orders` | 创建订单 | 订单创建请求 | `order.md` |
| GET | `/api/v1/orders/{order_id}` | 查询单笔订单 | 路径参数 `order_id` | `order.md` |
| POST | `/api/v1/orders/{order_id}/cancel` | 撤销订单 | 路径参数 `order_id` | `order.md` |
| GET | `/api/v1/positions` | 查询持仓列表 | `account_id` 必填，`symbol` 可选 | `position.md[]` |
| GET | `/api/v1/accounts/{account_id}` | 查询账户快照 | 路径参数 `account_id` | `account.md` |

## 3. 请求/响应约束

### 3.1 创建订单请求

`POST /api/v1/orders` 请求体最小字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| account_id | string | 是 | 下单账户 |
| symbol | string | 是 | 合约代码 |
| side | enum | 是 | `buy` / `sell` |
| offset | enum | 是 | `open` / `close` / `close_today` |
| volume | integer | 是 | 下单手数 |
| price | number | 否 | 限价时必填 |
| order_type | enum | 是 | `limit` / `market` |

响应返回完整订单对象，字段定义见 `order.md`。

### 3.2 健康检查响应

`GET /api/v1/health` 返回最小对象：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| status | string | 是 | `ok` / `degraded` / `error` |
| service | string | 是 | 固定为 `sim-trading` |
| timestamp | string | 是 | ISO 8601 |

## 4. 明确不纳入本轮的接口

以下接口暂不纳入第一批最小 API：

- 批量改单/撤单
- 成交明细查询
- 历史订单分页查询
- 风控配置管理
- 运维管理接口

这些能力待 sim-trading 骨架稳定后再评估是否纳入下一轮契约。