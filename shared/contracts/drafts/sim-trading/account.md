# DRAFT: account.md

状态: DRAFT
作者: 项目架构师
创建时间: 2026-04-03

描述：账户与资金模型草稿，列出最小必要字段。

字段草稿示例（最小必要字段）:

- account_id: string
- currency: string
- balance: decimal
- available: decimal
- frozen: decimal
- margin: decimal
- timestamp: iso8601

注：账户模型应与资金结算与交易记账保持一致，具体实现由模拟交易 agent 负责。
