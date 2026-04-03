# TASK-0003 Phase2 首轮真实回测预审

## 文档信息

- 任务 ID：TASK-0003（Phase2 首轮真实回测预审子文档）
- 文档类型：阶段预审与实施冻结
- 签名：项目架构师
- 建档时间：2026-04-03
- 设备：MacBook
- 输入来源：Jay.S 首次真实策略 YAML，源文件为 `/Users/jayshao/Desktop/FC-_5_cf_v1.yaml`

---

## 一、任务归属判定

### 结论

- **本轮工作继续归属 TASK-0003，不另开新任务。**

### 理由

1. 当前工作仍完全落在 `services/backtest/` 单服务边界内，目标是把回测主线从 60%“等待策略输入”推进到 75%“首轮真实回测完成”。
2. 本轮新增输入正是 TASK-0003 在 60% 检查点明确等待的正式策略 YAML，不构成新的服务边界或新的项目目标。
3. 本轮不要求提前进入 dashboard、Docker、远端交付或 backtest → decision 跨服务契约实现，因此没有形成独立 TASK 的必要。
4. 若后续 Jay.S 要求把手续费/滑点快照提升为对外正式契约，或要求在首轮结果前提前启动看板/跨服务 API，再单独拆出新的 P0 或跨服务子批次即可；当前不必新开 TASK。

---

## 二、首次真实回测输入冻结

以下口径已冻结并作为本轮 Phase2 预审基线：

- 首次真实回测策略：**FC-224_v3_intraday_trend_cf605_5m**
- 目标标的：**CZCE.CF605**
- 频率：**5m**
- 回测区间：**2024-04-03 至 2026-04-03**
- 首次总金额（initial_capital）：**1000000 CNY**
- 当前 YAML：**正式输入源**
- 风控口径：**仍以 YAML 为准**
- 首次真实回测必须纳入：**手续费、滑点、总金额**
- 看板状态：**继续后置，待首轮回测结果经 Jay.S 审阅后再启动**

### 冻结理由

1. 用户已明确要求“进行 2 年的回测”。
2. 当前日期为 2026-04-03，因此本轮按最近完整 2 年冻结为 2024-04-03 至 2026-04-03。
3. 当前 backtest job 合约与现有骨架默认金额均为 1000000.0，且用户未提供覆盖值，因此本轮先按 1000000 CNY 冻结。

### 当前 YAML 只读核验结论

1. YAML 顶层使用 `name`，未提供当前 JBT 期望的 `template_id`。
2. YAML 结构为 `factors / market_filter / signal / transaction_costs / risk`，与当前 JBT 仅支持的 `template_id / params / risk` 协议不一致。
3. 当前策略最小必需因子与过滤项如下：
   - 因子：MACD、RSI、VolumeRatio
   - 过滤项：ATR、ADX
4. YAML 已显式提供交易成本参数：
   - `slippage_per_unit: 1`
   - `commission_per_lot_round_turn: 8`
5. YAML 已显式提供风险参数，首轮真实回测不得在代码中覆盖或硬编码这些风险值。

---

## 三、只读技术预审结论

1. 当前 JBT backtest 已有固定模板注册框架，但**尚无 FC 模板实现**。
2. 当前 JBT backtest **尚无因子注册/计算库**，因此不能直接承接 FC YAML 中的因子列表与 `market_filter`。
3. 当前 `strategy_base.py` 的 YAML 解析器只接受通用 `template_id / params / risk` 结构，无法直接消费当前正式输入 YAML。
4. 当前 `runner.py` 已可同步执行、校验 `initial_capital` 与 YAML 目录边界，但还没有为 FC 模板、交易成本应用与结果留痕建立正式执行链。
5. 当前 `result_builder.py` 仅构建内存报告对象，**未完成首轮真实回测所需的最小结果落盘留痕**。
6. legacy 因子库中已存在 MACD、RSI、VolumeRatio、ATR、ADX 的只读实现与公式参考；**本轮只能参考公式，不得跨服务或跨仓复制整套 legacy 结构**。
7. `shared/contracts/backtest/` 当前并不是首轮真实回测的主阻塞项。首轮真实回测优先走 backtest 服务内部执行链，不应把范围膨胀成先改正式契约。

---

## 四、最小实施拆分

### 批次 R1 — 因子 / 模板 / 解析接入（P1）

目标：只解决“当前正式 YAML 不能被 JBT backtest 正确理解与装配”的问题，不做真实执行，不碰 API，不碰部署。

#### 白名单文件（建议控制 4 文件）

