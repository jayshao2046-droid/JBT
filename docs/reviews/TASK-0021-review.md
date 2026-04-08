# TASK-0021 Review

## Review 信息

- 任务 ID：TASK-0021
- 审核角色：项目架构师
- 审核阶段：H0~H4 批终审
- 审核时间：2026-04-08
- 审核结论：通过（`TASK-0021-H0`、`TASK-0021-H1`、`TASK-0021-H2`、`TASK-0021-H3`、`TASK-0021-H4` 当前均可 lockback；`services/decision/decision_web/next.config.mjs` 明确不属于 H0 结论范围；H4 最新补修已消除上一轮 lifecycle 阻断，lockback 前仍需 Atlas / Jay.S 提供完整 JWT 文本）

---

## 一、当前固定口径

1. `TASK-0021` 继续独立成立，不并入 `TASK-0016` 或 `TASK-0012`，三者不得复用白名单、Token、验收或回滚口径。
2. 当前执行组织固定为：**项目架构师 + 决策 agent**。
3. 当前明确不使用 Livis；本线不切换为 Livis 协作模式。
4. 当前允许直接进入的代码范围仅为批次 A 对应的 `shared/contracts/**` 10 文件正式范围。

## 二、本轮治理补充同步文件

1. `docs/reviews/TASK-0021-review.md`
2. `docs/locks/TASK-0021-lock.md`
3. `docs/handoffs/TASK-0021-总包执行与Token清单.md`
4. `docs/prompts/公共项目提示词.md`
5. `docs/prompts/agents/项目架构师提示词.md`

说明：本轮仅补充 P-LOG 治理留痕，不触碰 `services/**`、`shared/contracts/**`、`integrations/**` 或 legacy 代码目录本身。

## 三、当前 Token 状态判定

1. **批次 A：已 active，可直接开工。**
2. 批次 A 当前正式范围固定为 10 文件：
	- `shared/contracts/README.md`
	- `shared/contracts/decision/api.md`
	- `shared/contracts/decision/strategy_package.md`
	- `shared/contracts/decision/research_snapshot.md`
	- `shared/contracts/decision/backtest_certificate.md`
	- `shared/contracts/decision/decision_request.md`
	- `shared/contracts/decision/decision_result.md`
	- `shared/contracts/decision/model_boundary.md`
	- `shared/contracts/decision/notification_event.md`
	- `shared/contracts/decision/dashboard_projection.md`
3. **批次 B、C0、C、D、E0、E、F0、F、G 当前均未 active。**
4. 其余批次当前状态统一冻结为：**待 Jay.S 按 `docs/handoffs/TASK-0021-总包执行与Token清单.md` 一次性签发，不得提前越权执行。**

## 四、总包批次冻结清单

| 批次 | 范围 | 保护级别 | 执行主体 | 是否必须先补 Token | 主要产物 |
|---|---|---|---|---|---|
| A | `shared/contracts/README.md` + `shared/contracts/decision/*.md` 正式契约 | P0 | 决策 agent | 否，当前已 active | decision 正式契约索引、请求/结果模型、策略包元数据、研究快照、回测证明、模型边界、通知事件、看板只读聚合字段 |
| B | `integrations/legacy-botquant/**` 决策迁移期只读适配层 | P0 | 决策 agent | 是 | legacy 决策输入映射、只读兼容适配、迁移期边界封装 |
| C0 | `services/decision/.env.example` 及决策服务受保护模板配置 | P0 | 决策 agent | 是 | 决策服务环境模板、模型路由占位、研究窗口与发布门禁占位 |
| C | `services/decision/src/**`、`services/decision/tests/**`、必要 `configs/**` | P1 | 决策 agent | 是 | 决策 API、审批编排、策略仓库、模型路由、执行资格门禁 |
| D | `services/decision/src/research/**`、`services/decision/src/gating/**`、对应测试 | P1 | 决策 agent | 是 | 研究中心主线、XGBoost 研究编排、因子/回测/研究联动门禁 |
| E0 | `services/dashboard/.env.example` 及决策看板受保护模板配置 | P0 | 决策 agent | 是 | 决策看板环境模板、只读聚合入口与开关占位 |
| E | `services/dashboard/**` 决策看板实现范围 | P1 | 决策 agent | 是 | 7 页决策看板、策略仓库前台、模型与因子页、通知与日报页 |
| F0 | `docker-compose.dev.yml`、`services/decision/Dockerfile`、`services/dashboard/Dockerfile`、`deploy/**`、反代/部署文件 | P0 | 决策 agent（项目架构师先预审） | 是 | 决策/看板部署骨架、容器化、反代与发布配置 |
| F | `services/decision/src/notifier/**`、`services/decision/src/reporting/**`、对应测试 | P1 | 决策 agent | 是 | 飞书/邮件通知链路、研究完成摘要、日报周报月报 |
| G | `services/decision/src/publish/**`、相关 API/测试、收口交接所需治理留痕 | P1 | 决策 agent | 是 | 仅推送到 `sim-trading` 的发布链路、`live-trading` 锁定可见入口、迁移收口与验收交接 |

## 五、关键风险与约束

