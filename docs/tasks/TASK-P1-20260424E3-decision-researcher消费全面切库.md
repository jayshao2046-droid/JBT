# TASK-P1-20260424E3 — decision researcher 消费全面切库

## 任务类型
- P1 标准流程
- 服务归属：services/decision
- 母任务：TASK-P1-20260424E
- 预审依据：REVIEW-TASK-P1-20260424E-researcher-decision两地联调闭环-PRE
- 当前状态：可进入 Jay.S 文件级 Token 签发与实施

## 目标
1. 让 context_loader 不再把 Alienware /reports/latest 当 researcher 主事实源。
2. 让 news_scorer 不再把 Alienware /reports/latest 当 researcher 主事实源。
3. 让 pipeline 后段 researcher 消费切回 Decision 本地 ResearchStore / research query。

## 冻结白名单
1. services/decision/src/llm/context_loader.py
2. services/decision/src/research/news_scorer.py
3. services/decision/src/llm/pipeline.py
4. services/decision/tests/test_llm_context.py
5. services/decision/tests/test_llm_pipeline.py

## 明确排除
1. services/decision/src/llm/researcher_loader.py
2. services/decision/tests/test_researcher_integration.py
3. services/decision/.env.example
4. shared/contracts/**
5. 任意部署、runtime、logs、真实 .env 文件

## 验收标准
1. context_loader 不再直接读取 /reports/latest。
2. news_scorer 不再直接读取 /reports/latest。
3. pipeline 后段不再依赖远端 latest 作为 researcher 主事实源。
4. Decision researcher 消费统一落回本地 ResearchStore / query。

## 建议最小验证
- pytest services/decision/tests/test_llm_context.py -q
- pytest services/decision/tests/test_llm_pipeline.py -q