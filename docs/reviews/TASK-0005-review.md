# TASK-0005 Review

## Review 信息

- 任务 ID：TASK-0005
- review-id：REVIEW-TASK-0005-A / REVIEW-TASK-0005-B
- 审核角色：项目架构师
- 审核阶段：全量因子接入与模板解冻预审；批次 A 终审与锁回已追加；批次 B 最小预审、签发同步、代码终审与锁回已追加
- 审核时间：2026-04-04
- 审核结论：预审通过；批次 A 已完成、自校验通过、终审通过并已锁回；批次 B 已完成、自校验通过、终审通过并已锁回；批次 C 尚未开始，回测 Agent 不得继续扩写白名单外文件

---

## 一、任务边界核验

1. 任务归属明确：仅限 `services/backtest/` 单服务范围。
2. 本轮目标明确：不是只补 `factor_registry.py`，而是保证用户给定策略因子集合可以在 JBT 回测端完成“加载 → 校验 → 进入执行路径”的闭环。
3. 本轮明确不纳入：
   - `services/backtest/V0-backtext 看板/**`
   - `shared/contracts/**`
   - `docker-compose.dev.yml`
   - 其他服务目录
   - 运行态目录、真实 `.env`、logs、账本、数据库快照
4. 当前任务明确针对 **JBT/services/backtest**，不是 JBT backtext 看板目录，也不是 legacy 的 `J_BotQuant` 实施任务。

## 二、只读技术结论

1. 当前 `services/backtest/src/backtest/factor_registry.py` 仅实现 5 个因子：`MACD`、`RSI`、`VolumeRatio`、`ATR`、`ADX`。✅
2. 当前 `services/backtest/src/backtest/strategy_base.py` 的内置模板注册仅会加载 `fc_224_strategy.py`，未形成通用模板入口。✅
3. 当前 `services/backtest/src/backtest/runner.py` 仍围绕 FC-224 首轮正式回测冻结输入工作，不具备面向“后续所有策略”的通用执行接入能力。✅
4. 因此，仅补足因子数量并不能保证“后续所有策略可回测”；必须把因子能力与通用模板 / 执行链可扩展性一起纳入实施范围。✅

## 三、输入基线核验

1. 输入来源已冻结为用户提供的 `FACTORS.md` 与 `ALL_FACTORS.md`。✅
2. 预审采用并集口径，`MyFactor` 明确排除。✅
3. 当前并集后目标因子集合共 33 项。✅
4. 已登记的输入基线差异如下：
   - `ImpliedVolatility` 仅出现在 `FACTORS.md`，但按并集纳入目标范围。
   - `ATR`、`CCI`、`DEMA`、`MFI`、`OBV`、`OpenInterestFactor`、`VWAP`、`InventoryFactor`、`WarehouseReceiptFactor` 仅出现在 `ALL_FACTORS.md`，但按并集纳入目标范围。
   - `SentimentFactor`、`VolatilityFactor` 后续实现时仍需核实其在 JBT backtest 中的接入口径，但当前预审先纳入目标因子集合。

## 四、批次拆分与候选白名单

### 建议首批白名单候选（批次 A）

1. `services/backtest/src/backtest/factor_registry.py`
2. `services/backtest/src/backtest/strategy_base.py`
3. `services/backtest/src/backtest/generic_factor_strategy.py`（暂定新增）
4. `services/backtest/tests/test_factor_registry_baseline.py`（暂定新增）
5. `services/backtest/tests/test_generic_strategy_loading.py`（暂定新增）

### 后续批次候选方向

1. 批次 B：`runner.py` 为核心，必要时联动 `result_builder.py` 与执行链测试，解决“非 FC-224 模板无法进入执行路径”的冻结问题。
2. 批次 C：围绕 `factor_registry.py`、通用模板文件与对应补测，清理孤悬注册 / 未接入因子。

### 分批理由

1. `WORKFLOW.md` 明确限制单任务默认最多 5 文件。
2. 当前问题同时涉及因子能力、模板入口、runner 执行链与测试覆盖，不宜伪装成单批大改。
3. 分批后可以把“能加载”和“能执行”的风险拆开核验，避免一次性放大回归半径。

## 五、当前阻塞与风险结论

1. 批次 A 已锁回；Jay.S 已明确要求执行批次 B，且批次 B 继续归属 TASK-0005，不新开任务号。✅
2. 当前剩余前置条件已清除：Jay.S 已按本轮冻结白名单完成批次 B 5 文件 P1 Token 签发与真实 lockback；同范围 5 文件现已重新锁定。✅
3. 当前必须收口的风险已明确为两项：
   - 因子缺口。
   - FC-224 单模板冻结。