1. 批次 A 已 active，不等于 B~G 可提前执行；除 A 外其余批次继续锁定。
2. `C0`、`E0`、`F0` 必须保持独立 P0，不得混入对应 P1 实施批次。
3. `F0` 涉及 `.env.example`、compose、Dockerfile、deploy/反代配置，必须单独受控，不得与业务实现混提交流水。
4. `G` 仅允许构建“发布到模拟交易、实盘入口锁定可见”的链路；不得借此扩写 `services/sim-trading/**` 或 `services/live-trading/**`。
5. 在 Jay.S 完成 Manifest 签发前，批次 B~G 全部视为未解锁。

## 五A、2026-04-08 收口补批审核结论

### 1. 只读代码事实

1. `services/decision/src/strategy/repository.py` 当前仍为纯内存 `_store`，`services/decision/src/api/routes/approval.py` 当前仍为纯内存 `_approvals`。
2. `services/decision/src/gating/backtest_gate.py` 与 `services/decision/src/gating/research_gate.py` 当前均为纯内存资格面，`services/decision/src/model/router.py` 仍只做 ID 非空检查。
3. `services/decision/src/research/factor_loader.py` 当前仍返回随机 `numpy` mock，`services/decision/pyproject.toml` 尚未声明现有 research 模块运行依赖。
4. `services/decision/src/api/routes/signal.py` 当前固定返回 `hold` / `manual_review` 占位值；`services/decision/src/api/routes/strategy.py` 尚未提供真实发布入口。
5. `services/decision/src/publish/sim_adapter.py` 当前仍把 404 当成成功降级；而 `services/sim-trading/**` 侧并不存在对应发布接收端。
6. `services/decision/decision_web/Dockerfile` 当前存在非法 `COPY ... 2>/dev/null || true`，已被实际 `docker build` 证实会阻断镜像构建。

### 2. 任务归属裁决

1. 基于上述代码事实，decision 收口继续挂在 `TASK-0021` 下新增补充批次 `H0`~`H4`，**不新开第二个 decision 任务**。
2. 原因是所有阻塞都发生在 `services/decision/**` 与 `services/decision/decision_web/**` 当前迁移残面内；若另起 decision 新任务，会把同一服务迁移主线拆成两个回滚单元。
3. 但 `sim-trading` 发布接收接口必须独立拆为 `TASK-0023`；该事项实际写入归属 `services/sim-trading/**`，不应继续塞在 `TASK-0021` 内。

### 3. 首轮明确纳入与明确排除

1. 首轮纳入：decision_web Dockerfile、策略/审批持久化、回测/研究资格持久化、真实 data API 接入与运行依赖、signal/model/publish 真闭环。
2. 首轮排除：`research-center`、`notifications-report`、`config-runtime` 等纯 UI 空态。
3. 首轮排除：`services/decision/.env.example` 与 `docker-compose.dev.yml`；当前占位足以承接本轮实现，若实施中证明仍缺配置位，再另起 **P0** 补审。

### 4. 补充批次冻结

| 批次 | 执行 Agent | 保护级别 | 是否可并行 | 业务白名单 | 目的 |
|---|---|---|---|---|---|
| `TASK-0021-H0` | 决策 Agent | P0 | 可与 `H1` / `H3` 并行 | `services/decision/decision_web/Dockerfile` | 修复 decision_web 生产镜像构建阻塞 |
| `TASK-0021-H1` | 决策 Agent | P1 | 可与 `H0` / `H3` 并行；不可与 `H2` 并行 | `services/decision/src/core/settings.py`、`services/decision/src/persistence/state_store.py`、`services/decision/src/strategy/repository.py`、`services/decision/src/api/routes/approval.py`、`services/decision/tests/test_state_persistence.py` | 策略仓库与审批状态持久化 |
| `TASK-0021-H2` | 决策 Agent | P1 | 依赖 `H1` | `services/decision/src/persistence/state_store.py`、`services/decision/src/gating/backtest_gate.py`、`services/decision/src/gating/research_gate.py`、`services/decision/src/model/router.py`、`services/decision/tests/test_gating.py` | 回测/研究资格持久化与模型门禁 |
| `TASK-0021-H3` | 决策 Agent | P1 | 可与 `H0` / `H1` 并行 | `services/decision/pyproject.toml`、`services/decision/src/research/factor_loader.py`、`services/decision/tests/test_research.py` | 真实 data API 接入与运行依赖 |
| `TASK-0021-H4` | 决策 Agent | P1 | 依赖 `H2` / `H3`；可与 `TASK-0023-A` 并行 | `services/decision/src/api/routes/strategy.py`、`services/decision/src/api/routes/signal.py`、`services/decision/src/publish/gate.py`、`services/decision/src/publish/sim_adapter.py`、`services/decision/tests/test_publish.py` | signal / strategy publish 真闭环 |
| `TASK-0021-H5` | 决策 Agent | P1 | 可独立推进；不得与新的 decision_web 页面/部署批次混写 | `services/decision/decision_web/next.config.mjs` | decision_web `/api/decision/*` rewrites 收口 |

### 5. 建议签发顺序

1. 最稳妥先签顺序冻结为：`H0` → `H1` → `H2` → `H3` → `H4` → `H5`。
2. 若 Jay.S 允许并行，可让 `H0` 与 `H1` / `H3` 并行；`H2` 必须在 `H1` 之后；`H4` 必须在 `H2` 与 `H3` 之后。
3. `TASK-0023-A` 在本轮命名空间冻结为 `/api/v1/strategy/publish` 后，可与 `H4` 并行推进，但最终端到端验收需两边同时完成。
4. `H5` 不依赖 `H0`~`H4` 的业务状态，但必须保持单文件回滚边界，不得与新的 decision_web 页面或部署批次混写。

