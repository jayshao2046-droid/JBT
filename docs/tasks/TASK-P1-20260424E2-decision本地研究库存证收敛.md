# TASK-P1-20260424E2 — decision 本地研究库存证收敛

## 任务类型
- P1 标准流程
- 服务归属：services/decision
- 母任务：TASK-P1-20260424E
- 预审依据：REVIEW-TASK-P1-20260424E-researcher-decision两地联调闭环-PRE
- 当前状态：可进入 Jay.S 文件级 Token 签发与实施

## 目标
1. 把 researcher 推送批次稳定写入 Decision 本地 ResearchStore。
2. 让本地 store / query 能承载数据研报、情报研报、情绪研报对应事实源或摘要事实。
3. 为后续 context / scorer / pipeline 统一切库提供本地事实基面。

## 冻结白名单
1. services/decision/src/api/routes/researcher_evaluate.py
2. services/decision/src/research/research_store.py
3. services/decision/src/api/routes/research_query.py
4. services/decision/tests/test_research_extensions.py

## 明确排除
1. services/decision/src/api/app.py
2. services/decision/.env.example
3. shared/contracts/**
4. 任意部署、runtime、logs、真实 .env 文件

## 验收标准
1. ResearchStore 不再只保存瞬时评分结果，而能稳定保留 researcher 本地库存证。
2. 通过本地统一查询面可以稳定读取三类 researcher 事实。
3. 不引入 shared/contracts 变更。

## 建议最小验证
- pytest services/decision/tests/test_research_extensions.py -q