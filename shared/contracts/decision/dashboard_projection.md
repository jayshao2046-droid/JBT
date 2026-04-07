# dashboard_projection 契约

状态: ACTIVE
作者: 决策 Agent
登记时间: 2026-04-07
来源冻结口径: `TASK-0021` 批次 A

## 1. 用途

本契约定义决策看板的只读聚合字段，用于：

1. 支撑 7 页决策看板的数据投影边界。
2. 为后续 dashboard 实现提供稳定的只读聚合 schema。
3. 保证策略仓库、研究中心、通知与运行状态在同一投影对象下可追溯。

## 2. 根对象字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| projection_id | string | 是 | 投影 ID |
| generated_at | string | 是 | 聚合生成时间，ISO 8601 |
| overview | object | 是 | 总览页摘要 |
| signal_review_queue | object[] | 是 | 信号审查页列表 |
| model_factor_panel | object | 是 | 模型与因子页数据 |
| strategy_repository | object[] | 是 | 策略仓库页列表 |
| research_center | object[] | 是 | 研究中心页列表 |
| notification_digest | object[] | 是 | 通知与日报页列表 |
| runtime_config | object | 是 | 配置与运行页摘要 |

## 3. overview 字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| active_strategies | integer | 是 | 当前活跃策略数 |
| eligible_strategies | integer | 是 | 资格通过策略数 |
| blocked_strategies | integer | 是 | 被门禁阻塞策略数 |
| pending_reviews | integer | 是 | 待审查信号或人工复核数 |
| live_locked_count | integer | 是 | 实盘锁定可见入口数量 |
| last_decision_at | string | 否 | 最近一次决策时间 |

## 4. signal_review_queue 元素字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| signal_id | string | 是 | 信号或请求 ID |
| strategy_id | string | 是 | 策略 ID |
| symbol | string | 是 | 标的代码 |
| requested_target | string | 是 | 目标服务 |
| action | string | 是 | 当前建议动作 |
| confidence | number | 是 | 当前置信度 |
| review_status | string | 是 | 审查状态 |
| created_at | string | 是 | 创建时间 |

## 5. model_factor_panel 字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| model_profiles | string[] | 是 | 当前启用模型路线 ID 列表 |
| research_backend_status | string | 是 | 当前研究后端状态摘要 |
| active_factor_version_hash | string | 是 | 当前主因子版本哈希 |
| factor_heatmap | object[] | 是 | 因子热力图数据 |

### factor_heatmap 元素字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| factor_name | string | 是 | 因子名称 |
| score | number | 是 | 热度或贡献分数 |
| status | string | 是 | 当前状态摘要 |
| updated_at | string | 是 | 更新时间 |

说明：`factor_heatmap` 是“模型与因子”页的核心只读投影来源，后续前台布局必须能承接其首屏主卡展示。

## 6. strategy_repository 元素字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| strategy_id | string | 是 | 策略 ID |
| strategy_version | string | 是 | 策略版本 |
| lifecycle_status | string | 是 | 生命周期状态 |
| eligibility_status | string | 是 | 当前资格状态 |
| publish_target | string | 否 | 当前发布目标 |
| live_visibility_mode | string | 是 | 实盘可见模式 |
| updated_at | string | 是 | 最近更新时间 |

## 7. research_center 元素字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| strategy_id | string | 是 | 策略 ID |
| research_status | string | 是 | 研究状态 |
| research_backend | string | 是 | 研究后端 |
| valid_until | string | 是 | 研究快照有效期 |
| next_research_window | string | 否 | 下一建议研究窗口 |

## 8. notification_digest 元素字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| event_id | string | 是 | 通知事件 ID |
| category | string | 是 | 事件分类 |
| risk_level_or_type | string | 是 | 风险级别或类型 |
| title | string | 是 | 标题 |
| ack_status | string | 是 | 确认状态 |
| emitted_at | string | 是 | 事件时间 |

## 9. runtime_config 字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| decision_service_status | string | 是 | 决策服务状态 |
| model_route_status | string | 是 | 模型路线状态摘要 |
| publish_gate_status | string | 是 | 发布门禁状态摘要 |
| scheduler_status | string | 是 | 研究/通知编排状态摘要 |

## 10. 示例

```json
{
  "projection_id": "dp-20260407-0001",
  "generated_at": "2026-04-07T14:08:00+08:00",
  "overview": {
    "active_strategies": 12,
    "eligible_strategies": 8,
    "blocked_strategies": 4,
    "pending_reviews": 2,
    "live_locked_count": 8,
    "last_decision_at": "2026-04-07T14:05:00+08:00"
  },
  "signal_review_queue": [
    {
      "signal_id": "dr-20260407-0001",
      "strategy_id": "alpha-trend-001",
      "symbol": "DCE.p2605",
      "requested_target": "sim-trading",
      "action": "approve",
      "confidence": 0.86,
      "review_status": "ready",
      "created_at": "2026-04-07T14:00:00+08:00"
    }
  ],
  "model_factor_panel": {
    "model_profiles": ["local-primary-qwen3-14b", "cloud-default-qwen3.6-plus"],
    "research_backend_status": "xgboost_active",
    "active_factor_version_hash": "fac-5511c0f3",
    "factor_heatmap": [
      {
        "factor_name": "momentum_score",
        "score": 0.71,
        "status": "active",
        "updated_at": "2026-04-07T13:58:00+08:00"
      }
    ]
  },
  "strategy_repository": [
    {
      "strategy_id": "alpha-trend-001",
      "strategy_version": "2026.04.07",
      "lifecycle_status": "reserved",
      "eligibility_status": "eligible",
      "publish_target": "sim-trading",
      "live_visibility_mode": "locked_visible",
      "updated_at": "2026-04-07T14:06:00+08:00"
    }
  ],
  "research_center": [
    {
      "strategy_id": "alpha-trend-001",
      "research_status": "completed",
      "research_backend": "xgboost",
      "valid_until": "2026-05-07T00:00:00+08:00",
      "next_research_window": "2026-05-01T21:00:00+08:00"
    }
  ],
  "notification_digest": [
    {
      "event_id": "ne-20260407-0001",
      "category": "notify",
      "risk_level_or_type": "NOTIFY",
      "title": "策略包已进入模拟交易发布流程",
      "ack_status": "pending",
      "emitted_at": "2026-04-07T14:05:00+08:00"
    }
  ],
  "runtime_config": {
    "decision_service_status": "ok",
    "model_route_status": "healthy",
    "publish_gate_status": "sim_only",
    "scheduler_status": "idle"
  }
}
```

## 11. 明确排除项

以下内容不进入本契约：

- 原始日志、原始 SQL、SQLite 行号
- prompt 原文、思维链、模型权重路径
- 绝对路径、旧系统内部面板字段