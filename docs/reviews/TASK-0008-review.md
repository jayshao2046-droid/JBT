# TASK-0008 Review

## Review 信息

- 任务 ID：TASK-0008
- 审核角色：项目架构师
- 审核阶段：泛化正式引擎与正式报告导出预审
- 审核时间：2026-04-05
- 审核结论：通过（当前事项必须新建为 `TASK-0008`，不得复用 TASK-0004 / TASK-0007 白名单；本轮目标冻结为“一个通用正式引擎模板 + 多策略 YAML 严格填充”；A / B / C / D 四批白名单已冻结；执行角色口径冻结为“Atlas 当前会话直修 / 主导实现，项目架构师只做预审、公共状态同步与后续终审留痕，回测负责补写私有 prompt / handoff 与服务侧实施记录”）

---

## 一、任务边界核验

1. 任务目标明确：本轮不是再为 FC-224 之外单独新增一个策略模板，而是将正式引擎泛化为“一个通用正式引擎模板 + 多策略 YAML 严格填充”，并补齐正式报告导出链路。✅
2. 任务目录明确：实施区归属 `services/backtest/`；只有在 formal API / 报告导出契约必须补登时，才最小触及 `shared/contracts/backtest/api.md`。✅
3. 当前 TASK-0004 / TASK-0007 白名单均不覆盖本事项，不能复用旧任务号或旧 Token。✅
4. 当前项目架构师回合只允许写治理留痕与公共状态，不直接修改任何 `services/**` 业务代码。✅
5. 本轮明确禁止扩展到 `/Users/jayshao/JBT/` 外部目录、其他服务目录、`docker-compose.dev.yml`、运行态目录、真实 `.env`、日志、账本与数据库快照。✅

## 二、当前技术结论冻结

1. TQSDK 直接接收的会话层参数冻结为：`TqAuth(user_name, password)`、`TqBacktest(start_dt, end_dt)`、`TqSim(init_balance)`、`TargetPosTask(api, symbol, price, offset_priority, min_volume, max_volume, account)`。✅
2. `tqsdk 3.9.1` 中，`TqSim` 有 `set_commission(symbol, commission)`，没有 `set_slippage`。✅
3. 当前仓内只有 FC-224 模板被注册；现有结构为 `StrategyTemplateRegistry + FixedTemplateStrategy + FC224Strategy`。✅
4. 当前仓内没有现成的泛化表达式引擎；`market_filter / signal` 虽被 YAML 解析，但真正执行逻辑仍硬编码在 `fc_224_strategy.py`。✅
5. 当前真正形成正式执行闭环的风控只有 `position_fraction / position_adjustment`、`force_close_day`、`force_close_night`、`no_overnight`；`stop_loss / take_profit / max_drawdown / daily_loss_limit` 等尚未闭环。✅
6. 因此，本轮必须把“参数分类、泛化执行、正式结果导出”作为同一治理主线，而不是继续叠加专用模板。✅

## 三、五大参数与执行口径核验

1. 参数分类已冻结为：资金参数、策略参数、因子参数、信号参数、风控参数。✅
2. 会话层必须直接传入 TQSDK 的参数边界已冻结，不得把本地规则参数混写成“直接传 SDK”。✅
3. SDK 不支持直接 hook 的参数必须由本地正式引擎严格执行；其中滑点、止损、止盈、最大回撤、日亏损限制等不得再停留在“仅 YAML 被解析”的半成状态。✅
4. 手续费虽可通过 `TqSim.set_commission(symbol, commission)` 桥接到 SDK，但治理口径仍要求本地结果链路可复核、可导出、可审计。✅
5. 用户未来导入的策略，不得变更任何一个数字或符号，必须按 YAML 原值执行，并在正式报告中可追溯。✅
6. 前端体验冻结为“一键导入、一键执行、一键导出正式报告”，不允许另开独立风控配置页。✅

## 四、任务编号与执行责任核验

1. 当前事项已明确要求新建为 `TASK-0008`，不能复用旧白名单。✅
2. 执行责任口径已冻结为：本轮属于 Atlas 当前会话直修 / 主导实现。✅
3. 项目架构师负责预审、边界冻结、公共状态同步与后续终审留痕，不代写业务代码。✅
4. 回测负责后续补写私有 prompt、handoff 与服务侧实施记录。✅
5. 上述角色分工不替代 Token 机制；无 Jay.S 分批签发的有效 Token，仍不得写业务文件。✅

## 五、白名单冻结

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

### 当前不建议纳入的文件

1. TASK-0004 当前全部既有业务白名单文件
2. TASK-0007 当前全部既有业务白名单文件
3. `shared/contracts/backtest/backtest_job.md`
4. `shared/contracts/backtest/backtest_result.md`
5. `shared/contracts/backtest/performance_metrics.md`
6. `services/backtest/src/backtest/fc_224_strategy.py`
7. `docker-compose.dev.yml`
8. `services/backtest/Dockerfile`
9. 其他全部非白名单文件

## 六、必须分批推进的判断依据

1. 批次 A 涉及 `shared/contracts/**`，属于 P0；formal API / 报告导出契约若需变更，必须先契约后实现。
2. 批次 B 是正式引擎核心泛化，不能与正式结果导出或前端导出链路混做。
3. 批次 C 负责正式结果、正式报告导出与 API 并回，不应回头 reopen 批次 B 文件。
4. 批次 D 负责前端导入 / 结果 / 正式报告导出体验，且不得额外拆出独立风控配置页。
5. 任一批次若执行中需要白名单外文件，或膨胀到第 6 个业务文件，必须回交补充预审。

## 七、风险与缓解

| 风险 | 等级 | 缓解措施 |
|---|---|---|
| 继续沿用“每策略一个模板类”推进，导致通用化目标落空 | P1 | 预审明确冻结为“一个通用正式引擎模板 + 多策略 YAML 严格填充” |
| 把滑点、止损、止盈、最大回撤等继续停留在“YAML 已解析但未执行”状态 | P1 | 批次 B / C 明确要求形成本地正式执行与正式报告闭环 |
| 因仓内无现成泛化表达式引擎，执行中顺手拆出第 6 个文件 | P1 | 预审明确要求优先内聚到 `generic_strategy.py`；若超出 5 文件立即回交补充预审 |
| 借 TASK-0004 / TASK-0007 既有白名单继续推进，导致任务边界污染 | P-LOG | TASK-0008 独立建档、独立 Token、独立 lockback |
| 前端为临时实现再开独立风控配置页，偏离用户目标体验 | P1 | 批次 D 明确冻结“一键导入、一键执行、一键导出正式报告”，禁止独立风控页 |
| 以“Atlas 已获用户授权”为由跳过 Token | P0 / P1 | 评审明确：授权不替代 Token；业务写入仍需 Jay.S 分批签发有效 Token |

## 八、预审结论

1. **TASK-0008 预审通过。**
2. **本事项不得复用 TASK-0004 / TASK-0007 的任何白名单或 Token。**
3. **本轮必须按 A 契约先行 → B 正式引擎泛化 → C 正式结果 / 报告导出并回 → D 前端导入 / 结果 / 报告导出链路 的顺序推进。**
4. **本轮执行口径已冻结为“Atlas 当前会话直修 / 主导实现；项目架构师负责预审、边界冻结、公共状态同步与后续终审留痕；回测负责补写私有 prompt / handoff 与服务侧实施记录”。**
5. **当前可进入 Jay.S 分批签发 P0 / P1 Token 的准备态。**