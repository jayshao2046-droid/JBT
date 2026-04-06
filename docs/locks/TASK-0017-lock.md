# TASK-0017 Lock 记录

## Lock 信息

- 任务 ID：TASK-0017
- 阶段：sim-trading Docker 化与 Mini 部署预审
- 当前任务是否仍处于“预审未执行”状态：是
- 执行 Agent：
  - 项目架构师（当前 P-LOG 治理文件）
  - 对应服务 Agent（后续仓内 Docker 文件实现）
  - Atlas（后续远端 Mini 运维执行，但需 Jay.S 明确授权）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `services/sim-trading/**` / `services/dashboard/**` 中 Docker 相关文件：后续 P1 Token
  - `docker-compose.dev.yml`：后续 P0 Token
  - 各服务 `.env.example`：后续 P0 Token
  - 远端 Mini 运维动作：不适用 Git Token，但必须有 Jay.S 明确运维授权

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0017-sim-trading-Docker化与Mini部署预审.md`
2. `docs/reviews/TASK-0017-review.md`
3. `docs/locks/TASK-0017-lock.md`
4. `docs/rollback/TASK-0017-rollback.md`
5. `docs/handoffs/TASK-0017-Docker与Mini部署预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 当前锁定范围

1. `services/sim-trading/**`
2. `services/dashboard/**`
3. `docker-compose.dev.yml`
4. `services/sim-trading/.env.example`
5. `services/dashboard/.env.example`
6. 远端 Mini 的容器启停、镜像切换、Secret 注入与回滚验证动作
7. 其他全部非白名单文件

## 当前继续禁止修改的路径说明

1. 禁止把本任务与 `TASK-0011` legacy 清退混并。
2. 禁止在没有文件级白名单的情况下修改任何服务 Docker 文件或根级 compose。
3. 禁止把真实 Secret 烘焙进镜像、compose、`.env.example` 或治理账本。
4. 禁止在未获 Jay.S 明确授权前执行任何远端 Mini 运维动作。

## 进入执行前需要的 Token / 授权

1. `TASK-0009`、`TASK-0013`、`TASK-0010`、`TASK-0014`、`TASK-0015`、`TASK-0016` 的前置条件必须先满足。
2. 需要先冻结服务 Docker 文件、`docker-compose.dev.yml` 与 `.env.example` 的分批文件级白名单，再由 Jay.S 签发 P1 / P0 Token。
3. Jay.S 还需确认 Mini 部署窗口、远端 Secret 注入方案与是否同时包含 `services/dashboard/**` 部署。
4. Atlas 在执行远端步骤前，必须先获得逐条运维授权。

## 当前状态

- 预审状态：已通过
- Token 状态：未申请代码 Token
- 解锁时间：N/A
- 失效时间：N/A
- 锁回时间：N/A
- lockback 结果：尚未进入代码执行或远端运维阶段

## 结论

**TASK-0017 当前仍处于“预审未执行”状态；仓内 Docker 路径、根级 compose、服务环境模板与远端 Mini 运维动作继续锁定。**