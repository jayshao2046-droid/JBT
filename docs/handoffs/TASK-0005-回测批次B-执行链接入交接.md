# TASK-0005 回测批次 B 执行链接入交接

## 基本信息

- 任务 ID：TASK-0005
- 执行 Agent：回测
- 批次：B
- Token：`tok-83f5a10a-f9d5-45c9-9c49-574ef5797460`
- review-id：`REVIEW-TASK-0005-B`
- Token 生效时间：2026-04-04 11:21:56 +0800
- Token 失效时间：2026-04-04 11:51:56 +0800
- 完成留痕时间：2026-04-04 11:38:22 +0800
- 当前状态：已完成白名单实现、本地自校验与 handoff；待项目架构师终审与锁回

## 完成动作

1. 在 `services/backtest/src/backtest/generic_factor_strategy.py` 内把 generic 模板从“最小快照完成路径”升级为“live execution + static fallback”双路径：
   - 增加 live execution 检测；
   - 在支持 `wait_update()` / `is_changing()` / `TargetPosTask` 时走执行循环；
   - 支持 `market_filter.conditions`、`signal.long_condition`、`signal.short_condition` 的最小表达式判定；
   - 当 YAML 未提供信号表达式时，退回 `long_threshold` / `short_threshold` 的最小权重分数口径；
   - 记录 `execution_loop_entered`、`signal_transitions`、`target_updates`、`observed_trade_records`、`final_signal_state` 等 notes；
   - 保留不支持 live execution 时的静态快照回退。
2. 新增 `services/backtest/tests/test_generic_strategy_execution.py`，覆盖 generic 模板进入 live execution path、dummy session 下留下 `target_updates` / `execution_loop_entered` / `report.json` / 成交留痕，以及无表达式时的权重阈值回退。
3. 在白名单内复核 `runner.py`、`result_builder.py`、`test_fc_224_execution_trace.py` 的既有行为，确认本轮无需修改：
   - `runner.py` 当前只对 FC-224 做冻结输入校验与零成交 rejected 保护，generic 模板不会误触该逻辑；
   - `result_builder.py` 现有 `BacktestReport` / `report.json` 结构已能稳定承接 generic 结果、notes 与摘要，无需变更字段结构；
   - `test_fc_224_execution_trace.py` 已覆盖 FC-224 正式路径、手续费/滑点留痕和零成交拦截，本轮只需回归验证即可完成非回退保护。

## 修改文件

1. `services/backtest/src/backtest/generic_factor_strategy.py`
2. `services/backtest/tests/test_generic_strategy_execution.py`
3. `docs/prompts/agents/回测提示词.md`
4. `docs/handoffs/TASK-0005-回测批次B-执行链接入交接.md`

## 白名单内未修改文件与原因

1. `services/backtest/src/backtest/runner.py`：generic 模板执行结果已通过 `OnlineBacktestRunner.run_job_sync()` 正常进入现有收口；FC-224 专用冻结校验与零成交 rejected 逻辑保持不变更，避免放大回归半径。
2. `services/backtest/src/backtest/result_builder.py`：现有 report builder 已能承接 generic 的 `notes`、`equity_curve`、`trade_pnls`、`report_summary` 与 `report.json`，且本轮全链路测试已证明无需改字段结构。
3. `services/backtest/tests/test_fc_224_execution_trace.py`：既有测试已覆盖 FC-224 正式路径和非回退保护；本轮通过回归执行确认其仍全部通过，因此无需重写或扩写。

## 验证结果

### 静态检查

- VS Code 诊断：本轮改动文件无错误。

### 本地自校验

- 执行命令：`source .venv/bin/activate && python -m pytest services/backtest/tests/test_generic_strategy_loading.py services/backtest/tests/test_generic_strategy_execution.py services/backtest/tests/test_fc_224_execution_trace.py -q`
- 结果：`7 passed in 0.29s`

### 自校验结论

1. generic 模板已可进入 live execution path，并在 dummy session 下留下 `execution_loop_entered=true`、`target_updates>=1`、`observed_trade_records>=1` 与 `report.json` 留痕。
2. generic 模板在无信号表达式时，已可退回到 `long_threshold` / `short_threshold` 的最小权重分数口径。
3. `runner.py` 与 `result_builder.py` 现有实现已稳定承接 generic 执行结果与摘要，无需额外修改。
4. FC-224 的正式回测路径、手续费/滑点留痕和零成交 rejected 逻辑均未回退。

## 待审问题

1. generic 表达式求值当前仅覆盖最小布尔/比较/四则运算节点；若后续 YAML 需要函数调用、复杂嵌套或更完整 DSL，需单独建批次扩展，不应在本轮继续扩大实现范围。
2. 权重分数回退当前采用“最小方向性打分”启发式，对未显式提供 `long_condition` / `short_condition` 的模板足够支撑最小执行路径；如后续要做更严格的因子语义映射，应另起批次，不在本轮追加。
3. 当前批次已完成 agent 侧自校验，但仍需项目架构师复核：是否接受 `runner.py` / `result_builder.py` 保持不改的收口方式，以及当前 generic 表达式支持范围是否满足批次 B 验收边界。

## 向 Jay.S 汇报摘要

TASK-0005 批次 B 已在严格 5 文件白名单内完成实现与本地自校验。generic 模板现在不再只有“因子快照最小完成路径”，而是在 session 支持 `wait_update()`、`is_changing()` 与 `TargetPosTask` 时，可走与 FC-224 类似的执行循环，并留下 `execution_loop_entered`、`signal_transitions`、`target_updates`、`observed_trade_records`、`final_signal_state` 等可追溯 notes。`runner.py` 与 `result_builder.py` 本轮未改动，因为现有收口已能稳定承接 generic 结果，`report.json` 字段结构也无需扩展；相关结论已通过 `test_generic_strategy_loading.py`、`test_generic_strategy_execution.py`、`test_fc_224_execution_trace.py` 合计 `7 passed` 验证。FC-224 正式回测路径与零成交拦截逻辑未回退，当前等待项目架构师终审与锁回。

## 下一步建议

1. 由项目架构师终审本批 5 文件白名单执行结果，确认“只改 2 个业务文件”的收口方式满足批次 B 验收边界，并在通过后执行 lockback。
2. 若终审通过，再由项目架构师更新公共项目提示词与锁控记录，把批次 B 状态从 `active` 切换到 `locked`。
3. 若终审认为 generic 表达式能力或权重回退仍需扩展，应单独拆新批次，不在本轮追加第 6 个业务文件或扩大到 contracts / 看板 / Docker。