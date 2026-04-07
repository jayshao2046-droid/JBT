# TASK-0021 Review

## Review 信息

- 任务 ID：TASK-0021
- 审核角色：项目架构师
- 审核阶段：A批 contracts 终审同步
- 审核时间：2026-04-07
- 审核结论：通过（A 批 contracts 正式 10 文件已完成实施并通过终审，边界合规，当前可进入 lockback；B、C0、C、D、E0、E、F0、F、G 继续待 Jay.S 按 Manifest 一次性签发）

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