# TASK-0008 backtest 泛化正式引擎与正式报告导出预审

## 文档信息

- 任务 ID：TASK-0008
- 文档类型：新任务预审与范围冻结
- 签名：项目架构师
- 建档时间：2026-04-05
- 设备：MacBook

---

## 一、任务目标

在严格限制于 JBT 工作区内、且不复用 TASK-0004 / TASK-0007 既有白名单的前提下，把当前 backtest 正式引擎从“FC-224 单模板冻结实现”泛化为“一个通用正式引擎模板 + 多策略 YAML 严格填充”，并补齐正式报告导出所需的契约、结果构建、API 并回与前端导出链路。

本轮冻结目标如下：

1. 不再按“每个策略注册一个模板类”推进后续正式引擎；后续新增策略默认只新增 YAML，不再新增 FC-224 之外的单独策略模板类。
2. 只有在出现全新因子类型、全新信号语义或全新执行语义时，才允许扩展代码；单纯新增策略不得以“新增模板类”为默认实现路径。
3. 策略参数必须统一拆为五大类：资金参数、策略参数、因子参数、信号参数、风控参数。
4. 必须先明确哪些参数直接传给 TQSDK，哪些参数作为系统级参数在本地严格执行，不允许混写成模糊口径。
5. 用户未来导入的策略不得擅自变更任何一个数字或符号，必须按 YAML 原值严格执行，并在正式报告中保留可追溯性。
6. 系统级参数包括金额、滑点、手续费、止损、止盈、最大回撤等，必须在回测过程中形成正式执行闭环；目标体验冻结为“一键导入、一键执行”，不再额外开独立风控配置页。

---

## 二、任务编号与归属结论

### 任务编号结论

- **本事项必须新建为 `TASK-0008`。**

### 编号判定理由

1. 用户已明确指出：当前 TASK-0004 / TASK-0007 的白名单都不覆盖这次改造，不能复用旧白名单。
2. 当前事项的目标已从“看板两页收敛”与“8004 正式后端并回”升级为“正式引擎泛化 + 正式报告导出链路”，目标、风险、文件集与执行顺序都已变化。
3. 若继续借用旧任务号，会造成治理账本、Token 口径和后续 lockback 全部冲突，不符合一件事一审核一上锁流程。

### 服务归属结论

- **任务归属：`services/backtest/` 单服务范围；只有在补 formal API / 正式报告导出契约时，才最小触及 `shared/contracts/backtest/api.md`。**

### 强制边界

1. 严禁读取、引用或修改 `/Users/jayshao/JBT/` 之外的任何目录。
2. 不得扩展到 `services/decision/**`、`services/data/**`、`services/dashboard/**`、`integrations/**`、`docker-compose.dev.yml`、运行态目录、真实 `.env`、日志、账本或数据库快照。
3. 当前项目架构师回合只做治理建档、边界冻结、公共状态同步与后续终审留痕，不直接修改任何 `services/**` 业务代码。
4. TASK-0004、TASK-0007 当前既有白名单继续按各自任务独立生效，不自动并入 TASK-0008。

---

## 三、当前会话角色口径

1. 本轮属于**“Atlas 在当前会话获用户明确授权后的直修 / 主导实现”**。
2. 项目架构师负责：预审、边界冻结、公共状态同步与后续终审留痕。
3. 回测负责：后续补写私有 prompt、handoff 与服务侧实施记录。
4. 上述角色分工不替代 Token 流程；Atlas 或回测后续要改任一业务白名单文件，仍必须按批次取得 Jay.S 签发的有效 P0 / P1 Token。

---

## 四、当前技术结论冻结

本轮预审按当前会话已确认、且必须写入治理账本的技术结论冻结如下：

