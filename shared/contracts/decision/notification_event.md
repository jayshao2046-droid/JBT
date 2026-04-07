# notification_event 契约

状态: ACTIVE
作者: 决策 Agent
登记时间: 2026-04-07
来源冻结口径: `TASK-0021` 批次 A

## 1. 用途

本契约定义 decision 服务统一的通知事件载荷，用于：

1. 支撑研究完成、资格失效、发布预约、发布执行、模型回退与人工复核等事件通知。
2. 为飞书、邮件、看板通知中心与日报链路提供统一事件对象。
3. 为后续总包中的通知体系重建保留稳定字段边界。

## 2. 字段定义

| 字段 | 类型 | 必填 | 说明 | 约束 |
|---|---|---|---|---|
| event_id | string | 是 | 事件唯一 ID | 全局唯一 |
| service_name | string | 是 | 服务名 | 固定为 `decision` |
| stage | string | 是 | 事件所属阶段 | 如 `research`、`approval`、`publish`、`runtime` |
| category | enum | 是 | 事件分类 | `alert` / `trade` / `info` / `news` / `notify` |
| risk_level_or_type | string | 是 | 风险级别或类型标识 | 见第 3 节 |
| event_code | string | 是 | 事件代码 | 稳定可检索 |
| title | string | 是 | 事件标题 | 供渲染层使用 |
| summary | string | 是 | 事件摘要 | 不含思维链 |
| trace_id | string | 是 | 跨链路追踪 ID | 用于关联请求与结果 |
| strategy_id | string | 否 | 关联策略 ID | 如有则填写 |
| decision_id | string | 否 | 关联决策结果 ID | 如有则填写 |
| channels | string[] | 是 | 建议投递渠道 | `feishu` / `email` / `dashboard` |
| ack_status | enum | 是 | 确认状态 | `pending` / `acknowledged` / `closed` |
| emitted_at | string | 是 | 事件时间 | ISO 8601 |

## 3. 风险级别与类型约束

1. 当 `category=alert` 时，`risk_level_or_type` 只能取 `P0`、`P1`、`P2`。
2. 当 `category` 为非告警时，`risk_level_or_type` 只能取 `TRADE`、`INFO`、`NEWS`、`NOTIFY`。
3. 渲染层的颜色、图标、飞书卡片与邮件 HTML 模板不写入本契约；实现层必须按全局通知标准映射。

## 4. 典型事件语义

| event_code | 语义 |
|---|---|
| `RESEARCH_COMPLETED` | 研究快照完成 |
| `BACKTEST_CERT_EXPIRED` | 回测证明过期 |
| `PUBLISH_RESERVED` | 策略包已预约发布 |
| `PUBLISH_EXECUTE_REQUESTED` | 策略包已进入发布流程 |
| `LIVE_TARGET_LOCKED_VISIBLE` | 实盘入口仅锁定可见 |
| `MODEL_ROUTE_FALLBACK` | 决策过程发生模型回退 |
| `MANUAL_REVIEW_REQUIRED` | 需要人工复核 |

## 5. 示例

```json
{
  "event_id": "ne-20260407-0001",
  "service_name": "decision",
  "stage": "publish",
  "category": "notify",
  "risk_level_or_type": "NOTIFY",
  "event_code": "PUBLISH_EXECUTE_REQUESTED",
  "title": "策略包已进入模拟交易发布流程",
  "summary": "alpha-trend-001 已完成审批，当前进入 sim-trading 发布队列。",
  "trace_id": "tr-20260407-0001",
  "strategy_id": "alpha-trend-001",
  "decision_id": "dd-20260407-0001",
  "channels": ["feishu", "email", "dashboard"],
  "ack_status": "pending",
  "emitted_at": "2026-04-07T14:05:00+08:00"
}
```

## 6. 明确排除项

以下内容不进入本契约：

- Webhook URL、SMTP 用户名密码、收件人地址
- 飞书卡片原文、邮件 HTML 原文、思维链文本
- 绝对路径、SQLite 行号、legacy 通知内部细节