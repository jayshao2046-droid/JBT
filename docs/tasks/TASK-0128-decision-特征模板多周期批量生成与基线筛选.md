# TASK-0128 — decision 特征模板多周期批量生成与基线筛选

【类型】P1 标准流程  
【建档】Atlas  
【日期】2026-04-26  
【状态】脚本实现批已完成并通过窄测；运行批待后续按显式产物文件二次签发  
【执行 Agent】决策  
【服务边界】仅限 services/decision 单服务

## 1. 任务目标

基于 decision 当前本地策略库，新增一条“不依赖在线模型首批生成”的候选策略生产链，满足以下目标：

1. 首批候选 YAML 不通过在线模型生成。
2. 以 services/decision/strategy_library 下现有因子簇模板为种子源。
3. 默认覆盖 42 个期货品种，口径对齐 scripts/generate_profile_driven_strategies.py 中的 ALL_42_SYMBOLS。
4. 结合 SymbolProfiler 与参数映射规则，为每个品种生成最适合的候选策略。
5. 覆盖 5、15、30、60、120、240 分钟六个周期。
6. 生成结果必须同时满足本地 formal local 回测与 TqSdk YAML 兼容要求。
7. 对生成结果先跑 baseline formal local backtest，再通过筛选器产出“适合后续调优”的 YAML 清单。
8. 当前批次只完成“生成 + baseline + 筛选 + 回传 MacBook”，待 Jay.S 确认后再进入 LLM 自动化调优。

## 2. 已确认事实

1. Jay.S 最新口径已明确：本任务首批默认 universe 不是 35 品种，而是 42 品种。
2. 旧主控脚本 services/decision/scripts/run_full_pipeline_35_symbols.py 的首阶段仍绑定在线 OpenAICompatibleClient + CodeGenerator，不符合“首批不通过在线模型生成”的要求。
3. strategy_library 当前几乎全部为 60m 种子模板，尚无 5/15/30/120/240 的多周期版本。
4. strategy_library 内每个品种目前包含多个因子簇目录，可作为本地确定性模板源。
5. LocalFormalBacktestClient 已具备 formal local baseline 回测能力。
6. TqSdkBacktestClient 已具备 YAML 兼容校验能力，可作为后续 tuning candidate 的静态筛选门槛。

## 3. 本轮最小实现范围

本轮最小实现固定为：

1. 新增一条独立的本地模板批处理脚本。
2. 默认以 42 品种 universe 为输入集；支持后续通过命令行下钻到单品种 smoke。
3. 从 strategy_library 的 60m 种子模板出发，扩展生成 5/15/30/60/120/240 六周期工作副本。
4. 基于 SymbolProfiler + ParamMappingApplicator 做确定性参数播种，不调用在线生成模型。
5. 对全部候选执行 formal local baseline backtest。
6. 依据 baseline 结果与 TqSdk 兼容规则筛选出“适合后续调优”的 YAML 清单。
7. 落盘生成目录、筛选目录与汇总报告。
8. 本轮不启动 LLM 自动化调优。

## 4. 建议输出目录

为避免污染旧 strategy_library 与 llm_generated 语义目录，本轮输出建议冻结为：

1. services/decision/strategies/template_seed_generated/
2. services/decision/strategies/template_seed_reports/
3. services/decision/strategies/template_seed_tuning_candidates/

说明：

1. strategy_library 继续作为只读种子库，不原地改写。
2. llm_generated / llm_ranked 不纳入本轮首批生成目录。
3. 生成完成后，如执行面发生在 Studio，需要将上述目录同步回 MacBook 本地。

## 5. 建议白名单（待预审冻结）

### 5.1 必须

1. services/decision/scripts/run_template_seed_baseline_pipeline.py

### 5.2 可选

1. services/decision/tests/test_template_seed_baseline_pipeline.py

## 6. 明确排除项

1. 不修改 services/decision/scripts/run_full_pipeline_35_symbols.py
2. 不修改 strategy_library 下现有种子 YAML
3. 不修改 shared/contracts/**
4. 不修改 shared/python-common/**
5. 不修改 services/data/**
6. 不修改 services/backtest/**
7. 不修改 services/dashboard/**
8. 不修改 runtime/**、logs/**、任何真实 .env
9. 不在本轮启动 LLM 自动化调优

## 7. 验收标准

1. 新脚本不再引用 OpenAICompatibleClient、CodeGenerator、llm_generated、llm_ranked 作为首批生成入口。
2. 能以 strategy_library 的 60m 模板为种子，生成六个周期的工作 YAML。
3. 生成结果满足现有本地 formal local 与 TqSdk YAML 规范。
4. 至少完成单品种 smoke 验证，并能对候选执行 baseline formal local backtest。
5. 输出筛选后的 tuning candidate 清单。
6. 当前批次结束时不触发 LLM 自动化调优，等待 Jay.S 确认。

## 8. 建议最小验证

1. 代码静态核验：新脚本对 OpenAICompatibleClient / CodeGenerator / llm_generated / llm_ranked 的引用为 0。
2. 单品种 smoke：任选 1 个品种，生成 2 到 3 个候选 YAML。
3. baseline 验证：至少 1 个候选 formal local backtest 返回 completed。
4. 筛选验证：能输出一份 tuning candidate 清单与原因说明。
5. 白名单边界验证：无 strategy_library 原地修改，无 shared/contracts 改动。

## 9. 后续衔接

本任务完成后：

1. 先向 Jay.S 交付“候选 YAML + baseline 报告 + tuning candidate 清单”。
2. 待 Jay.S 明确确认后，再单独启动后续 LLM 自动化调优批次。