# TASK-0005 backtest 全量因子接入与模板解冻预审

## 文档信息

- 任务 ID：TASK-0005
- 文档类型：新任务预审与范围冻结
- 签名：项目架构师
- 建档时间：2026-04-04
- 设备：MacBook
- 输入基线：用户提供的 `FACTORS.md` 与 `ALL_FACTORS.md`，按并集冻结，显式排除 demo/test 项 `MyFactor`
- 当前治理状态：批次 A 已完成并锁回；本次同步批次 B 最小预审与 5 文件白名单冻结

---

## 一、任务正式成立

### 归属结论

- **TASK-0005 正式成立。**
- **任务归属：`services/backtest/` 单服务范围。**
- **批次 B 继续归属 TASK-0005，不新开任务号。**

### 当前任务目标

本轮目标不是“只补 `factor_registry.py` 的因子数量”，而是保证**用户给定策略因子集合**在 JBT 回测端能够完成以下闭环：

1. 被策略输入层加载。
2. 被模板 / 注册层识别与校验。
3. 被执行链接纳并进入可执行路径。
4. 不再被 FC-224 单模板冻结阻断。

### 优先级调整

1. Jay.S 已明确把优先级从 TASK-0004 看板切换到 `services/backtest/` 的“全量因子一次性部署”。
2. TASK-0004 保持“已预审、未实施”的后置状态，待 TASK-0005 首轮接入推进后再回看。

---

## 二、输入基线冻结

### 输入来源

1. 用户附件：`FACTORS.md`
2. 用户附件：`ALL_FACTORS.md`

### 基线规则

1. 预审以两份附件的**并集**作为目标范围。
2. `MyFactor` 明确视为 demo/test 项，**排除**出本任务目标。
3. 若两份附件存在不一致，预审先登记为“输入基线差异”，仍按并集纳入目标范围，后续实现时逐项核实公式、参数与可执行性。

### 并集后的目标因子集合（33 项）

#### 趋势 / 反转 / 量价

- `ADX`
- `ATR`
- `BollingerBands`
- `CCI`
- `DEMA`
- `EMA`
- `Ichimoku`
- `MACD`
- `MFI`
- `OBV`
- `ParabolicSAR`
- `RSI`
- `SMA`
- `Supertrend`
- `VolumeRatio`
- `VWAP`
- `WilliamsR`

#### 波动率

- `GarmanKlass`
- `HistoricalVol`
- `ImpliedVolatility`
- `VolatilityFactor`

#### 套利 / 价差

- `BasisSpread`
- `CointResidual`
- `SpreadCrosscommodity`
- `SpreadCrossperiod`
- `SpreadRatio`
- `ZScoreSpread`

#### 情绪

- `NewsSentiment`
- `SocialSentiment`
- `SentimentFactor`

#### 基本面

- `InventoryFactor`
- `OpenInterestFactor`
- `WarehouseReceiptFactor`

### 当前已知基线差异

1. `ImpliedVolatility` 仅出现在 `FACTORS.md`，仍按并集纳入目标范围。
2. `ATR`、`CCI`、`DEMA`、`MFI`、`OBV`、`OpenInterestFactor`、`VWAP`、`InventoryFactor`、`WarehouseReceiptFactor` 仅出现在 `ALL_FACTORS.md`，仍按并集纳入目标范围。
3. `SentimentFactor`、`VolatilityFactor` 在附件中带有聚合实现口径，后续实现时需核实其在 JBT backtest 中应按“聚合因子”还是“可直接执行因子”接入，但本预审先按目标因子登记。

---

## 三、当前只读现状结论

1. 当前 `factor_registry.py` 仅实现 5 个因子：`MACD`、`RSI`、`VolumeRatio`、`ATR`、`ADX`。
2. 当前 `strategy_base.py` 的内置模板注册仅会加载 `fc_224_strategy.py`，尚未形成可扩展的通用模板入口。
3. 当前 `runner.py` 仍围绕 FC-224 首轮正式回测冻结输入工作，包含 `strategy_template_id`、标的、周期、日期、资金与交易成本的 FC-224 专用校验。
4. 因此，“只把缺失因子继续塞入 `factor_registry.py`”**不能**保证“后续所有策略可回测”；必须把**因子能力**与**通用模板 / 执行链可扩展性**一并纳入 TASK-0005。

---

## 四、核心阻塞与收口目标

### 核心阻塞 1：因子缺口

- 当前支持 5 项，目标基线为 33 项，存在大规模缺口。
- 若只补当前 FC-224 之外少量因子，仍不能覆盖用户给出的策略因子集合。

### 核心阻塞 2：FC-224 单模板冻结

- 目前模板注册和执行链都默认围绕 FC-224 运行。
- 即使因子数量补齐，如果模板注册、输入校验、runner 接入仍保持 FC-224 专用冻结，后续策略依旧无法进入执行路径。

### 本任务必须删除的非阻塞风险

