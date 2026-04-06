# TASK-0017 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0017
- 执行 Agent：
  - 项目架构师（当前治理补录）
  - 对应服务 Agent（未来仓内 Docker 文件实现）
  - Atlas（未来远端 Mini 运维执行，但需 Jay.S 明确授权）
- 对应提交 ID：待后续任务提交后补填
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：代码层定向 `git revert` + 远端 Mini 独立运维回滚
- 回滚结果：当前无代码执行或远端执行，无需回滚

## 影响文件（当前治理阶段）

1. `docs/tasks/TASK-0017-sim-trading-Docker化与Mini部署预审.md`
2. `docs/reviews/TASK-0017-review.md`
3. `docs/locks/TASK-0017-lock.md`
4. `docs/rollback/TASK-0017-rollback.md`
5. `docs/handoffs/TASK-0017-Docker与Mini部署预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 当前轮次回滚结论

1. 当前轮次只发生治理账本写入，尚未发生服务 Docker 文件、`docker-compose.dev.yml`、`.env.example` 或远端 Mini 运维执行。
2. 当前不存在需要对仓内 Docker 代码、compose 或远端环境执行的回滚动作。
3. 若需要撤销本轮，只允许对治理账本提交执行定向 `git revert`。

## 未来进入执行后的回滚粒度

1. `services/sim-trading/**` 或 `services/dashboard/**` 中的 Docker 相关服务文件必须作为独立 P1 批次、独立提交、独立 revert。
2. `docker-compose.dev.yml` 的改动必须作为独立 P0 提交，不能与服务 Docker 文件混回滚。
3. 各服务 `.env.example` 的改动必须作为独立 P0 提交，不能与 compose 或服务代码混回滚。
4. 远端 Mini 的镜像切换、容器启停、Secret 注入与回滚验证属于独立运维动作，不得用 Git 全局回退替代。

## Secret / 远端环境 / compose / integrations 回滚要求

1. 所有 Secret 只允许运行时注入；回滚时只能恢复占位符、挂载方式与注入说明，不得写入真实 Secret。
2. 远端 Mini 执行前必须先保留镜像快照或明确回滚点；发生失败时，优先恢复远端镜像与容器状态，不得先在线修补。
3. `docker-compose.dev.yml` 的回滚必须独立执行，不能顺带回退无关服务。
4. 本任务未来不应触碰 `integrations/**`；若部署过程依赖兼容层调整，必须由 `TASK-0012` / `TASK-0016` 单独闭环。

## 当前结论

1. 当前轮次尚未发生代码执行或远端运维执行。
2. 当前无 compose、Docker 文件或 Mini 运维动作需要回滚。
3. 后续如进入实施，必须保持服务 Docker 文件、compose、`.env.example` 与远端 Mini 动作四层可独立回滚。