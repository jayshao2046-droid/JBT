# TASK-0017 Docker 与 Mini 部署预审交接单

【签名】项目架构师
【时间】2026-04-06
【设备】MacBook

## 任务结论

1. `TASK-0017` 已完成预审建档与第二轮治理账本补齐。
2. Docker 化与 Mini 部署已与 `TASK-0011` 的 legacy 清退边界分离。
3. 当前轮次只完成治理冻结，不进入仓内 Docker 实现或远端运维执行。

## 该任务交给谁执行

1. 仓内 Docker / 启动脚本实现：对应服务 Agent。
2. 根级 compose 与环境模板批次：按 P0 路径独立执行。
3. 远端 Mini 运维执行：Atlas，但仅在 Jay.S 明确逐条授权后。

## 执行前置依赖

1. `TASK-0009`、`TASK-0013`、`TASK-0010`、`TASK-0014`、`TASK-0015`、`TASK-0016` 必须先满足部署前置条件。
2. Jay.S 必须确认 Mini 部署窗口。
3. 需要先明确远端 Secret 注入方案与回滚点保留方案。
4. 需要先冻结服务 Docker 文件、`docker-compose.dev.yml` 与 `.env.example` 的文件级白名单。

## 不得跨越的边界

1. 不得把本任务与 `TASK-0011` legacy 清退混并。
2. 不得把服务 Docker 文件、根级 compose、`.env.example` 与远端 Mini 运维动作混成一个提交或一次执行。
3. 不得把任何真实 Secret 烘焙进镜像、compose、`.env.example` 或治理账本。
4. 未获 Jay.S 明确授权前，Atlas 不得执行任何远端 Mini 命令。

## 进入执行前 Atlas / Jay.S / 对应 Agent 还需完成什么

### Atlas

1. 先把服务 Docker 文件、`docker-compose.dev.yml`、`.env.example` 和远端 Mini 运维拆成四类清单。
2. 未完成拆批和授权前，不得执行任何终端命令或部署动作。

### Jay.S

1. 确认 Mini 部署窗口与远端 Secret 注入方式。
2. 确认是否将 `services/dashboard/**` 与 `services/sim-trading/**` 同轮纳入部署。
3. 在远端执行前明确回滚点要求和容器命名口径。

### 对应 Agent

1. 提交服务 Docker 文件与启动脚本的文件级白名单申请。
2. 提交本地最小健康检查、只减仓、最小通知与回滚验证计划。
3. 每完成一动作同步私有 prompt 与 handoff。

## 当前授权状态

1. `TASK-0017-A1` / `A2` / `A3` 已完成实施、终审与锁回；当前扩展批次仅 `TASK-0017-A4` 为 `pending_token`。
2. 当前不允许 reopen `docker-compose.dev.yml`、任一 `.env.example` 或远端 Mini 运维动作。

## 向 Atlas 汇报摘要

1. `TASK-0017` 的 review / lock / rollback / handoff 已补齐。
2. Docker / compose / `.env.example` / 远端 Mini 的拆批与边界已冻结。
3. 当前仍是“预审未执行”状态，需等待前置依赖、P0 / P1 Token 与 Jay.S 的远端运维授权。

## 下一步建议

1. 先按 `TASK-0017-A4` 收口本地 clean pre-deploy / 假交互去伪。
2. `TASK-0022-B` 必须等待 `TASK-0017-A4` 与 `TASK-0014-A4` 锁回后再签发。
3. 未获授权前，不 reopen `docker-compose.dev.yml`、`.env.example` 或任何远端 Mini 命令。

## 九、2026-04-09 扩展预审更新（以本节为准）

1. 本轮“sim-trading 清理 / 本地 clean pre-deploy”继续复用 `TASK-0017`，不新开任务号。
2. 新增 `TASK-0017-A4`：`services/sim-trading/sim-trading_web/app/operations/page.tsx` + `app/intelligence/page.tsx`，保护级别 **P1**，执行 Agent 固定为模拟交易。
3. A4 目标只限去除骨架阶段假成功反馈，不新增 API，不修改 `src/main.py` / `src/api/router.py`，不修改 `docker-compose.dev.yml` 或任一 `.env.example`。
4. `TASK-0017-A4` 可与 `TASK-0014-A3` / `TASK-0014-A4` 并行；`TASK-0022-B` 必须等待 A4 锁回后再启动。
5. 根级 compose、`.env.example`、治理账本与远端运维动作继续保留给 Atlas / Jay.S 处理。