4. 当前必须删除的非阻塞风险也已登记：
   - 单模板冻结残留。
   - 孤悬注册 / 未接入因子。

## 六、预审结论

1. **TASK-0005 预审通过。**
2. **当前已完成批次 B 5 文件 P1 Token 签发、执行、自校验、终审与锁回；同范围白名单已重新锁定。**
3. **任务边界、风险、批次拆分和候选白名单已经建立。**
4. **TASK-0004 看板任务目前应降为后置，优先级让位于 backtest 全量因子接入。**
5. **当前公共状态应切换为：TASK-0005 批次 B 已锁回；等待 Jay.S 决定是否进入批次 C 或恢复 TASK-0004。**

## 七、批次 A 终审补充（2026-04-04 02:51:37 +0800）

1. 范围核验通过：`git status --short -- services/backtest` 显示当前业务改动仅限以下 5 个白名单文件，未出现第 6 个业务文件：
   - `services/backtest/src/backtest/factor_registry.py`
   - `services/backtest/src/backtest/strategy_base.py`
   - `services/backtest/src/backtest/generic_factor_strategy.py`
   - `services/backtest/tests/test_factor_registry_baseline.py`
   - `services/backtest/tests/test_generic_strategy_loading.py`
2. 静态核验通过：上述 5 个白名单业务文件 `get_errors` 均无错误。
3. 因子基线核验通过：`services/backtest/src/backtest/factor_registry.py` 中 `@factor_registry.register` 共 33 处命中，`MyFactor` 无命中；正式因子基线已与预审冻结的 33 项一致。
4. 模板路径核验通过：`StrategyTemplateRegistry.resolve()` 先匹配精确 `template_id`，仅在未命中时才回退 `_fallback_template`；`services/backtest/tests/test_generic_strategy_loading.py` 同时断言 `strategy_registry.resolve(FC_224_TEMPLATE_ID).__name__ == "FC224Strategy"`，因此 FC-224 既有路径未被 generic fallback 覆盖。
5. 最小回归通过：`source .venv/bin/activate && python -m pytest services/backtest/tests/test_fc_224_strategy_loading.py services/backtest/tests/test_factor_registry_baseline.py services/backtest/tests/test_generic_strategy_loading.py -q` 结果为 `8 passed in 0.14s`。
6. 批次 A 范围收口成立：预审中的“仅 5 因子”与“仅 FC-224 单模板”两项非阻塞风险已在本批收口；其余剩余风险已明确后置到批次 B，包括：
   - `runner.py` / `result_builder.py` 仍未解冻，通用模板当前只建立最小完成路径；
   - 情绪、库存、仓单、价差、隐波等依赖外部列的因子仍采用“显式列优先、缺失时中性回退”口径；
   - 更完整的多信号执行循环与执行摘要扩展仍不在批次 A 范围内。
7. 锁回收口已完成：Jay.S 已为同范围 5 文件补签 replacement token `tok-a6e29fe8-4e49-4019-9b06-1b2c98bc8eae`；issue 时间戳与 lockback 时间戳均为 `1775242660`，对应 `2026-04-04 02:57:40 +0800`；notes 为 `TASK-0005 批次A补签用于终审后锁回；范围不变；用于修复缺失 lockctl 记录后的闭环`。
8. lockback 结果已记录：review-id `REVIEW-TASK-0005-A`，结果 `approved`，lockback 摘要 `TASK-0005 批次A完成，自校验通过，执行锁回`，当前状态 `locked`。
9. 当时终审结论：**TASK-0005 批次 A 已完成、自校验通过、终审通过并已锁回；批次 B 已完成预审并于 2026-04-04 11:21:56 +0800 正式签发，当时状态为执行中；本轮仅 `runner.py`、`result_builder.py`、`generic_factor_strategy.py`、`test_generic_strategy_execution.py`、`test_fc_224_execution_trace.py` 五文件可写，其余非白名单文件继续锁定。**

## 八、批次 B 最小预审与签发同步补充（2026-04-04）

1. 任务归属复核通过：批次 B 继续归属 TASK-0005，不新开任务号。
2. 范围边界复核通过：批次 B 只处理执行链接入，不回头改批次 A 已锁回的 `factor_registry.py` 基线，也不重新打开 `strategy_base.py`。
3. 本轮冻结白名单已收敛为以下 5 文件：
   - `services/backtest/src/backtest/runner.py`
   - `services/backtest/src/backtest/result_builder.py`
   - `services/backtest/src/backtest/generic_factor_strategy.py`
   - `services/backtest/tests/test_generic_strategy_execution.py`
   - `services/backtest/tests/test_fc_224_execution_trace.py`
