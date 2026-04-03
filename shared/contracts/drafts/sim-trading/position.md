# DRAFT: position.md

状态: DRAFT
作者: 项目架构师
创建时间: 2026-04-03

描述：持仓模型草稿，列出最小必要字段。

字段草稿示例（最小必要字段）:

- position_id: string
- symbol: string
- account_id: string
- quantity: decimal
- avg_price: decimal
- unrealised_pnl: decimal
- realised_pnl: decimal
- timestamp: iso8601

注：用于记录当前持仓与盈亏统计，后续由模拟交易 agent 与账本模块对应实现。
