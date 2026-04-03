# TASK-0003 Review

## Review 信息

- 任务 ID：TASK-0003
- 审核角色：项目架构师
- 审核阶段：Phase1 正式建档 + 批次 A 终审 + P0 契约迁移终审 + 批次 B 终审 + 首轮真实回测 Phase2 预审治理补充
- 审核时间：2026-04-03
- 审核结论：通过（建档合规；backtest 四份正式契约与 drafts 一致；批次 B 五个白名单文件核验通过；D-BT-01~05 未违反；未提前进入看板、Docker、远端交付；当前已达到“只差策略输入即可执行一次正式回测”的检查点；两枚 Token 已完成 lockback，当前状态均为 `locked`；首轮真实回测区间与首次总金额已完成冻结）

---

## Jay.S 已确认设计决策核验

| 决策编号 | 内容摘要 | 核验结论 |
|---|---|---|
| D-BT-01 | 第一阶段只支持期货回测；TqSim() + TqBacktest；股票接口暂不启用 | ✅ 已登记到建档文件与白名单约束 |
| D-BT-02 | .env.example 以 J_BotQuant 为基础整合；TUSHARE_TOKEN 替换为占位符；本次建档授权直接更新 | ✅ 已执行 —— services/backtest/.env.example 已更新 |
| D-BT-03 | 风控参数必须从 YAML 策略文件读取，禁止硬编码；配置层最高优先级 | ✅ 已登记到批次 A/B 强制约束 |
| D-BT-04 | 策略推送接口（backtest→decision）需登记 shared/contracts；本轮只登记需求不写入 | ✅ 已在 Phase1 建档文件中登记，批次 B 后另建契约 |
| D-BT-05 | 后端+看板同一独立设备、同一 docker-compose；具体主机 Jay.S 后续指定 | ✅ 已登记到批次 C 约束与 Token 申请清单 |

## 核验内容

### 边界核验

- 回测服务旧口径（离线研究）已明确修正为"在线 TqSdk 路径"，README 将随批次 A Token 一并修正。✅
- 项目架构师仅负责阶段一契约草稿与派发，不进入 `services/backtest/` 代码写入。✅
- 回测 Agent 负责阶段二全部 Python 后端与部署文件，分批次派发。✅
- `docker-compose.dev.yml` 与 `services/backtest/.env.example` 均为 P0 保护文件，需单独走 P0 Token，不随批次 C 代码并入。✅
### 文件白名单核验

- `docs/tasks/TASK-0003-*.md`：P-LOG 区，项目架构师可写。✅
- `docs/handoffs/TASK-0003-*.md`：P-LOG 区，项目架构师可写。✅
- `shared/contracts/drafts/backtest/`：草稿区，当前批次可写，无需 Token。✅
- `shared/contracts/backtest/`：P0 区，Jay.S 已为四份正式契约签发文件级 Token；本轮仅允许写入 `backtest_job.md`、`backtest_result.md`、`performance_metrics.md`、`api.md`。✅
- `services/backtest/src/`：P1 区，待批次分批 Token，回测 Agent 执行。⏳
- `docker-compose.dev.yml`：P0 区，批次 C 前单独 Token。⏳
- `services/backtest/.env.example`：P0 区，**D-BT-02 授权，已在 Phase1 建档中由架构师更新。** ✅

### 阶段一草稿自校验结论

- `backtest_job.md`：字段覆盖 TqBacktest 必要配置；已排除 TqSdk 内部实现字段、策略层参数、真实账户字段。✅
- `backtest_result.md`：字段仅保留外部可见结果指标与文件路径；不含 TqSdk 内部状态与归档实现字段。✅
- `performance_metrics.md`：字段与 legacy `PerformanceMetrics` 模型一一对应；已排除进阶分析字段（walk-forward、overfitting）；风险利率为计算配置项，不作为结果字段。✅
- `api.md`：7 个最小 MVP 端点（health + 任务 CRUD + 结果查询 + 指标 + 权益曲线）；已排除参数扫描、walk-forward、批量管理、WebSocket、管理员接口。✅
- 四份草稿均未引入 legacy 业务逻辑，未绑定 TqSdk 内部实现细节。✅

