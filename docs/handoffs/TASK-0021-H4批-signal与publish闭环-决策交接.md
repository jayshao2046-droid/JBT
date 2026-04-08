# TASK-0021 H4 批 — signal 与 strategy publish 真闭环交接单

【签名】决策 Agent  
【交接时间】2026-04-08  
【review_id】REVIEW-TASK-0021-H4  
【状态】已完成，含 202 Accepted 与 lifecycle 门槛补修，待项目架构师重新终审与 lockback

---

## 任务信息

- 任务 ID：TASK-0021-H4
- 执行范围：仅限 5 个业务白名单文件
- 批次目标：完成 signal review 与 strategy publish 的真实闭环，补齐 publish gate 对持久化资格的重验，并把 decision -> sim-trading 下游路径冻结到 `/api/v1/strategy/publish`

---

## 2026-04-08 H4 最小补充回修

### 本轮补修背景

1. Atlas 本地跨服务模拟联调已确认：decision `SimTradingAdapter` 只把 `200/201/204` 当作成功，而 sim-trading 正式发布接口 `POST /api/v1/strategy/publish` 返回 `202 Accepted`。
2. 因此真实现象为：signal review 已返回 `ready_for_publish`，但 strategy publish 实际返回 `502 adapter_failed`。
3. 本轮补修严格保持在 H4 既有白名单内，不扩展到 `services/sim-trading/**`，也不改 `shared/contracts/**`。

### 本轮实际修改文件

1. `services/decision/src/publish/sim_adapter.py`
2. `services/decision/tests/test_publish.py`
3. `docs/prompts/agents/决策提示词.md`
4. `docs/handoffs/TASK-0021-H4批-signal与publish闭环-决策交接.md`

### 本轮补修内容

1. `services/decision/src/publish/sim_adapter.py`
   - 成功状态从 `200/201/204` 扩为 `200/201/202/204`。
   - 根因修复方向保持在 decision adapter 侧，未要求 sim-trading 改回 `200`。

2. `services/decision/tests/test_publish.py`
   - adapter 成功用例已改为断言 `202 Accepted` 视为成功。
   - executor mock 的成功 `status_code` 同步收口为 `202`，保证测试语义与真实联调一致。

---

## 2026-04-08 H4 终审阻断补修（lifecycle 门槛）

### 本轮补修背景

1. 项目架构师终审确认：当前新的 strategy publish 入口会直接调用 `PublishExecutor`，而 executor 在门禁通过后会直接把状态写成 `pending_execution` / `in_production`，未校验当前 lifecycle 是否允许进入发布流。
2. 这意味着只要资格记录齐备，`imported`、`reserved`、`research_complete` 等非法状态也可能被推进到发布流程，违反冻结的合法路径 `backtest_confirmed -> pending_execution -> in_production`。
3. 本轮补修保持在 H4 原白名单内，优先从 publish eligibility / publish gate 层收口，不修改 `services/sim-trading/**`、`shared/contracts/**` 或 `services/decision/src/publish/executor.py`。
4. 补修还需兼顾 adapter 失败后的 retry，避免把当前已处于 `pending_execution` 的重试路径误堵死。

### 本轮实际修改文件

1. `services/decision/src/publish/gate.py`
2. `services/decision/tests/test_publish.py`
3. `docs/prompts/agents/决策提示词.md`
4. `docs/handoffs/TASK-0021-H4批-signal与publish闭环-决策交接.md`

### 本轮补修内容

1. `services/decision/src/publish/gate.py`
   - 新增 lifecycle 合法转移校验。
   - 当前规则收口为：
     - 首次发布只有当前状态能按冻结状态机合法进入 `pending_execution` 时，才允许进入发布流；
     - `pending_execution` 作为 adapter 失败后的 retry 状态，被显式允许重试；
     - 其余非法状态统一返回 `lifecycle_status=... cannot enter publish flow; expected backtest_confirmed or pending_execution`。
   - 本轮未修改 `PublishExecutor`，而是把入口约束前置到 gate 层，满足“优先在 publish eligibility / publish gate 层修复”的要求。