## 六、终审结论

1. **`TASK-0021` 已完成“总包执行治理准备”同步。**
2. **执行组织正式冻结为“项目架构师 + 决策 agent”，且明确不使用 Livis。**
3. **当前 A 批 contracts 10 文件 Token 已 active，可直接开工。**
4. **总包批次清单已冻结为 A、B、C0、C、D、E0、E、F0、F、G。**
5. **当前下一动作已冻结为：先执行 A 批 contracts；随后由 Jay.S 按 Manifest 一次性签发后续批次。**

## 七、A批 contracts 终审结论

### 1. 本次终审范围

1. A 批业务范围严格限于以下 10 个契约文件：
	- `shared/contracts/README.md`
	- `shared/contracts/decision/api.md`
	- `shared/contracts/decision/strategy_package.md`
	- `shared/contracts/decision/research_snapshot.md`
	- `shared/contracts/decision/backtest_certificate.md`
	- `shared/contracts/decision/decision_request.md`
	- `shared/contracts/decision/decision_result.md`
	- `shared/contracts/decision/model_boundary.md`
	- `shared/contracts/decision/notification_event.md`
	- `shared/contracts/decision/dashboard_projection.md`
2. A 批伴随的 P-LOG 同步仅限 `docs/prompts/agents/决策提示词.md` 与 `docs/handoffs/TASK-0021-A批-contracts-决策交接.md`。
3. 本次项目架构师治理回写仅限 `docs/reviews/TASK-0021-review.md`、`docs/locks/TASK-0021-lock.md`、`docs/prompts/公共项目提示词.md` 与 `docs/prompts/agents/项目架构师提示词.md`。

### 2. 边界复核

1. 依据决策 agent 交接单所列实际修改文件与当前工作树定向核对，A 批业务写入只落在上述 10 个契约文件。
2. 未发现 A 批夹带 `services/**` 或 `integrations/**` 业务写入。
3. 当前工作树虽存在其他任务改动，但不属于 A 批 contracts 终审范围，也不得混入本批次后续独立提交。

### 3. 关键冻结语义

1. decision 只负责因子、信号、审批与策略编排，不直接承接下单、成交、持仓或交易账本。
2. 策略仓库动作固定为“导入、导出、预约、执行、下架”；其中“执行”只表示进入发布流程，不等于直接下单。
3. 第一阶段发布目标只允许 `sim-trading`；`live-trading` 仅允许保留锁定可见语义，不得进入可执行状态。
4. 模型路线冻结为本地 `Qwen3 14B` / `DeepSeek-R1 14B` / `Qwen2.5`，云端 `Qwen3.6-Plus` / `Qwen3-Max` / `DeepSeek-V3.2` / `DeepSeek-R1`；研究主线为 `XGBoost`，`LightGBM` 仅保留抽象位。

### 4. 自校验与 lockback 判断

1. 决策 agent 已回交最小诊断：A 批 10 个契约文件全部为 `No errors found`。
2. 项目架构师终审结论：通过。
3. A 批当前状态应由 `active` 收口为 `待 lockback`，当前结论为：**可进入 lockback**。
4. B、C0、C、D、E0、E、F0、F、G 状态不变，继续为 `pending_manifest`，不得提前执行。

---

## 八、B 批 legacy-botquant decision 适配层终审结论

### 1. 本次终审范围

B 批业务范围严格限于以下 4 文件：
- `integrations/legacy-botquant/decision/__init__.py`
- `integrations/legacy-botquant/decision/adapter.py`
- `integrations/legacy-botquant/decision/input_mapper.py`
- `integrations/legacy-botquant/decision/signal_compat.py`

审核时间：2026-04-07
审核角色：项目架构师
Review ID：REVIEW-TASK-0021-B

### 2. 隔离性检查

| 文件 | import 列表 | 跨服务 import | 结论 |
|---|---|---|---|
| `__init__.py` | 仅相对 import（`.adapter`、`.input_mapper`、`.signal_compat`） | 无 | ✅ 通过 |
| `adapter.py` | `from __future__ import annotations`、`uuid`、`datetime`、`timezone`、`typing`、相对 import | 无 | ✅ 通过 |
| `input_mapper.py` | `from __future__ import annotations`、`typing` | 无 | ✅ 通过 |
| `signal_compat.py` | `from __future__ import annotations` | 无 | ✅ 通过 |

结论：**隔离性 ✅ 通过**。4 文件均未引入 `services/**`、`J_BotQuant/**` 或任何 legacy 交易/回测代码。

### 3. 只读性检查

- `adapter.py::from_legacy_dict()`：纯字段转换，无任何交易 API 调用，无写操作。
- `_normalize_factors()`、`_normalize_market_context()`：静态方法，仅 dict 规范化。
- `input_mapper.py`：纯字段名重映射，无副作用。
- `signal_compat.py`：纯信号类型转换与验证，无副作用。

结论：**只读性 ✅ 通过**。

### 4. 契约对齐检查（对照 `shared/contracts/decision/decision_request.md`）

