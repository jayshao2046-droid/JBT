# TASK-NOTIFY-20260423-C decision 通知分群整理

## 任务信息

- 任务 ID：TASK-NOTIFY-20260423-C
- 服务：decision（Studio，Docker `JBT-DECISION-8104`）
- 执行 Agent：决策 Agent
- 创建人：Atlas
- 创建时间：2026-04-23
- 当前状态：📋 已建档 / 待预审
- 父批次：TASK-NOTIFY-20260423-000

## 现状

- 飞书 + 邮件双通道已具备，但 6+ 个触发点（factor_loader / daily / gate_reviewer / failover / executor / signal / researcher_evaluate）混在一个 webhook。
- 日报 cron 已是 11:35 / 15:05 / 23:05，与期货节奏接近但未完全对齐。
- billing_notifier 1h 一次，量较小但可优化。
- 落款未标准化为 `JBT-决策`。

## 改造目标

1. 拆 3 webhook：`FEISHU_ALERT/TRADE/INFO_WEBHOOK_URL`，按 `NotifyLevel + event_type` 路由：
   - `P0/P1/P2` → 报警群
   - `SIGNAL / GATE_*` → 交易群（无静默）
   - `RESEARCH / DAILY / NOTIFY` → 资讯群
2. 日报 cron 对齐期货 5 节段：`09:05,11:35,15:05,21:05,23:05`。
3. billing_notifier 1h → 4h；余额 <20% 时插播报警群 P2。
4. failover 切换通知：交易群 + 报警群双发（确保看到）。
5. researcher 评分卡：交易群（避免淹没在资讯群）。
6. 中文化、统一前缀、统一落款 `JBT-决策`。
7. 静默窗口 08:00–24:10；信号/门控/failover 穿透。
8. 反馈机制；新增 `/api/v1/notify/health`。

## 文件白名单（候选）

```
services/decision/src/notifier/__init__.py
services/decision/src/notifier/dispatcher.py        # 三群路由 + 静默 + 反馈
services/decision/src/notifier/feishu.py            # 标题/颜色/落款/中文化
services/decision/src/notifier/email.py             # HTML 模板中文化
services/decision/src/notifier/daily_summary.py     # 5 节段对齐 + 落款
services/decision/src/notifier/gate_notifications.py# 门控类强制交易群
services/decision/src/notifier/health_monitor.py    # 报警群路由
services/decision/src/notifier/quiet_window.py      # ★新建
services/decision/src/notifier/feedback.py          # ★新建
services/decision/src/llm/billing_notifier.py       # 1h → 4h
services/decision/src/api/app.py                    # 调度时点更新 + /notify/health
services/decision/.env.example                      # 三 webhook 文档
```

共 12 个文件（含 2 个新建）。

## 关键实现点

### C1. 三群路由

`dispatcher.dispatch` 增加 `_resolve_webhook(event)`：
```python
if event.notify_level in (P0, P1, P2): -> ALERT
if event.event_type in ("SIGNAL", "GATE_*"): -> TRADE
if event.event_type in ("RESEARCH", "DAILY"): -> INFO
default: -> INFO
```

### C2. 节段对齐

`api/app.py::_start_daily_summary_scheduler`:
```
DECISION_DAILY_SUMMARY_TIMES = "09:05,11:35,15:05,21:05,23:05"
```

### C3. billing_notifier

`llm/billing_notifier.py::_scheduler_loop`:
- `await asyncio.sleep(3600)` → `await asyncio.sleep(14400)`
- 余额 <20% 触发 → 走报警群 P2

### C4. 信号/门控无静默

`SIGNAL` 与 `GATE_*` 类事件强制 `bypass_quiet_hours=True`。

### C5. 中文化

- `gate_notifications` 全英文模板改中文。
- `daily_summary` 主题 `[JBT-决策] {时点}日报 {date}`。

### C6. 反馈与健康端点

同 §A.7、§B.5。

## 验收标准

1. 信号触发 → 5s 内交易群收到 `[决策-信号]` 卡。
2. P1 异常 → 报警群单独收到。
3. 日报 09:05/11:35/15:05/21:05/23:05 准时。
4. 02:00 触发研究类 → 飞书无推送，08:00 累积卡。
5. 抓样 5 张：100% 中文 + 标题 + 落款 `JBT-决策`。
6. `curl http://192.168.31.142:8104/api/v1/notify/health` 返回 200。

## 风险与回滚

- Studio Docker：滚动重启 `JBT-DECISION-8104`。
- 备份：`services/decision/src/notifier_backup_20260423/`。
- 回滚：恢复备份 + 容器重启。

## 依赖

- 项目架构师终审。
- Jay.S 签 Token。
