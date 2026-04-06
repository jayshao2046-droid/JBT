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

1. 当前只完成治理账本闭环，不含任何代码 Token或远端运维授权。
2. 当前不允许进入仓内 Docker 文件、`docker-compose.dev.yml`、`.env.example` 或远端 Mini 执行。

## 向 Atlas 汇报摘要

1. `TASK-0017` 的 review / lock / rollback / handoff 已补齐。
2. Docker / compose / `.env.example` / 远端 Mini 的拆批与边界已冻结。
3. 当前仍是“预审未执行”状态，需等待前置依赖、P0 / P1 Token 与 Jay.S 的远端运维授权。

## 下一步建议

1. 先完成 `TASK-0010` 到 `TASK-0016` 的执行前置条件。
2. 再由 Atlas 准备部署相关四类清单与 Token 申请项。
3. 未获授权前，所有服务 Agent 与 Atlas 继续保持待命。