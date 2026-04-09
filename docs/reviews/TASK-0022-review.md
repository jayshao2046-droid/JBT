# TASK-0022 Review

## Review 信息

- 任务 ID：TASK-0022
- 审核角色：项目架构师
- 审核阶段：TASK-0022-A 第二次正式终审；2026-04-10 TASK-0022-B 终审
- 审核时间：2026-04-08 02:57 +0800；2026-04-10（批次 B 终审）
- 审核结论：通过（批次 A/B 均已完成终审与锁回）

---

## 一、任务目标

1. 冻结 sim-trading 当前 4 项新增问题的正式归属与任务边界。
2. 冻结“主卡片 50 万本地虚拟盘口径”与“CTP 快照次级展示”字段边界。
3. 冻结最小只读日志查看的后端 / 前端最小实现范围。

## 二、当前轮次白名单

1. `docs/tasks/TASK-0022-sim-trading-运行态交互收口与只读日志预审.md`
2. `docs/reviews/TASK-0022-review.md`
3. `docs/locks/TASK-0022-lock.md`
4. `docs/handoffs/TASK-0022-sim-trading-运行态交互预审交接单.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

## 三、归属与边界审核结论

1. `TASK-0017` 已冻结为 Docker / Mini 部署治理，本轮 4 项问题不属于部署问题，不得并入。
2. `TASK-0015` 历史口径为 dashboard 正式归属与 `/tmp` 临时看板，不等于当前仓内真实运行的 sim-trading 控制台；本轮应归属 `services/sim-trading/**`。
3. 当前前端真实路径为 `services/sim-trading/sim-trading_web/**`，后端真实路径为 `services/sim-trading/src/**`，因此本轮是 **sim-trading 单服务运行态收口**，不是 dashboard 聚合任务。
4. 当前轮次不进入 `shared/contracts/**`；`shared/contracts/sim-trading/account.md` 保持不变，避免把单服务 UI 收口误升级为跨服务契约变更。

## 四、代码 Token 策略

1. 当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。
2. 批次 A 需要 **P1 Token**，建议白名单为：
   - `services/sim-trading/src/api/router.py`
   - `services/sim-trading/src/gateway/simnow.py`
   - `services/sim-trading/sim-trading_web/app/operations/page.tsx`
   - `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`
   - `services/sim-trading/tests/test_console_runtime_api.py`
3. 批次 B 需要 **P1 Token**，建议白名单为：
   - `services/sim-trading/src/main.py`
   - `services/sim-trading/src/api/router.py`
   - `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`
   - `services/sim-trading/tests/test_log_view_api.py`
4. 当前任务不需要 P0 Token；若后续要改 `.env.example` 或 `shared/contracts/**`，必须另行补做 P0 预审。

## 五、正式冻结结论

1. 自动补齐必须只显示期货合约，不能继续混入期权样式代码或杂项键名。
2. 主卡片必须固定回到“本地虚拟盘总本金 50 万”口径；CTP 账户 `balance`、`available`、`margin` 等只允许作为次级快照展示。
3. L2 曲线说明必须集中展示，并明确“触碰什么阈值会触发什么动作”。
4. 日志查看最小实现只允许“当前服务最近日志的只读查看”；不允许文件路径输入、目录浏览、下载或写操作。
5. 批次 A / B 因共享 `router.py` 与 `intelligence/page.tsx`，默认 **不可并行**。

## 六、当前轮次通过标准

1. 已把本事项独立为 `TASK-0022`，并明确不复用 `TASK-0015` / `TASK-0017`。
2. 已冻结服务归属为 `services/sim-trading/**` 单服务范围。
3. 已冻结 2 个 P1 批次、白名单、保护级别、验收标准与是否可并行。
4. 已明确当前轮次只做 P-LOG，不进入服务代码执行。

## 七、当前轮次未进入代码执行的原因

1. 当前仅完成预审建档，尚未由 Jay.S 为模拟交易 Agent 签发批次 A / B 的 P1 Token。
2. 批次 B 的最小只读日志方案仍被明确限制为“进程内只读缓冲”；若 Jay.S 要求跨容器或持久文件级日志查看，当前白名单必须重做。
3. 当前 `services/**`、`shared/contracts/**`、`.env.example` 与其他非白名单文件继续锁定。

## 八、预审结论

1. **`TASK-0022` 预审通过。**
2. **本事项当前正式归属 `services/sim-trading/**`，不走 dashboard，不并入 `TASK-0017`。**
3. **当前 4 项问题已拆为 2 个 P1 批次，默认顺序执行，均待 Jay.S 签发对应 P1 Token。**
4. **本轮仅完成治理冻结，不进入代码执行。**

## 九、TASK-0022-A 第一次正式终审（历史留痕）

- 审核阶段：批次 A 正式终审
- review-id：`REVIEW-TASK-0022-A`
- 审核时间：2026-04-08
- 审核结论：**未通过；不得 lockback**

### 1. 定向核验范围

1. 本次终审仅按 `TASK-0022-A` 五个白名单文件定向核验：
   - `services/sim-trading/src/api/router.py`
   - `services/sim-trading/src/gateway/simnow.py`
   - `services/sim-trading/sim-trading_web/app/operations/page.tsx`
   - `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`
   - `services/sim-trading/tests/test_console_runtime_api.py`
2. 仓库内其他 dirty files 不纳入本批结论；但若同一白名单文件内部混入与批次 A 无关的 hunk，仍视为本批阻断。

### 2. 已复核通过项

1. 5 个白名单文件 `get_errors = 0` 已复核。
2. 已独立复跑 `PYTHONPATH=. ../../.venv/bin/pytest tests/test_console_runtime_api.py tests/test_health.py tests/test_ctp_notify.py -q`，结果为 `6 passed, 4 warnings`。
3. futures-only 自动补齐、主卡片 50 万口径与 L2 说明集中化三项目标均已在代码中看到对应落点。

### 3. 阻断点

1. **`services/sim-trading/sim-trading_web/app/operations/page.tsx` 引入了 stale closure 回归。**
   `poll` 当前仍是空依赖回调，却在内部读取 `availableContracts`、`contractInput` 与 `orderParams.contract`，后续轮询会继续使用初始态而不是用户当前选择，导致 `exactInputContract`、`defaultContract` 与 `setOrderBook(...)` 存在绑定错误风险；这会直接影响自动补齐与盘口联动，不能作为通过态锁回。
2. **`services/sim-trading/sim-trading_web/app/intelligence/page.tsx` 混入了超出批次 A 目标的 hunk，且新增逻辑与当前接口结构不一致。**
   本批目标只允许“L2 黄线 / 红线说明居中收口并写清触发动作”，但当前文件同时新增了 `dailyPnlMap`、历史清空按钮、日历盈亏着色等范围外行为；更关键的是，`handleRefresh()` 读取的是 `acct?.net_pnl`，而当前 `/api/v1/account` 已改为 `ctp_snapshot.net_pnl` 结构，说明新增日历逻辑本身就未与本批接口变更对齐。
3. **`services/sim-trading/src/api/router.py` 夹带了不属于批次 A 冻结目标的 runtime hunk。**
   当前 diff 除账户主口径拆分外，还改动了默认 `ctp_md_front` / `ctp_td_front`、新增 `ctp_app_id` / `ctp_auth_code`、以及“连接成功通知去重”逻辑；这些不在 `TASK-0022-A` 的冻结目标或验收标准内，导致本批文件状态无法被视为“仅为 A 批实现所做的最小修改”。

### 4. 终审结论

1. **`TASK-0022-A` 正式终审未通过。**
2. **本批不得执行 lockback。**
3. **`TASK-0022-B` 继续保持锁定，不得提前启动。**
4. **请模拟交易 Agent 在不扩白名单的前提下清理范围外 hunk，并修复 `operations/page.tsx` 的 stale closure 后重新回交终审。**

## 十、TASK-0022-A 第二次正式终审

- 审核阶段：批次 A 第二次正式终审
- review-id：`REVIEW-TASK-0022-A`
- 当前有效 token_id：`tok-6610ebec-c5ab-4271-8e62-b5cb12f85666`
- 审核时间：2026-04-08 02:57 +0800
- 审核结论：**通过，可 lockback / 已 lockback**

### 1. 定向核验范围

1. 本次重审仍严格限于 `TASK-0022-A` 的 5 个白名单文件：
   - `services/sim-trading/src/api/router.py`
   - `services/sim-trading/src/gateway/simnow.py`
   - `services/sim-trading/sim-trading_web/app/operations/page.tsx`
   - `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`
   - `services/sim-trading/tests/test_console_runtime_api.py`
2. 仓库内其他 dirty files 不纳入本批结论；本次通过结论仅基于上述 5 文件与对应最小自校验结果。

### 2. 上次 3 个阻断的消除确认

1. **`services/sim-trading/sim-trading_web/app/operations/page.tsx` 的 stale closure 已清除。**
   `poll` 仍保持空依赖回调，但当前只读取 `availableContractsRef.current`、`contractInputValueRef.current` 与 `selectedContractRef.current` 这些当前态 ref，不再直接闭包捕获 `availableContracts`、`contractInput` 与 `orderParams.contract` 的旧值；自动补齐与盘口联动的回归风险已消除。
2. **`services/sim-trading/sim-trading_web/app/intelligence/page.tsx` 的接口不一致与大块范围外 hunk 已清除。**
   `handleRefresh()` 当前仅复核 health / positions / orders，不再读取 `/api/v1/account` 的 `acct?.net_pnl`；此前阻断中的 `dailyPnlMap`、历史清空与日历盈亏着色逻辑未出现在当前源码差异中，当前新增内容已收口为 L2 黄线 / 红线与说明集中展示。
3. **`services/sim-trading/src/api/router.py` 的非 A 批 runtime hunk 已清除。**
   当前差异只剩 `local_virtual + ctp_snapshot` 账户主次口径拆分及其辅助函数；未再看到 `ctp_app_id`、`ctp_auth_code`、默认 CTP front 变更或连接成功去重等非 A 批冻结目标改动。

### 3. 自校验复核

1. 5 个白名单文件 `get_errors = 0` 已独立复核。
2. 已独立复跑 `PYTHONPATH=. ../../.venv/bin/pytest tests/test_console_runtime_api.py tests/test_health.py tests/test_ctp_notify.py -q`，结果为 `6 passed, 4 warnings`。
3. 4 条 warnings 仅为 `src/main.py` 的 FastAPI `on_event` deprecation 提示，不在本批 5 文件白名单内，也不构成本批新增阻断。
4. 当前有效 token `tok-6610ebec-c5ab-4271-8e62-b5cb12f85666` 已独立执行 `lockctl validate`，任务、agent、action 与 5 个白名单文件全部匹配。

### 4. 锁回收口

1. 已于 `2026-04-08 02:57:17 +0800` 对当前有效 token 执行正式 lockback。
2. lockback 结果：`approved`。
3. lockback 后 token 状态：`locked`。
4. lockback 摘要：`TASK-0022-A 第二次正式终审通过，执行锁回`。

### 5. 终审结论

1. **`TASK-0022-A` 第二次正式终审通过，可 lockback / 已 lockback。**
2. **本批结论严格基于 5 个白名单文件，不受仓库其他 dirty files 干扰。**
3. **`TASK-0022-B` 继续保持 `pending_token`，当前不得自动启动。**

## 十一、2026-04-09 B 批次补录

1. `TASK-0022-B` 继续保持独立归属，不并入 `TASK-0017`；原因是其目标是“最小只读日志能力”，而不是部署前本地 clean pre-deploy。
2. `services/sim-trading/tests/test_log_view_api.py` 在本轮被明确允许作为新增测试文件，不再视为治理漂移。
3. `TASK-0022-B` 必须等待 `TASK-0014-A4` 与 `TASK-0017-A4` 锁回后再启动，因为共享 `src/main.py` / `src/api/router.py` / `app/intelligence/page.tsx`。

## 十二、2026-04-10 TASK-0022-B 终审补录

1. 批次名称：批次 B — 最小只读日志查看
2. 执行 Agent：模拟交易 Agent
3. token_id：`tok-2bd2b52d-1451-4104-bfb4-5b213c0a0009`
4. review-id：`REVIEW-TASK-0022-B`
5. 实际白名单严格限于：`services/sim-trading/src/main.py`、`src/api/router.py`、`sim-trading_web/app/intelligence/page.tsx`、`tests/test_log_view_api.py`
6. 最小自校验结果：50 passed / 1 skipped
7. lockback 时间：2026-04-10
8. lockback 结果：`approved`
9. 当前 Token 状态：`locked`
10. 终审结论：TASK-0022-B 通过；TASK-0022 全部批次均已闭环。