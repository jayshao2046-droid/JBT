# TASK-P1-20260423D2 — decision researcher 直连解耦

## 任务类型
- P1 标准流程
- 服务边界：仅 `services/decision/**`
- 当前状态：已完成，已锁回（2026-04-23）

## 任务来源
- 来源母任务：`TASK-P1-20260423D`
- 预审依据：`docs/reviews/REVIEW-TASK-P1-20260423D-decision直连Alienware-researcher链路收敛-PRE.md`

## 根因
- `services/decision/src/llm/context_loader.py` 仍请求 Mini `:8105/api/v1/researcher/report/latest`。
- `services/decision/src/research/news_scorer.py` 仍把 `DATA_SERVICE_URL` 当 researcher 报告源。
- `services/decision/src/llm/pipeline.py` 初始化 `ResearcherLoader` 时仍传入 `DATA_SERVICE_URL`。
- 结果是 researcher 报告源与 data 行情源混绑，decision 内部存在 Mini 与 Alienware 双链路混用。

## 目标
1. 让 `context_loader.py` 不再请求 Mini researcher latest。
2. 让 `news_scorer.py` 不再把 `DATA_SERVICE_URL` 当 researcher 源。
3. 让 `pipeline.py` 初始化 `ResearcherLoader` 时改为 researcher 专用 URL。
4. 保持 `DATA_SERVICE_URL` 仅承担 data 行情与上下文供数职责。

## 冻结白名单
- `services/decision/src/llm/context_loader.py`
- `services/decision/src/research/news_scorer.py`
- `services/decision/src/llm/pipeline.py`
- `services/decision/tests/test_llm_context.py`
- `services/decision/tests/test_llm_pipeline.py`

## 明确排除
- `services/decision/src/llm/researcher_loader.py`
- `services/decision/src/core/settings.py`
- `services/decision/tests/test_researcher_integration.py`
- `services/decision/.env.example`

## 验收标准
1. 上述 3 个源码文件全部改为 researcher 专用 URL 读取研报。
2. 不再出现 Mini `:8105/api/v1/researcher/report/latest` 作为 decision researcher 读取路径。
3. `DATA_SERVICE_URL` 不再被 researcher 报告消费复用。
4. 窄测通过：
   - `pytest services/decision/tests/test_llm_context.py -q`
   - `pytest services/decision/tests/test_llm_pipeline.py -q`

## 约束
- 本批不处理 `.env.example`，避免把 P0 配置样例与 P1 代码批次混签。
- 若实施中证明必须修改 `researcher_loader.py` 或 `core/settings.py`，必须回项目架构师补充预审。