1. `services/backtest/src/backtest/strategy_base.py`
2. `services/backtest/src/backtest/factor_registry.py`
3. `services/backtest/src/backtest/fc_224_strategy.py`
4. `services/backtest/tests/test_fc_224_strategy_loading.py`

#### Token 类型

- **P1 Token**（回测 Agent）

#### 本批次允许做的事

1. 让解析层接受当前正式 YAML：最小支持 `name`、`factors`、`market_filter`、`signal`、`transaction_costs`、`risk`。
2. 建立 JBT 回测因子最小库：仅实现 MACD、RSI、VolumeRatio、ATR、ADX 五项。
3. 为 FC-224_v3_intraday_trend_cf605_5m 实现固定模板类，并在模板内完成最小信号装配。
4. 对 `symbols` 与 `timeframe_minutes` 做最小校验，确保首轮正式输入锁定在 CZCE.CF605、5m。

#### 本批次明确禁止

1. 不实现泛化表达式引擎；`market_filter` 与 `signal` 只支持当前策略必需的最小判定，不扩展成通用 DSL。
2. 不接 HTTP 路径。
3. 不改 `shared/contracts/**`。
4. 不进入 dashboard、Docker、远端交付。

#### 验收标准

1. 当前正式 YAML 可被解析。
2. FC 模板可被注册。
3. 五个必需因子能在最小样例上产出结果。
4. 风控参数仍由 YAML `risk` 段输出，不被代码默认值覆盖。

### 批次 R2 — 首次真实回测执行与结果留痕（P1）

目标：只做首轮真实执行链闭环，把手续费、滑点、总金额纳入，并留下最小可审计结果。

#### 白名单文件（建议控制 4 文件）

1. `services/backtest/src/backtest/session.py`
2. `services/backtest/src/backtest/runner.py`
3. `services/backtest/src/backtest/result_builder.py`
4. `services/backtest/tests/test_fc_224_execution_trace.py`

#### Token 类型

- **P1 Token**（回测 Agent）

#### 本批次允许做的事

1. 把 YAML 中的手续费、滑点参数接入真实执行链。
2. 把首次真实回测的总金额通过 `initial_capital` 冻结到执行上下文。
3. 用 backtest 服务本地执行入口完成 CZCE.CF605、5m、2024-04-03 至 2026-04-03 窗口的首轮真实回测。
4. 生成最小结果留痕，至少固化：策略名、标的、频率、起止日期、总金额、手续费、滑点、最终状态与报告摘要。

#### 本批次明确禁止

1. 不返工批次 A HTTP 骨架。
2. 不提前要求 `POST /api/v1/jobs` 成为首轮真实回测唯一入口。
3. 不改看板与 Docker。
4. 不把范围扩展到 `shared/contracts/**`。

#### 验收标准

1. 首轮真实回测可实际执行。
2. 结果留痕中明确包含手续费、滑点、总金额。
3. 风控仍以 YAML 为准。
4. 形成面向 Jay.S 的首轮结果摘要，可进入 75% 检查点判断。

### 可选批次 P0-X — 正式契约补录（当前不建议先做）

仅在 Jay.S 明确要求“手续费/滑点快照必须先进入 shared/contracts 才能执行首轮回测”时启用。

#### 白名单文件（建议控制 3 文件）

1. `shared/contracts/backtest/backtest_job.md`
2. `shared/contracts/backtest/backtest_result.md`
3. `shared/contracts/backtest/api.md`

#### Token 类型

- **P0 Token**（项目架构师）

#### 当前预审判断

- **本批次当前不是首轮真实回测的必需前置。**
- 理由：
  1. `initial_capital` 已存在于当前 job 输入与内部执行快照中；
  2. 手续费、滑点可先作为 backtest 服务内部 YAML 执行配置与报告留痕处理；
  3. 首轮真实回测优先目标是得到 Jay.S 可审阅结果，而不是先升级对外契约。

---

## 五、建议的 Token 申请顺序

1. 先申请 **批次 R1 的 P1 Token**。
2. R1 自校验通过并提交 handoff 后，再申请 **批次 R2 的 P1 Token**。
3. 仅当 Jay.S 明确要求先补正式契约时，再单独申请 **P0-X Token**；不得把 P0-X 与 R1/R2 混批。

---

## 六、仍保留的非 Token 前置条件

以下事项仍需在首轮真实回测执行前落实，但已不再包含日期或首次总金额的不确定性：