1. TQSDK 直接接收的会话层参数可归纳为：`TqAuth(user_name, password)`、`TqBacktest(start_dt, end_dt)`、`TqSim(init_balance)`、`TargetPosTask(api, symbol, price, offset_priority, min_volume, max_volume, account)`。
2. 当前安装版本 `tqsdk 3.9.1` 中，`TqSim` 有 `set_commission(symbol, commission)`，没有 `set_slippage` 方法。
3. 当前仓内只有 FC-224 模板被注册；现有结构为 `StrategyTemplateRegistry + FixedTemplateStrategy + FC224Strategy` 专用实现。
4. 当前仓内没有现成的泛化表达式引擎；`market_filter` / `signal` 虽被 YAML 解析，但真正执行逻辑仍硬编码在 `fc_224_strategy.py`。
5. 当前真正已执行的风险控制只有 `position_fraction / position_adjustment`、`force_close_day`、`force_close_night`、`no_overnight`；`stop_loss / take_profit / max_drawdown / daily_loss_limit` 等尚未形成正式执行闭环。
6. 因此，本事项的根问题不是“再补一个 FC-224 之外的模板类”，而是把正式引擎、参数分类、风险执行与正式报告导出统一泛化。

---

## 五、五大参数分类与执行口径冻结

| 参数大类 | 典型内容 | 直接传给 TQSDK 的口径 | 本地严格执行的口径 |
|---|---|---|---|
| 资金参数 | 初始资金、仓位占比、仓位调整、资金约束 | `initial_capital` 需进入 `TqSim(init_balance)`；与下单目标相关的数量结果最终映射到 `TargetPosTask` | 资金分配、仓位比例、仓位调整、金额约束仍须由本地正式引擎按 YAML 原值计算并可在正式报告追溯 |
| 策略参数 | `symbols`、周期、回测区间、模板标识、合约规格 | `start_dt / end_dt` 进入 `TqBacktest`；交易标的与委托参数进入 `TargetPosTask`；行情订阅按正式引擎会话组织 | 模板选择、YAML 解析、合约规格解释、参数归档与报告落盘仍由本地正式引擎负责 |
| 因子参数 | 因子清单、权重、指标窗口、输入列、聚合规则 | 不直接传给 TQSDK | 由本地因子注册表与通用正式引擎严格按 YAML 原值解析与执行 |
| 信号参数 | `market_filter`、`signal` 条件、阈值、确认 bars | 不直接传给 TQSDK | 由本地正式引擎完成表达式求值、状态切换、目标仓位决策与报告留痕 |
| 风控参数 | 滑点、手续费、止损、止盈、最大回撤、日亏损限制、强平时点、不隔夜 | 仅 SDK 具备直接 hook 的部分可桥接，例如 `commission -> TqSim.set_commission(symbol, commission)` | 滑点、止损、止盈、最大回撤、日亏损限制、强平、报告导出与所有可追溯审计信息必须由本地正式引擎严格执行；即便手续费桥接到 SDK，也仍需在本地结果链路可复核 |

补充冻结口径：

1. 用户未来导入的策略，任何数字、字符串、合约符号、条件表达式都不得被前端或后端静默改写。
2. 正式引擎与正式报告导出必须保证“YAML 原值 -> 执行结果 -> 报告字段”三段可追溯。
3. 不允许为本事项另开独立风控配置页；风控参数必须随策略 YAML 一起导入、执行与导出。

---

## 六、批次拆分结论

### 是否必须拆批

- **必须拆批，且冻结为 A / B / C / D 四个代码批次。**

### 拆批理由

1. `shared/contracts/backtest/api.md` 属于 P0 保护区，且 formal API / 正式报告导出契约若需补登，必须先契约后实现。
2. 正式引擎泛化核心、正式结果与 API 并回、前端导入与报告导出链路属于三个不同层级，不能混成一次大改。
3. 任一批次若执行中需要新增白名单外文件，或膨胀到第 6 个业务文件，必须回交补充预审。

### 批次 A：formal API / 报告导出边界补登（P0）

目标：如需补 formal API 或正式报告导出契约，必须先在 formal contract 冻结边界，再进入服务实现。

冻结白名单：

1. `shared/contracts/backtest/api.md`

说明：

1. 本批只改 formal API / 报告导出边界，不改任何 `services/**` 业务代码。
2. 若执行中证明仅 `api.md` 不足以承载正式报告导出口径，必须补充 P0 预审，不能顺手打开其他 contract 文件。

### 批次 B：通用正式引擎模板核心泛化（P1，5 文件内）

目标：把正式引擎核心从 FC-224 单模板冻结形态泛化为“一个通用正式引擎模板 + 多策略 YAML 严格填充”的最小执行主链。

冻结白名单：

