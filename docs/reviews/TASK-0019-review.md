# TASK-0019 Review

## Review 信息

- 任务 ID：TASK-0019
- 审核角色：项目架构师
- 审核阶段：sim-trading 收盘统计邮件 / 定时报表预审
- 审核时间：2026-04-07
- 审核结论：通过（当前轮次已冻结定时编排、时间窗、批次拆分与 legacy env 映射建议；本轮白名单仅限治理账本与 prompt，不进入 `services/sim-trading/**` 代码执行）

---

## 一、任务目标

1. 冻结收盘统计邮件 / 定时报表与即时通知的边界。
2. 冻结 scheduler、时间窗、报表数据面与批次拆分口径。
3. 冻结 legacy env 映射建议与 Secret 治理规则。

## 二、当前轮次白名单

1. `docs/tasks/TASK-0019-sim-trading-收盘统计邮件预审.md`
2. `docs/reviews/TASK-0019-review.md`
3. `docs/locks/TASK-0019-lock.md`
4. `docs/rollback/TASK-0019-rollback.md`
5. `docs/handoffs/TASK-0019-收盘统计邮件预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 三、当前轮次代码 Token 策略

1. 当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。
2. `TASK-0019-B0` 若进入实施，`services/sim-trading/.env.example` 需要单文件 P0 Token，且默认由 Atlas / Jay.S 处理。
3. `TASK-0019-B1` 若进入实施，`services/sim-trading/src/main.py`、`src/notifier/email.py`、`src/ledger/service.py`、`tests/test_notifier.py`、`tests/test_report_scheduler.py`（允许新增）需要 P1 Token。
4. `TASK-0019-B2` 若进入实施，`services/sim-trading/src/gateway/simnow.py`、`src/ledger/service.py`、`src/api/router.py`、`tests/test_ctp_notify.py`、`tests/test_report_scheduler.py` 需要 P1 Token。
5. 后续若新增跨服务报表契约到 `shared/contracts/**`，需要 P0 Token。

## 四、正式冻结结论

1. `TASK-0019` 独立于 `TASK-0014`，因为其属于定时编排 + 报表数据面。
2. 报表建议时间窗先冻结为 `15:20`、`23:10`（或 `23:40`）、`02:40`。
3. 批次拆分已冻结为 B0（如需要，`.env.example` 单文件 P0）/ B1（scheduler + 最小邮件报表骨架，P1）/ B2（账户 / 持仓 / 成交报表充实，P1）。
4. legacy env 映射建议已冻结为：`FEISHU_ALERT_WEBHOOK_URL` 优先于 `FEISHU_WEBHOOK_URL`；`SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` / `FROM_ADDR` / `TO_ADDRS` 映射到 `ALERT_EMAIL_*`。
5. legacy `J_BotQuant/.env` 只允许作为部署侧凭证来源，不得把 `/Users/jayshao/J_BotQuant/.env` 路径耦合进服务代码。

## 五、当前轮次通过标准

1. 已明确 `TASK-0019` 与 `TASK-0014` 的任务边界。
2. 已明确 `TASK-0019-B0` / `B1` / `B2` 的保护级别与建议白名单。
3. 已明确建议时间窗与 legacy env 映射规则。
4. 已明确真实 Secret 不得写入 Git、`.env.example` 或治理账本。

## 六、当前轮次未进入代码执行的原因

1. 本任务当前轮次只做治理冻结，不做服务实现。
2. `TASK-0014-A1` 与 `TASK-0014-A2` 应先于本任务进入执行。
3. 当前尚未取得 B0 / B1 / B2 的 P0 / P1 Token，也未最终冻结 B1 / B2 的精确测试文件名单。
4. 真实收件人、SMTP 凭证与 webhook 只允许运行时注入，不能先用仓内占位实现替代正式授权。

## 七、预审结论

1. **TASK-0019 预审通过。**
2. **当前轮次只完成收盘统计邮件 / 定时报表治理冻结，不进入代码执行。**
3. **后续进入实施前，必须由 Jay.S 先确认晚间时间窗最终值，并在 `TASK-0014-A4`、`TASK-0017-A4`、`TASK-0022-B` 收口后，按 B0（如需要）→ B1 → B2 顺序签发对应 P0 / P1 Token。**

## 八、2026-04-09 扩展预审补录

1. `TASK-0019-B0` 已升级为“剩余通知 / 报表模板占位合并批次”，文件严格限于 `services/sim-trading/.env.example`，默认由 Atlas / Jay.S 处理，不派发模拟交易 Agent。
2. `TASK-0019-B1` 的测试白名单已收紧为 `services/sim-trading/tests/test_notifier.py` 与 `services/sim-trading/tests/test_report_scheduler.py`（允许新增）。
3. `TASK-0019-B2` 的测试白名单已收紧为 `services/sim-trading/tests/test_ctp_notify.py` 与 `services/sim-trading/tests/test_report_scheduler.py`。
4. 串行关系冻结为：`TASK-0019-B1` / `TASK-0019-B2` 均需等待 `TASK-0014-A4`、`TASK-0017-A4`、`TASK-0022-B` 收口；B0 若启用，必须在 B1 前独立完成。