1. **单模板冻结残留**：后续策略明明已具备因子，却仍被模板加载或 runner 校验卡死。
2. **孤悬注册 / 未接入因子**：因子名已注册，但模板解析、参数校验、执行链或测试未跟上，导致“表面已支持、实际不可跑”。

---

## 五、预审级白名单候选范围

以下为 TASK-0005 已登记的批次范围；批次 A 已完成并锁回，批次 B 在本轮冻结为建议白名单，不代表已完成 Token 签发：

### 关键实现文件类别

1. `services/backtest/src/backtest/factor_registry.py`
2. `services/backtest/src/backtest/strategy_base.py`
3. `services/backtest/src/backtest/runner.py`
4. 可能新增的通用策略模板文件，例如 `services/backtest/src/backtest/generic_factor_strategy.py`
5. 可能补充的执行结果或适配文件，例如 `services/backtest/src/backtest/result_builder.py`

### 对应 tests 文件类别

1. `services/backtest/tests/test_factor_registry_baseline.py`
2. `services/backtest/tests/test_generic_strategy_loading.py`
3. `services/backtest/tests/test_generic_strategy_execution.py`
4. 若复用既有测试，也可能涉及 `services/backtest/tests/test_fc_224_strategy_loading.py`
5. 若复用既有执行测试，也可能涉及 `services/backtest/tests/test_fc_224_execution_trace.py`

### 当前明确不在本任务预审范围内

1. `services/backtest/V0-backtext 看板/**`
2. `shared/contracts/**`
3. `docker-compose.dev.yml`
4. 其他服务目录
5. 运行态目录、真实 `.env`、logs、账本、数据库快照

---

## 六、最小安全拆分建议

根据 `WORKFLOW.md` 的“单任务默认最多 5 文件”约束，TASK-0005 不建议一次性打成单批；建议按以下最小安全路径分批。

### 批次 A：输入基线解冻与通用模板入口（已完成并锁回）

目标：先让“用户基线因子集合 + 通用模板入口”有合法承接点，不继续把模板注册锁死在 FC-224。

#### 建议首批白名单候选（5 文件）

1. `services/backtest/src/backtest/factor_registry.py`
2. `services/backtest/src/backtest/strategy_base.py`
3. `services/backtest/src/backtest/generic_factor_strategy.py`（暂定新增）
4. `services/backtest/tests/test_factor_registry_baseline.py`（暂定新增）
5. `services/backtest/tests/test_generic_strategy_loading.py`（暂定新增）

#### 本批目标

1. 冻结并校验 33 项因子基线名单。
2. 让模板注册不再只依赖 `fc_224_strategy.py`。
3. 建立通用模板最小入口，保证策略输入可以加载、识别、校验。
4. 明确排除 `MyFactor` 这类 demo/test 因子，不把示例项混入正式能力范围。

### 批次 B：执行链接入与结果承接（本轮最小预审冻结）

目标：让非 FC-224 的模板与因子组合不只“能加载”，还能够通过 runner 进入执行路径。

#### 冻结白名单建议范围（5 文件）

1. `services/backtest/src/backtest/runner.py`
2. `services/backtest/src/backtest/result_builder.py`
3. `services/backtest/src/backtest/generic_factor_strategy.py`
4. `services/backtest/tests/test_generic_strategy_execution.py`
5. `services/backtest/tests/test_fc_224_execution_trace.py`

#### 本批目标

1. 让 generic strategy 从“最小快照路径”升级到更完整的执行路径。
2. 让 `runner.py` 与 `result_builder.py` 能承接非 FC-224 模板的执行结果与摘要。
3. 保持 FC-224 既有正式回测能力不回退。
4. 批次 B 只处理执行链接入，不回头改批次 A 已锁回的 `factor_registry.py` 基线。

#### 本批验收重点

1. generic strategy 应从最小快照路径升级到更完整的执行路径。
2. `runner.py` / `result_builder.py` 需要承接非 FC-224 模板的执行结果与摘要。
3. FC-224 的冻结正式回测路径和零成交拦截逻辑不得回退。
4. 不允许顺带进入看板、Docker、contracts 或其他服务。

#### 本批继续锁定范围

1. `services/backtest/src/backtest/strategy_base.py`
2. `services/backtest/src/backtest/factor_registry.py`
3. `services/backtest/src/backtest/fc_224_strategy.py`
4. `services/backtest/V0-backtext 看板/**`
5. `shared/contracts/**`
6. `docker-compose.dev.yml`
7. `services/backtest/.env.example`
8. 其他全部非白名单文件

### 批次 C：孤悬注册 / 漏接因子收口

目标：把实现后仍可能残留的“名册已列、实际未接通”的问题在本任务内收口。

#### 候选白名单方向

1. `services/backtest/src/backtest/factor_registry.py`
2. `services/backtest/src/backtest/generic_factor_strategy.py`
3. 对应补测文件 1 至 3 个

#### 本批目标

