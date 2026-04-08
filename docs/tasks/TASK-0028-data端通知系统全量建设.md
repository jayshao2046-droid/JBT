# TASK-0028 — 数据端通知系统全量建设

| 字段 | 值 |
|------|-----|
| 任务 ID | TASK-0028 |
| 父任务 | TASK-0027 (数据端迁移) |
| 执行 Agent | 数据 |
| 审核 Agent | Atlas |
| 优先级 | P1 |
| 状态 | 🚧 执行中 |
| 创建时间 | 2026-04-09 |

## 目标

为 JBT 数据端构建完整通知系统：飞书三群路由（报警/交易/资讯）+ QQ 邮箱日报 + P0 按钮修复。

## 批次

| 批次 | 内容 | 状态 |
|------|------|------|
| B1 | dispatcher + card_templates + news_pusher (新建) | ⏳ |
| B2 | feishu.py + email_notify.py + __init__.py (重写) | ⏳ |
| B3 | scheduler / health_check / heartbeat 嵌入通知触发 | ⏳ |
| B4 | main.py ops API + .env.example | ⏳ |
| B5 | test_notify.py + 实测验证 | ⏳ |

## 约束

- 飞书 3 个独立 Webhook（报警/交易/资讯）
- 邮件：17621181300@qq.com → 17621181300@qq.com + ewangli@iCloud.com
- 使用 JBT 统一卡片颜色标准
- P0 告警支持飞书操作按钮