4. 本轮继续锁定范围明确如下：
   - `services/backtest/src/backtest/strategy_base.py`
   - `services/backtest/src/backtest/factor_registry.py`
   - `services/backtest/src/backtest/fc_224_strategy.py`
   - `services/backtest/V0-backtext 看板/**`
   - `shared/contracts/**`
   - `docker-compose.dev.yml`
   - `services/backtest/.env.example`
   - 其他全部非白名单文件
5. 风险与验收重点已冻结：
   - generic strategy 应从最小快照路径升级到更完整的执行路径；
   - `runner.py` / `result_builder.py` 需要承接非 FC-224 模板的执行结果与摘要；
   - FC-224 的冻结正式回测路径和零成交拦截逻辑不得回退；
   - 不允许顺带进入看板、Docker、contracts 或其他服务。
6. 签发时结论：**TASK-0005 批次 B 已完成最小预审；Jay.S 已按冻结白名单签发 5 文件 P1 Token，review-id `REVIEW-TASK-0005-B`，token_id `tok-83f5a10a-f9d5-45c9-9c49-574ef5797460`，有效期 `2026-04-04 11:21:56 +0800` 至 `2026-04-04 11:51:56 +0800`；签发时状态为执行中；TASK-0004 继续后置。**

## 九、批次 B 签发信息补充（2026-04-04 11:21:56 +0800）

1. Jay.S 已为回测 Agent 正式签发批次 B 5 文件 P1 Token，token_id `tok-83f5a10a-f9d5-45c9-9c49-574ef5797460`，review-id `REVIEW-TASK-0005-B`，签发时间戳 `1775272916`，失效时间戳 `1775274716`，对应时间为 `2026-04-04 11:21:56 +0800` 至 `2026-04-04 11:51:56 +0800`。
2. 本轮签发 notes 已冻结为：`TASK-0005 批次B：执行链接入与 runner 接入；generic strategy 升级执行路径；保持 FC-224 不回退`。
3. 当前仅允许回测 Agent 写入以下 5 个白名单文件：`services/backtest/src/backtest/runner.py`、`services/backtest/src/backtest/result_builder.py`、`services/backtest/src/backtest/generic_factor_strategy.py`、`services/backtest/tests/test_generic_strategy_execution.py`、`services/backtest/tests/test_fc_224_execution_trace.py`。
4. `services/backtest/src/backtest/factor_registry.py`、`services/backtest/src/backtest/strategy_base.py`、`services/backtest/src/backtest/fc_224_strategy.py`、`services/backtest/V0-backtext 看板/**`、`shared/contracts/**`、`docker-compose.dev.yml`、`services/backtest/.env.example` 与其他全部非白名单文件继续锁定。
5. 签发时状态仅为“已预审、已签发、执行中”；后续状态以本文件第十节终审补充为准，在 lockback 完成前仍不得写成“已锁回”。

## 十、批次 B 终审补充（2026-04-04 11:44:42 +0800）

