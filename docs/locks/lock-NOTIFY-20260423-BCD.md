# 锁回记录 — TASK-NOTIFY-20260423 B/C/D

| 字段 | 值 |
|------|-----|
| 记录时间 | 2026-04-23 |
| 批次 | NOTIFY Round-1（B/C/D 三端） |
| 操作人 | Atlas |
| 审核 ID | REVIEW-TASK-NOTIFY-20260423-PRE |
| Commit | d588e80fa |
| 分支 | backup-settings-p0p1-20260420-193000 |

## Token 锁回状态

| Token ID | 任务 | 服务 | 状态 |
|----------|------|------|------|
| tok-38cf910c-489c-417b-8516-10c0c4a4cd73 | TASK-NOTIFY-20260423-B | data | locked ✅ |
| tok-f404d071-0126-4021-95d7-5cf1d4b93e1a | TASK-NOTIFY-20260423-C | decision | locked ✅ |
| tok-2c657332-e103-4707-bcb7-efb4f4183971 | TASK-NOTIFY-20260423-D | backtest | locked ✅ |

## 变更摘要

### Token B — data 通知降噪

变更文件：
- `services/data/src/notify/feishu.py` — 标题/落款统一格式
- `services/data/src/notify/news_pusher.py` — BATCH_INTERVAL_SEC 1800→3600
- `services/data/src/notify/card_templates.py` — SERVICE_NAME/heartbeat+4h
- `services/data/src/notify/dispatcher.py` — 静默窗口 08:00–24:10
- `services/data/src/scheduler/data_scheduler.py` — 删除 collector_start 噪音通知、下线 email_morning/afternoon、news_push_batch 改1h

### Token C — decision 通知分群

变更文件：
- `services/decision/src/notifier/feishu.py` — 三群路由 + 标题/落款统一
- `services/decision/src/notifier/dispatcher.py` — 静默窗口 + alarm.log 反馈
- `services/decision/.env.example` — 补三群 webhook 变量

### Token D — backtest 新增通知

变更文件（新建）：
- `services/backtest/src/notifier/__init__.py`
- `services/backtest/src/notifier/feishu.py`
- `services/backtest/src/notifier/dispatcher.py`

变更文件（更新）：
- `services/backtest/src/backtest/manual_runner.py` — 钩入完成/失败通知
- `services/backtest/.env.example` — 补 webhook 变量

## 部署验证

| 设备 | 服务 | 同步方式 | 状态 |
|------|------|---------|------|
| Mini | data:8105 | rsync 内网 | 已同步 ✅ |
| Studio | decision:8104 | rsync 内网 | 已同步 ✅ |
| Studio | backtest:8103 | rsync 内网 | 已同步 ✅ |

## 自校验

- `python3 -m py_compile` 全部通过
- git commit d588e80fa：12 files changed, 406 insertions(+), 56 deletions(-)

---
*Atlas | 2026-04-23*
