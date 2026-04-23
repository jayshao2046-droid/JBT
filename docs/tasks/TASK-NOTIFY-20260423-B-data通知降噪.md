# TASK-NOTIFY-20260423-B data 通知降噪 + 节奏对齐

## 任务信息

- 任务 ID：TASK-NOTIFY-20260423-B
- 服务：data（Mini，Docker `JBT-DATA-8105`）
- 执行 Agent：数据 Agent
- 创建人：Atlas
- 创建时间：2026-04-23
- 当前状态：📋 已建档 / 待预审
- 父批次：TASK-NOTIFY-20260423-000

## 现状

- 资讯群每日 120–160 张采集摘要卡，刷掉关键开收盘/新闻信息。
- 新闻批推 30min 一次，单卡 50 条，密度过高。
- 2h 心跳 + 多个开收盘卡时间窗口堆叠。
- session_am 当前在 09:30，与期货实际开盘 09:00 错位。
- RSS 推送已带 `[标题](URL)` 格式，但需复核所有路径。
- 已用三 webhook，但路由路径与新群边界不完全一致。

## 改造目标

1. **采集摘要分流**（不再删，按结果路由）：
   - 单器成功完成 → 交易群（`[数据-采集]` 1 行紧凑）
   - 60s 窗口聚合摘要 → 资讯群（保留现有摘要卡，频率不变）
   - 失败 / 0 产出 → 报警群 P2（带升级）
2. **新闻批推 30min → 60min**，单卡上限 30 条；每条强制带链接，无链接条目过滤掉。
3. **黑天鹅即时推送**：增加同关键词 10 分钟内合并；多源触发列在同一卡。
4. **心跳 2h → 4h**：08/12/16/20 整点；任一采集器连续失败 ≥3 轮立即提前推。
5. **开收盘节段对齐**：
   - 取消 09:30 session_am，改为 09:00。
   - 新增 13:30、21:00 开盘卡。
   - 11:30、15:00、02:30 收盘卡保留。
   - 08:55 盘前检查卡（新增）。
6. **邮件夜报**：23:30 新增，全天采集器 SLA + 异常 Top10 + 新闻话题聚类。
7. 全部中文化、统一标题前缀、统一落款 `JBT-数据`。
8. 静默窗口 08:00–24:10；P0 + 报警群事件穿透。
9. 通道失败反馈机制；新增 `/api/v1/notify/health`。

## 文件白名单（候选 · 待项目架构师终审）

```
services/data/src/notify/__init__.py
services/data/src/notify/dispatcher.py             # 静默窗口 + 反馈机制 + 三群路由口径校准
services/data/src/notify/feishu.py                 # 标题前缀 + 落款 + 中文化
services/data/src/notify/email_notify.py           # HTML 模板中文化 + 落款
services/data/src/notify/news_pusher.py            # 30→60min + 链接强校验 + 黑天鹅冷却
services/data/src/notify/card_templates.py         # 七色映射 + 标题前缀
services/data/src/notify/quiet_window.py           # ★新建：静默窗口工具
services/data/src/notify/feedback.py               # ★新建：失败横幅累计
services/data/src/scheduler/data_scheduler.py      # 心跳 4h + 节段对齐 09/13:30/21 + 邮件夜报
services/data/src/scheduler/pipeline.py            # 采集摘要分流路由（如涉及）
services/data/src/main.py                          # /api/v1/notify/health 端点
services/data/.env.example                         # 复核 ALERT/TRADE/INFO 三键文档
```

共 12 个文件（含 2 个新建），P0 区域不涉及。

## 关键实现点

### B1. 采集摘要分流

`dispatcher.record_collection_result` 改为按 `status` 分流：
- `success` → `_emit_trade_group_oneliner()` 立即推交易群（无聚合，1 行）
- 同时进入 60s 聚合窗口 → 资讯群摘要卡（保留 `flush_collection_window`）
- `zero_output` → 资讯群"0 产出"摘要
- `failed` → 报警群 P2（接入升级 P2→P1→P0 链）

### B2. 新闻批推升级

`news_pusher.py`:
- `BATCH_INTERVAL_SEC = 1800` → `3600`
- `_build_batch_body` `max_show=50` → `max_show=30`
- 新增 `_validate_link(item)`：无 URL 直接 drop，统计入"丢弃因无链接 N 条"
- 新增 `_breaking_dedup`：黑天鹅同关键词 600s 内合并，多源 URL 列在同一卡

### B3. 节段对齐

`data_scheduler.py` 调度调整：
- `session_am` cron `09:30` → `09:00`
- 新增 `session_noon` cron `13:30 mon-fri`
- `session_pm` cron `21:00 mon-thu` 保留
- 新增 `session_premarket` cron `08:55 mon-fri`
- 心跳 `IntervalTrigger(hours=2)` → `hours=4`
- 新增 `daily_email_evening` cron `23:30`

### B4. 静默窗口

新增 `quiet_window.py::_in_push_window()`：08:00–24:10 窗口；其他时间静默。
`dispatcher.dispatch` 调用此函数；P0 / `bypass_quiet_hours=True` 穿透。
静默期非穿透事件 → `_quiet_pending_queue`，08:00 推汇总卡。

### B5. 反馈机制

- 新增 `feedback.py::FeedbackTracker`：跟踪失败次数与最早时间。
- `dispatcher.dispatch` 失败 → 写 `runtime/logs/data_alarm.log` JSONL。
- 下次成功推送在卡片底部追加 `⚠️ 上次推送失败累计 N 条，最早 HH:MM:SS`。
- 新增 `GET /api/v1/notify/health` 端点。

### B6. 中文化与落款

- 所有 `card_templates.alert_card` 中的 `Body` / `Trace` / `Source` 等 label 改中文。
- 落款固定 `JBT-数据 | YYYY-MM-DD HH:MM:SS`。
- 标题前缀按 §A.4 规范。
- 英文变量名（如 `notify_type`、`event_code`）必须有中文注释。

### B7. RSS 链接强制

- `_normalize_record` 后增加 `if not normalized.get("url"): continue`。
- `news_dedup_uids.json` 不变。

## 验收标准

1. 资讯群日均通知量 ≤ 40 张（当前 120–160）。
2. 交易群增加"采集流水"1 行卡，盘中每 1–2 分钟 1 张，可识别。
3. 09:00 / 13:30 / 21:00 准时收到对应开盘卡。
4. 02:00 触发任一非 P0 → 飞书无推送，08:00 收到"夜间累积"。
5. 抓样 5 张卡：100% 中文 + 标题 + 落款 + RSS 必带链接。
6. 23:30 收到邮件夜报，HTML Card 格式。
7. `curl http://192.168.31.74:8105/api/v1/notify/health` 返回 200。
8. 模拟双通道失败 → `data_alarm.log` 出现条目。

## 风险与回滚

- Mini Docker 部署：先 `git stash` + 灰度，验证 30min 后再固化。
- 备份：`services/data/src/notify_backup_20260423/`
- 回滚：恢复备份 + `docker restart JBT-DATA-8105`。
- 节段对齐次日早 09:00 必须人工抓样验证。

## 依赖

- 项目架构师终审。
- Jay.S 签 Token。
- Mini 现网调度器可滚动重启（无影响 24/7 采集，最长中断 30s）。
