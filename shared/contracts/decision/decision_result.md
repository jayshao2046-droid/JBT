# decision_result 契约

状态: ACTIVE
作者: 决策 Agent
登记时间: 2026-04-07
来源冻结口径: `TASK-0021` 批次 A

## 1. 用途

本契约定义 decision 服务对外输出的统一审批结果模型，用于：

1. 返回单次决策分析的动作结论与置信度。
2. 体现研究、回测、因子与发布目标的门禁结果。
3. 为通知事件、看板与后续发布流程提供稳定输出。

## 2. 字段定义

| 字段 | 类型 | 必填 | 说明 | 约束 |
|---|---|---|---|---|
| decision_id | string | 是 | 决策结果 ID | 全局唯一 |
| request_id | string | 是 | 关联请求 ID | FK → `decision_request.md` |
| trace_id | string | 是 | 跨链路追踪 ID | 与请求一致 |
| strategy_id | string | 是 | 策略 ID | 对齐 `strategy_package.md` |
| action | enum | 是 | 审批动作 | `approve` / `reject` / `hold` / `escalate` |
| confidence | number | 是 | 置信度 | 范围 `[0, 1]` |
| layer | enum | 是 | 功能层级 | `L1_rules` / `L2_local_review` / `L3_cloud_review` / `manual_review` |
| model_profile | object | 是 | 模型路线摘要 | 仅允许引用 `model_boundary.md` 已冻结路线 |
| eligibility_status | enum | 是 | 资格门禁状态 | `eligible` / `blocked` / `expired` / `manual_review` / `locked_visible` |
| publish_target | string | 否 | 当前发布目标 | 第一阶段仅 `sim-trading` 有效 |
| publish_workflow_status | enum | 是 | 发布流程状态 | `none` / `ready_for_publish` / `queued` / `locked_visible` |
| reasoning_summary | string | 是 | 简要结论摘要 | 允许摘要，不允许思维链 |
| notification_event_id | string | 否 | 关联通知事件 ID | FK → `notification_event.md` |
| generated_at | string | 是 | 生成时间 | ISO 8601 |

## 3. 动作语义冻结

| action | 含义 |
|---|---|
| approve | 通过门禁并允许进入发布流程 |
| reject | 明确不通过，不进入发布流程 |
| hold | 信息不足、资格未齐或阶段受限，暂缓 |
| escalate | 需要更高层级模型或人工复核 |

补充说明：

1. `approve` 只表示“允许进入发布流程”，不表示直接下单。
2. 若 `publish_target=live-trading` 且当前仍处第一阶段，结果必须收口到 `eligibility_status=locked_visible` 或 `publish_workflow_status=locked_visible`。
3. `reasoning_summary` 只保留面向审阅的简述，不得暴露 prompt 原文或思维链。

## 4. model_profile 对象最小字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| profile_id | string | 是 | 模型路线 ID |
| model_name | string | 是 | 模型名称 |
| deployment_class | string | 是 | `local` / `cloud` |
| route_role | string | 是 | 该路线在当前结果中的角色 |

## 5. 示例

```json
{
  "decision_id": "dd-20260407-0001",
  "request_id": "dr-20260407-0001",
  "trace_id": "tr-20260407-0001",
  "strategy_id": "alpha-trend-001",
  "action": "approve",
  "confidence": 0.86,
  "layer": "L2_local_review",
  "model_profile": {
    "profile_id": "local-primary-qwen3-14b",
    "model_name": "Qwen3 14B",
    "deployment_class": "local",
    "route_role": "primary_local_review"
  },
  "eligibility_status": "eligible",
  "publish_target": "sim-trading",
  "publish_workflow_status": "ready_for_publish",
  "reasoning_summary": "研究快照与回测证明均有效，因子版本一致，当前允许进入模拟交易发布流程。",
  "notification_event_id": "ne-20260407-0001",
  "generated_at": "2026-04-07T14:02:00+08:00"
}
```

## 6. 明确排除项

以下内容不进入本契约：

- prompt 原文、思维链、完整推理日志
- API Key、模型 Secret、缓存命中细节
- 绝对路径、SQLite 行号、旧系统内部返回码