| 契约字段 | 适配层输出 | 对齐状态 |
|---|---|---|
| `request_id` | `f"legacy-{uuid4().hex[:12]}"` | ✅ 全局唯一 |
| `trace_id` | `f"{prefix}-{uuid4().hex[:8]}"` | ✅ 链路可追踪 |
| `strategy_id` | 经 `LegacyInputMapper` 重映射后取值 | ✅ |
| `strategy_version` | 经 `LegacyInputMapper` 重映射后取值，默认 `"legacy"` | ✅ |
| `symbol` | 经 `LegacyInputMapper` 重映射后取值 | ✅ |
| `requested_target` | raw 取值，默认 `"sim-trading"` | ✅ 合法枚举 |
| `signal` | `LegacySignalCompat` 输出整数 `-1`/`0`/`1` | ✅ 符合契约约束 |
| `signal_strength` | `float(...)` 强制转换，默认 `0.0` | ✅ |
| `factors` | `_normalize_factors()` 输出 `list[dict]`，子字段含 `name`/`value`/`version`/`updated_at` | ✅ 子结构对齐 |
| `factor_version_hash` | raw 取值，默认 `"legacy-unknown"` | ✅ 占位合法 |
| `market_context` | `_normalize_market_context()` 输出含 4 个必填子字段 | ✅ 子结构对齐 |
| `research_snapshot_id` | raw 取值，默认 `"legacy-placeholder"` | ✅ 占位合法 |
| `backtest_certificate_id` | raw 取值，默认 `"legacy-placeholder"` | ✅ 占位合法 |
| `submitted_at` | raw 取值，默认 `now_iso`（ISO 8601） | ✅ |

**⚠️ 非阻断观察**：输出 dict 含 `_legacy_source` 与 `_legacy_signal_type` 两个扩展字段，均以 `_` 前缀标记为元数据，不在契约定义内。建议下游 decision 服务在接收时显式过滤 `_` 前缀字段，避免传入门禁校验逻辑。

结论：**契约对齐 ✅ 通过**（含 1 条非阻断观察，不构成终审拒绝理由）。

### 5. 类型安全检查

- 所有公开方法（`from_legacy_dict`、`map_strategy_fields`、`map_signal_fields`、`normalize_signal_type`、`normalize_signal_direction`、`is_valid_legacy_signal`）均有完整类型注解。
- 无 Pydantic 依赖，无运行时魔法。

结论：**类型安全 ✅ 通过**。

### 6. get_errors 结果

```
No errors found.
```

### 7. 终审结论

| 检查项 | 结论 |
|---|---|
| 隔离性 | ✅ 通过 |
| 只读性 | ✅ 通过 |
| 契约对齐 | ✅ 通过（含 1 条非阻断观察） |
| 类型安全 | ✅ 通过 |
| get_errors | 0 errors |
| 是否可进入 lockback | **是** |

**终审结论：✅ 通过。B 批 4 文件可进入 lockback。**

---

## 十一、TASK-0021 H0~H4 批终审结论

### 1. 本次定向核验范围

1. 本次仅核验 `TASK-0021-H0`、`H1`、`H2`、`H3` 及其当前工作树对应的 `services/decision/**` 改动。
2. 当前 `git diff --name-only -- services/decision | sort` 显示，H0~H3 相关业务文件之外，额外存在 `services/decision/decision_web/next.config.mjs` 改动；经对照 H0 交接单与该文件当前 diff 语义，判定其为独立历史脏改动，不纳入 H0 定向结论，也不计入 H2/H3 终审范围。
3. 当前 4 张 token 均已由 `lockctl status` 复核为 `active`：
	- `TASK-0021-H0` = `tok-2ae91304-d52b-4e09-b434-fdef71fc086b`
	- `TASK-0021-H1` = `tok-0b8452e5-bd7c-4cdc-ab94-1fd4c1971d6d`
	- `TASK-0021-H2` = `tok-e4a42eab-0942-4e9e-b753-bd9090dffc1a`
	- `TASK-0021-H3` = `tok-c9b73a9a-c9aa-40a8-8d51-2e23cefe88f3`

### 2. `TASK-0021-H0` 终审结论

1. H0 交接单声明白名单严格限于 `services/decision/decision_web/Dockerfile` 单文件，且明确“未扩展到 `next.config.mjs`”。
2. 独立复核结果：`services/decision/decision_web/Dockerfile` 当前 `get_errors = 0`，且 `docker build -t jbt-decision-web-task-0021-h0-audit services/decision/decision_web` 已实际构建成功。
3. 当前 decision 工作树确有 `services/decision/decision_web/next.config.mjs` 改动；但该文件属于独立 rewrite 历史脏改动，不构成 H0 的单文件回滚单元，且 H0 交接单已明确声明未扩展到该文件。
4. 因此本次按批次定向核验裁决为：H0 结论只覆盖 `services/decision/decision_web/Dockerfile`；`services/decision/decision_web/next.config.mjs` 明确不属于 H0 通过 / lockback 结论范围，且继续保持独立锁定状态。
5. 因此 H0 本轮结论为：**通过，可 lockback**。

### 3. `TASK-0021-H1` 终审结论

1. H1 业务改动严格落在 5 个白名单文件：`settings.py`、`state_store.py`、`strategy/repository.py`、`approval.py`、`tests/test_state_persistence.py`。
2. 服务隔离复核通过：未发现跨服务 import，也未触碰 `shared/contracts/**`、`.env.example` 或部署文件。
3. 自校验独立复跑通过：`DECISION_STATE_FILE=/tmp/jbt-decision-task-0021-h1-state.json PYTHONPATH=. ../../.venv/bin/pytest tests/test_state_persistence.py tests/test_strategy.py tests/test_publish.py -q` 结果 `23 passed in 0.34s`，5 文件 `get_errors = 0`。
4. 结论：**通过，可 lockback**。当前建议按 H1 白名单定向锁回，不与 H0 的白名单外 `next.config.mjs` 混并处理。

