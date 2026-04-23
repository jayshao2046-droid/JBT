# REVIEW-TASK-P1-20260423D2-decision-researcher直连解耦-PRE

- 审核人：项目架构师
- 审核时间：2026-04-23
- 对应任务：TASK-P1-20260423D2
- 审核类型：标准预审（P1 / decision 单服务）

---

## 1. 审核结论

**结论：通过，允许进入 Jay.S 文件级 Token 签发。**

前置约束：

1. 本预审仅承接母预审已确认的既有只读事实，不重复扩大检查面。
2. 执行 Agent 固定为决策，Atlas 只负责预审、终审、白名单冻结与验收裁定，不代写 `services/decision/**` 业务代码。
3. 若实施中证明必须新增任一白名单外文件，当前预审立即失效，必须回到项目架构师补充预审。

---

## 2. 任务边界

### 2.1 批准范围

- 仅处理 `services/decision/**` 内 researcher 报告消费链路与 `DATA_SERVICE_URL` 的职责解耦。
- 目标仅限让 `context_loader.py`、`news_scorer.py`、`pipeline.py` 不再把 Mini researcher 链路或 `DATA_SERVICE_URL` 继续当作 researcher 报告源。
- 本批只收敛 decision 内 researcher URL 使用口径，不扩展为 ResearcherLoader 重构、settings 收口或 integration 测试体系清理。

### 2.2 明确排除

- 排除 `services/decision/src/llm/researcher_loader.py`。
- 排除 `services/decision/src/core/settings.py`。
- 排除 `services/decision/tests/test_researcher_integration.py`。
- 排除 `services/decision/.env.example`。
- 排除其他任意 `services/decision/**` 文件。

---

## 3. 根因判断

### 3.1 context_loader 仍请求 Mini researcher latest

根因判断：**成立。**

母预审已确认：`services/decision/src/llm/context_loader.py` 当前仍请求 Mini `:8105/api/v1/researcher/report/latest`。这与 researcher 直连 Alienware `:8199` 的目标口径不一致。

### 3.2 news_scorer 仍把 DATA_SERVICE_URL 当 researcher 报告源

根因判断：**成立。**

母预审已确认：`services/decision/src/research/news_scorer.py` 当前仍把 `DATA_SERVICE_URL` 当作 researcher 报告源，并访问 researcher latest 路径。

这导致 data 行情源与 researcher 报告源继续混绑。

### 3.3 pipeline 初始化时仍把 DATA_SERVICE_URL 传给 ResearcherLoader

根因判断：**成立。**

母预审已确认：`services/decision/src/llm/pipeline.py` 当前仍读取 `DATA_SERVICE_URL` 并将其传给 `ResearcherLoader`。因此，即便下层已有 Alienware researcher API 风格实现，上游初始化仍把链路导回旧 data URL。

### 3.4 researcher_loader 与 settings 不是当前批准改动面

根因判断：**已裁定为非本批直接故障点。**

母预审已确认：

1. `services/decision/src/llm/researcher_loader.py` 已按 Alienware researcher API 风格实现，不是当前直接故障控制点。
2. `services/decision/src/core/settings.py` 不是当前最小改动必经面。

因此这两个文件当前不批准进入白名单；若实施中证明必须改动其一，必须回到项目架构师补充预审。

---

## 4. 冻结白名单

本次最终冻结为 **5 个文件**，不得扩大：

1. `services/decision/src/llm/context_loader.py`
2. `services/decision/src/research/news_scorer.py`
3. `services/decision/src/llm/pipeline.py`
4. `services/decision/tests/test_llm_context.py`
5. `services/decision/tests/test_llm_pipeline.py`

裁定说明：

1. 上述 3 个源码文件覆盖了母预审已锁定的全部 decision 控制点。
2. 上述 2 个测试文件是当前最小、最直接的窄测验证面。
3. 不批准纳入 `services/decision/tests/test_researcher_integration.py`；该文件当前口径滞后，纳入后会把本批扩展成旧测试体系清理。

---

## 5. 排除项

以下文件或范围当前明确排除：

- `services/decision/src/llm/researcher_loader.py`
- `services/decision/src/core/settings.py`
- `services/decision/tests/test_researcher_integration.py`
- `services/decision/.env.example`
- 其他任意 `services/decision/**` 文件
- `shared/contracts/**`
- `shared/python-common/**`
- `docker-compose.dev.yml`
- 任一 `.env.example`
- `runtime/**`
- `logs/**`
- 任一真实 `.env`

特别裁定：

1. 本批不批准顺手清理 researcher_loader 的实现细节。
2. 本批不批准把 researcher URL 配置样例并入当前代码批次；`.env.example` 必须继续走 D3 单独预审与单独签发。
3. 本批不批准把旧的 `test_researcher_integration.py` 一并改造成新链路验证面。

---

## 6. 验收标准

### 6.1 行为验收

1. `services/decision/src/llm/context_loader.py` 不再请求 Mini `:8105/api/v1/researcher/report/latest`。
2. `services/decision/src/research/news_scorer.py` 不再把 `DATA_SERVICE_URL` 当 researcher 报告源。
3. `services/decision/src/llm/pipeline.py` 初始化 `ResearcherLoader` 时不再传入 `DATA_SERVICE_URL`。
4. `DATA_SERVICE_URL` 继续只承担 data 行情与上下文供数职责，不再复用为 researcher 报告消费源。
5. 本批不得引入白名单外文件改动。

### 6.2 最小验证要求

执行 Agent 至少完成以下最小验证：

1. `pytest services/decision/tests/test_llm_context.py -q`
2. `pytest services/decision/tests/test_llm_pipeline.py -q`
3. 在 handoff 中明确说明 Mini researcher latest 旧链路已从上述 3 个源码文件中移除。

---

## 7. 进入签发结论

**是否允许进入 Jay.S 文件级 Token 签发：是。**

签发口径：

- 任务类型：P1 单服务标准流程
- 服务归属：`services/decision/**`
- 执行 Agent：决策
- Token 范围：仅限本 review 冻结的 5 个文件

补充限制：

1. `services/decision/src/llm/researcher_loader.py`、`services/decision/src/core/settings.py`、`services/decision/tests/test_researcher_integration.py` 当前均不批准进入签发。
2. 若后续需要新增上述任一文件，必须先补充预审，再申请新的 Jay.S 文件级 Token。