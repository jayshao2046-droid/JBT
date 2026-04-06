# TASK-0013 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0013
- 执行 Agent：
  - 项目架构师（当前治理补录）
  - 模拟交易 Agent / 实盘交易 Agent（未来按批次实施）
- 对应提交 ID：待后续任务提交后补填
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：定向 `git revert`，不得使用 `git reset --hard`
- 回滚结果：当前无业务代码执行，无需代码回滚

## 影响文件（当前治理阶段）

1. `docs/tasks/TASK-0013-sim-live-统一风控核心与阶段预设治理预审.md`
2. `docs/reviews/TASK-0013-review.md`
3. `docs/locks/TASK-0013-lock.md`
4. `docs/rollback/TASK-0013-rollback.md`
5. `docs/handoffs/TASK-0013-统一风控核心与阶段预设预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 当前轮次回滚结论

1. 当前轮次只发生治理账本写入，尚未发生 `shared/python-common/**`、`services/sim-trading/**`、`services/live-trading/**` 代码执行。
2. 当前不存在需要对业务代码、共享代码或远端环境执行的回滚动作。
3. 若需要撤销本轮，只允许对治理账本提交执行定向 `git revert`，不得波及其他任务提交。

## 未来进入执行后的回滚粒度

1. 统一风控核心若落在 `shared/python-common/**`，必须作为独立 P0 批次、独立提交、独立 revert。
2. SimNow adapter 若落在 `services/sim-trading/**`，必须作为独立 P1 批次、独立提交、独立 revert。
3. 实盘 adapter 若落在 `services/live-trading/**`，必须作为独立 P1 批次、独立提交、独立 revert。
4. `.env.example` 或 `shared/contracts/**` 的 preset / 风险事件字段若发生变更，必须独立于代码批次提交，不得与服务实现混回滚。

## Secret / 远端环境 / compose / integrations 回滚要求

1. Secret 只允许运行时注入；回滚时只能回滚占位符、字段说明与接入方案，不得把真实 Secret 写入任何回滚提交。
2. 本任务未来不应触碰远端环境或 `docker-compose.dev.yml`；若实际需要触碰，视为越界，必须另开任务而不是沿用本回滚口径。
3. 本任务未来也不应触碰 `integrations/**`；若执行方案扩展到兼容层，必须拆回 `TASK-0012` 或其他独立任务，不得混入本任务回滚边界。

## 当前结论

1. 当前轮次尚未发生代码执行。
2. 第二轮补审当前仅补齐治理账本，无业务代码需要回滚。
3. 后续若进入执行，必须继续维持“单任务、单批次、单提交、定向回滚”的粒度。