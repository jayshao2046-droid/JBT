# TASK-P1-20260423B：外汇日线元数据修正 + delayed 误标预防

## 基本信息

| 字段 | 内容 |
|------|------|
| 任务 ID | TASK-P1-20260423B |
| 优先级 | P1（延迟误标风险）+ P2（元数据错误）|
| 服务 | services/data |
| 负责 Agent | 数据 |
| 创建时间 | 2026-04-23 |
| 状态 | U0已完成 |

## 问题描述

全面核查外汇日线（forex）采集器，发现 3 项问题：

### [P1] forex 缺少 SOURCE_DELAY_THRESHOLDS 配置

- 快照固化 `delay_h: 13.0`（= threshold 26h × 0.5）
- 工作日 17:20 采集，次日 06:20 后 age_h 超过 13.0 → 误标 `delayed`
- 与 TASK-P1-20260423 的 shipping 问题完全同类

### [P2] SOURCE_SCHEDULE_HINTS["forex"] 错误

- 当前值：`"0 6 * * *"`（UTC 6:00，无限制）
- 应为：`"20 17 * * 1-5"`（工作日 17:20）

### [P2] SOURCE_PROVIDER_HINTS["forex"] 错误

- 当前值：`"yfinance"`
- 应为：`"Tushare"`（forex_collector.py 实际使用 tushare Pro API）

## 修复范围

**仅修改 `services/data/src/main.py`**（与 TASK-P1-20260423 同文件）

变更内容：
1. `SOURCE_DELAY_THRESHOLDS` 增加 `"forex": 25.0`
2. `SOURCE_SCHEDULE_HINTS["forex"]` 改为 `"20 17 * * 1-5"`
3. `SOURCE_PROVIDER_HINTS["forex"]` 改为 `"Tushare"`

## 验收标准

- `curl /api/v1/dashboard/collectors` 中 forex 的 `schedule_expr` = `"20 17 * * 1-5"`
- `data_source` = `"Tushare"`
- 今日 17:20 调度运行后，次日早晨 age_h > 13h 时 status 仍为 `success`（不触发 delayed）

## 文件白名单

- `services/data/src/main.py`

## 关联

- 同类问题：TASK-P1-20260423（shipping delayed 误标，已修复）
- 核查发现时间：2026-04-23 约 11:30