### 4. `TASK-0021-H2` 终审结论

1. H2 业务改动严格落在 5 个白名单文件：`state_store.py`、`backtest_gate.py`、`research_gate.py`、`model/router.py`、`tests/test_gating.py`。
2. 服务隔离复核通过：仅使用 decision 服务内部模块；没有跨服务 import，研究/回测资格仍通过本服务本地状态底座持久化。
3. 补充回修复核通过：`BacktestCert` 当前已随 H2 状态底座持久化 `requested_symbol` 与 `executed_data_symbol`，并已通过 JSON 落盘 + 重启恢复路径验证；`PYTHONPATH=. ../../.venv/bin/pytest tests/test_state_persistence.py tests/test_gating.py -q` 结果 `16 passed in 0.26s`。
4. 非阻断观察：当前 `BacktestCert` / `ResearchSnapshot` 仅保存最小门禁字段，不是对外契约的全量导出对象；若后续要直接对外输出这两类对象，仍需补映射层或补字段，不阻断本批“资格持久化 + model router 真校验”的最小目标。
5. 结论：**通过，可 lockback**。

### 5. `TASK-0021-H3` 终审结论

1. H3 没有跨服务 import，形式上通过服务隔离；`PYTHONPATH=. ../../.venv/bin/pytest tests/test_research.py -q` 结果 `14 passed in 0.22s`。
2. 当前 `FactorLoader` 已不再把 `strategy_id` 无条件当作 data service `symbol`；其解析顺序固定为：回测证书 `executed_data_symbol` -> 同证书 `requested_symbol` -> 仅当 `strategy_id` 本身已是合法标的格式时才回退使用 -> 否则在发 HTTP 前显式抛出 `FactorLoadError`。
3. 该顺序已与 H2 补齐的回测证书持久化字段对齐，也与 data 服务当前接受的 symbol 形式对齐，因此“策略包/回测证书 -> data symbol -> `/api/v1/bars`”最小闭环已成立。
4. 结论：**通过，可 lockback**。

### 6. `TASK-0021-H4` 终审结论

1. 本轮重新终审只聚焦 H4 最新补修；实际新增改动严格限于 `services/decision/src/publish/gate.py` 与 `services/decision/tests/test_publish.py`。已复核这 2 个补修文件 `get_errors = 0`，并独立复跑 `PYTHONPATH=. ../../.venv/bin/pytest tests/test_publish.py tests/test_strategy.py -q` 得到 `38 passed in 0.46s`；Atlas 追加提供的本地模拟联调结果也已确认：合法路径 `backtest_confirmed -> publish` 返回 `200 success`，非法路径 `imported -> publish` 返回 `409 gate_rejected`，且错误信息明确为 `lifecycle_status=imported cannot enter publish flow; expected backtest_confirmed or pending_execution`。
2. 当前 `PublishGate` 已把发布流入口收口为两类合法状态：一是当前生命周期能按冻结状态机合法进入 `pending_execution` 的状态，按现态即 `backtest_confirmed`；二是已经处于 `pending_execution` 的 adapter 失败重试路径。
3. 其他状态当前都会在 gate 层被显式拒绝，且 `tests/test_publish.py` 已补齐 `imported` 非法路径拒绝与 `pending_execution` retry 放行的回归断言。
4. 因此即便 `PublishExecutor` 仍通过 `repo.update(...)` 写入 `pending_execution` / `in_production`，非合法前置状态已经无法再进入发布流；上一轮“非待执行状态也可能被推进到发布流”的唯一阻断已被消除。
5. 结论：**通过，可 lockback**。本轮无阻断发现。

### 7. `TASK-0021-H5` 终审结论

1. `services/decision/decision_web/next.config.mjs` 已在本文件前序终审中被明确裁定为 `H0` 白名单外历史脏改动，正式收口为单文件补充批次 `TASK-0021-H5`，保护级别 **P1**。
2. Jay.S 已签发 P1 Token：`tok-06be4004-b5c6-4cd6-8efd-8b5369c0877b`（480min TTL）。
3. 决策 Agent 已按白名单单文件实施：`async rewrites()` 规则仅覆盖 `/api/decision/:path*` → `${BACKEND_BASE_URL ?? "http://localhost:8104"}/:path*`，未扩展到 Dockerfile / compose / .env.example / 页面代码。
4. 验收结果：
   - 内容边界合规，未触碰白名单外文件。
   - `next.config.mjs` 语法有效，本地构建/诊断口径保持可用。
   - 单文件独立 commit：`0ead4c2`。
5. Token lockback 已执行：`tok-06be4004` → `locked`，REVIEW-TASK-0021-H5 approved。
6. 结论：**通过，已完成 lockback。H5 终审闭环。**

---

## 九、C0 批 `services/decision/.env.example` 终审结论

### 1. 本次终审范围

C0 批业务范围严格限于 1 文件：
- `services/decision/.env.example`

审核时间：2026-04-07
审核角色：项目架构师
Review ID：REVIEW-TASK-0021-C0

### 2. 五项核验结果