### 强制约束核验

- TqSdk 在线回测路径已在 TASK-0003 任务文件中明确列为强制约束。✅
- 批次拆分满足"单批次最多 5 文件"治理规则（批次 A：5，批次 B：5，批次 C：5 + 需单独 Token 的 2 个 P0 受保护文件）。✅
- 各批次对应独立提交，支持独立回滚。✅

### 风险矩阵

| 风险 | 等级 | 缓解措施 |
|---|---|---|
| 回测 Agent 复用 legacy 本地数据路径 | P0 | 强制约束已明确，草稿区不含 legacy 逻辑，代码审查时检查 |
| Q1-Q5 未确认就开始批次 A 写入 | P1 | 批次 A P1 Token 签发前，项目架构师提醒 Jay.S 确认 Q1 |
| `docker-compose.dev.yml` 被顺带修改 | P0 | 锁记录与 Token 分离申请已明确 |
| V0 看板目录名空格导致部署路径错误 | P2 | Q3 确认后统一改名，在批次 C 前执行 |
| TqAuth 凭证明文写入代码 | P0 | 凭证必须只来自环境变量，代码审查时检查 |

## P0 Token 申请清单（阶段一）

- `shared/contracts/backtest/backtest_job.md`
- `shared/contracts/backtest/backtest_result.md`
- `shared/contracts/backtest/performance_metrics.md`
- `shared/contracts/backtest/api.md`

## P0 Token 执行态登记

- 签发日期：2026-04-03
- token_id：tok-361fbc06-5016-4250-a7b0-38d167c21340
- 文件范围摘要：`shared/contracts/backtest/` 下四份正式契约文件（`backtest_job.md`、`backtest_result.md`、`performance_metrics.md`、`api.md`）
- 当前状态：四份正式契约已迁入正式目录并完成最小自校验，已于 2026-04-03 19:01:15 +0800 执行 lockback，当前状态为 `locked`

## P0 契约迁移执行态核验

### 范围与边界核验

- 本轮 P0 正式迁移仅写入 Token 白名单中的四份正式契约文件，未新增任何其他 `shared/contracts/**`、`services/**`、`dashboard/**`、`docker-compose.dev.yml` 或 `decision/**` 变更。✅
- 四份正式契约均保持“最小必要字段 + 最小接口说明”边界，未复制 legacy 实现逻辑，未把 TqSdk 运行态内部对象写入 shared 契约。✅

### 最小自校验

- `backtest_job.md`：字段表、状态机、排除字段与 draft 保持一致；补充说明已明确 `strategy_id` 指向固定模板，策略参数与风控参数统一来自用户上传的一体化 YAML 文件。✅
- `backtest_result.md`：结果字段、Parquet 路径说明与排除项与 draft 保持一致，未引入额外归档实现字段。✅
- `performance_metrics.md`：指标字段、排除项与计算说明与 draft 保持一致，未扩展进阶分析或过拟合指标。✅
- `api.md`：MVP 端点列表与 draft 保持一致；`POST /api/v1/jobs` 已明确采用“固定模板 + 用户上传参数 + 一体化 YAML 风控文件”口径；仅额外登记 backtest 服务内的策略推送需求说明，未引入 decision 侧未建档实现细节。✅
- 四份正式契约之间的交叉引用稳定：`api.md` 仅引用 `backtest_job.md`、`backtest_result.md`、`performance_metrics.md`，未出现路径或命名漂移。✅

### P0 契约 Lockback 收口

- 架构核验通过。
- 结论：**TASK-0003 backtest 四份正式契约的 P0 lockback 已于 2026-04-03 19:01:15 +0800 执行完成。**
- 对应里程碑：30% 契约迁移里程碑已正式闭环。

## 批次 B 终审结论

### Token 与范围核验

