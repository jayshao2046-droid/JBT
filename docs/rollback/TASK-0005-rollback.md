# TASK-0005 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0005
- 执行 Agent：
  - 项目架构师（预审治理）
  - 回测 Agent（业务文件执行主体；如执行运行态 `8004` 容器例外，则由其在运行环境处理）
- 对应提交 ID：待任务完成后补填
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：定向 `git revert`（不得使用 `git reset --hard`）
- 回滚结果：N/A

## 影响文件（治理阶段）

1. `docs/tasks/TASK-0005-backtest-容器命名规范统一.md`
2. `docs/reviews/TASK-0005-review.md`
3. `docs/locks/TASK-0005-lock.md`
4. `docs/rollback/TASK-0005-rollback.md`
5. `docs/handoffs/TASK-0005-backtest-容器命名交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 影响文件（开发阶段，待 Token 后）

1. `services/backtest/docker-compose.yml`
2. 对应执行 Agent 的私有 prompt
3. 对应开发 handoff 文件

## 运行态例外说明

1. `botquant-backtest-api:8004` 若在运行环境被更名为 `JBT-BACKTEST-8004`，该动作不属于 Git 版本库文件改动。
2. 若需撤销该运行态例外，应由执行 Agent 在运行环境中单独恢复容器命名，不得通过仓库全局回退替代。

## 回滚原则

1. 治理文件与业务文件应随各自独立提交分别回滚，不得混用一次全局回退。
2. 若开发阶段仅涉及 `services/backtest/docker-compose.yml`，则回滚也只允许针对该批次提交执行定向 revert。
3. 不得顺带回退 `docker-compose.dev.yml`、`services/backtest/Dockerfile`、前端页面文件或本轮未纳入白名单的其他文件。
4. 若后续发生补充预审扩白名单，则必须在本文件追加新的影响文件与对应回滚边界。

## 当前结论

- 预审账本已建立。
- 开发阶段尚未开始，当前无业务提交需要回滚。# TASK-0005 Rollback 方案

## Rollback 信息

- 任务 ID：TASK-0005
- 执行 Agent：
  - 项目架构师（预审治理）
  - 回测 Agent（建议执行主体；以 Jay.S 最终签发 Token 绑定主体为准）
- 对应提交 ID：待任务完成后补填
- 回滚时间：N/A
- 回滚原因：N/A
- 回滚方式：定向 `git revert`（不得使用 `git reset --hard`）
- 回滚结果：N/A

## 影响文件（治理阶段）

1. `docs/tasks/TASK-0005-backtest-全量因子接入与模板解冻预审.md`
2. `docs/reviews/TASK-0005-review.md`
3. `docs/locks/TASK-0005-lock.md`
4. `docs/rollback/TASK-0005-rollback.md`
5. `docs/prompts/agents/项目架构师提示词.md`

## 影响文件（批次 A，待 Token 后）

1. `services/backtest/src/backtest/factor_registry.py`
2. `services/backtest/src/backtest/strategy_base.py`
3. `services/backtest/src/backtest/generic_factor_strategy.py`
4. `services/backtest/tests/test_factor_registry_baseline.py`
5. `services/backtest/tests/test_generic_strategy_loading.py`
6. `docs/prompts/agents/回测提示词.md`
7. 对应开发 handoff 文件

## 回滚原则

1. 当前阶段尚未产生业务代码写入，因此暂无实际回滚动作。
2. 未来批次 A 若执行，回滚粒度必须绑定 TASK-0005 与首批 5 文件对应提交，不得使用全局回退替代。
3. 若首批未通过终审，只处理本任务内变更，不得波及 `runner.py`、`result_builder.py`、`fc_224_strategy.py`、看板目录、`shared/contracts/**` 或其他无关文件。
4. 不得使用 `git reset --hard`；历史必须保留，默认仅允许对 TASK-0005 对应提交执行定向 `git revert`。
5. 若后续补充预审扩展白名单，必须在本文件追加新的影响文件与新的回滚边界，不得沿用当前 5 文件口径覆盖后续批次。

## 当前结论

- 预审账本已建立。
- 当前无业务代码提交需要回滚。
- 后续如进入批次 A，必须继续保持“单任务、单批次、单提交、定向回滚”的治理边界。