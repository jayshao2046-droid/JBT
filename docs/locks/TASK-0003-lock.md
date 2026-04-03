# TASK-0003 Lock 记录

## Lock 信息

- 任务 ID：TASK-0003
- 执行 Agent：
  - 项目架构师（P-LOG 区账本 + P0 区契约，阶段一）
  - 回测 Agent（P1 区服务代码，阶段二 批次A/B/C；阶段三看板联调）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `shared/contracts/drafts/backtest/`（草稿区）：当前已完成，无需 Token
  - `shared/contracts/backtest/`（P0 区）：Jay.S 已为项目架构师签发文件级 P0 Token；token_id `tok-361fbc06-5016-4250-a7b0-38d167c21340`，签发日期 2026-04-03，文件范围限 `backtest_job.md`、`backtest_result.md`、`performance_metrics.md`、`api.md`
  - `services/backtest/` 批次 A 六文件（P1 区）：Jay.S 已为回测 Agent 签发文件级 P1 Token；token_id 摘要 `tok-311d1a36-0cff-4141-939a-e96acadb9a38`，签发时间 2026-04-03 17:49，文件范围限 `main.py`、`app.py`、`health.py`、`jobs.py`、`settings.py` 与 `README.md`
  - `services/backtest/src/`（P1 区，批次 B 5 文件）：Jay.S 已为回测 Agent 签发文件级 P1 Token；token_id 摘要 tok-60193dc1-e1be-459b-8133-c49e454adc0c，签发日期 2026-04-03，文件范围限 `session.py`、`runner.py`、`strategy_base.py`、`result_builder.py`、`tests/test_health.py`
  - `services/backtest/` 部署文件（P1 区，批次 C）：**需要单独 P1 Token**
  - `docker-compose.dev.yml`（P0 区）：**批次 C 前，需要 Jay.S 单独 P0 Token**
  - `services/backtest/.env.example`（P0 区）：**D-BT-02 授权，Phase1 建档中由架构师直接更新，已完成** ✅

- 白名单文件（当前阶段：建档 + 草稿区 + Phase1 建档授权）：
  - `docs/tasks/TASK-0003-backtest-Phase1-正式建档.md`（新增）
  - `docs/tasks/TASK-0003-backtest-全开发任务拆解与契约登记.md`
  - `docs/reviews/TASK-0003-review.md`
  - `docs/locks/TASK-0003-lock.md`
  - `docs/rollback/TASK-0003-rollback.md`
  - `docs/handoffs/TASK-0003-回测全开发阶段一预审与启动交接.md`
  - `docs/prompts/公共项目提示词.md`
  - `docs/prompts/agents/项目架构师提示词.md`
  - `shared/contracts/drafts/backtest/backtest_job.md`
  - `shared/contracts/drafts/backtest/backtest_result.md`
  - `shared/contracts/drafts/backtest/performance_metrics.md`
  - `shared/contracts/drafts/backtest/api.md`
  - `services/backtest/.env.example`（P0，D-BT-02 授权，架构师执行）✅

- 白名单文件（阶段一正式迁移，P0 Token 已签发并执行中）：
  - `shared/contracts/backtest/backtest_job.md`
  - `shared/contracts/backtest/backtest_result.md`
  - `shared/contracts/backtest/performance_metrics.md`
  - `shared/contracts/backtest/api.md`

- 白名单文件（阶段二批次 A，P1 Token 已执行并已锁回）：
  - `services/backtest/src/main.py`
  - `services/backtest/src/api/app.py`
  - `services/backtest/src/api/routes/health.py`
  - `services/backtest/src/api/routes/jobs.py`
  - `services/backtest/src/core/settings.py`
  - `services/backtest/README.md`（口径修正，随批次 A P1 Token 一并执行）

- 白名单文件（阶段二批次 B，P1 Token 已执行并已锁回）：
  - `services/backtest/src/backtest/session.py`
  - `services/backtest/src/backtest/runner.py`
  - `services/backtest/src/backtest/strategy_base.py`
  - `services/backtest/src/backtest/result_builder.py`
  - `services/backtest/tests/test_health.py`

- 白名单文件（阶段二批次 C，待 P1 + 部分 P0 Token）：
  - `services/backtest/Dockerfile`（P1）
  - `services/backtest/requirements.txt`（P1）
  - `services/backtest/configs/logging.yaml`（P1）
  - `services/backtest/configs/backtest.default.yaml`（P1）
  - `services/backtest/.env.example`（P0，单独 Token）
  - `docker-compose.dev.yml`（P0，单独 Token）