- 批次 B P1 Token 已签发，token_id 摘要：tok-60193dc1-e1be-459b-8133-c49e454adc0c。
- 服务代码实际写入仅落在五个白名单文件：services/backtest/src/backtest/session.py、services/backtest/src/backtest/runner.py、services/backtest/src/backtest/strategy_base.py、services/backtest/src/backtest/result_builder.py、services/backtest/tests/test_health.py。
- 额外发生的 P-LOG 写入仅有 docs/handoffs/TASK-0003-回测批次B-在线回测引擎交接.md 与 docs/prompts/agents/回测提示词.md，均属于回测 Agent 自有 handoff / 私有 prompt，不构成 P1 越权。
- 未触碰 shared/contracts/**、services/backtest/src/api/**、services/backtest/src/main.py、services/backtest/src/core/settings.py、services/backtest/README.md、services/backtest/configs/**、services/backtest/V0-backtext 看板/**、docker-compose.dev.yml、services/dashboard/**、services/decision/** 或任何远端交付文件。✅

### D-BT-01 ~ D-BT-05 终审复核

- D-BT-01：session.py 只允许 online + sim，并通过 TqSim() + TqBacktest 建立会话；未引入股票路径。✅
- D-BT-02：批次 B 仅通过 settings 读取环境变量声明字段，未读取真实 .env，未引入凭证落盘。✅
- D-BT-03：strategy_base.py 通过一体化 YAML 读取策略参数与风控参数；result_builder.py 将 risk_summary.source 固定为 yaml；代码内未硬编码止损、最大回撤、仓位上限等风控指标。✅
- D-BT-04：本轮只实现 backtest 内部执行链与结果结构，未写入 backtest → decision 跨服务契约或推送实现。✅
- D-BT-05：本轮未进入看板、Docker、同机同 compose 部署或远端交付实现。✅

### 关键文件复核

- session.py：会话配置层强制仅允许 online + sim；真实正式回测前必须配置 TQSDK_AUTH_USERNAME 与 TQSDK_AUTH_PASSWORD。✅
- strategy_base.py：固定模板注册表、一体化 YAML 解析、风险模型快照与 TargetPosTask 封装已落地。✅
- runner.py：已实现 YAML 路径约束、同步执行入口、异步提交骨架，以及“缺策略输入时返回 strategy_input_required”的收口逻辑。✅
- result_builder.py：已实现完整报告结构、绩效指标、risk_summary 与 completed / failed / strategy_input_required 三种状态。✅
- test_health.py：现有 app 导入、健康路由暴露和健康响应元数据校验已覆盖，pytest 结果 3 passed。✅

### 自校验复核

- py_compile：批次 A/B 相关 Python 文件语法编译通过。✅
- 包路径导入：services.backtest.src.main 导入成功。✅
- pytest：services/backtest/tests/test_health.py 结果为 3 passed。✅
- 伪运行验证 1：临时 YAML + dummy session manager + smoke template 可返回 completed，报告结构含 final_equity、风险参数快照与 notes。✅
- 伪运行验证 2：缺少策略 YAML 时，执行器稳定返回 strategy_input_required，并明确提示“当前已到达需要 Jay.S 提供策略输入的检查点”。✅

### 检查点判定

- 结论：**批次 B 已达到“只差策略输入即可执行一次正式回测”的检查点。**
- 判定依据：内部执行链已可完成 YAML 解析、模板解析、会话配置校验、报告汇总与失败/缺输入收口；当前唯一缺失的业务输入为 Jay.S 提供首轮真实策略模板实现与配套一体化 YAML 文件。
- 备注：批次 B 白名单未包含批次 A 路由文件，因此 HTTP 接线路径仍保持批次 A 骨架状态；该限制不影响本轮对“策略输入检查点”达成的判定。

### Lockback 收口

- 架构终审通过。
- 结论：**TASK-0003 批次 B 的 P1 lockback 已于 2026-04-03 19:01:15 +0800 执行完成。**
- 对应里程碑：回测主线已按里程碑收口到 60%，当前进入“等待 Jay.S 提供策略文件以执行首轮真实回测”检查点。

## Lockback 收口

- 2026-04-03 19:01:15 +0800：Atlas 已执行 TASK-0003 backtest 四份正式契约的 P0 lockback，review-id `REVIEW-TASK-0003-P0`，summary `TASK-0003 backtest 正式契约迁移完成，终审通过，执行锁回`；lockback 事件结果为 `approved`，Token 当前状态为 `locked`。
- 2026-04-03 19:01:15 +0800：Atlas 已执行 TASK-0003 批次 B 的 P1 lockback，review-id `REVIEW-TASK-0003-P1B`，summary `TASK-0003 批次B完成，达到策略介入点，执行锁回`；lockback 事件结果为 `approved`，Token 当前状态为 `locked`。
- 收口结论：TASK-0003 本轮两枚 Token 均已锁回，回测主线已正式收口到 60%，当前只等待 Jay.S 提供首轮真实策略模板实现与配套一体化 YAML 文件。

## 批次 A 终审结论

### Token 与范围核验

- 批次 A P1 Token 已签发，token_id 摘要：`tok-311d1a36-0cff-4141-939a-e96acadb9a38`。
- 服务代码实际写入仅落在六个白名单文件：`services/backtest/src/main.py`、`services/backtest/src/api/app.py`、`services/backtest/src/api/routes/health.py`、`services/backtest/src/api/routes/jobs.py`、`services/backtest/src/core/settings.py`、`services/backtest/README.md`。
- 额外发生的 P-LOG 写入仅有 `docs/handoffs/TASK-0003-回测批次A-后端骨架交接.md` 与 `docs/prompts/agents/回测提示词.md`，均属于回测 Agent 自有 handoff / 私有 prompt，同样符合 `WORKFLOW.md`，不构成越权。
- 未触碰 `shared/contracts/**`、`services/backtest/tests/**`、`services/backtest/configs/**`、`services/backtest/src/backtest/**`、`services/backtest/V0-backtext 看板/**` 或批次 B/C 白名单外文件。

### D-BT-01 ~ D-BT-05 终审复核

- D-BT-01：`jobs.py` 将 `asset_type` 固定为 `futures`，未引入股票路径或股票开关。✅
- D-BT-02：`settings.py` 只读取环境变量与占位符路径，未读取真实 `.env`，未引入密钥落盘。✅
- D-BT-03：`jobs.py` 明确采用“固定策略模板 + 用户上传一体化 YAML 文件”；`risk_config_source` 固定为 `yaml`，代码内未硬编码止损、最大回撤、仓位上限等风控指标。✅
- D-BT-04：批次 A 只保留“回测通过后再推送决策端”的口径说明，未擅自写入 backtest → decision 跨服务契约。✅
- D-BT-05：`README.md` 已对齐“后端 + 看板同机同 compose 部署”的公共口径。✅

### 关键文件复核

- `services/backtest/src/api/routes/jobs.py` 已明确体现“用户上传参数 + 固定策略模板”与“一体化 YAML 风控”模型，且当前仅做批次 A 骨架，不回退到最小 SMA 示例。✅
- `services/backtest/README.md` 已与当前公共口径一致：在线回测主路径、固定模板 + 用户参数、一体化 YAML 风控、回测后推送决策端、同机同 compose。✅

### 自校验复核

- VS Code 诊断：批次 A 五个 Python 文件无错误。✅
- `python3 -m py_compile`：批次 A 五个 Python 文件语法编译通过。✅
- 当前终端运行 `python3 -c 'import fastapi, pydantic'` 失败，原因是本机审查终端缺少 `fastapi` 依赖；因此 `GET /api/v1/health` 的运行态校验需在目标运行环境或镜像内补做。⚠️

### Lockback 建议

- 架构终审通过。
- 结论：**可以立即执行 TASK-0003 批次 A lockback**。
- 残留事项不属于本批次代码越权或实现偏航，而是当前审查终端缺少运行时依赖；建议在批次 B 开始前补做一次真实启动与 `GET /api/v1/health` 校验。

## 下一步

1. 向 Jay.S 汇报：回测主线已正式收口到 60%，当前只等待提供首轮真实策略模板实现与配套一体化 YAML 文件。
2. 当前已完成首轮真实回测日期与首次总金额冻结，可直接进入 R1 P1 Token 签发。
3. 在 R2 正式执行前，目标运行环境需提供 TQSDK_AUTH_USERNAME / TQSDK_AUTH_PASSWORD，并确保正式 YAML 以不改内容方式进入 TQSDK_STRATEGY_YAML_DIR。
4. 在 Jay.S 看过首轮真实回测结果前，不进入看板、Docker、远端交付或新的跨服务实现。

批次 A 已锁回：2026-04-03，Atlas 已执行批次 A lockback，结果为 `locked`。
P0 正式契约：2026-04-03 19:01:15 +0800 已锁回，当前状态为 `locked`。
批次 B：2026-04-03 19:01:15 +0800 已锁回，当前状态为 `locked`。

## 首轮真实回测预审结论（2026-04-03）

### 任务归属判定

- 结论：**继续归属 TASK-0003，不另开新任务。**
- 理由：本轮工作仍属于回测主线从 60% 检查点推进到 75% 首轮真实回测完成的同一服务内闭环；Jay.S 当前提供的是 TASK-0003 明确等待的正式策略 YAML，而不是新的跨服务范围。

### 正式输入冻结

- 首次真实回测策略：`FC-224_v3_intraday_trend_cf605_5m`
- 目标标的：`CZCE.CF605`
- 频率：`5m`
- 回测区间：`2024-04-03 至 2026-04-03`
- 首次总金额（initial_capital）：`1000000 CNY`
- 当前 YAML 为正式输入源，风控仍以 YAML 为准。
- 首次真实回测必须纳入：手续费、滑点、总金额。
- 看板继续后置，待首轮回测结果经 Jay.S 审阅后再启动。

### 冻结理由

1. 用户已明确要求“进行 2 年的回测”。
2. 当前日期为 2026-04-03，因此按最近完整 2 年冻结为 2024-04-03 至 2026-04-03。
3. 当前 backtest job 合约与现有骨架默认金额为 1000000.0，且用户未提供覆盖值，因此本轮先按 1000000 CNY 冻结。

### 读后技术结论

1. 当前 backtest 只有固定模板注册框架，没有 FC 模板实现，也没有最小因子库。
2. 当前正式 YAML 结构为 `factors / market_filter / signal / transaction_costs / risk`，与现有 `template_id / params / risk` 协议不兼容。
3. 当前策略最小必需因子与过滤项只需：MACD、RSI、VolumeRatio、ATR、ADX。
4. 当前回测结果结构能生成内存报告，但尚未构成首轮真实回测所需的最小执行留痕。
5. legacy 因子实现可只读参考公式，但本轮不得整包搬运。

### 建议批次与 Token

#### 批次 R1 — 因子 / 模板 / 解析接入

- Token 类型：**P1**
- 建议白名单：
	1. `services/backtest/src/backtest/strategy_base.py`
	2. `services/backtest/src/backtest/factor_registry.py`
	3. `services/backtest/src/backtest/fc_224_strategy.py`
	4. `services/backtest/tests/test_fc_224_strategy_loading.py`

#### 批次 R2 — 首次真实回测执行与结果留痕

- Token 类型：**P1**
- 建议白名单：
	1. `services/backtest/src/backtest/session.py`
	2. `services/backtest/src/backtest/runner.py`
	3. `services/backtest/src/backtest/result_builder.py`
	4. `services/backtest/tests/test_fc_224_execution_trace.py`

#### 可选批次 P0-X — 正式契约补录（仅在 Jay.S 明确要求时启用）

- Token 类型：**P0**
- 建议白名单：
	1. `shared/contracts/backtest/backtest_job.md`
	2. `shared/contracts/backtest/backtest_result.md`
	3. `shared/contracts/backtest/api.md`
- 预审判断：**当前不是首轮真实回测的必需前置。**

### 仍存在的非 Token 前置条件

1. 目标运行环境仍需准备 `TQSDK_AUTH_USERNAME / TQSDK_AUTH_PASSWORD`。
2. 正式 YAML 需以不改内容的方式进入 `TQSDK_STRATEGY_YAML_DIR`。

### 预审结论

- **预审通过，可进入 Token 申请准备态。**
- 当前建议路径：可直接进入 R1 P1 Token 签发，再在 R1 自校验与 handoff 通过后申请 R2 P1。
- 在 Jay.S 看过首轮真实回测结果前，不启动看板、Docker、远端交付，也不提前展开 P0 契约补录。
