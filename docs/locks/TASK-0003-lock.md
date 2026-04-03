# TASK-0003 Lock 记录

## Lock 信息

- 任务 ID：TASK-0003
- 执行 Agent：
  - 项目架构师（P-LOG 区账本 + P0 区契约，阶段一）
  - 回测 Agent（P1 区服务代码，阶段二 批次A/B/C；阶段三看板联调）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `shared/contracts/drafts/backtest/`（草稿区）：当前已完成，无需 Token
  - `shared/contracts/backtest/`（P0 区）：**需要 Jay.S 为项目架构师签发 P0 Token**
  - `services/backtest/src/`（P1 区，批次 A 5 文件）：**需要 Jay.S 为回测 Agent 签发 P1 Token**
  - `services/backtest/src/`（P1 区，批次 B 5 文件）：**需要单独 P1 Token**
  - `services/backtest/` 部署文件（P1 区，批次 C）：**需要单独 P1 Token**
  - `docker-compose.dev.yml`（P0 区）：**批次 C 前，需要 Jay.S 单独 P0 Token**
  - `services/backtest/.env.example`（P0 区）：**Q2 确认后，需要 Jay.S 单独 P0 Token**

- 白名单文件（当前阶段：建档 + 草稿区）：
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

- 白名单文件（阶段一正式迁移，待 P0 Token）：
  - `shared/contracts/backtest/backtest_job.md`
  - `shared/contracts/backtest/backtest_result.md`
  - `shared/contracts/backtest/performance_metrics.md`
  - `shared/contracts/backtest/api.md`

- 白名单文件（阶段二批次 A，待 P1 Token）：
  - `services/backtest/src/main.py`
  - `services/backtest/src/api/app.py`
  - `services/backtest/src/api/routes/health.py`
  - `services/backtest/src/api/routes/jobs.py`
  - `services/backtest/src/core/settings.py`
  - `services/backtest/README.md`（口径修正，随批次 A 一并执行）

- 白名单文件（阶段二批次 B，待单独 P1 Token）：
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
- 锁回时间：待填写（分批次锁回）
- P0 Token 签发时间（契约迁移）：待 Jay.S 提供
- 批次 A P1 Token 签发时间：待 Jay.S 确认 Q1 后提供
- 当前状态：阶段一草稿与自校验已完成，P0 正式写入待 Token；Q1～Q5 待 Jay.S 确认

## 说明

TASK-0003 为多阶段、多批次任务，Token 需按批次独立签发。每批次完成后需单独提交、终审、锁回，再由项目架构师申请下一批次 Token。不得跨批次混并写入。
