# TASK-NOTIFY-20260423-E live-trading 通知占位

## 任务信息

- 任务 ID：TASK-NOTIFY-20260423-E
- 服务：live-trading（暂未部署）
- 执行 Agent：实盘交易 Agent
- 创建人：Atlas
- 创建时间：2026-04-23
- 当前状态：📋 已建档 / 待预审（实施可延期至实盘开通后）
- 父批次：TASK-NOTIFY-20260423-000

## 背景

- live-trading 当前仅有 `services/live-trading/{configs,src,tests}` 骨架，未真正部署。
- 按 ATLAS_PROMPT 总规划，实盘启用前必须先准备完整通知占位结构。
- 本任务只产出**结构占位 + 模板复制**，实施侧不接入真实 CTP 回调。

## 改造目标

1. 复制 sim-trading 完成后的 `notifier/` 模块结构到 `services/live-trading/src/notifier/`。
2. 全部标题前缀替换为 `[实盘-*]`。
3. 落款固定 `JBT-实盘`。
4. **强制 + 双发**：所有 P0/P1/P2 与成交回报，**飞书报警群 + 邮件**双发，不允许单通道。
5. 灰度阶段：邮件抄送 Jay.S + 团队成员（待 .env.example 列出）。
6. 静默窗口仍为 08:00–24:10，但实盘任何成交回报 / 风控触发穿透。

## 文件白名单（候选 · 全新建占位）

```
services/live-trading/src/notifier/__init__.py
services/live-trading/src/notifier/dispatcher.py        # 复制 sim 版本 + 双发约束
services/live-trading/src/notifier/feishu.py
services/live-trading/src/notifier/email.py
services/live-trading/src/notifier/trade_push.py
services/live-trading/src/notifier/quiet_window.py
services/live-trading/src/notifier/feedback.py
services/live-trading/.env.example                       # 三 webhook + SMTP + 灰度收件人
```

共 8 个文件（全部新建）。

## 关键实现点

### E1. 双发约束

`dispatcher.dispatch`:
- 任何 `RiskEvent.category in {TRADE, ORDER, RISK_LIMIT, CTP_*}` → 强制 `channels={"feishu", "email"}`，且必须两通道同时成功才返回 True。
- 任一通道失败 → 立即写 `live_trading_alarm.log` + 同时再尝试 1 次。

### E2. 标题前缀

```
🚨 [P0-实盘报警] / ⚠️ [P1-实盘报警] / 🔔 [P2-实盘报警]
📈 [实盘-成交] / 📈 [实盘-订单] / 📊 [实盘-节段]
```

### E3. 灰度收件人

`.env.example`:
```
LIVE_EMAIL_CC=jayshao@xxx,team@xxx,backup@xxx
```

## 验收标准

1. 模块结构完整复制（与 sim-trading 完成后版本一致）。
2. 单元测试：模拟 P1 → 飞书报警群 + 邮件均收到。
3. 单元测试：模拟成交 → 飞书 + 邮件双发。
4. 任一通道失败模拟 → 重试 1 次后失败，写 alarm.log。
5. 占位完成不需要部署到任何设备（live-trading 未上线）。

## 风险与回滚

- 全新建，零现有逻辑影响。
- 实施可延后到实盘开通前 1 周再启动。

## 依赖

- TASK-NOTIFY-20260423-A 完成（复制 sim-trading 模板）。
- 项目架构师终审。
- Jay.S 签 Token。
