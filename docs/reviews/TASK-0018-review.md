# TASK-0018 Review

## Review 信息

- 任务 ID：TASK-0018
- 审核角色：项目架构师
- 审核阶段：D201（自建回测系统）建档预审 + 2026-04-09 批次 B / C-SUP 终审收口
- 审核时间：2026-04-09
- 审核结论：条件通过（建档通过；批次 A/B/C/D/E 已锁回；批次 C 补充范围终审通过并已完成 lockback）

---

## 一、预审范围

1. 仅审任务边界、分批策略、白名单模板与治理约束。
2. 本轮不写任何 `services/**` 或 `shared/contracts/**` 业务代码。

## 二、预审结论

1. 任务目标清晰：保留 TqSdk/TqBacktest 既有系统 + 新增 local 自建回测系统，并提供统一执行入口。
2. 批次拆分合理：A（P0 契约扩展）-> B（P1 data API）-> C（P1 双引擎编排）-> D（P1 系统级风控联动）-> E（P1 引擎选择控件）-> F（P1 完整报告导出与展示）。
3. 服务边界清晰：data 供数、backtest 消费与执行、contracts 统一边界。
4. 治理约束已冻结：禁止跨服务 import、禁止跨目录直读、禁止改动运行态敏感路径。

## 三、关键风险

1. 契约漂移风险：契约先行不充分会导致 B/C 批次接口对不齐。
2. 数据延迟风险：Mini API 延迟或抖动会影响回测窗口与重试策略。
3. 确定性回测风险：缓存与重试若处理不当会破坏回测可重复性。
4. 风控语义偏差风险：夜盘/日切锚点定义不一致会导致回测与实盘解释偏差。
5. 双引擎结果口径漂移风险：同一输入下 `tqsdk` 与 `local` 结果可能产生不可解释偏差。
6. 双引擎风控语义不一致风险：不同引擎触发风控事件的证据链粒度不一致。
7. 报告 schema 漂移风险：两引擎报告字段演进不同步导致导出/展示断裂。
8. UI 误触发默认引擎风险：引擎选择控件默认值不透明导致误执行。

## 四、阻断条件

1. 无 Token 不得写保护区（`shared/contracts/**`、`services/**` 等）。
2. 批次外文件禁止改动，若需扩白名单必须回交补充预审。
3. 未完成自校验不得提交终审。
4. 未完成终审与锁回不得宣布批次完成。

## 五、当前轮次白名单