1. **目标运行环境必须备好 TQSDK_AUTH_USERNAME / TQSDK_AUTH_PASSWORD。** 当前本地预审无法代替真实运行环境凭证准备。
2. **正式 YAML 需要进入 `TQSDK_STRATEGY_YAML_DIR` 的可执行目录。** `/Users/jayshao/Desktop/FC-_5_cf_v1.yaml` 仍视为正式输入源，但执行时需以不改内容的方式复制/挂载进入运行目录。

---

## 七、预审结论

1. **TASK-0003 可直接进入首轮真实回测 Phase2。**
2. **最小落地路径为两批次 R1 / R2，均为 P1。**
3. **当前不需要先拆出 P0 正式契约批次。**
4. **看板继续后置，待首轮真实回测结果经 Jay.S 审阅后再启动。**
5. **一切执行仍需遵守“一件事一审核一上锁”，R1 与 R2 不得合并申请 Token。**
6. **日期与首次总金额已完成冻结，当前可直接进入 R1 的 P1 Token 签发准备；剩余两项非 Token 前置条件继续保留给目标运行环境与正式执行阶段。**

## 八、首轮真实运行复盘后的 R3 补充预审（2026-04-03）

### 实际运行复盘

1. Atlas 已执行批次 R2 lockback；首轮真实回测随后已在当前可运行环境中实际跑通一遍。
2. 当前实际运行结果为：`completed`、`final_equity=1000000`、`total_trades=0`。
3. 该结果**不得**作为 75% 里程碑的正式首轮结果交付；回测主线仍停留在 60%。

### 根因确认

1. 当前 FC-224 模板已具备因子、`market_filter` 与 `signal` 的最小解析能力。
2. 但 `fc_224_strategy.py` 当前 `run()` 仍未进入 `wait_update() + TargetPosTask` 的真实执行循环。
3. 因此本轮 `completed + zero trades` 应判定为**“策略执行逻辑未闭环”**，而不是“策略本身无交易”。

### 任务归属复核

- **继续归属 TASK-0003，不另开新任务。**
- 理由：当前仍只是在 `services/backtest/` 单服务边界内，把首轮真实回测从“已能启动”推进到“真实执行链闭环且结果可交付”；没有新增跨服务契约、看板、Docker、README 或部署目标。

### 批次 R3 — FC-224 真实执行循环补齐（P1）

目标：只补 FC-224 模板进入真实执行循环与正式结果判定，不返工 R1/R2 已锁回的其他范围。

#### 白名单文件（冻结为 3 个服务文件）

1. `services/backtest/src/backtest/fc_224_strategy.py`
2. `services/backtest/src/backtest/runner.py`
3. `services/backtest/tests/test_fc_224_execution_trace.py`

#### Token 类型

- **P1 Token**（回测 Agent）

#### 本批次允许做的事

1. **继续坚持在线 TqBacktest 路线**，保持 `TqApi + TqSim + TqBacktest + TqAuth` 主路径不变。
2. 在策略模板内进入 `wait_update() + TargetPosTask` 的真实执行循环，补齐 FC-224 的执行闭环。
3. 在正式结果判定层明确：若 FC-224 首轮真实回测再次出现 `completed` 且 `total_trades=0`，必须判定为**“策略执行逻辑未闭环”**，不能作为正式首轮结果交付。
4. 复用现有正式输入冻结口径：FC-224_v3_intraday_trend_cf605_5m、CZCE.CF605、5m、2024-04-03 至 2026-04-03、initial_capital=1000000、手续费=1、双边手续费=8。

#### 本批次明确禁止

1. **不引入本地数据采集路径**，不新增 CSV / Parquet / Tushare / 跨服务取数回放路径。
2. 不改 API、README、`shared/contracts/**`、dashboard、Docker、`.env.example`、`session.py`、`result_builder.py` 或其他服务目录。
3. 当前不预授权第 4 个服务文件；若回测 Agent 证明必须新增 `strategy_base.py` 作为共享 helper 抽取点，必须先重新提交补充预审，未经复审不得擅自扩白名单。

#### 验收标准

1. FC-224 模板已进入官方模式的真实执行循环，而不是只做解析与静态判定。
2. 在线 TqBacktest 路线保持不变，且未引入本地数据采集路径。
3. 首轮真实回测若仍为零成交，结果会被明确标记为“策略执行逻辑未闭环”，不能再以正式结果口径交付。
4. 本批次服务代码写入仍严格限制在 3 个白名单文件内。

### R3 补充结论

1. **R3 继续沿用 TASK-0003，不另开任务。**
2. **R3 最小白名单已冻结为 3 个服务文件，Token 类型为 P1。**
3. **当前可以直接进入 R3 的 P1 Token 签发准备。**