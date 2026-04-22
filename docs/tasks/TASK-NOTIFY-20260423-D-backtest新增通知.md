# TASK-NOTIFY-20260423-D backtest 新增通知模块

## 任务信息

- 任务 ID：TASK-NOTIFY-20260423-D
- 服务：backtest（**Studio 单点** `JBT-BACKTEST-8103`；Air 为体外循环，不接入通知）
- 执行 Agent：回测 Agent
- 创建人：Atlas
- 创建时间：2026-04-23
- 当前状态：📋 已建档 / 待预审
- 父批次：TASK-NOTIFY-20260423-000

## 现状

- backtest 服务**完全没有飞书/邮件通知模块**。
- 回测任务完成、失败、超时 → 用户无感知。
- 仅 dashboard 看板可查询。

## 改造目标

新建最小通知模块（参考 sim-trading 模板）：

1. 新建 `services/backtest/src/notifier/`（dispatcher + feishu + email + quiet_window + feedback）。
2. 三 webhook 路由 + 静默窗口 + 反馈机制（与全工作区统一）。
3. 触发点：
   - 单次回测完成 → 交易群（含品种/区间/收益/夏普/回撤）
   - 失败/超时 → 报警群 P1
   - Optuna 参数优化批次完成 → 交易群（含 Top3 参数组）
4. 每日 17:00 邮件汇总：当日所有回测任务表（HTML 表格）。
5. 全中文 + 标题前缀 + 落款 `JBT-回测`。

## 文件白名单（候选 · 全新建 + 最小接入）

```
services/backtest/src/notifier/__init__.py              # ★新建
services/backtest/src/notifier/dispatcher.py            # ★新建（参考 sim-trading）
services/backtest/src/notifier/feishu.py                # ★新建
services/backtest/src/notifier/email.py                 # ★新建
services/backtest/src/notifier/quiet_window.py          # ★新建
services/backtest/src/notifier/feedback.py              # ★新建
services/backtest/src/backtest/stock_runner.py          # 接入：完成/失败钩子
services/backtest/src/backtest/manual_runner.py         # 接入：完成/失败钩子
services/backtest/src/api/app.py（如适用）              # 调度日邮件 + /notify/health
services/backtest/.env.example                          # 新增三 webhook + SMTP
```

共 ≤ 10 个文件。

## 关键约束：Air 不接入通知

Air（192.168.31.245）为体外循环节点，用于参数优化等离线批跑，**不部署通知模块，不推送飞书/邮件**。所有通知推送统一由 Studio（192.168.31.142）的 `JBT-BACKTEST-8103` 容器负责。Air 触发的回测结果若需通知，须回传 Studio 后由 Studio 统一推送（如有需求，后续单独建档）。

## 关键实现点

### D1. 触发点接入

- `stock_runner.run()` finally 块：
  ```python
  from src.notifier.dispatcher import get_dispatcher, BacktestEvent
  get_dispatcher().dispatch(BacktestEvent(...))
  ```
- 失败：`except` 块推 P1。

### D2. 卡片字段

```
🔬 [回测-完成] {策略名} {品种} {区间}
收益：+12.3%  夏普：1.8  最大回撤：-5.2%
胜率：54%     交易次数：120
[查看详情](http://Air:3001/backtest/{task_id})
落款：JBT-回测 | {ts}
```

### D3. 邮件日汇总

- cron 17:00 触发 `/api/v1/backtest/daily-summary`，生成 HTML 表格邮件。
- 主题：`[JBT-回测] 当日回测汇总 YYYY-MM-DD`。

### D4. 静默 + 反馈

- 同 §A、§B、§C。

## 验收标准

1. 触发一次回测 → 完成后 5s 内交易群收到 `[回测-完成]` 卡。
2. 故意 raise 一次 → 报警群收到 P1。
3. 17:00 邮件汇总：HTML 表格 + 中文 + 落款。
4. 02:00 触发回测 → 飞书无推送，08:00 累积卡。
5. `curl http://192.168.31.142:8103/api/v1/notify/health` 返回 200（Studio 单点）。
6. Air 节点无通知推送（体外循环，不部署 notifier 模块）。

## 风险与回滚

- 新增模块，对现有回测逻辑零侵入（仅在 runner 末尾追加钩子）。
- 备份：无需（新建文件）。
- 回滚：删除 `notifier/` 目录 + `git revert`。

## 依赖

- 项目架构师终审。
- Jay.S 签 Token。
- Air / Studio 现网均可滚动重启。