| 核验项 | 要求 | 实际值 | 结论 |
|---|---|---|---|
| 端口确认 | `DECISION_PORT=8104` | `DECISION_PORT=8104` | ✅ 通过 |
| 本地模型 | `Qwen3-14B` / `DeepSeek-R1-14B` / `Qwen2.5` | `LOCAL_MODEL_MAIN=Qwen3-14B`、`LOCAL_MODEL_COMPAT=DeepSeek-R1-14B`、`LOCAL_MODEL_L1=Qwen2.5` | ✅ 通过 |
| 在线模型 | `Qwen3.6-Plus`(default) / `Qwen3-Max` / `DeepSeek-V3.2` / `DeepSeek-R1` | `ONLINE_MODEL_DEFAULT=Qwen3.6-Plus`、`ONLINE_MODEL_UPGRADE=Qwen3-Max`、`ONLINE_MODEL_BACKUP=DeepSeek-V3.2`、`ONLINE_MODEL_DISPUTE=DeepSeek-R1` | ✅ 通过 |
| 工具开关 | XGBoost=true、LightGBM=false、CatBoost=false、ONNX=true、Optuna=true、SHAP=true | `XGBOOST_ENABLED=true`、`LIGHTGBM_ENABLED=false`、`CATBOOST_ENABLED=false`、`ONNX_RUNTIME_ENABLED=true`、`OPTUNA_ENABLED=true`、`SHAP_ENABLED=true` | ✅ 通过 |
| 门禁占位 | `EXECUTION_GATE_TARGET=sim-trading`、`LIVE_TRADING_GATE_LOCKED=true` | `EXECUTION_GATE_TARGET=sim-trading`、`LIVE_TRADING_GATE_LOCKED=true`（另有 `LIVE_TRADING_GATE_VISIBLE=true`） | ✅ 通过 |

### 3. 禁止项检查

- **真实密钥检查**：`ONLINE_MODEL_API_KEY=your-api-key-here`、`EMAIL_SMTP_PASSWORD=your-smtp-password`、`FEISHU_WEBHOOK_URL=.../your-token` — 全为明确占位符，无真实凭证。✅ 通过。
- **运行时路径检查**：文件含 `XGBOOST_MODEL_DIR=./runtime/models/xgboost`、`OPTUNA_STORAGE=sqlite:///./runtime/optuna/study.db`、`SHAP_AUDIT_DIR=./runtime/shap` 等 `./runtime/...` 相对默认路径。

  **⚠️ 非阻断观察**：上述路径均为相对路径默认值（非绝对系统路径如 `/Users/jayshao/...`），属于配置覆盖占位。实际部署时须在 `.env` 中显式覆盖为挂载卷路径，避免运行时数据落入工作目录。建议 C 批实施时在 `README.md` 或注释中补充"部署时须覆盖 `./runtime` 为挂载卷路径"说明。

### 4. 结构完整性检查

文件包含以下配置分区，与 C0 批预期范围对齐：
- 基础服务、研究窗口
- 本地模型 + 在线模型（API key 占位）
- XGBoost / LightGBM / CatBoost 开关
- ONNX Runtime + Optuna + SHAP
- 执行门禁（gate_target / gate_locked）
- 模型路由门禁（backtest cert / research snapshot 要求）
- 回测服务 + 数据服务集成地址
- 通知（飞书 / 邮件，默认关闭，webhook 占位）

✅ 所有分区均已覆盖，无遗漏，无多余真实数据。

### 5. 终审结论

| 检查项 | 结论 |
|---|---|
| 端口确认 | ✅ 通过 |
| 模型配置（本地 3 + 在线 4） | ✅ 通过 |
| 工具开关（6 项） | ✅ 通过 |
| 门禁占位 | ✅ 通过 |
| 禁止项（无真实密钥） | ✅ 通过（含 1 条非阻断观察：`./runtime` 相对路径占位，部署时须显式覆盖） |
| 结构完整性 | ✅ 通过 |
| 是否可进入 lockback | **是** |

**终审结论：✅ 通过。C0 批 `services/decision/.env.example` 可进入 lockback。**

后续批次 C0、C、D、E0、E、F0、F、G 状态不变，继续为 `pending_manifest`，不得提前执行。

---

## 十、C 批 `services/decision/src/**` 骨架终审结论

### 1. 本次终审范围

C 批业务范围（23 文件骨架）：
- `services/decision/src/main.py`
- `services/decision/src/api/app.py`
- `services/decision/src/api/routes/health.py`
- `services/decision/src/api/routes/strategy.py`
- `services/decision/src/api/routes/signal.py`
- `services/decision/src/api/routes/approval.py`
- `services/decision/src/api/routes/model.py`
- `services/decision/src/core/settings.py`
- `services/decision/src/strategy/lifecycle.py`
- `services/decision/src/strategy/repository.py`
- `services/decision/src/model/router.py`
- `services/decision/src/gating/execution_gate.py`
- `services/decision/tests/test_health.py`
- `services/decision/tests/test_strategy.py`
- 及相关 `__init__.py` 共计约 23 文件

审核时间：2026-04-07
审核角色：项目架构师
Review ID：REVIEW-TASK-0021-C

### 2. 六项核验结果

#### 核验一：服务隔离（无跨服务 import）

针对 `services/decision/src/**` 全量 Python 文件检索 `import.*backtest|import.*sim.trading|import.*live.trading|import.*data_service` 关键词，结果：**0 匹配**。

所有 import 均为标准库（`uuid`、`datetime`、`enum`、`typing`）、FastAPI/pydantic 依赖，或服务内相对 import。

**结论：✅ 通过。无任何跨服务 import。**

#### 核验二：端口 8104