1. `services/backtest/src/backtest/strategy_base.py`
2. `services/backtest/src/backtest/factor_registry.py`
3. `services/backtest/src/backtest/generic_strategy.py`
4. `services/backtest/src/backtest/runner.py`
5. `services/backtest/tests/test_generic_strategy_pipeline.py`

说明：

1. 本批严格卡在 5 文件上限内，不允许把 `fc_224_strategy.py`、`result_builder.py` 或额外表达式引擎文件顺手并入。
2. 当前仓内没有现成泛化表达式引擎，因此如需最小表达式求值能力，应优先内聚在 `generic_strategy.py` 这一新文件内；若执行中证明必须再拆出第 6 个文件，当前 Token 立即失效。
3. 本批验收重点是：通用模板入口、五大参数分类承接、YAML 原值严格执行、非 FC-224 策略能进入正式执行链，而不是继续新增专用模板类。

### 批次 C：正式结果构建与 API / 报告导出并回（P1，5 文件内）

目标：把正式执行结果、正式报告导出与后端 API 返回链路并回到 JBT 正式后端。

冻结白名单：

1. `services/backtest/src/backtest/result_builder.py`
2. `services/backtest/src/api/routes/backtest.py`
3. `services/backtest/src/api/routes/strategy.py`
4. `services/backtest/src/api/routes/support.py`
5. `services/backtest/tests/test_formal_report_api.py`

说明：

1. 本批只处理正式结果、报告导出与 API 返回，不回头 reopen 批次 B 白名单文件。
2. 若执行中证明 formal report export 需要新增 contract 字段或第 6 个业务文件，必须先回交补充预审。

### 批次 D：前端导入 / 结果 / 正式报告导出链路（P1，5 文件内）

目标：在仓内前端形成“一键导入、一键执行、一键导出正式报告”的闭环体验，不新增独立风控配置页。

冻结白名单：

1. `services/backtest/backtest_web/src/utils/api.ts`
2. `services/backtest/backtest_web/app/agent-network/page.tsx`
3. `services/backtest/backtest_web/app/operations/page.tsx`
4. `services/backtest/backtest_web/src/utils/reportExport.ts`

说明：

1. 本批默认只冻结 4 个业务文件；若执行中证明还需要新增第 5 个前端 helper / 模板 / 文档文件，也必须先回交补充预审，不得用“还没到第 6 个文件”为理由跳过白名单复审。
2. 本批必须保持“按 YAML 原值展示并执行”的体验口径，不得额外拆出独立风控配置页。

---

## 七、最小白名单冻结

### 批次 A：P0 白名单

1. `shared/contracts/backtest/api.md`

### 批次 B：P1 白名单

1. `services/backtest/src/backtest/strategy_base.py`
2. `services/backtest/src/backtest/factor_registry.py`
3. `services/backtest/src/backtest/generic_strategy.py`
4. `services/backtest/src/backtest/runner.py`
5. `services/backtest/tests/test_generic_strategy_pipeline.py`

### 批次 C：P1 白名单

1. `services/backtest/src/backtest/result_builder.py`
2. `services/backtest/src/api/routes/backtest.py`
3. `services/backtest/src/api/routes/strategy.py`
4. `services/backtest/src/api/routes/support.py`
5. `services/backtest/tests/test_formal_report_api.py`

### 批次 D：P1 白名单

1. `services/backtest/backtest_web/src/utils/api.ts`
2. `services/backtest/backtest_web/app/agent-network/page.tsx`
3. `services/backtest/backtest_web/app/operations/page.tsx`
4. `services/backtest/backtest_web/src/utils/reportExport.ts`

### 当前明确继续锁定的重点文件

1. TASK-0004、TASK-0007 当前全部既有业务白名单文件，不因 TASK-0008 自动解锁。
2. `shared/contracts/backtest/backtest_job.md`
3. `shared/contracts/backtest/backtest_result.md`
4. `shared/contracts/backtest/performance_metrics.md`
5. `services/backtest/src/backtest/fc_224_strategy.py`
6. `docker-compose.dev.yml`
7. `services/backtest/Dockerfile`
8. `services/backtest/src/api/app.py`
9. 其他全部非白名单文件

---

## 八、P0 / P1 分级与 Token 建议

### 保护级别结论

