# TASK-0028 锁控记录

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0028 |
| 任务标题 | 数据端通知系统全量建设 |
| 锁控管理人 | 项目架构师 |
| 创建日期 | 2026-04-09 |

---

## 锁控文件清单

### H0 批次（历史补档）— 协同账本区，无需 Token

| 文件 | 操作 | 状态 | 写入者 |
|------|------|------|--------|
| docs/tasks/TASK-0028-data端通知系统全量建设.md | 更新 | ✅ 已完成 | Atlas |
| docs/reviews/TASK-0028-review.md | 新建 | ✅ 已完成 | Atlas |
| docs/locks/TASK-0028-lock.md | 新建 | ✅ 已完成 | Atlas |

### B1-B5 主批次（历史补录）— 已实施

| 文件 | 操作 | 状态 | 保护级别 |
|------|------|------|----------|
| services/data/src/notify/card_templates.py | 新建 | ✅ 历史已实施 | P1 |
| services/data/src/notify/dispatcher.py | 新建 | ✅ 历史已实施 | P1 |
| services/data/src/notify/news_pusher.py | 新建 | ✅ 历史已实施 | P1 |
| services/data/tests/test_notify.py | 新建 | ✅ 历史已实施 | P1 |
| services/data/src/notify/feishu.py | 重写 | ✅ 历史已实施 | P1 |
| services/data/src/notify/email_notify.py | 重写 | ✅ 历史已实施 | P1 |
| services/data/src/notify/__init__.py | 重写 | ✅ 历史已实施 | P1 |
| services/data/src/scheduler/data_scheduler.py | 修改 | ✅ 历史已实施 | P1 |
| services/data/src/health/health_check.py | 修改 | ✅ 历史已实施 | P1 |
| services/data/src/health/heartbeat.py | 修改 | ✅ 历史已实施 | P1 |
| services/data/src/main.py | 修改 | ✅ 历史已实施 | P1 |
| services/data/.env.example | 修改 | ✅ 历史已实施 | P0 |

### B6 批次（通知体验优化与 0 产出策略收口）— 需 Jay.S Token

| 文件 | 操作 | 状态 | 保护级别 |
|------|------|------|----------|
| services/data/src/scheduler/data_scheduler.py | 修改 | 🔒 locked (`tok-6fc51e92-756e-476d-8b43-7c35db059334`) | P1 |
| services/data/src/notify/dispatcher.py | 修改 | 🔒 locked (`tok-6fc51e92-756e-476d-8b43-7c35db059334`) | P1 |
| services/data/src/notify/news_pusher.py | 修改 | 🔒 locked (`tok-6fc51e92-756e-476d-8b43-7c35db059334`) | P1 |
| services/data/tests/test_notify.py | 修改 | 🔒 locked (`tok-6fc51e92-756e-476d-8b43-7c35db059334`) | P1 |

### B6 明确排除

| 文件/路径 | 原因 |
|-----------|------|
| services/data/src/scheduler/pipeline.py | 本批只调通知，不修采集链 |
| services/data/src/collectors/overseas_minute_collector.py | 0 产出根因已知，但不在本批改动范围 |
| services/data/src/main.py | 不属于通知体验优化必要范围 |
| services/data/src/health/** | 不属于本批目标 |
| services/data/.env.example | 不改运行态配置 |
| shared/contracts/** | 无跨服务契约变更 |

---

## 锁控日志

| 时间 | 操作 | 批次 | 说明 |
|------|------|------|------|
| 2026-04-09 09:05 | 补档 | H0 | 补齐 TASK-0028 review/lock 账本 |
| 2026-04-09 09:05 | 冻结 | B6 | 冻结 4 文件白名单，状态 pending_token |
| 2026-04-09 09:12 | issue + validate | B6 | Jay.S 已签发并校验通过 P1 Token `tok-1e39e91a-191a-4b6f-afde-03dcc6f7b8c4` |
| 2026-04-09 13:39 | expired | B6 | 首张 B6 Token `tok-1e39e91a-191a-4b6f-afde-03dcc6f7b8c4` 过期，需补签执行锁回 |
| 2026-04-09 13:53 | issue + validate | B6 | Jay.S 已补签并校验通过锁回票 `tok-6fc51e92-756e-476d-8b43-7c35db059334`，范围与 review-id `REVIEW-TASK-0028-B6` 不变 |
| 2026-04-09 13:55 | lockback | B6 | `REVIEW-TASK-0028-B6` 复审通过，11 项通知测试通过，已执行 approved lockback |

---

【签名】项目架构师
【时间】2026-04-09 09:05
【设备】MacBook