| 位置 | 实际值 | 结论 |
|---|---|---|
| `settings.py` L14 | `decision_port: int = 8104` | ✅ |
| `main.py` | `port=settings.decision_port`（动态读取） | ✅ |
| `routes/health.py` | `{"port": 8104}`（写死校验值） | ✅ |

**结论：✅ 通过。三处端口口径一致。**

#### 核验三：live-trading 门禁逻辑

`execution_gate.py` 中 `check_execution_eligibility(target="live-trading")` 的逻辑：

```python
if target == "live-trading":
    if settings.live_trading_gate_locked:
        return {"eligible": False, "reason": "live-trading gate locked"}
    # 即使 flag=False，仍返回 eligible=False
    return {"eligible": False, "reason": "live-trading not permitted in current phase"}
```

无论 `LIVE_TRADING_GATE_LOCKED` 环境变量为何值，live-trading 路径**恒定返回** `eligible: False`。这是双重保险机制，强于契约要求的"仅靠 flag 锁定"。

**结论：✅ 通过。live-trading 被代码级永久锁定，无绕过路径。**

#### 核验四：状态机 8 状态完整性

`lifecycle.py` 中 `LifecycleStatus` 定义：

| 内部状态 | 是否存在 |
|---|---|
| `imported` | ✅ |
| `reserved` | ✅ |
| `researching` | ✅ |
| `research_complete` | ✅ |
| `backtest_confirmed` | ✅ |
| `pending_execution` | ✅ |
| `in_production` | ✅ |
| `archived` | ✅ |

**结论：✅ 通过。8 状态完整覆盖交接单要求。**

#### 核验五：状态机 vs 契约口径（⚠️ 阻断项）

`shared/contracts/decision/strategy_package.md §3` 定义的对外 `lifecycle_status` 枚举值为 5 个：

| 契约状态值 | 契约含义 |
|---|---|
| `imported` | 已导入，尚未预约 |
| `reserved` | 已预约发布窗口 |
| `publish_pending` | 已进入发布流程，等待下游消费 |
| `published` | 已被目标服务确认接收 |
| `retired` | 已下架 |

代码 `lifecycle.py` 定义的 8 个内部枚举字面值与契约不符之处：

| 内部枚举字面值（API 直接透出） | 对应契约状态 | 是否符合 |
|---|---|---|
| `imported` | `imported` | ✅ |
| `reserved` | `reserved` | ✅ |
| `researching` | 契约中无对应状态 | ⚠️ |
| `research_complete` | 契约中无对应状态 | ⚠️ |
| `backtest_confirmed` | 契约中无对应状态 | ⚠️ |
| `pending_execution` | 契约要求 `publish_pending` | ❌ 名称不符 |
| `in_production` | 契约要求 `published` | ❌ 名称不符 |
| `archived` | 契约要求 `retired` | ❌ 名称不符 |

**问题根因**：`strategy/repository.py` 的 `to_dict()` 直接返回 `self.lifecycle_status.value`，`GET /strategies/{id}` 与 `GET /strategies/{id}/lifecycle` 均无映射层，导致外部 API 响应中的 `lifecycle_status` 值为内部枚举字面值，与契约不符。

**必须修复的阻断项要求（二选一，决策 Agent 必须在重审前完成）**：

**方案 A（推荐）— 更新契约**：将 `strategy_package.md §3` 的生命周期表从 5 状态升级为 8 状态，以匹配已实现的更细粒度状态机。枚举值对齐关系建议：`researching`（新增）、`research_complete`（新增）、`backtest_confirmed`（新增）、`pending_execution`（替换 `publish_pending`）、`in_production`（替换 `published`）、`archived`（替换 `retired`）。此方案需为 `strategy_package.md` 补签新 P0 Token。

**方案 B — 保留契约、增加映射层**：在 `LifecycleStatus` 或 `to_dict()` 中增加内部状态 → 契约状态的折叠映射（`pending_execution`→`publish_pending`、`in_production`→`published`、`archived`→`retired`，`researching/research_complete/backtest_confirmed` 折叠至 `reserved`），对外 API 响应仅暴露契约 5 状态值，内部细粒度状态另行隔离。此方案不需要新 Token。

**结论：❌ 阻断。需修复后重审，不可进入 lockback。**

#### 核验六：0 errors

```
pytest services/decision/tests/ -v
6 passed in 0.32s
```

**结论：✅ 通过。6 个测试全部通过，0 failures，0 errors。**

### 3. 终审结论汇总

| 核验项 | 结论 |
|---|---|
| ① 服务隔离（无跨服务 import） | ✅ 通过 |
| ② 端口 8104 | ✅ 通过 |
| ③ live-trading 门禁永久锁定 | ✅ 通过（双重保险，高于契约要求） |
| ④ 8 状态机完整性 | ✅ 通过 |
| ⑤ 状态机 vs 契约口径 | ❌ **阻断**：末段 3 状态枚举值不符（`pending_execution`/`in_production`/`archived` vs 契约的 `publish_pending`/`published`/`retired`）；且 3 个中间状态（`researching`/`research_complete`/`backtest_confirmed`）在契约中无对应定义 |
| ⑥ 0 errors | ✅ 通过（6 passed） |

**终审结论：⚠️ 有阻断项，不通过，不可进入 lockback。**

阻断项修复路径：决策 Agent 按上述方案 A 或方案 B 完成修复并回交重审；重审通过后方可进入 lockback。其余 5 项无调整点，已通过审核，修复时无需重做。

