# TASK-NOTIFY-20260423-A sim-trading 通知重构（成交即时 + 三群分流）

## 任务信息

- 任务 ID：TASK-NOTIFY-20260423-A
- 服务：sim-trading（Alienware，裸 Python 部署）
- 执行 Agent：模拟交易 Agent
- 创建人：Atlas
- 创建时间：2026-04-23
- 当前状态：📋 已建档 / 待预审
- 父批次：TASK-NOTIFY-20260423-000

## 现状

- 飞书走单一 `FEISHU_WEBHOOK_URL`，所有事件混在一个群。
- **没有成交回报、订单状态的即时推送**（最大缺口）。
- 心跳 2h 一次，与 data 端 2h 心跳重叠，资讯群噪音叠加。
- 23:10 邮件日报已存在，HTML 模板偏简陋。
- 落款 `JBT SimTrading`（英文），需改为 `JBT-模拟交易`。

## 改造目标

1. 拆分 3 webhook：`FEISHU_ALERT/TRADE/INFO_WEBHOOK_URL`，按事件类型自动路由。
2. **新增成交即时推送**：CTP `OnRtnTrade` → 立即推交易群，<3s，无去重。
3. **新增订单状态推送**：拒单/部成/全成/撤单 → 交易群，1 行紧凑卡，无去重。
4. 心跳 2h → 4h，CTP 断开立即提前推。
5. 开收盘卡对齐 09:00 / 13:30 / 21:00（盘前 08:55 + 收盘 11:30/15:00/02:30）。
6. 邮件日报升级 HTML Card（成交明细 + 风控事件 + CTP 稳定性）。
7. 全部中文化、统一标题前缀、统一落款 `JBT-模拟交易`。
8. 静默窗口 08:00–24:10。
9. 通道失败反馈机制（飞书失败 → 邮件兜底，双通道失败 → alarm.log + 下次推送附横幅）。

## 文件白名单（候选 · 待项目架构师终审）

```
services/sim-trading/src/notifier/__init__.py
services/sim-trading/src/notifier/dispatcher.py          # 改 3 webhook + 静默 + 反馈
services/sim-trading/src/notifier/feishu.py              # 改路由 + 标题/颜色/落款
services/sim-trading/src/notifier/email.py               # 改 HTML 模板 + 中文化
services/sim-trading/src/notifier/trade_push.py          # ★新建：成交/订单即时推送器
services/sim-trading/src/notifier/quiet_window.py        # ★新建：静默窗口工具
services/sim-trading/src/health/heartbeat.py             # 中文化 + 4h 节奏
services/sim-trading/src/main.py                         # 心跳调度 + 节段卡 + 反馈横幅
services/sim-trading/src/api/router.py                   # 接入成交/订单回调推送 + /notify/health
services/sim-trading/src/risk/guards.py                  # 中文落款
services/sim-trading/.env.example                        # 新增 ALERT/TRADE/INFO 三键
```

共 11 个文件（含 2 个新建），P0 区域不涉及。

## 关键实现点

### A1. dispatcher 三群路由

`RiskEvent.category` → 群映射：
- `RISK_LIMIT / CTP_*` → ALERT
- `TRADE / ORDER / SESSION_CLOSE_SUMMARY` → TRADE
- `HEARTBEAT / SYSTEM` → INFO
- 路由失败兜底链：TRADE → INFO → ALERT。

### A2. 成交即时推送（trade_push.py）

接入点：`router.py` 现有 CTP 回调（OnRtnTrade）。

推送字段：
```
📈 [模拟-成交] {合约} {方向} {手数}@{价格}
账户：{account}  策略：{strategy}  信号：{signal_id}
本次盈亏：{pnl}  累计今日：{today_pnl}
落款：JBT-模拟交易 | {ts}
```

约束：无去重、无静默（成交永远推），但走交易群不打扰报警群。

### A3. 订单状态推送

OnRtnOrder → 仅在状态变化为终态（全成/拒单/撤单）或部成时推送。
拒单：颜色橙色，进交易群；连续 5 笔拒单 → 升级到 ALERT P1。

### A4. 心跳 4h + 异常优先

- 默认 `IntervalTrigger(hours=4)`：08/12/16/20 整点。
- 若 `_system_state.ctp_md_connected==False` 持续 ≥3min → 提前发心跳，附 P1 标识。

### A5. 节段卡（08:55 / 09:00 / 11:30 / 13:30 / 15:00 / 21:00 / 02:30）

新增 `_session_anchor_scheduler`，每个时点合并推送：
- 盘前 08:55：CTP 状态 + 账户余额 + 风控状态
- 开盘 09:00/13:30/21:00：开盘提示 + 当前持仓 + 当前挂单
- 收盘 11:30/15:00/02:30：本节段成交笔数 + 净盈亏 + 持仓变化

### A6. 静默窗口

- 利用 `quiet_window.py::_in_push_window()`。
- P0 + 成交回报 + 订单终态穿透。
- 静默期非穿透事件进 `_pending_quiet_queue`，08:00 推一张"夜间累积"汇总卡。

### A7. 反馈机制

- `dispatcher` 跟踪 `_last_failure_ts`、`_pending_failure_count`。
- 任一通道发送失败 → 写 `runtime/logs/sim_trading_alarm.log`（JSONL）。
- 下一次任意通道成功推送 → 在卡片底部追加 `⚠️ 上次推送失败累计 N 条，最早 HH:MM:SS`。
- 新增 `GET /api/v1/notify/health`：返回 24h 成功率、失败次数、最近失败原因 Top3。

## 验收标准

1. CTP 模拟成交一笔 → 3s 内交易群收到 `[模拟-成交]` 卡片。
2. 模拟下单被拒 → 5s 内交易群收到 `[模拟-订单]` 卡片，颜色橙色。
3. 任一非 P0 在 02:00 触发 → 飞书无推送，08:00 整点收到"夜间累积"卡。
4. 手工 unset webhook 后触发一次告警 → `sim_trading_alarm.log` 出现一行；恢复 webhook 后下次推送顶部出现 `⚠️ 上次推送失败累计 1 条`。
5. 抓样 5 张飞书卡片：100% 中文 + 标题 `JBT 模拟交易 [...] xxx` + 落款 `JBT-模拟交易`。
6. `curl http://192.168.31.223:8101/api/v1/notify/health` 返回 200 + JSON。
7. 23:10 邮件日报：HTML Card + 中文 + 主题 `[JBT-模拟交易] 收盘日报 YYYY-MM-DD`。

## 风险与回滚

- 备份：`services/sim-trading/src/notifier_backup_20260423/`
- 回滚命令：`cp -r notifier_backup_20260423/* notifier/`
- 部署窗口：选择非交易时段（夜盘 02:30–08:55 之间）。
- Alienware 部署遵循 `TASK-P1-20260422-Alienware-sim-trading真演练` 已收口的 deploy/rollback 链路。

## 依赖

- 项目架构师终审通过。
- Jay.S 签发本任务的 Token。
- Alienware 现网 sim-trading 进程可控（`JBT_SimTrading_Watchdog`）。
