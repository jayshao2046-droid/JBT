# TASK-0018 Lock 记录

## Lock 信息

- 任务 ID：TASK-0018
- 阶段：D201 建档预审
- 当前状态：batch_e_locked_b_c_active
- 执行 Agent：
  - 项目架构师（当前建档）
  - 数据 Agent（批次 B）
  - 回测 Agent（批次 C/D/E/F）
- 说明：本文件仅登记批次级白名单模板；对已实际签发的批次记录真实 token 摘要，不记录虚构 token_id。

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0018-backtest-API化重建-Phase1.md`
2. `docs/reviews/TASK-0018-review.md`
3. `docs/locks/TASK-0018-lock.md`
4. `docs/handoffs/TASK-0018-架构预审交接.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

## 批次级白名单模板

### 批次 A（P0，契约）

- 状态：locked
- 保护路径：`shared/contracts/**`
- 白名单模板示例：
  1. `shared/contracts/backtest/api.md`
- token_id：`tok-38d7c21e-36bd-4fe1-a4dc-843178e351dc`

批次 A 执行留痕（2026-04-07）：

1. 执行 Agent：项目架构师
2. 实际业务改动文件：`shared/contracts/backtest/api.md`
3. 已完成内容：`engine_type` 冻结（`tqsdk`/`local`）、系统级风控证据链结构冻结、完整报告导出统一 schema 冻结
4. 最小自校验：仅 1 个业务文件 + 指定治理留痕文件改动，未触碰 `services/**`
5. 当前阶段：等待终审确认后执行 lockback
6. 收口标记：`TASK-0018-A-LOCK-2026-04-07`
7. lockback 结果：approved（review-id: `REVIEW-TASK-0018-A`）

### 批次 B（P1，data 最小只读 API）

- 状态：active
- 保护路径：`services/data/**`
- 当前有效业务白名单：
  1. `services/data/src/main.py`
  2. `services/data/tests/test_main.py`
- 最小能力冻结：只允许 `health`、`version`、`symbols`、`bars` 四类只读 API，不得扩展到策略逻辑、跨服务直读或运行态写入。
- token_id：`tok-9ef072bb-776e-4e02-a814-7072fa63c836`
- review-id：`REVIEW-TASK-0018-B`
- validate：passed（2026-04-07）
- 执行 Agent：数据
- 当前阶段：Token 已签发并通过 validate，可进入代码实施

### 批次 C（P1，backtest 双引擎执行编排层）

- 状态：locked
- 保护路径：`services/backtest/**`
- 白名单文件：
  1. `services/backtest/src/backtest/local_engine.py`（新建）
  2. `services/backtest/src/backtest/engine_router.py`（新建）
  3. `services/backtest/src/api/routes/jobs.py`（修改）
  4. `services/backtest/tests/test_local_engine.py`（新建）
- token_id：`tok-4f7d7a03-e4be-4c40-bc88-493175e8f587`
- 签发时间：2026-04-07
- 执行 Agent：回测
- 终审结论：⚠️ 有保留通过（2026-04-07）
- lockback 结果：approved（review-id: REVIEW-TASK-0018-C）
- 保留项（后续补全）：(1) artifacts.equity_curve=None 待批次 D/F；(2) job.strategy_id 待批次 D/E
- 主批次当前状态：locked
- 补充预审冻结的未闭环范围：
  1. 最小业务白名单：`services/backtest/src/backtest/local_engine.py`、`services/backtest/src/api/routes/backtest.py`、`services/backtest/tests/test_local_engine_generic.py`
  2. 用途限定：`ApiDataProvider + YAML 驱动本地成交回测`
  3. token_id：`tok-bfd51a47-63e2-40a5-aa62-25e705a75584`
  4. review-id：`REVIEW-TASK-0018-C-SUP`
  5. validate：passed（2026-04-07）
  6. 当前状态：active
  7. 说明：该补充范围已完成独立签发与 validate，回测 Agent 可按白名单进入代码实施

### 批次 D（P1，系统级风控联动层）

- 状态：locked
- 保护路径：`services/backtest/**`
- 白名单文件：
  1. `services/backtest/src/backtest/local_engine.py`（修改：equity_curve 序列化 + risk_event 联动）
  2. `services/backtest/src/backtest/risk_engine.py`（新建：统一风控执行层）
  3. `services/backtest/tests/test_risk_engine.py`（新建）