1. `docs/tasks/TASK-0018-backtest-API化重建-Phase1.md`
2. `docs/reviews/TASK-0018-review.md`
3. `docs/locks/TASK-0018-lock.md`
4. `docs/handoffs/TASK-0018-架构预审交接.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

## 六、当前下一步准入条件

1. 批次 E 已完成 Atlas lockback，当前状态 `locked`；lockback review-id=`REVIEW-TASK-0018-E`，锁回摘要为“批次E终审通过；两文件白名单边界合规，允许锁回。”。
2. 批次 B 当前有效业务白名单为 `services/data/src/main.py` 与 `services/data/tests/test_main.py`；当前执行口径已切换为 replacement token=`tok-040a489d-5546-4be4-abd1-4cc5cb4758fe`，review-id=`REVIEW-TASK-0018-B`，lockback 已实际执行，当前状态 `locked`。
3. 批次 C 主批次已锁回；补充范围有效业务白名单为 `services/backtest/src/backtest/local_engine.py`、`services/backtest/src/api/routes/backtest.py`、`services/backtest/tests/test_local_engine_generic.py`；`REVIEW-TASK-0018-C-SUP` 执行 token 为 `tok-393d60ba-f539-4f9c-8a56-02ed156fa914`（3 天窗口 replacement token）；2026-04-07 初始 token `tok-bfd51a47-63e2-40a5-aa62-25e705a75584` 为历史留痕；Atlas 已于 2026-04-09 执行 lockback，当前状态 `locked`。
4. 新增统一执行口径：3 年分钟 K 回测场景中，`requested_symbol` 可继续来自用户 YAML 的 `DCE.p2605`，但 `executed_data_symbol` 必须使用 Mini 上具备完整区间的 p 品种连续主力 `KQ_m_DCE_p` / `DCE.p` 连续主力完成 `2023-04-03` 至 `2026-04-03` 的 3 年回测；结果与报告必须显式区分两者，避免误导为“全程直接使用交割月 `DCE.p2605` 分钟数据回放”。
5. 同一输入下，两引擎结果仍必须可解释，允许数值差异，但必须保留证据链与执行口径说明。

---

## 七、批次 A 执行记录（2026-04-07）

- 执行结论：已执行（仅契约单文件）
- 业务文件：`shared/contracts/backtest/api.md`
- 关联 token_id：`tok-38d7c21e-36bd-4fe1-a4dc-843178e351dc`

本批已在 `shared/contracts/backtest/api.md` 补齐并冻结：

1. `engine_type` 字段：固定支持 `tqsdk`、`local`，默认值 `tqsdk`，保留既有 TqSdk 路径兼容。
2. 系统级风控事件证据链结构：统一 `risk_event` 最小字段，覆盖触发原因、阈值、观测值、时间、引擎归属，并要求双引擎共用。
3. 完整报告导出统一结构：冻结 `formal_report_v1` schema，要求两引擎输出同一主字段集合并挂接风控证据链。

## 八、批次 A 最小自校验

1. 业务改动范围校验通过：仅 `shared/contracts/backtest/api.md`。
2. 治理留痕校验通过：仅更新 `docs/reviews/TASK-0018-review.md`、`docs/locks/TASK-0018-lock.md`、`docs/prompts/公共项目提示词.md`、`docs/prompts/agents/项目架构师提示词.md`。
3. 未发生 `services/**` 目录改动。
4. 结论：批次 A 可提交终审并执行锁回。
5. 收口标记：`TASK-0018-A-EXECUTED-2026-04-07`。

## 九、批次 A 终审与锁回结果

1. 终审结论：通过（approved）。
2. lockback 已执行：`review-id=REVIEW-TASK-0018-A`。
3. Token 状态：locked。

---

## 批次 C 终审（2026-04-07）

### 终审基本信息

- 终审时间：2026-04-07
- 审核角色：项目架构师
- 对应 Token：`tok-4f7d7a03-e4be-4c40-bc88-493175e8f587`
- Atlas 自校验结论：18 passed，2 个预存在失败与本批次无关

### 终审结论

```
【终审结论】⚠️ 有保留通过

【边界合规】
  A1 – 实际改动严格限于白名单 4 文件：通过
  A2 – generic_strategy.py 未被触碰（git diff 零输出）：通过
  A3 – runner.py 未被触碰（git diff 零输出）：通过
  A4 – 无跨服务 import（grep 四文件零命中）：通过
  A5 – 批次 C 自身未写入 shared/contracts；但 shared/contracts/backtest/api.md
       有批次 A 未提交的 §6.2 全部内容处于未提交状态，须在批次 C 提交前先提交
       批次 A 修改（独立 commit），属流程保留项，非代码违规：有保留通过

【验收标准】
  B1 – tqsdk 路径（generic_strategy.py / runner.py）零改动，jobs.py 对 tqsdk
       路径仅新增 execution_stage 判断，既有响应字段未移除：通过
  B2 – local 引擎可运行最小回测并产出 LocalBacktestReport；summary 含
       final_equity / max_drawdown / pnl / win_rate / sharpe，但
       artifacts.equity_curve = None（内部 equity 列表未序列化到报告）；
       批次 C MVP 可接受，需在批次 D/F 中补全：有保留通过
  B3 – EngineRouter 正确分发，不支持的值抛 EngineTypeError，API 层转 422
       并含 "engine_type" 字样："Unsupported engine_type: '...' "：通过
  B4 – DataProvider 抽象层（ABC）已建立，MockDataProvider 实现完整；
       批次 B/D 可无改动引擎核心直接替换 Provider：通过
  B5 – jobs.py 改动最小化：新增 engine_type 校验调用 + execution_stage 字段，
       全部原响应字段保留，无字段删除或重命名：通过

【契约对齐】
  C1 – engine_type 限定 tqsdk/local，默认 None→tqsdk，与 api.md §6.2.1 一致：通过
  C2 – schema_version="formal_report_v1" ✓；job / summary / transaction_costs /
       risk_events / artifacts 主字段均存在 ✓；但 job.strategy_id 字段在契约
       §6.2.3 最小示例中存在而报告实现中缺失（MVP 阶段未绑定 strategy_template）；
       当前可接受，须在批次 D/E 中补全：有保留通过
  C3 – 批次 C MVP 不产生 risk_events（空列表），不存在格式违规：通过

【代码质量】
  D1 – 无硬编码凭证、无 SQL 查询（无注入面）、无用户路径拼接（无路径穿越）：OK
  D2 – equity_curve 内存列表随回测窗口线性增长，超长期回测可能 OOM；
       _JOB_STORE 先写后限的非原子逻辑为批次 A 遗留，不新引入；SMA 窗口
       内层切片为 O(n·k)，MVP 数据量下可接受：WARN
  D3 – ValueError / EngineTypeError 显式抛出，API 层统一捕获转 HTTPException，
       无静默吞掉异常路径：OK

【关键发现】
  1. 流程保留：shared/contracts/backtest/api.md §6.2 全部内容（批次 A 成果）
     尚处于未提交状态，需在批次 C 独立提交前先独立提交批次 A。
  2. 工程保留（B2）：artifacts.equity_curve = None；建议批次 D/F 在
     _simulate() 返回 equity_curve 后将其写入 artifacts（可序列化为 base64
     或 inline list），以满足 formal_report_v1 完整性要求。
  3. 契约保留（C2）：job.strategy_id 字段缺失；建议批次 D 在接入 strategy_template
     后同步补全；批次 C MVP 阶段引擎使用内置 EMA5/20 策略，无外部 strategy_id，
     可临时填写 "local_ema_crossover_v1" 作为占位。

【锁回授权】是
【备注】18 个测试全部通过；核心功能（双引擎路由、local 引擎执行、API 分发）均已闭环；
        三条保留项均属 MVP 工程范围内的可接受延迟，不阻塞批次 C 锁回。
        批次 D 启动前必须先补全批次 A commit，再正式锁回批次 C。
```

---

## 批次 E 补充预审收口与执行留痕（2026-04-07）

### 当前收口结论

1. 历史单文件 token `tok-06e8df29-1d9f-42e6-9df8-9f87bb10d98d` 仅对应早前单文件白名单与阻断结论，当前不再作为批次 E 的有效执行口径。
2. 基于当前工作树真实状态，批次 E 代码面已实际落在以下两文件：
     - `services/backtest/backtest_web/app/agent-network/page.tsx`
     - `services/backtest/src/api/routes/backtest.py`
3. 因此，批次 E 在补充预审阶段已先从 `pending_reissue` 收口为“待架构终审 / 待终审锁回”；当前已由 Atlas 完成正式 lockback，状态切换为 `locked`。
4. 批次 E 当前执行留痕 token 为 `tok-12cffb12-0149-4aa8-90c0-7011297f77ec`，review-id 继续挂 `REVIEW-TASK-0018-E`；lockback 摘要为“批次E终审通过；两文件白名单边界合规，允许锁回。”；当前最小有效业务白名单即上述两文件。

### 当前代码面收口

1. `services/backtest/backtest_web/app/agent-network/page.tsx` 已提供显式 `tqsdk/local` 引擎选择器，并在单策略回测、批量回测、策略列表快速回测统一透传 `engine_type`。
2. 同文件已把当前策略摘要、运行中任务卡片、策略列表“最新回测”位置的引擎来源做可视化回显，默认引擎可见可审计。
3. `services/backtest/src/api/routes/backtest.py` 已声明 `BacktestRunPayload.engine_type`，并通过 `EngineRouter.validate_engine_type()` 统一校验。
4. 同文件当前已形成双路径收口：`engine_type=tqsdk` 保持既有异步正式引擎行为不回归；`engine_type=local` 走 `EngineRouter.route_local(LocalBacktestParams(...))`，并把 `source=local_backtest_engine`、`payload.engine_type=local`、`execution_profile.engine_type=local`、`report.job.engine_type=local` 写回兼容层结果与报告。

### 当前自校验与非阻断项

1. 两个业务文件当前静态诊断均为 0 errors。
2. 本地 local 冒烟已通过：兼容层 `POST /api/backtest/run` 传 `engine_type=local` 后，结果详情与报告均可读到 `local` 引擎来源字段。
3. 现存 `pytest services/backtest/tests/test_formal_report_api.py -q` 失败点仍为既有断言要求 `tqsdk` 路径同步返回 `completed`，与本轮 `local` 引擎接入不构成同一阻断项；当前记为非阻断遗留，不影响本次补充预审收口。

### 补充预审冻结：真正未闭环范围

1. 批次 B 真正未闭环范围冻结为 `services/data/src/**` + `services/data/tests/**` 的最小只读 API，仅限 `health`、`version`、`symbols`、`bars` 四类接口，不得膨胀为策略逻辑、缓存治理或跨服务直读。
2. 批次 C 真正未闭环范围冻结为补充范围，最小业务文件仅 `services/backtest/src/backtest/local_engine.py` 与 `services/backtest/src/api/routes/backtest.py`，用途限定为“ApiDataProvider + YAML 驱动本地成交回测”；该补充范围不复用已锁回的批次 C 主白名单。
3. 3 年分钟 K 执行口径冻结如下：`requested_symbol` 可继续记录用户 YAML 中的 `DCE.p2605`；但 `executed_data_symbol` 必须切换为 Mini 上有完整时间区间的 p 品种连续主力 `KQ_m_DCE_p` / `DCE.p` 连续主力，以完成 `2023-04-03` 至 `2026-04-03` 的 3 年回测；结果页、报告导出与后续契约字段必须避免把连续主力执行误写成“直接使用 `DCE.p2605` 完整 3 年分钟数据”。

### 当前状态

1. 批次 E：locked（lockback 已完成，review-id=`REVIEW-TASK-0018-E`，摘要“批次E终审通过；两文件白名单边界合规，允许锁回。”）。
2. 批次 B：locked（replacement token=`tok-040a489d-5546-4be4-abd1-4cc5cb4758fe`，review-id=`REVIEW-TASK-0018-B`，lockback=approved；摘要“TASK-0018-B 完成最小实施与终审留证据，自校验通过，执行锁回”；白名单=`services/data/src/main.py`、`services/data/tests/test_main.py`）。
3. 批次 C 补充范围：pending_lockback（review-id=`REVIEW-TASK-0018-C-SUP`；当前执行口径以 3 天窗口 replacement active token 为准，完整 token_id 待 Atlas 锁回时回填；历史初始 token=`tok-bfd51a47-63e2-40a5-aa62-25e705a75584` 已降为 validate 留痕；白名单=`services/backtest/src/backtest/local_engine.py`、`services/backtest/src/api/routes/backtest.py`、`services/backtest/tests/test_local_engine_generic.py`）。

---

## 批次 E 终审（2026-04-07）

### 终审基本信息

1. 终审时间：2026-04-07
2. review-id：`REVIEW-TASK-0018-E`
3. 对应执行 token：`tok-12cffb12-0149-4aa8-90c0-7011297f77ec`
4. 审核范围：仅 `services/backtest/backtest_web/app/agent-network/page.tsx` 与 `services/backtest/src/api/routes/backtest.py`
5. 终审结论：✅ 通过（approved）

### 边界合规

1. 白名单边界通过：当前业务 diff 仅落在 `services/backtest/backtest_web/app/agent-network/page.tsx` 与 `services/backtest/src/api/routes/backtest.py` 两文件，未发现第 3 个业务文件进入本批次实现面。
2. 服务边界通过：本批仅发生在 `services/backtest/**` 单服务内，未发现跨服务 import、跨目录读写或 shared/contracts 漂移。
3. token 口径通过：历史单文件 token `tok-06e8df29-1d9f-42e6-9df8-9f87bb10d98d` 已按补审结论退役；当前执行留痕与终审继续绑定 `tok-12cffb12-0149-4aa8-90c0-7011297f77ec` + `REVIEW-TASK-0018-E`，账本口径一致。
4. 终审范围通过：本次仅做两文件代码核验与 P-LOG 留痕，不重开测试白名单，不扩展到 `services/backtest/tests/**` 或其他后端文件。

### 验收项

1. 显式引擎选择通过：`page.tsx` 已提供可见的 `tqsdk/local` 选择器，默认值为 `tqsdk`，且当前策略摘要区同步回显引擎选择，满足“显式默认值、可审计”的验收要求。
2. `engine_type` 透传通过：单策略保存后回测、批量回测、策略列表快速回测三类入口均通过前端 payload 显式透传 `engine_type`。
3. compat route 分流通过：`backtest.py` 已把 `BacktestRunPayload.engine_type` 纳入兼容层请求模型，并通过 `EngineRouter.validate_engine_type()` 收口 `local/tqsdk` 分流；`tqsdk` 路径继续保持异步正式引擎行为，未发生回归性改写。
4. 结果来源回写通过：`local` 路径结果已稳定写回 `source=local_backtest_engine`、`payload.engine_type=local`、`execution_profile.engine_type=local`，且报告中的 `job.engine_type=local` 可由 `/api/backtest/results/{task_id}/report` 直接导出。
5. 详情与报告链路通过：详情接口直接返回带引擎来源的完整结果对象；报告接口在 `report_path` 不存在时会回退到内存中的 `formal_report`，满足 local 场景最小报告导出闭环。
6. 自校验证据通过：两文件 VS Code 静态诊断为 0 errors；local smoke 已证明 `/api/backtest/run` 传 `engine_type=local` 后，详情与报告均保留 local 引擎来源字段。

### 非阻断遗留

1. `pytest services/backtest/tests/test_formal_report_api.py -q` 仍有 1 个既有失败，根因是旧断言要求 `tqsdk` 路径同步返回 `completed`，而当前兼容层基线仍为异步 `running`；该失败不由本批次 E 引入，也不阻断本批次终审。
2. 批次 B 与批次 C 补充范围已切换为 `active` 并进入后续实施阶段；它们属于 E 之后的继续闭环范围，不影响当前批次 E 的前后端选择器与 compat route 闭环成立。

### 锁回授权

1. Atlas 是否已执行 lockback：是。
2. 当前批次状态：`locked`。
3. 说明：正式 `locked` 口径已完成回写；锁回摘要为“批次E终审通过；两文件白名单边界合规，允许锁回。”。

---

## 批次 B 终审（2026-04-09）

### 终审基本信息

1. 终审时间：2026-04-09
2. review-id：`REVIEW-TASK-0018-B`
3. 当前有效执行 token：`tok-040a489d-5546-4be4-abd1-4cc5cb4758fe`
4. 历史 token：`tok-9ef072bb-776e-4e02-a814-7072fa63c836` 已退化为历史留痕，不再作为当前执行口径。
5. 终审范围：仅 `services/data/src/main.py` 与 `services/data/tests/test_main.py`

### 实际实施收口

1. `services/data/src/main.py` 已把 Python 3.10 风格的 `str | None` 收口为 `Optional[str]`，修复 Python 3.9.6 下导入失败问题。
2. `services/data/tests/test_main.py` 已把版本断言改为读取 `SERVICE_NAME` 与 `SERVICE_VERSION` 常量，避免硬编码漂移。

### 验证证据

1. 本地静态诊断：`services/data/src/main.py` 与 `services/data/tests/test_main.py` 均为 `No errors found`。
2. 本地测试：在 `/Users/jayshao/JBT` 执行 `pytest services/data/tests/test_main.py -q`，结果 `4 passed in 0.95s`。

### 终审结论

1. 白名单边界通过：未发现超出 `services/data/src/main.py` 与 `services/data/tests/test_main.py` 的业务改动。
2. 契约治理通过：未发现 `shared/contracts/**` 漂移或跨服务契约越界。
3. 行为回归检查通过：本次兼容性修复与测试收口未发现新的行为回退。
4. 当前执行口径已切换到 replacement token `tok-040a489d-5546-4be4-abd1-4cc5cb4758fe`，review-id 继续使用 `REVIEW-TASK-0018-B`。
5. 终端 lockback 事实已确认：`review-id=REVIEW-TASK-0018-B`、`token=tok-040a489d-5546-4be4-abd1-4cc5cb4758fe`、`summary=TASK-0018-B 完成最小实施与终审留证据，自校验通过，执行锁回`、`result=approved`，exit code=0。
6. 当前状态为 `locked`；本批次不再保留 `pending_lockback` 口径。

---

## 批次 C 补充范围终审（2026-04-09）

### 终审基本信息

1. 终审时间：2026-04-09
2. review-id：`REVIEW-TASK-0018-C-SUP`
3. 当前执行口径：3 天窗口 replacement active token 已到位，完整 token_id 待 Atlas 锁回时回填；2026-04-07 初始 token `tok-bfd51a47-63e2-40a5-aa62-25e705a75584` 仅保留为历史 validate 留痕。
4. 终审范围：仅 `services/backtest/src/backtest/local_engine.py`、`services/backtest/src/api/routes/backtest.py`、`services/backtest/tests/test_local_engine_generic.py`

### 只读复核与验证证据

1. 白名单 3 文件当前无未提交差异，未见白名单外污染。
2. 3 文件静态诊断当前无错误。
3. 本地执行 `pytest services/backtest/tests/test_local_engine_generic.py -q`，结果 `3 passed`。
4. 本轮未新增代码写入；终审基于当前仓内实现与回测 Agent 自校验事实完成。

### 能力收口确认

1. `local_engine.py` 在未传 `strategy_yaml_filename` 时继续保留无 YAML 的 MVP fallback。
2. 传入 `strategy_yaml_filename` 后，local 路径已切换为 data API 真数据 + YAML 驱动的本地成交回测链路。
3. `requested_symbol`、`executed_data_symbol` 与 `source_kind` 已进入结果与报告留痕，满足 3 年分钟 K 执行口径的可追溯要求。
4. compat route 的 `engine_type=local` 路径已接入 `ApiDataProvider`，与补充范围目标一致。

### 终审结论

1. 白名单边界通过：未发现超出 3 文件范围的业务污染或跨服务 import。
2. 行为口径通过：补充范围要求的 `ApiDataProvider + YAML 驱动本地成交回测 + 请求/执行标的区分留痕` 已闭环。
3. 当前执行口径应以 3 天窗口 replacement active token 为准；因本次未取得完整 replacement token_id，账本不虚构，待 Atlas 实际 lockback 时回填。
4. 当前状态为 `pending_lockback`，结论 **通过，可 lockback**；仍待 Atlas 执行最后 lockback 动作。
