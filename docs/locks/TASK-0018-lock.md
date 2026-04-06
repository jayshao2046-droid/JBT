# TASK-0018 Lock 记录

## Lock 信息

- 任务 ID：TASK-0018
- 阶段：D201 建档预审
- 当前状态：pending_token
- 执行 Agent：
  - 项目架构师（当前建档）
  - 数据 Agent（批次 B）
  - 回测 Agent（批次 C/D/E/F）
- 说明：本文件仅登记批次级白名单模板，不记录虚构 token_id。

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

- 状态：pending_token
- 保护路径：`services/data/**`
- 白名单模板示例：
  1. `services/data/src/**`
  2. `services/data/tests/**`
- token_id：pending

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

- 状态：pending_token
- 保护路径：`services/backtest/backtest_web/**`
- 白名单模板示例：
  1. `services/backtest/backtest_web/app/**`
  2. `services/backtest/backtest_web/src/**`
- token_id：pending

### 批次 F（P1，完整报告导出与展示）

- 状态：pending_token
- 保护路径：`services/backtest/**`、`services/backtest/backtest_web/**`
- 白名单模板示例：
  1. `services/backtest/src/**`
  2. `services/backtest/tests/**`
  3. `services/backtest/backtest_web/src/**`
  4. `services/backtest/backtest_web/app/**`
- token_id：pending

## 当前锁定范围

1. `shared/contracts/**`（批次 A 解锁前保持锁定）
2. `services/data/**`（批次 B 解锁前保持锁定）
3. `services/backtest/**`（批次 C/D/F 解锁前保持锁定）
4. `services/backtest/backtest_web/**`（批次 E/F 解锁前保持锁定）
5. 所有非白名单文件保持锁定

## 统一阻断规则

1. 无有效 Token，不得写保护区。
2. 批次外文件不得改动。
3. 若新增文件需求，必须回交补充预审并更新白名单。
4. 每批完成后必须锁回，再进入下一批。
