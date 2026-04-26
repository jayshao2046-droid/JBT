# TASK-P1-20260424-0127F1 — decision LLM 参数放宽与策略质量提升

## 任务类型
- P1 标准流程
- 服务归属：services/decision
- 母任务：TASK-0127 LLM 全品种自动化策略生产闭环
- 当前状态：待项目架构师预审 → 待 Jay.S 文件级 Token 签发

## 背景与根因

2026-04-24 已确认 TASK-0127 的自动化主链本身可以真实跑通，`rb_trend_60m_v1` 已完成“生成 → 调优 → 本地回测 → TqSdk → 评分 → 分桶 → 飞书通知”的单策略闭环。

当前更主要的问题已不再是链路是否可达，而是 LLM 生成/调优阶段的产物质量偏低，具体表现为：

1. 有些参数卡得过紧，导致策略难以产出有价值的入场逻辑。
2. 一部分策略虽然生成成功，但会因为 `*_main0` 数据符号口径、表达式兼容、非法风控参数等问题在后续阶段提前失败。
3. 当前流水线会消耗大量 token 和调优轮次在“先天低质量”策略上，拉低 35 品种整体推进效率。

## 目标

1. 放宽 LLM 生成阶段过紧的策略约束，允许产出更有信息量的策略逻辑。
2. 同步增加非法 YAML / 非法风险参数 / 不兼容表达式的前置约束，减少无效策略进入正式链路。
3. 提升单品种 7 策略矩阵中的有效候选比例，降低 `0 交易`、非法参数和 formal local 语法失败比例。
4. 为 TASK-0127 的 35 品种正式推进建立新的默认生成口径。

## 候选白名单（待预审冻结）

1. `services/decision/scripts/run_full_pipeline_35_symbols.py`
2. `services/decision/src/research/code_generator.py`
3. `services/decision/src/research/strategy_param_optimizer.py`
4. `services/decision/src/research/yaml_signal_executor.py`
5. `services/decision/src/research/local_formal_backtest_client.py`
6. 与本任务直接相关的 `docs/handoffs/**`

## 明确排除（本批次不动）

1. `shared/contracts/**`
2. `services/data/**`
3. `services/backtest/**`
4. `services/dashboard/**`
5. 任何 `runtime/**`、`logs/**`、真实 `.env`

## 验收标准

1. 单品种策略矩阵中，进入评分阶段的策略比例明显高于当前基线。
2. 非法风险参数和 formal local 不兼容表达式的失败率显著下降。
3. 不再把“主链可达性”作为主要阻塞，阻塞点转移到可解释的策略质量问题。
4. 调整后结果可直接服务于 TASK-0127 后续 35 品种正式推进。

## 建议最小验证

- 选 `rb` 或另一高频验证品种做单品种 7 策略矩阵复跑。
- 统计进入评分阶段的策略数、被 `*_main0` / 语法 / 风控参数拦截的策略数。
- 对比调整前后的有效候选数量与失败原因构成。

## 执行顺序与责任

1. Atlas 建档并冻结问题边界
2. 项目架构师预审
3. Jay.S 签发最小白名单 Token
4. 执行 Agent：决策 / Livis
5. 完成后回写 TASK-0127 的后续推进结论