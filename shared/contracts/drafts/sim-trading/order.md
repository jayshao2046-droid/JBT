# DRAFT: order.md

状态: DRAFT
作者: 项目架构师
创建时间: 2026-04-03

描述：订单模型草稿，仅列出最小必要字段供讨论与终审使用。最终版本迁入 `shared/contracts/sim-trading/`（P0 保护区）需 Jay.S 签发 P0 Token。

字段草稿示例（最小必要字段）:

- order_id: string  // 全局唯一订单 ID
- symbol: string    // 合约/标的代码
- side: enum(buy,sell)
- quantity: decimal
- price: decimal
- order_type: enum(limit,market)
- timestamp: iso8601
- status: enum(pending,filled,cancelled,partially_filled)

注：仅为讨论草稿，字段可精简或调整。
