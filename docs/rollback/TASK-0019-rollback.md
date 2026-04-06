# TASK-0019 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0019
- 执行 Agent：
  - 项目架构师（当前治理补录）
  - 模拟交易 Agent（未来服务实现主体）
- 对应提交 ID：待后续任务提交后补填
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：定向 `git revert`，不得使用 `git reset --hard`
- 回滚结果：当前无业务代码执行，无需代码回滚

## 影响文件（当前治理阶段）

1. `docs/tasks/TASK-0019-sim-trading-收盘统计邮件预审.md`
2. `docs/reviews/TASK-0019-review.md`
3. `docs/locks/TASK-0019-lock.md`
4. `docs/rollback/TASK-0019-rollback.md`
5. `docs/handoffs/TASK-0019-收盘统计邮件预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 当前轮次回滚结论

1. 当前轮次只发生治理账本写入，尚未发生 `services/sim-trading/**`、`.env.example` 或 `shared/contracts/**` 代码执行。
2. 当前不存在需要对 scheduler、报表实现或环境模板执行的回滚动作。
3. 若需要撤销本轮，只允许对治理账本提交执行定向 `git revert`。

## 未来进入执行后的回滚粒度

1. `TASK-0019-B0` 若启用，`services/sim-trading/.env.example` 的改动必须作为独立 P0 提交、独立 revert。
2. `TASK-0019-B1` 的 scheduler 与最小邮件报表骨架必须作为独立 P1 批次、独立提交、独立 revert。
3. `TASK-0019-B2` 的账户 / 持仓 / 成交报表充实必须作为独立 P1 批次、独立提交、独立 revert。
4. 若未来新增 `shared/contracts/**` 报表契约，必须独立 P0 提交，不能与服务代码混回滚。

## Secret / env mapping 回滚要求

1. 真实收件人、SMTP Secret 与 webhook 不得入库；回滚只处理占位说明，不处理真实 Secret。
2. legacy `J_BotQuant/.env` 只允许作为部署侧凭证来源；回滚时不得在仓内补写或保留任何外部 `.env` 路径耦合逻辑。
3. 部署侧 env mapping / fallback 若需回退，只能回退映射方案与占位说明，不得把真实 Secret 写回 Git。

## 当前结论

1. 当前轮次尚未发生代码执行。
2. 当前无服务提交需要回滚。
3. 后续如进入实施，必须保持 B0、B1、B2 与潜在契约补录各自独立回滚。