1. 范围核验通过：本轮仅审批次 B 白名单与对应 P-LOG 留痕；`git status --short -- ...` 复核结果显示，批次 B 相关业务层实际改动对象仅为 `services/backtest/src/backtest/generic_factor_strategy.py` 与 `services/backtest/tests/test_generic_strategy_execution.py`，另有回测 Agent 私有 prompt 与批次 B handoff 留痕；`runner.py`、`result_builder.py`、`test_fc_224_execution_trace.py` 本轮无代码改动，不构成越权，也不构成“少改文件数”的边界违规。
2. 静态核验通过：`get_errors` 对 `generic_factor_strategy.py`、`test_generic_strategy_execution.py`、批次 B handoff 与回测私有 prompt 复核均无错误。
3. generic 执行链接入核验通过：当前 `generic_factor_strategy.py` 已同时具备 static fallback 与 live execution 双路径；在 session 提供 `wait_update()`、`is_changing()` 与 `TargetPosTask` 时，会进入真实执行循环，并留下 `execution_loop_entered`、`signal_transitions`、`target_updates`、`observed_trade_records`、`final_signal_state` 等执行留痕。
4. 信号判定边界核验通过：generic 模板已支持 `market_filter.conditions`、`signal.long_condition`、`signal.short_condition` 的最小表达式求值；当 YAML 未提供显式条件时，可回退到 `long_threshold` / `short_threshold` 的最小权重分数口径。该实现满足批次 B 预审冻结的“执行链接入”目标，但尚未扩展为更完整 DSL；更完整 DSL 仍应后置到新批次处理。
5. 既有 FC-224 路径未回退：`runner.py` 中冻结正式回测校验与 `completed + total_trades=0` 拒收逻辑仍只对 FC-224 首轮正式模板生效，generic 模板不会误触该保护；`test_fc_224_execution_trace.py` 本轮回归通过，说明 FC-224 的正式路径、手续费/滑点留痕与零成交拦截逻辑未回退。
6. `runner.py` / `result_builder.py` 无需改动的收口理由成立：现有 `OnlineBacktestRunner.run_job_sync()` 已能承接 generic 模板执行，`BacktestResultBuilder` 现有 `strategy_name`、`timeframe`、`transaction_costs`、`notes`、`report_summary` 与 `report.json` 落盘结构已可稳定承接 generic 结果；本轮未修改这两个文件不构成验收缺口。
7. 最小回归通过：`source /Users/jayshao/JBT/.venv/bin/activate && python -m pytest services/backtest/tests/test_generic_strategy_loading.py services/backtest/tests/test_generic_strategy_execution.py services/backtest/tests/test_fc_224_execution_trace.py -q` 结果为 `7 passed in 0.19s`。
8. 当时终审结论：**TASK-0005 批次 B 代码终审通过。当前状态应切换为“代码终审通过，待执行 lockback”；不得提前写成已锁回。`runner.py`、`result_builder.py`、`test_fc_224_execution_trace.py` 已复核确认本轮无需变更，不构成越权；FC-224 既有路径未回退，generic live execution path 已接入，但更完整 DSL 仍后置。**

## 十一、批次 B 锁回补充（2026-04-04）

1. Jay.S 已使用原批次 B token `tok-83f5a10a-f9d5-45c9-9c49-574ef5797460` 完成真实 lockback，白名单范围保持不变，无需补签 replacement token。
2. lockback 结果已记录：review-id `REVIEW-TASK-0005-B`，结果 `approved`，lockback 摘要 `TASK-0005 批次B完成，自校验通过，执行锁回`，当前状态 `locked`。
3. 当前批次 B 统一结论：**已完成、自校验通过、终审通过、已锁回。**
4. 批次 C 尚未开始；若需启动，必须重新预审、重新冻结白名单并重新签发 Token。
5. `factor_registry.py`、`strategy_base.py`、`fc_224_strategy.py`、`services/backtest/V0-backtext 看板/**`、`shared/contracts/**`、`docker-compose.dev.yml`、`services/backtest/.env.example` 与其他非白名单文件继续冻结；当前等待 Jay.S 决定是否进入批次 C 或恢复 TASK-0004。
## 十二、批次 C 预审（2026-04-04）

1. 任务归属复核通过：批次 C 继续归属 TASK-0005，不新开任务号。
2. 范围调整依据已登记：Jay.S 已明确确认所有 33 项因子必须永久保留，不得删除，后续可能还会继续增加；因此批次 C 的目标由"清理孤悬注册"调整为"补全 33 项因子在 generic 执行路径中的接线完整性"。
3. 唯一接线缺口已确认：`GarmanKlass` 未出现在 `_FACTOR_SCORE_KEYS` 或 `_NON_DIRECTIONAL_KEYS` 任一结构中，但 `factor_registry.py` 已有完整实现（line 1068）；应将 `"garmanKlass"` 加入 `_NON_DIRECTIONAL_KEYS`（波动率指标，无方向性）。
4. 冻结白名单已收敛为 2 文件：
   - `services/backtest/src/backtest/generic_factor_strategy.py`
   - `services/backtest/tests/test_factor_registry_coverage.py`（新增）
5. 本批继续锁定范围明确如下：
   - `services/backtest/src/backtest/factor_registry.py`
   - `services/backtest/src/backtest/strategy_base.py`
   - `services/backtest/src/backtest/fc_224_strategy.py`
   - `services/backtest/src/backtest/runner.py`
   - `services/backtest/src/backtest/result_builder.py`
   - `services/backtest/V0-backtext 看板/**`
   - `shared/contracts/**`
   - `docker-compose.dev.yml`
   - `services/backtest/.env.example`
   - 其他全部非白名单文件