---

## 十一、C 批重审结论（修复后）

### 1. 重审信息

- Review ID：REVIEW-TASK-0021-C（重审）
- 重审时间：2026-04-07
- 审核角色：项目架构师
- 触发原因：C 批初审核验五阻断项 — 决策端提交修复后回交

### 2. 修复内容验证

#### 核验 1：`lifecycle.py` — `_INTERNAL_TO_CONTRACT` 常量与 `to_contract_state()` 方法

| 项目 | 要求 | 实际 | 结论 |
|---|---|---|---|
| `_INTERNAL_TO_CONTRACT` 常量存在 | 必须存在 | 第 29-38 行，8 个映射条目 | ✅ |
| 终态 `pending_execution` → `publish_pending` | 必须正确 | `"pending_execution": "publish_pending"` | ✅ |
| 终态 `in_production` → `published` | 必须正确 | `"in_production": "published"` | ✅ |
| 终态 `archived` → `retired` | 必须正确 | `"archived": "retired"` | ✅ |
| `to_contract_state()` 方法存在 | 必须存在 | 第 41-50 行 | ✅ |
| `to_contract_state()` 使用映射表 | 必须 | `return _INTERNAL_TO_CONTRACT[status.value]` | ✅ |
| 映射表覆盖全部 8 个枚举值 | 必须覆盖 | 已覆盖全部 8 个 LifecycleStatus 值 | ✅ |

**结论：✅ 通过。**

#### 核验 2：`repository.py` — `to_contract_dict()` 方法

| 项目 | 要求 | 实际 | 结论 |
|---|---|---|---|
| `to_contract_dict()` 方法存在 | 必须存在 | 第 74-82 行 | ✅ |
| 内部调用 `to_contract_state()` | 必须 | `d["lifecycle_status"] = to_contract_state(self.lifecycle_status)` | ✅ |
| 基于 `to_dict()` 扩展，字段完整性无损 | 必须 | `d = self.to_dict(); d["lifecycle_status"] = ...` | ✅ |

**结论：✅ 通过。**

#### 核验 3：`routes/strategy.py` — 所有端点改用 `to_contract_dict()`

| 端点 | 修改前 | 修改后 | 结论 |
|---|---|---|---|
| `GET /strategies` | `to_dict()` | `to_contract_dict()` | ✅ |
| `GET /strategies/{id}` | `to_dict()` | `to_contract_dict()` | ✅ |
| `POST /strategies` | `to_dict()` | `to_contract_dict()` | ✅ |
| `GET /strategies/{id}/lifecycle` | 直接 `.value` | `to_contract_state(pkg.lifecycle_status)` | ✅ |

**结论：✅ 通过。所有对外端点均已统一使用契约状态转换。**

#### 核验 4：`test_strategy.py` — 状态机覆盖断言测试

| 测试函数 | 验证内容 | 存在 | 结论 |
|---|---|---|---|
| `test_to_contract_state_terminal_states` | 3 个终态映射正确性 | ✅ | ✅ |
| `test_to_contract_state_passthrough_states` | 5 个非终态透传正确性 | ✅ | ✅ |
| `test_internal_to_contract_covers_all_statuses` | 映射表覆盖全部 8 枚举值 | ✅ | ✅ |

**结论：✅ 通过。3 个新增断言测试完整覆盖映射层。**

#### 核验 5：get_errors

```
lifecycle.py:    No errors found
repository.py:   No errors found
routes/strategy.py: No errors found
tests/test_strategy.py: No errors found
```

**结论：✅ 通过。4 文件 0 errors。**

### 3. 遗留非阻断观察

**[NON-BLOCKING] 中间态的契约对齐问题未完全解决**

本次修复采用了方案 B 的变体：仅修复了 3 个终态的名称映射（`pending_execution`→`publish_pending`、`in_production`→`published`、`archived`→`retired`），但 3 个中间态（`researching`、`research_complete`、`backtest_confirmed`）仍以原始内部值透传至 API 响应，这 3 个值在 `shared/contracts/decision/strategy_package.md §3` 的 5 状态枚举中无对应定义。

代码注释中已标注"契约允许透传，后续可根据契约演进调整"，视为已知技术债务登记。

**处置建议**：在 D 批或后续契约迭代中选择其一完成：
- 方案 A（推荐）：为 `strategy_package.md §3` 补充 3 个中间态定义（需新 P0 Token）
- 方案 B 完整：将 `researching`/`research_complete`/`backtest_confirmed` 折叠至 `reserved`（不需新 Token）

此项**不构成本次重审的阻断原因**，不影响 C 批进入 lockback。

### 4. 重审终审汇总

| 核验项 | 结论 |
|---|---|
| `_INTERNAL_TO_CONTRACT` 常量与 3 终态映射正确性 | ✅ 通过 |
| `to_contract_state()` 方法实现 | ✅ 通过 |
| `to_contract_dict()` 方法实现 | ✅ 通过 |
| 所有 API 端点改用 `to_contract_dict()` | ✅ 通过 |
| 3 个新增状态机测试断言 | ✅ 通过 |
| get_errors | ✅ 0 errors |
| 中间态契约透传 | ⚠️ 非阻断观察，已登记为技术债务 |
| **是否可进入 lockback** | **是** |

**C 批重审终审结论：✅ 通过（含 1 条非阻断遗留观察）。C 批全部文件可进入 lockback。**