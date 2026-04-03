# DRAFT: api.md

状态: DRAFT
作者: 项目架构师
创建时间: 2026-04-03

描述：sim-trading 对外暴露的最小 API 清单草稿（供 decision、dashboard 调用）。最终 API 的权限和版本需在终审时确认。

示例端点（草稿）:

- GET /health -> 返回服务健康状态
- POST /orders -> 创建订单，返回 order_id
- GET /orders/{order_id} -> 查询订单状态
- GET /positions/{account_id} -> 查询账户持仓
- GET /accounts/{account_id} -> 查询账户信息

注：接口输入/输出字段在契约文件（order.md、position.md、account.md）中定义。