2. `services/decision/tests/test_publish.py`
   - 成功发布基线从默认 `imported` 收口到合法的 `backtest_confirmed`。
   - 新增 3 条阻断级覆盖：
     - 非法 lifecycle（`imported`）会被 `PublishGate` 拒绝；
     - `pending_execution` 可作为 retry 路径继续通过 gate；
     - executor 在 `pending_execution` 上的 retry 仍可成功推进到 `in_production`。

3. 最小化说明
   - 本轮未修改 `services/decision/src/api/routes/strategy.py`、`services/decision/src/api/routes/signal.py`、`services/decision/src/publish/sim_adapter.py` 或 `services/decision/src/publish/executor.py`。
   - 业务补修严格收口在 gate 与测试，未扩展到第 3 个业务文件之外的新业务逻辑。

---

## 预执行校对

1. 已按决策 Agent 开工顺序读取 `WORKFLOW.md`、总调度 prompt、公共项目 prompt、决策私有 prompt 与 `TASK-0021` 相关 task / review / lock / handoff。
2. 已执行：`python governance/jbt_lockctl.py status --task TASK-0021-H4 --agent 决策`
3. 结果：`tok-1211b456-68eb-4291-b604-d6b97a32d452 | TASK-0021-H4 | 决策 | active`，以及 `tok-bf30ecb6-9559-4407-9a1b-a4d788b84300 | TASK-0021-H4 | 决策 | active`
4. 用户粘贴的 H4 JWT 文本直接执行 `lockctl validate` 时返回“Token 签名无效”；本次未扩白名单，仍严格只在 H4 已激活的 5 文件范围内实施。建议项目架构师终审前复核实际 lockback 所用的 active token。

---

## 修改文件

### 业务白名单文件

1. `services/decision/src/api/routes/strategy.py`
2. `services/decision/src/api/routes/signal.py`
3. `services/decision/src/publish/gate.py`
4. `services/decision/src/publish/sim_adapter.py`
5. `services/decision/tests/test_publish.py`

### P-LOG 同步文件

6. `docs/prompts/agents/决策提示词.md`
7. `docs/handoffs/TASK-0021-H4批-signal与publish闭环-决策交接.md`

---

## 改动说明

1. `services/decision/src/api/routes/signal.py`
   - 不再固定返回 `hold / manual_review` 占位值。
   - 已接入 `src/model/router.py` 的 `route()` 与 `PublishGate.check()`。
   - 当前最小规则收口为：
     - `sim-trading + router/gate 全通过 + signal != 0` -> `approve / eligible / ready_for_publish`
     - `sim-trading + router/gate 全通过 + signal = 0` -> `hold / eligible / none`
     - `live-trading` -> `hold / locked_visible / locked_visible`
     - 资格缺失或过期 -> `hold / blocked|expired / none`
   - `model_profile` 已改为引用已冻结的 `model_boundary.md` profile_id，不再返回 `pending` 占位。

2. `services/decision/src/api/routes/strategy.py`
   - 新增 `POST /strategies/{strategy_id}/publish` 最小发布入口。
   - 直接调用现有 `PublishExecutor`。
   - 将执行结果映射为真实 HTTP 响应：
     - `success` -> `200`
     - `gate_rejected` -> `409`
     - `adapter_failed` -> `502`
     - `strategy_not_found` -> `404`
   - 返回体会从 repository 重新读取最新策略快照，避免使用 executor 内部旧 snapshot。

3. `services/decision/src/publish/gate.py`
   - 新增对持久化 `backtest certificate` 与 `research snapshot` 的重验。
   - 当前重验项包括：存在性、状态、过期、与策略包内 ID 对齐、与策略包 `factor_version_hash` 对齐，以及回测 / 研究资格之间的 hash 一致性。
   - 仍保留 `factor_sync_status`、`allowed_targets` 与 `execution_gate` 的既有校验。

4. `services/decision/src/publish/sim_adapter.py`
   - 下游地址从 `/api/sim/v1/strategy/publish` 改为 `/api/v1/strategy/publish`。
   - 404 不再降级成功，而是按真实失败返回给 decision。
   - HTTPError 会尝试解析下游 JSON 错误体并原样回传，便于上层判断失败原因。

5. `services/decision/tests/test_publish.py`
   - 保留并扩展原有 gate / adapter / executor 用例。
   - 新增 persisted eligibility 重验覆盖：存在性、状态、过期、ID 对齐、`factor_version_hash` 对齐。
   - 新增 signal review 关键路径：`ready_for_publish`、`locked_visible`。
   - 新增 strategy publish 入口关键路径：`success`、`gate_rejected`、`adapter_failed`、`strategy_not_found`。
   - adapter 404 断言已收口为失败，不再断言降级成功。