1. `shared/contracts/backtest/api.md` 属于 **P0**，且必须先做。
2. `services/backtest/src/backtest/**`、`services/backtest/src/api/**`、`services/backtest/tests/**`、`services/backtest/backtest_web/**` 中被白名单点名的文件属于本任务 **P1** 实施区。
3. 本轮不伪造任何 `token_id`；当前只冻结“待 Jay.S 按批次签发 P0 / P1 Token”的治理口径。
4. `docs/tasks/**`、`docs/reviews/**`、`docs/locks/**`、`docs/handoffs/**`、`docs/prompts/**` 属于 P-LOG 区，无需文件级 Token，但必须遵守角色独占写权限。

### 建议执行主体口径

1. 批次 A / B / C / D：**Atlas**。
2. 当前理由：用户已在本会话明确授权 Atlas 完成全部改造，并要求“本轮由 Atlas 当前会话直修 / 主导实现”。
3. 项目架构师不代写服务代码，只负责本轮预审、公共状态同步与后续终审留痕。
4. 回测 Agent 在 Atlas 每步实施后负责补写私有 prompt、handoff 与服务侧实施记录。

### Jay.S 后续应签发的精确 Token 口径

#### 批次 A（P0）

请为 Atlas 签发 `TASK-0008` 批次 A 的单 Agent、单任务、单文件 P0 Token，允许修改文件仅 `shared/contracts/backtest/api.md`，动作类型 `edit`，目的为补 formal API / 正式报告导出边界；有效期 30 分钟；白名单外文件继续锁定。

#### 批次 B（P1）

请为 Atlas 签发 `TASK-0008` 批次 B 的单 Agent、单任务、5 文件 P1 Token，允许修改文件仅 `services/backtest/src/backtest/strategy_base.py`、`services/backtest/src/backtest/factor_registry.py`、`services/backtest/src/backtest/generic_strategy.py`、`services/backtest/src/backtest/runner.py`、`services/backtest/tests/test_generic_strategy_pipeline.py`，动作类型 `edit/create`，目的为完成通用正式引擎模板核心泛化；有效期 30 分钟；若执行中需要白名单外文件或第 6 个业务文件，当前 Token 立即失效并回交补充预审。

#### 批次 C（P1）

请为 Atlas 签发 `TASK-0008` 批次 C 的单 Agent、单任务、5 文件 P1 Token，允许修改文件仅 `services/backtest/src/backtest/result_builder.py`、`services/backtest/src/api/routes/backtest.py`、`services/backtest/src/api/routes/strategy.py`、`services/backtest/src/api/routes/support.py`、`services/backtest/tests/test_formal_report_api.py`，动作类型 `edit/create`，目的为完成正式结果、正式报告导出与 API 并回；有效期 30 分钟；若执行中需要新增 contract 字段或第 6 个业务文件，必须回交补充预审。

#### 批次 D（P1）

请为 Atlas 签发 `TASK-0008` 批次 D 的单 Agent、单任务、4 文件 P1 Token，允许修改文件仅 `services/backtest/backtest_web/src/utils/api.ts`、`services/backtest/backtest_web/app/agent-network/page.tsx`、`services/backtest/backtest_web/app/operations/page.tsx`、`services/backtest/backtest_web/src/utils/reportExport.ts`，动作类型 `edit/create`，目的为完成前端导入 / 结果 / 正式报告导出链路；有效期 30 分钟；若执行中新增任一白名单外文件，必须补充预审。

---

## 九、预审结论

1. **TASK-0008 正式成立。**
2. **本事项不得复用 TASK-0004 / TASK-0007 的任何白名单或 Token。**
3. **本轮目标冻结为“一个通用正式引擎模板 + 多策略 YAML 严格填充”，而不是再新增 FC-224 之外的单独策略模板类。**
4. **五大参数分类、TQSDK 直传参数与本地严格执行参数的边界已冻结。**
5. **本轮执行口径已冻结为“Atlas 当前会话直修 / 主导实现；项目架构师负责预审、边界冻结、公共状态同步与后续终审留痕；回测负责后续补写私有 prompt / handoff 与服务侧实施记录”。**
6. **当前可进入 Jay.S 分批签发 A / B / C / D Token 的准备态。**