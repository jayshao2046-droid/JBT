# REVIEW FINAL — TASK-P1-20260423D2

- review_id: REVIEW-TASK-P1-20260423D2-decision-researcher直连解耦-FINAL
- task_id: TASK-P1-20260423D2
- token_id: tok-543c4acf-3301-4069-be24-17a8db3db6b0
- reviewer: Atlas
- status: PASSED
- reviewed_at: 2026-04-23

## 修改内容

### 1. `services/decision/src/llm/context_loader.py`

- `get_l2_context()` 第 3 步研报拉取：从 `{DATA_API_URL}/api/v1/researcher/report/latest` 改为 `{RESEARCHER_SERVICE_URL}/reports/latest`
- 响应解析逻辑更新：Alienware API 直接返回报告对象（不是 `{report: {...}}` 包装），新增 `report_id` 字段判断

### 2. `services/decision/src/research/news_scorer.py`

- `__init__` 中研报来源从 `DATA_SERVICE_URL`（Mini `:8105`）改为 `RESEARCHER_SERVICE_URL`（Alienware `:8199`）
- `_fetch_latest_report()` 中 URL 从 `{data_api_url}/api/v1/researcher/report/latest` 改为 `{researcher_api_url}/reports/latest`

### 3. `services/decision/src/llm/pipeline.py`

- `LLMPipeline.__init__()` 中 `ResearcherLoader` 初始化：从 `DATA_SERVICE_URL`（`http://192.168.31.74:8105`）改为 `RESEARCHER_SERVICE_URL`（`http://192.168.31.187:8199`）

## 验证结果

- `pytest services/decision/tests/test_llm_context.py tests/test_llm_pipeline.py -q` → **15 passed** ✅
- AST 语法校验 3/3 通过  ✅

## 越界检查

- 仅修改 D2 白名单 3 个源码文件 + 2 个测试文件（实际测试文件未需改动）  ✅
- 未触碰 `researcher_loader.py`、`core/settings.py`、`.env.example` 或任何其他文件  ✅
- `DATA_SERVICE_URL` 保留用于 K 线/行情数据，不受影响  ✅

## 结论

D2 实施完成，验收通过，可锁回。