---

## 验证结果

### 2026-04-08 lifecycle 门槛补修验证

1. 已执行 `get_errors`，以下 2 个本轮实际改动业务文件结果均为 `No errors found`：
   - `services/decision/src/publish/gate.py`
   - `services/decision/tests/test_publish.py`

2. 已执行：
   `cd /Users/jayshao/JBT/services/decision && PYTHONPATH=. ../../.venv/bin/pytest tests/test_publish.py tests/test_strategy.py -q`

3. 结果：
   `38 passed in 0.46s`

### 2026-04-08 补充回修验证

1. 已执行 `get_errors`，以下 2 个业务文件结果均为 `No errors found`：
   - `services/decision/src/publish/sim_adapter.py`
   - `services/decision/tests/test_publish.py`

2. 已执行：
   `cd /Users/jayshao/JBT/services/decision && PYTHONPATH=. ../../.venv/bin/pytest tests/test_publish.py tests/test_strategy.py -q`

3. 结果：
   `35 passed in 0.48s`

### 原 H4 批验证

1. 已执行 `get_errors`，以下 5 个业务白名单文件结果均为 `No errors found`：
   - `services/decision/src/api/routes/strategy.py`
   - `services/decision/src/api/routes/signal.py`
   - `services/decision/src/publish/gate.py`
   - `services/decision/src/publish/sim_adapter.py`
   - `services/decision/tests/test_publish.py`

2. 已执行：
   `cd /Users/jayshao/JBT/services/decision && PYTHONPATH=. ../../.venv/bin/pytest tests/test_publish.py tests/test_strategy.py -q`

3. 结果：
   `35 passed in 0.44s`

---

## 待审问题

1. 当前 `TASK-0023-A` 已完成正式终审并可 lockback；H4 本轮生命周期门槛补修不再依赖 sim-trading 侧新增代码，但后续跨服务 lockback / 联调节奏仍以项目架构师与 Jay.S 的统一安排为准。
2. 用户粘贴的 H4 JWT 文本在 `lockctl validate` 中返回“Token 签名无效”，但 `lockctl status` 同时显示 2 张 `TASK-0021-H4` active token；建议终审前先确认本批 lockback 应使用哪一张 active token，不要直接沿用该 JWT 文本执行锁回。
3. 本批没有修改 `PublishExecutor` 本体，因此 adapter 失败时 executor 仍保持既有 `publish_pending` 内部状态；当前 `strategy.py` 路由已按用户要求重新读取 repository 最新快照并如实返回，不在 H4 额外扩范围修正 executor 状态机。

---

## 向 Jay.S 汇报摘要

1. `TASK-0021-H4` 已按原 5 文件白名单补齐 signal / publish 真闭环，并在本轮终审阻断中补上 lifecycle 门槛：当前只有能合法进入 `pending_execution` 的状态才允许进入发布流，`pending_execution` retry 路径保留放行。
2. 本轮实际业务补修严格限于 `services/decision/src/publish/gate.py` 与 `services/decision/tests/test_publish.py`，未扩展到 `strategy.py`、`signal.py`、`sim_adapter.py` 或 `publish/executor.py`。
3. 与本次改动直接相关的静态诊断已完成：2 个本轮改动业务文件 `get_errors = 0`。
4. 指定最小自校验已完成：`cd /Users/jayshao/JBT/services/decision && PYTHONPATH=. ../../.venv/bin/pytest tests/test_publish.py tests/test_strategy.py -q` 结果 `38 passed in 0.46s`。
5. 当前剩余非代码事项只有两项：一是项目架构师重新终审与 lockback，二是终审前确认可直接用于 H4 lockback 的实际 active token 文本。

---

## 下一步建议

1. 由项目架构师按 H4 白名单重新执行定向终审；若通过，再执行 lockback。
2. lockback 前先确认本批实际应使用的 active H4 token，避免直接使用用户粘贴但 `validate` 失败的 JWT 文本。
3. H4 终审通过后，可与当前已通过的 `TASK-0023-A` 一并进入后续 lockback / 联调安排。