# TASK-0015 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0015
- 执行 Agent：
  - 项目架构师（当前治理补录）
  - 看板 Agent（未来前端实现主体）
- 对应提交 ID：待后续任务提交后补填
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：定向 `git revert`，不得使用 `git reset --hard`
- 回滚结果：当前无业务代码执行，无需代码回滚

## 影响文件（当前治理阶段）

1. `docs/tasks/TASK-0015-dashboard-SimNow-临时Next.js看板预审.md`
2. `docs/reviews/TASK-0015-review.md`
3. `docs/locks/TASK-0015-lock.md`
4. `docs/rollback/TASK-0015-rollback.md`
5. `docs/handoffs/TASK-0015-SimNow-临时看板预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 当前轮次回滚结论

1. 当前轮次只发生治理账本写入，尚未发生 `services/dashboard/**`、`.env.example` 或只读契约的代码执行。
2. 当前不存在需要对前端页面、前端配置或远端环境执行的回滚动作。
3. 若需要撤销本轮，只允许对治理账本提交执行定向 `git revert`。

## 未来进入执行后的回滚粒度

1. `services/dashboard/**` 前端业务文件必须作为独立 P1 批次、独立提交、独立 revert。
2. `services/dashboard/.env.example` 若发生变更，必须独立 P0 提交，不得与前端业务实现混回滚。
3. 若未来新增 `shared/contracts/**` 的只读契约字段，必须独立 P0 提交，不能与页面代码混回滚。
4. 若后续因新增只读 API 字段需要补审，必须在本文件追加新的回滚边界。

## Secret / 远端环境 / compose / integrations 回滚要求

1. 前端环境变量只能保留占位符，不得写入任何真实 Secret；回滚也只允许恢复占位说明。
2. 本任务未来不应触碰远端环境或 `docker-compose.dev.yml`；如需部署动作，必须交由 `TASK-0017` 独立管理。
3. 本任务未来不应触碰 `integrations/**`；若前端接入被错误绕到兼容层，应立即停止并回交补审。

## 当前结论

1. 当前轮次尚未发生代码执行。
2. 当前无前端提交需要回滚。
3. 后续如进入实施，必须保持页面实现、环境模板与契约文件三类变更可独立回滚。