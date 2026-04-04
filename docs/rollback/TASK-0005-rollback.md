# TASK-0005 Rollback 方案

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