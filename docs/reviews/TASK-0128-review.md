# REVIEW-TASK-0128 — decision 特征模板多周期批量生成与基线筛选

【审核角色】项目架构师  
【审核阶段】PRE 预审  
【日期】2026-04-26  
【状态】approved_for_token

## 1. 服务边界裁定

该事项属于 services/decision 单服务闭环，可在不修改 shared/contracts 的前提下实施。

依据：

1. 现有首阶段在线生成控制点位于 services/decision/scripts/run_full_pipeline_35_symbols.py。
2. 本轮只替换“首批候选生成方式”，下游继续复用 decision 内部已有的 LocalFormalBacktestClient、StrategyParamOptimizer、StrategyEvaluator、SymbolProfiler 与参数映射能力。
3. 不新增跨服务字段，不引入 shared/contracts 变更。

## 2. 预审结论

通过，按 decision 单服务标准 P1 新任务建档实施。

当前 35 品种主链的第一阶段仍是在线模型生成，不应在本任务中继续复用；最小落地应新增一条独立的本地模板批处理脚本，从 strategy_library 的现有 YAML 模板出发，结合 SymbolProfiler 与参数映射做确定性候选生成。首批候选必须先完成 formal local baseline backtest，再把基线过线者送入现有 StrategyParamOptimizer 与 StrategyEvaluator 所代表的后续调优链。当前不批准回写 strategy_library 源文件，不批准把 TqSdk 双回测、llm_ranked 归档、飞书通知与 shared/contracts 变更并入首批范围。

## 3. 冻结白名单建议

### 3.1 必须

1. services/decision/scripts/run_template_seed_baseline_pipeline.py

### 3.2 可选

1. services/decision/tests/test_template_seed_baseline_pipeline.py

## 4. 明确排除项

1. services/decision/scripts/run_full_pipeline_35_symbols.py
2. services/decision/strategy_library/**
3. shared/contracts/**
4. shared/python-common/**
5. services/data/**
6. services/backtest/**
7. services/dashboard/**
8. runtime/**
9. logs/**
10. 任意真实 .env

## 5. 最小验证集

1. 新脚本对 OpenAICompatibleClient、CodeGenerator、llm_generated、llm_ranked 的引用为 0。
2. 单品种生成 2~3 个候选 YAML。
3. 至少 1 个候选 baseline formal local backtest 返回 completed。
4. 生成 tuning candidate 清单。
5. strategy_library 源文件无原地修改。

## 6. 审核意见

1. 当前只批准“模板种子生成 + baseline + 筛选”这一最小闭环。
2. 当前不批准直接进入 LLM 自动化调优。
3. 若实施中证明必须改动 run_tuning_pipeline.py 或其他 decision 文件，需先补充预审。