1. 清理“已注册但未被模板或 runner 使用”的因子。
2. 清理“已能加载但未有最小测试覆盖”的因子。
3. 确保 TASK-0005 收口时，不遗留孤悬注册与未接入因子。

---

## 七、当前可进入的状态

1. **TASK-0005 已完成预审建档，且批次 A 已完成真实 lockback。**
2. **Jay.S 已明确要求执行批次 B；批次 B 继续归属 TASK-0005，不新开任务号。**
3. **批次 B 最小预审与 5 文件白名单冻结已完成，可直接进入 Jay.S 为回测 Agent 签发 5 文件 P1 Token 的状态。**
4. **在新 Token 签发前，回测 Agent 仍不得写入批次 B 业务文件；签发后也仅允许改动本轮冻结的 5 文件。**

---

## 八、预审结论

1. **TASK-0005 正式成立，归属 `services/backtest/`。**
2. **本任务目标不是只补 `factor_registry.py`，而是保证用户给定策略因子集合在 JBT 回测端可被加载、校验并进入可执行路径。**
3. **当前核心阻塞明确为两项：因子缺口、FC-224 单模板冻结。**
4. **批次 A 已锁回；批次 B 最小预审与 5 文件白名单冻结已完成。**
5. **批次 B 只处理执行链接入，不回头改批次 A 已锁回的 `factor_registry.py` 基线。**
6. **TASK-0004 看板当前继续后置；当前公共状态应切换为“TASK-0005 批次 B 已预审，可直接签发 5 文件 P1 Token”。**
---

## 批次 C 预审（2026-04-04）

### 批次 C 调整背景

Jay.S 已明确确认：**所有 33 项因子必须永久保留，不得删除，后续可能还会继续增加。** 因此批次 C 的目标从"清理孤悬注册"调整为"补全 33 项因子在 generic 执行路径中的接线完整性"。

原预审文件第六节对批次 C 的方向描述为"清理孤悬注册 / 未接入因子"。依据 Jay.S 本次确认，该方向整体调整为仅做接线补全，不做删除操作。

### 唯一接线缺口：GarmanKlass

经技术现状扫描，`generic_factor_strategy.py` 中存在两个因子映射结构：

- `_FACTOR_SCORE_KEYS`：30 项因子的方向性得分键映射
- `_NON_DIRECTIONAL_KEYS`：非方向性因子集合，包含 `adx`、`atr` 及 bollinger/ichimoku 的子键

扫描结论：`GarmanKlass` 未出现在 `_FACTOR_SCORE_KEYS` 或 `_NON_DIRECTIONAL_KEYS` 任一结构中，但 `factor_registry.py` 已有完整的 `GarmanKlass` 实现（line 1068）。若一个策略 YAML 使用 `garmanKlass` 作为因子 key，当前执行路径会静默跳过该因子，不会抛出可见错误，但结果也不会纳入该因子的信号贡献。

由于 `GarmanKlass` 是波动率指标，不具备多空方向性，应将 `"garmanKlass"` 加入 `_NON_DIRECTIONAL_KEYS` 而非 `_FACTOR_SCORE_KEYS`。

批次 C 修改范围：仅在 `generic_factor_strategy.py` 的 `_NON_DIRECTIONAL_KEYS` 集合中加入 `"garmanKlass"` 一项，修正接线缺口。

### 冻结白名单（2 文件）

1. `services/backtest/src/backtest/generic_factor_strategy.py`
2. `services/backtest/tests/test_factor_registry_coverage.py`（新增）

说明：白名单共 2 文件，在 WORKFLOW 5 文件上限内。本批次不打开 `factor_registry.py`、`strategy_base.py`、`fc_224_strategy.py`、`runner.py`、`result_builder.py` 或其他已锁回文件，不扩展到看板、contracts、docker 或其他服务。

### 批次 C 验收重点

1. `generic_factor_strategy.py` 的 `_NON_DIRECTIONAL_KEYS` 集合必须包含 `"garmanKlass"`。
2. 新增 `test_factor_registry_coverage.py` 必须覆盖所有 33 项官方因子：验证每个因子的 key 要么出现在 `_FACTOR_SCORE_KEYS`，要么出现在 `_NON_DIRECTIONAL_KEYS`，不允许有"注册了但接线空白"的因子。
3. 现有回归测试 `test_generic_strategy_loading.py`、`test_generic_strategy_execution.py`、`test_fc_224_execution_trace.py` 必须继续通过，不得回退批次 A、批次 B 的执行链能力。
4. 不允许顺带进入看板、Docker、contracts、`factor_registry.py`、`strategy_base.py`、`fc_224_strategy.py`、`runner.py`、`result_builder.py` 或其他服务。

### 预审结论

**TASK-0005 批次 C 预审通过，冻结白名单 2 文件，唯一接线缺口为 `garmanKlass` 写入 `_NON_DIRECTIONAL_KEYS`，可进入 Jay.S 签发 Token 环节。**