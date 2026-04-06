# TASK-0014 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0014
- 执行 Agent：
  - 项目架构师（当前治理补录）
  - 模拟交易 Agent（未来服务实现主体）
- 对应提交 ID：待后续任务提交后补填
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：定向 `git revert`，不得使用 `git reset --hard`
- 回滚结果：当前无业务代码执行，无需代码回滚

## 影响文件（当前治理阶段）

1. `docs/tasks/TASK-0014-sim-trading-风控通知链路预审.md`
2. `docs/reviews/TASK-0014-review.md`
3. `docs/locks/TASK-0014-lock.md`
4. `docs/rollback/TASK-0014-rollback.md`
5. `docs/handoffs/TASK-0014-风控通知链路预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 当前轮次回滚结论

1. 当前轮次只发生治理账本写入，尚未发生 `services/sim-trading/**`、`.env.example` 或 `shared/contracts/**` 代码执行。
2. 当前不存在需要对通知实现、通知契约或远端环境执行的回滚动作。
3. 若需要撤销本轮，只允许对治理账本提交执行定向 `git revert`。

## 未来进入执行后的回滚粒度

1. `services/sim-trading/src/**` 与 `services/sim-trading/tests/**` 的通知实现必须作为独立 P1 批次、独立提交、独立 revert。
2. `services/sim-trading/.env.example` 的通知字段占位必须独立 P0 提交，不得与服务实现混回滚。
3. 若未来新增 `shared/contracts/**` 通知事件契约，必须独立 P0 提交，不能与服务代码混回滚。
4. 任一新增白名单文件或新增批次，都必须先补充本回滚文件，不得沿用当前粒度覆盖后续执行。

## Secret / 远端环境 / compose / integrations 回滚要求

1. 飞书 webhook、邮箱账号、邮箱密码与 SMTP Secret 不得入库；回滚只处理占位说明，不处理真实 Secret。
2. 本任务未来不应触碰远端环境或 `docker-compose.dev.yml`；若实施过程中出现此需求，必须另开任务。
3. 本任务未来不应触碰 `integrations/**`；若通知链路被错误扩展到兼容层，应视为越界并回交补审。

## 当前结论

1. 当前轮次尚未发生代码执行。
2. 当前无服务提交需要回滚。
3. 后续如进入实施，必须保持服务实现、`.env.example` 与契约文件各自独立回滚。