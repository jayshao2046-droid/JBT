# TASK-0005 回测批次 A 全量因子接入与模板解冻交接

## 基本信息

- 任务 ID：TASK-0005
- 执行 Agent：回测
- 批次：A
- Token：`tok-b2422733-d465-4bef-98b4-516ff3628fc1`
- Token 生效时间：2026-04-04 02:30:05 +0800
- Token 失效时间：2026-04-04 03:00:05 +0800
- 完成留痕时间：2026-04-04 02:45:04 +0800
- 当前状态：已完成白名单 5 文件写入、本地自校验与 handoff；待项目架构师终审

## 完成动作

1. 在 `services/backtest/src/backtest/factor_registry.py` 内补齐用户输入基线并集的 33 项正式因子注册，显式未纳入 `MyFactor`。
2. 在 `services/backtest/src/backtest/strategy_base.py` 的模板注册器中加入通用模板回退逻辑，并让内置模板加载同时覆盖 `fc_224_strategy.py` 与 `generic_factor_strategy.py`。
3. 新增 `services/backtest/src/backtest/generic_factor_strategy.py`，提供面向任意未注册 `template_id` 的通用模板入口：可读取 `factors`、计算因子结果、完成最小运行路径并输出确定性报告备注。
4. 新增 `services/backtest/tests/test_factor_registry_baseline.py`，覆盖 33 因子基线、`MyFactor` 排除以及额外依赖因子的中性回退口径。
5. 新增 `services/backtest/tests/test_generic_strategy_loading.py`，覆盖未知 `template_id` 的通用模板回退、FC-224 既有模板保留，以及通过 runner 的最小完成路径。

## 修改文件

1. `services/backtest/src/backtest/factor_registry.py`
2. `services/backtest/src/backtest/strategy_base.py`
3. `services/backtest/src/backtest/generic_factor_strategy.py`
4. `services/backtest/tests/test_factor_registry_baseline.py`
5. `services/backtest/tests/test_generic_strategy_loading.py`
6. `docs/prompts/agents/回测提示词.md`
7. `docs/handoffs/TASK-0005-回测批次A-全量因子接入与模板解冻交接.md`

## 验证结果

### 静态检查

- VS Code 诊断：本轮 5 个白名单业务文件均无错误。

### 本地自校验

- 执行命令：`source .venv/bin/activate && python -m pytest services/backtest/tests/test_fc_224_strategy_loading.py services/backtest/tests/test_factor_registry_baseline.py services/backtest/tests/test_generic_strategy_loading.py -q`
- 结果：`8 passed in 0.17s`

### 自校验结论

1. FC-224 既有模板注册与加载能力未回退。
2. 33 项因子基线已全部可注册、可计算；`MyFactor` 未进入正式能力范围。
3. 未注册 `template_id` 的 YAML 在存在 `factors` 配置时，已可通过通用模板回退完成加载与最小运行，不再直接因单模板冻结失败。

## 待审问题

1. 通用模板当前采用“因子快照 + 最小完成路径”口径，尚未扩展到更完整的多信号执行循环；如需进一步解冻 runner 执行链，应进入 TASK-0005 批次 B。
2. 情绪、库存、仓单、价差、隐波等依赖外部列的因子，当前遵循“优先读取显式列，缺失时输出中性结果”的确定性策略；请项目架构师确认该口径满足批次 A 的验收边界。
3. 模板注册器对未知 `template_id` 现在统一走通用模板回退；当 YAML 缺少 `factors` 时，将在通用模板内以配置错误失败，而不再在注册阶段提前报“未注册模板”。

## 向 Jay.S 汇报摘要

TASK-0005 批次 A 已在严格 5 文件白名单内完成：回测端现已承接 33 项正式因子，`MyFactor` 已排除；模板注册不再只冻结在 FC-224，未知 `template_id` 且带 `factors` 的策略 YAML 已可通过通用模板入口完成加载、校验与最小运行。相关本地回归已执行，`test_fc_224_strategy_loading.py`、`test_factor_registry_baseline.py`、`test_generic_strategy_loading.py` 合计 `8 passed`，未触碰 `runner.py`、`result_builder.py`、`fc_224_strategy.py`、看板目录、`shared/contracts/**` 或其他非白名单文件。当前等待项目架构师终审与锁回。

## 下一步建议

1. 由项目架构师终审本批 5 文件改动，确认无越权修改、无第 6 文件扩展，并在通过后执行 lockback。
2. 若终审通过，再由 Jay.S 决定下一步是进入 TASK-0005 批次 B 的 runner 解冻，还是恢复 TASK-0004 看板阶段优先级。
3. 若终审认为通用模板需要更完整执行路径，应单独建批次，不在本轮追加越权修改。