6. 验收重点已冻结：
   - `_NON_DIRECTIONAL_KEYS` 必须包含 `"garmanKlass"`；
   - 新增 `test_factor_registry_coverage.py` 必须覆盖全部 33 项官方因子的接线完整性（每个因子 key 要么在 `_FACTOR_SCORE_KEYS`，要么在 `_NON_DIRECTIONAL_KEYS`）；
   - 现有回归（批次 A、B 测试）必须继续通过，不得回退既有能力；
   - 不允许顺带进入看板、Docker、contracts 或其他服务。
7. 预审结论：**TASK-0005 批次 C 预审通过，冻结白名单 2 文件，唯一接线缺口为 `garmanKlass` 写入 `_NON_DIRECTIONAL_KEYS`，可进入 Jay.S 签发 Token 环节。**

## 十三、批次 C 代码终审（2026-04-04）

1. 范围核验通过：本轮仅审批次 C 冻结白名单 2 文件（`generic_factor_strategy.py` + 新增 `test_factor_registry_coverage.py`），未触碰 `factor_registry.py`、`strategy_base.py`、`fc_224_strategy.py`、`runner.py`、`result_builder.py`、看板、contracts、docker、`.env.example` 或其他服务目录。
2. `_NON_DIRECTIONAL_KEYS` 新增键核验通过：实际写入值为 `"garmanklass"`（全小写），与现有 `"adx"`、`"atr"` 命名风格一致；预审记录中的 `"garmanKlass"` 为大小写笔误，实现时已自行修正为规范的全小写形式，符合集合内统一命名约定。
3. 33 项因子接线完整性核验通过：`_FACTOR_SCORE_KEYS` 共 30 个因子键 + `_NON_DIRECTIONAL_KEYS` 中 3 个因子键（`adx`、`atr`、`garmanklass`）= 33 项，与预审冻结的 33 项官方因子全量吻合，无静默漏接。
4. 两集合互斥核验通过：`_FACTOR_SCORE_KEYS.keys()` 与 `_NON_DIRECTIONAL_KEYS` 无交集，不存在歧义因子。
5. 覆盖测试逻辑核验通过：
   - `test_all_official_factors_have_explicit_mapping`：对 `OFFICIAL_FACTOR_BASELINE` 中每个因子名 `.lower()` 后检查是否在 `_FACTOR_SCORE_KEYS` 或 `_NON_DIRECTIONAL_KEYS`，逻辑正确，测试通过。
   - `test_factor_score_keys_and_non_directional_keys_are_disjoint`：检查两集合 key 交集，逻辑正确，测试通过。
6. FC-224 相关逻辑无回退：本次修改仅向 `_NON_DIRECTIONAL_KEYS` 追加一个字符串字面值，未修改任何执行逻辑或条件分支；FC-224 专属路径未被触碰。
7. 全量回归通过：Atlas 独立复跑 5 个测试文件共 12 个用例，结果 `12 passed in 0.22s`，包含：
   - `test_factor_registry_baseline`（3 个）
   - `test_factor_registry_coverage`（2 个，本批次新增）
   - `test_generic_strategy_loading`（2 个）
   - `test_generic_strategy_execution`（2 个）
   - `test_fc_224_execution_trace`（3 个）
8. 代码终审结论：**TASK-0005 批次 C 代码终审通过。当前状态切换为"代码终审通过，待执行 lockback"；不得提前写成已锁回。33 项官方因子在 generic strategy 中已全部有明确映射，GarmanKlass 接线缺口已收口，两集合互斥已验证，既有回归无回退。**

## 十四、批次 C 锁回补充（2026-04-04）

1. Jay.S 已使用 token `tok-4d65bb9a-a51c-40bb-b50d-4dd804294d13` 完成真实 lockback，白名单范围保持不变，无需补签 replacement token。
2. lockback 结果已记录：review-id `REVIEW-TASK-0005-C`，结果 `approved`，lockback 摘要 `GarmanKlass接线修复，33项因子全覆盖测试通过，执行锁回`，当前状态 `locked`。
3. 当前批次 C 统一结论：**已完成、自校验通过、终审通过、已锁回。**
4. TASK-0005 全三批次（A、B、C）均已完成、终审通过并已锁回；33 项官方因子在 generic strategy 中完整接线，GarmanKlass 接线缺口已收口，两集合互斥已验证，既有回归无回退。
5. TASK-0005 全任务闭环；`factor_registry.py`、`strategy_base.py`、`fc_224_strategy.py`、`services/backtest/V0-backtext 看板/**`、`shared/contracts/**`、`docker-compose.dev.yml`、`services/backtest/.env.example` 与其他非白名单文件继续冻结，等待下一个任务的独立预审与 Token。