- token_id：`tok-62909012-2bbf-4f38-aa36-0ed247faffb4`
- 签发时间：2026-04-07
- 执行 Agent：回测
- lockback 结果：approved（review-id: REVIEW-TASK-0018-D）
- commit：`4a96c5b`

### 批次 E（P1，backtest_web 引擎选择控件与执行入口）

- 状态：locked
- 保护路径：`services/backtest/backtest_web/**`、`services/backtest/src/api/routes/backtest.py`
- 历史失效 token：`tok-06e8df29-1d9f-42e6-9df8-9f87bb10d98d`
- 当前执行 token：`tok-12cffb12-0149-4aa8-90c0-7011297f77ec`
- review-id：`REVIEW-TASK-0018-E`
- lockback 摘要：`批次E终审通过；两文件白名单边界合规，允许锁回。`
- 当前实际业务白名单：
  1. `services/backtest/backtest_web/app/agent-network/page.tsx`
  2. `services/backtest/src/api/routes/backtest.py`
- 当前代码收口：
  1. `page.tsx` 已提供显式引擎选择器，并在单策略、批量、快速回测入口统一透传 `engine_type`
  2. `backtest.py` 已接入 `BacktestRunPayload.engine_type`、`EngineRouter.validate_engine_type()` 与 `local/tqsdk` 双路径收口
  3. `local` 路径结果与报告当前可写回 `source=local_backtest_engine`、`payload.engine_type`、`execution_profile.engine_type`、`job.engine_type`
- 自校验留痕：
  1. 两个业务文件静态诊断为 0 errors
  2. local 冒烟已通过，兼容层 `/api/backtest/run` 可返回 `engine_type=local` 并在详情 / 报告中保留引擎来源
  3. `pytest services/backtest/tests/test_formal_report_api.py -q` 现存 1 个既有失败，原因为 `tqsdk` 路径同步返回 `completed` 的旧断言，与本批 `local` 接入不构成同一阻断
- 终审结论：approved（2026-04-07）
- 非阻断遗留：`pytest services/backtest/tests/test_formal_report_api.py -q` 的 1 个既有失败继续保留，不阻断批次 E 锁回
- Token 口径结论：
  1. `tok-06e8df29-1d9f-42e6-9df8-9f87bb10d98d` 不再作为当前有效执行口径，仅保留为历史失效留痕
  2. `tok-12cffb12-0149-4aa8-90c0-7011297f77ec` 为批次 E 当前执行留痕 token
  3. lockback review-id：`REVIEW-TASK-0018-E`
  4. lockback 已执行：是
  5. 当前阶段：Atlas 已完成正式 lockback；当前状态 `locked`

### 批次 F（P1，完整报告导出与展示）

- 状态：pending_token
- 保护路径：`services/backtest/**`、`services/backtest/backtest_web/**`
- 白名单模板示例：
  1. `services/backtest/src/**`
  2. `services/backtest/tests/**`
  3. `services/backtest/backtest_web/src/**`
  4. `services/backtest/backtest_web/app/**`
- token_id：pending

## 补充执行口径冻结（2026-04-07）

1. 3 年分钟 K 回测场景中，`requested_symbol` 可继续来自用户 YAML 的 `DCE.p2605`。
2. 实际执行数据口径必须切换为 Mini 上具备完整区间的 p 品种连续主力 `KQ_m_DCE_p` / `DCE.p` 连续主力，覆盖 `2023-04-03` 至 `2026-04-03`。
3. 结果页、报告导出与后续契约字段必须显式区分 `requested_symbol` 与 `executed_data_symbol`，不得误导为“直接使用 `DCE.p2605` 完整 3 年分钟数据回测”。

## 当前锁定范围

1. `shared/contracts/**`（批次 A 解锁前保持锁定）
2. `services/data/**` 中除批次 B 当前 active 白名单 `services/data/src/main.py`、`services/data/tests/test_main.py` 外，其余保持锁定
3. `services/backtest/**` 中除批次 C 补充范围当前 active 白名单 `services/backtest/src/backtest/local_engine.py`、`services/backtest/src/api/routes/backtest.py`、`services/backtest/tests/test_local_engine_generic.py` 外，其余保持锁定
4. `services/backtest/backtest_web/**` 当前因批次 E 已锁回、批次 F 未解锁，全部保持锁定
5. 所有非白名单文件保持锁定

## 统一阻断规则

1. 无有效 Token，不得写保护区。
2. 批次外文件不得改动。
3. 若新增文件需求，必须回交补充预审并更新白名单。
4. 每批完成后必须锁回，再进入下一批。
