# TASK-0014 Review

## Review 信息

- 任务 ID：TASK-0014
- 审核角色：项目架构师
- 审核阶段：sim-trading 风控通知链路预审 + `TASK-0014-A1` / `TASK-0014-A2` 终审补录 + 2026-04-09 扩展预审补录
- 审核时间：2026-04-09
- 审核结论：通过（预审冻结结论继续有效；`TASK-0014-A1` / `TASK-0014-A2` 已锁回，2026-04-09 已新增 A3 / A4 扩展批次预审）

---

## 一、任务目标

1. 冻结 SimNow 的独立飞书 + 独立邮件双通道风控通知口径。
2. 冻结最小风险事件字段与 P0 / P1 / P2 分级要求。
3. 冻结通知失败必须反向抬升系统风险状态的失败收口规则。
4. 冻结“即时通知继续归入 `TASK-0014`”的补充批次 A1 / A2 与凭证来源治理口径。

## 二、当前轮次白名单

1. `docs/tasks/TASK-0014-sim-trading-风控通知链路预审.md`
2. `docs/reviews/TASK-0014-review.md`
3. `docs/locks/TASK-0014-lock.md`
4. `docs/rollback/TASK-0014-rollback.md`
5. `docs/handoffs/TASK-0014-风控通知链路预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 三、当前轮次代码 Token 策略

1. 当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。
2. 补充批次 A1 若进入实施，`services/sim-trading/src/main.py`、`src/risk/guards.py`、`src/notifier/dispatcher.py` 与对应测试文件需要 P1 Token。
3. 补充批次 A2 若进入实施，`services/sim-trading/src/api/router.py`、`src/gateway/simnow.py` 与最多 2 个测试文件需要 P1 Token。
4. 后续若补充 `services/sim-trading/.env.example` 的通知字段占位，需要单文件 P0 Token。
5. 后续若新增跨服务通知事件契约到 `shared/contracts/**`，需要 P0 Token。

## 四、即时通知补充批次冻结

1. `TASK-0014` 继续承接“即时飞书 / 邮件告警”，不另开任务号。
2. A1 冻结为“通知 bootstrap 与风险钩子闭环”，建议白名单为 `services/sim-trading/src/main.py`、`src/notifier/dispatcher.py`、`src/risk/guards.py`、`tests/test_notifier.py`、`tests/test_risk_hooks.py`。
3. A2 冻结为“系统事件来源接线”，建议白名单为 `services/sim-trading/src/api/router.py`、`src/gateway/simnow.py` 与最多 2 个测试文件。
4. 执行顺序冻结为 `TASK-0014-A1` → `TASK-0014-A2`；当前 A1 已闭环，A2 继续待执行。
5. Jay.S 已明确允许 legacy `J_BotQuant/.env` 作为凭证来源，但只允许部署侧 env mapping / fallback，不得把 `/Users/jayshao/J_BotQuant/.env` 路径耦合进服务代码。

## 五、当前轮次通过标准

1. 独立飞书 + 独立邮件双通道已冻结为正式治理口径。
2. 最小事件字段与风险分级口径已冻结。
3. 已明确单通道失败、双通道失败的系统风险收口规则。
4. 已明确即时通知继续归入 `TASK-0014` 的补充批次 A1 / A2。
5. 已明确真实通知凭证不得写入 Git、`.env.example` 或治理账本。

## 六、当前轮次未进入代码执行的原因

1. 本任务当前轮次只做治理冻结，不做服务实现。
2. `TASK-0009`、`TASK-0013`、`TASK-0010` 仍是执行前置，其中 `TASK-0010` 还需先提供最小风险事件输出与风控钩子占位。
3. 在 2026-04-06 预审轮次中，A1 / A2 虽已冻结建议白名单，但当时尚未取得对应 P1 Token，也未最终冻结 A2 的精确测试文件名单。
4. 若后续需要补 `services/sim-trading/.env.example` 字段，占位补录必须拆成独立 P0 批次。
5. 真实 webhook、邮箱鉴权与 SMTP Secret 当前只允许运行时注入，不能先用仓内占位实现替代正式授权。

## 七、预审结论

1. **TASK-0014 预审通过。**
2. **当前轮次只完成通知链路治理冻结，不进入代码执行。**
3. **即时通知继续归入 `TASK-0014` 的补充批次 A1 / A2 / A3 / A4；其中 `TASK-0014-A1` / `TASK-0014-A2` 已完成实施、终审与锁回，A3 / A4 当前待执行。**
4. **后续进入 `TASK-0014-A3` / `TASK-0014-A4` 或 contracts 扩展前，仍必须由 Jay.S 先按顺序签发对应 P1 / P0 Token；`.env.example` 剩余模板占位统一并入 `TASK-0019-B0`。**

## 八、2026-04-07 TASK-0014-A1 终审补录

1. `TASK-0014-A1` 实际业务白名单严格限于 5 个文件：`services/sim-trading/src/main.py`、`services/sim-trading/src/notifier/dispatcher.py`、`services/sim-trading/src/risk/guards.py`、`services/sim-trading/tests/test_notifier.py`、`services/sim-trading/tests/test_risk_hooks.py`。
2. 实现收口为：`main.py` 完成 notifier bootstrap；`dispatcher.py` 完成单例 register / get / clear / bootstrap；`risk/guards.py` 完成 `emit_alert` 到最小 `RiskEvent` 的映射。
3. 最小自校验结果为 `13 passed, 1 skipped`；对应代码提交为 `d4b5817`。
4. 本批次 P1 token_id 为 `tok-7ab3cadf-043b-4709-b8e7-d00519f1ae81`；lockback review-id 为 `REVIEW-TASK-0014-A1`，当前状态 `locked`。
5. 终审复核确认：本批未扩展到 scheduler、日报、CTP 事件接线或 legacy `.env` 路径读取。
6. 终审结论：通过；通知主线下一执行批次更新为 `TASK-0014-A3` → `TASK-0014-A4`。

## 九、2026-04-09 扩展预审补录

1. 本轮通知系统扩容继续复用 `TASK-0014`，不新增任务号。
2. `TASK-0014-A3` 正式冻结为“通知内核专业化”，建议白名单为 `services/sim-trading/src/notifier/dispatcher.py`、`src/notifier/email.py`、`src/notifier/feishu.py`、`src/risk/guards.py`、`tests/test_notifier.py`，保护级别 **P1**。
3. `TASK-0014-A4` 正式冻结为“运行时事件源与守护恢复接线”，建议白名单为 `services/sim-trading/src/main.py`、`src/api/router.py`、`src/gateway/simnow.py`、`tests/test_ctp_notify.py`、`tests/test_risk_hooks.py`，保护级别 **P1**。
4. 串行关系冻结为 `TASK-0014-A3` → `TASK-0014-A4`；`TASK-0017-A4` 可与通知扩容并行，但 `TASK-0022-B` 需等待 `TASK-0014-A4` 完成后再启动。
5. 为避免同一受保护文件重复签发，`.env.example` 相关剩余模板占位统一并入 `TASK-0019-B0`，`TASK-0014` 本轮不再单独申请 `.env.example` P0 Token。
6. 当前终审状态更新为：A1 / A2 = `locked`，A3 / A4 = `pending_token`。