- 解锁时间：2026-04-03（建档与草稿区当批即解锁）
- 失效时间：TASK-0003 全部阶段终审通过后逐批锁回
- 锁回时间：2026-04-03（批次 A、P0 契约与批次 B 均已锁回）
- lockback 结果（批次 A）：`locked`
- lockback review-id（批次 A）：`REVIEW-TASK-0003-P1A`
- lockback 摘要（批次 A）：`TASK-0003 批次A完成，终审通过，执行锁回`
- P0 Token 签发时间（契约迁移）：2026-04-03
- P0 契约 lockback 时间（阶段一正式迁移）：2026-04-03 19:01:15 +0800
- P0 契约 lockback review-id：`REVIEW-TASK-0003-P0`
- P0 契约 lockback 摘要：`TASK-0003 backtest 正式契约迁移完成，终审通过，执行锁回`
- P0 契约 lockback 结果：事件结果 `approved`，Token 当前状态 `locked`
- 批次 A P1 Token 签发时间：2026-04-03 17:49
- 批次 B P1 Token 签发时间：2026-04-03
- 批次 B P1 lockback 时间：2026-04-03 19:01:15 +0800
- 批次 B P1 lockback review-id：`REVIEW-TASK-0003-P1B`
- 批次 B P1 lockback 摘要：`TASK-0003 批次B完成，达到策略介入点，执行锁回`
- 批次 B P1 lockback 结果：事件结果 `approved`，Token 当前状态 `locked`
- 当前状态：批次 A、P0 正式契约与批次 B 均已完成并锁回；回测主线已正式收口到 60%，当前只等待 Jay.S 提供首轮真实策略模板实现与配套一体化 YAML 文件；看板、Docker、远端交付继续后置

## 说明

TASK-0003 为多阶段、多批次任务，Token 需按批次独立签发。每批次完成后需单独提交、终审、锁回，再由项目架构师申请下一批次 Token。不得跨批次混并写入。

回测 Agent 在本轮同步更新 `docs/prompts/agents/回测提示词.md` 并提交 `docs/handoffs/TASK-0003-回测批次A-后端骨架交接.md`、`docs/handoffs/TASK-0003-回测批次B-在线回测引擎交接.md`，均属于 P-LOG 区自有文件，不计入 P1 Token 越权。

## 执行记录（变更）

- 2026-04-03：Jay.S 批准 TASK-0003 进入正式建档，D-BT-01~05 已登记到账本。
- 2026-04-03：Jay.S 已签发 TASK-0003 backtest 正式契约迁移 P0 Token，token_id `tok-361fbc06-5016-4250-a7b0-38d167c21340`，文件范围限 `shared/contracts/backtest/` 下四份正式契约。
- 2026-04-03：项目架构师已同步 TASK-0003 task / review / lock / 公共项目提示词 / 私有提示词，确认 Q1 与 Q-NEW 均已解除阻塞并进入执行态。
- 2026-04-03：已完成 `shared/contracts/backtest/backtest_job.md`、`backtest_result.md`、`performance_metrics.md`、`api.md` 四份正式契约迁移。
- 2026-04-03：已完成最小自校验，确认四份正式契约与 drafts 主体字段/端点口径一致，且 `api.md` 未引入未建档的跨服务实现细节。
- 2026-04-03 17:49：Jay.S 已签发 TASK-0003 批次 A P1 Token，token_id 摘要 `tok-311d1a36-0cff-4141-939a-e96acadb9a38`，文件范围限批次 A 六个白名单文件。
- 2026-04-03 17:59：回测 Agent 已完成批次 A 六文件写入并提交 handoff。
- 2026-04-03：项目架构师终审确认：无白名单外服务代码写入，D-BT-01~05 未违反，`jobs.py` 与 `README.md` 口径一致，可执行 lockback。
- 2026-04-03：Atlas 已执行 TASK-0003 批次 A lockback，review-id `REVIEW-TASK-0003-P1A`，summary `TASK-0003 批次A完成，终审通过，执行锁回`，终端结果为 `locked`。
- 2026-04-03：项目架构师终审确认：P0 正式契约与 drafts 一致，已体现“固定模板 + 用户上传参数 + 一体化 YAML 风控文件”，未引入未建档跨服务实现细节，可立即执行 P0 lockback。
- 2026-04-03：Jay.S 已签发 TASK-0003 批次 B P1 Token，token_id 摘要 tok-60193dc1-e1be-459b-8133-c49e454adc0c，文件范围限批次 B 五个白名单文件。
- 2026-04-03：回测 Agent 已完成批次 B 五文件写入并提交 handoff；本地自校验通过，pytest 结果 3 passed。
- 2026-04-03：项目架构师终审确认：批次 B 未越权写入白名单外服务文件，未进入看板 / Docker / 远端交付，D-BT-01~05 未违反，当前已达到“需要策略输入”检查点，可立即执行批次 B lockback。
- 2026-04-03 19:01:15 +0800：Atlas 已执行 TASK-0003 P0 契约 lockback，review-id `REVIEW-TASK-0003-P0`，summary `TASK-0003 backtest 正式契约迁移完成，终审通过，执行锁回`；lockback 事件结果为 `approved`，Token 当前状态为 `locked`。
- 2026-04-03 19:01:15 +0800：Atlas 已执行 TASK-0003 批次 B P1 lockback，review-id `REVIEW-TASK-0003-P1B`，summary `TASK-0003 批次B完成，达到策略介入点，执行锁回`；lockback 事件结果为 `approved`，Token 当前状态为 `locked`。
