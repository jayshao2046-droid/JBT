# REVIEW-TASK-P1-20260424E-researcher-decision两地联调闭环-PRE

- 审核人：项目架构师
- 审核时间：2026-04-24
- 对应任务：TASK-P1-20260424E
- 审核类型：标准预审（P1 / 跨 services/data + services/decision）

---

## 1. 审核结论

结论：通过，允许按 E1 / E2 / E3 三子批次进入 Jay.S 文件级 Token 签发。

本次预审同时作出以下冻结裁定：

1. 本事项已由只读事实确认属于跨服务标准流程任务，只能按 data / decision 分批冻结，不能走 U0 或 V2。
2. 当前批准按 E1 / E2 / E3 三子批次推进，但白名单不按任务单候选清单原样照收；其中 E1 与 E3 均需收口。
3. 本轮允许先不触碰 `shared/contracts/**`，按“复用现有 researcher 批次字段 + Decision 本地库存证收敛”作为最小闭环方案推进。
4. `shared/contracts/**` 当前不需要单独预审；只有在实施中证明现有 `ReportBatchRequest` 字段与 Decision 本地库存证方案无法承载目标时，才允许回项目架构师补充 contracts 预审。
5. 推荐签发顺序固定为：E1 -> E2 -> E3。E3 依赖 E2 先把 Decision 本地研究库存证和统一查询面收口。

---

## 2. 服务边界与模式裁定

### 2.1 服务边界

本事项属于标准流程下的跨服务任务：

1. `services/data/run_researcher_server.py` 和 `services/data/src/researcher/scheduler.py` 控制 Alienware researcher 的 callback 入口与现役 stream 主链。
2. `services/decision/src/api/routes/researcher_evaluate.py`、`services/decision/src/research/research_store.py`、`services/decision/src/api/routes/research_query.py` 控制 Decision 本地研究库存证与查询面。
3. `services/decision/src/llm/context_loader.py`、`services/decision/src/research/news_scorer.py`、`services/decision/src/llm/pipeline.py` 控制 Decision 内 researcher 消费面。

因此当前事项不能按单服务任务整体签发，必须拆为子批次分服务冻结。

### 2.2 适用模式

本事项只能走标准流程。

不适用原因：

1. 事项横跨 `services/data/**` 与 `services/decision/**`，不符合 V2 的单服务前提。
2. 本事项不是 Jay.S 明确下达的单服务 U0 直修，不符合 U0 适用条件。
3. 当前目标包含 researcher 主链收敛、Decision 本地库存证和消费切库，属于标准联调，不属于单点热修。

---

## 3. 只读事实核验

### 3.1 callback 仍回流到旧 hourly 链

已核实 `services/data/run_researcher_server.py`：

1. `/callback` 当前收到 Mini 回调后直接执行 `await trigger_research(hour=hour)`。
2. `trigger_research()` 当前通过独立 event loop 执行 `scheduler.execute_hourly(hour=h)`。

因此 callback 当前进入的不是现役 stream 主链，而是旧 hourly 兼容入口。

### 3.2 现役 stream 主链已在 scheduler 内独立存在

已核实：

1. `run_researcher_server.py` 的 `_continuous_loop_thread()` 持续调用 `scheduler.execute_stream_cycle()`。
2. `services/data/src/researcher/scheduler.py` 的 `execute_stream_cycle()` 已负责：
   - 刷新 Mini 上下文
   - 注入 Mini `news_api` / `rss`
   - 流式文章分析
   - 盘后日 K 分析
   - `_push_rich_report_to_decision()` 推送 `news_report` / `futures_report` / `macro_report`

结论：现役主链已存在，本轮不需要推倒重写，只需要把 callback 接入现役 stream / 事件语义。

### 3.3 Decision researcher 路由已挂载，无需扩到 app 启动面

已核实 `services/decision/src/api/app.py`：

1. `researcher_evaluate_router` 已 include。
2. `research_query_router` 已 include。

结论：E2 不需要把 `services/decision/src/api/app.py`、`services/decision/src/main.py` 或其它启动文件并入白名单。

### 3.4 Decision 当前只保存评分结果，不是三类研报原始事实库

已核实 `services/decision/src/api/routes/researcher_evaluate.py`：

1. 当前对 `futures_report` / `stocks_report` / `news_report` / `macro_report` 做评分后，保存到 `ResearchStore` 的是 `result_record`，核心是评分结果和少量结构化字段。
2. 当前未把原始 report payload 作为本地事实完整保留。
3. 当前 `rss_report` 与 `sentiment_report` 虽在 `ReportBatchRequest` 中定义，但此路由尚未纳入处理。

结论：Decision 已有本地 store 落点，但还没有形成“可供后续 LLM / scorer / pipeline 统一消费的本地 researcher 事实库”。

### 3.5 ResearchStore / research_query 当前能力仍偏窄

已核实：

1. `services/decision/src/research/research_store.py` 当前提供 `save()`、`get_latest()`、`get_history()`、`get_all_latest()`、`get_macro_summary()`。
2. `services/decision/src/api/routes/research_query.py` 当前只暴露 latest / history / macro-summary 查询面。

结论：E2 需要在现有本地 store / query 面上做库存证收敛，但这是 Decision 服务内部演进，不构成当前必须修改 `shared/contracts/**` 的事实依据。

### 3.6 Decision researcher 消费面仍存在多处直连 Alienware latest

已核实：

1. `services/decision/src/llm/context_loader.py` 的 `get_l2_context()` 仍直接 GET `RESEARCHER_SERVICE_URL/reports/latest`。
2. `services/decision/src/research/news_scorer.py` 的 `_fetch_latest_report()` 仍直接 GET `RESEARCHER_SERVICE_URL/reports/latest`。
3. `services/decision/src/llm/pipeline.py` 初始化 `ResearcherLoader(RESEARCHER_SERVICE_URL)`，并在 `evaluate_researcher_report()` 中继续调用 `self.researcher_loader.get_latest_report()`。
4. 当前仓内对 `ResearcherLoader` 的实际使用点已只读核实为 `pipeline.py`。

结论：Decision 仍未形成“本地研究库 / query 为唯一 researcher 事实源”的统一消费口径。

### 3.7 现有旧测试中存在偏离当前主链的验证面

已核实：

1. `services/data/tests/test_researcher_scheduler.py` 仍围绕 `execute_segment()` / `execute_hourly()` / `generate_report()` / `_push_to_data_api()` 等旧链路编写，未覆盖 callback -> stream 主链。
2. `services/decision/tests/test_researcher_integration.py` 仍写死 `http://192.168.31.74:8105` 和旧 researcher API 口径，不适合本轮切库收敛直接复用。

结论：上述两份旧测试文件当前都不批准进入本轮白名单。

---

## 4. 根因判断

### 4.1 E1 根因：callback 没有接入现役 stream / 事件语义

根因成立。

现状是：

1. researcher 的现役主链已经在 `_continuous_loop_thread() -> execute_stream_cycle()` 上运行。
2. Mini callback 却仍通过 `trigger_research() -> execute_hourly()` 走旧 hourly 链。

因此 researcher 形成“现役 stream 主链 + callback 回流旧 hourly 链”的双链并存状态，事件驱动语义不成立。

### 4.2 E2 根因：Decision 本地 store 只有评分结果，没有统一库存证

根因成立。

现状是：

1. `researcher_evaluate.py` 已把 researcher 批次导入 `ResearchStore`。
2. 但当前导入的是评分结果记录，不是可供后续统一消费的三类研报原始事实 / 摘要事实。
3. `research_query.py` 现有查询面也还不足以表达“数据研报 / 情报研报 / 情绪研报”的统一本地读取口径。

因此 Decision 虽有本地 store，但还没有真正成为 researcher 事实源。

### 4.3 E3 根因：Decision researcher 消费仍多头直连远端 latest

根因成立。

现状是：

1. `context_loader.py` 直接读 Alienware latest。
2. `news_scorer.py` 直接读 Alienware latest。
3. `pipeline.py` 仍通过 `ResearcherLoader` 读取 Alienware latest。

因此即便 E2 完成入库，如果 E3 不做，Decision 内仍会同时存在“本地 store/query”与“远端 latest”两套 researcher 事实源。

### 4.4 contracts 不是当前最小闭环的先决根因

当前判断：不成立为本轮前置阻断。

理由：

1. 当前 `ReportBatchRequest` 已具备 `futures_report` / `news_report` / `macro_report` / `rss_report` / `sentiment_report` 等字段承载面。
2. 当前现役 stream 主链已实际推送 `news_report` / `futures_report` / `macro_report` 三类事实，已足以映射本轮最小闭环中的数据研报 / 情报研报 / 情绪研报。
3. E2 / E3 的核心工作是 Decision 服务内部的本地库存证与消费统一，不要求当前先扩跨服务契约。

因此本轮先不触碰 `shared/contracts/**` 是成立的。

---

## 5. 白名单裁定（按 E1 / E2 / E3）

### 5.1 E1：data / Alienware 事件主链接管

结论：通过，但不按候选清单原样照收；最终白名单收口为 2 个文件。

最终冻结白名单：

1. `services/data/run_researcher_server.py`
2. `services/data/src/researcher/scheduler.py`

裁定说明：

1. `run_researcher_server.py` 是 callback 入口与连续 stream 线程控制面，必属白名单。
2. `scheduler.py` 是 `execute_stream_cycle()` 与 `_push_rich_report_to_decision()` 的直接控制面。若要把 callback 安全接入现役 stream / 事件语义，不能假设只改 server 文件即可闭环。
3. 不批准 `services/data/tests/test_researcher_scheduler.py`。理由是它当前仍是旧 hourly / segment 验证面，会把本批验证目标做偏。

### 5.2 E2：Decision 本地研究库存证收敛

结论：通过，候选 4 文件白名单予以保留。

最终冻结白名单：

1. `services/decision/src/api/routes/researcher_evaluate.py`
2. `services/decision/src/research/research_store.py`
3. `services/decision/src/api/routes/research_query.py`
4. `services/decision/tests/test_research_extensions.py`

裁定说明：

1. `researcher_evaluate.py` 控制 researcher 批次如何写入本地 store，是 E2 的直接入口。
2. `research_store.py` 控制本地库存证结构，是 E2 的直接存储面。
3. `research_query.py` 已挂载到现有 app，且是对外统一读取面的直接控制点。
4. `test_research_extensions.py` 当前虽未覆盖本地库存证，但它是现有最接近 Decision research 扩展面的窄测落点，可用于补充 E2 最小验证；当前不需要新增 `api/app.py` 或新建测试文件作为前置条件。

### 5.3 E3：Decision researcher 消费全面切库

结论：通过，但不按候选 6 文件原样照收；必须收口到 5 文件以内。

最终冻结白名单：

1. `services/decision/src/llm/context_loader.py`
2. `services/decision/src/research/news_scorer.py`
3. `services/decision/src/llm/pipeline.py`
4. `services/decision/tests/test_llm_context.py`
5. `services/decision/tests/test_llm_pipeline.py`

裁定说明：

1. `WORKFLOW.md` 默认单任务最多 5 个文件；候选 E3 的 6 文件清单不批准原样签发。
2. 当前仓内 `ResearcherLoader` 的实际使用点已核实只剩 `pipeline.py`。因此优先在 `pipeline.py` 层切断其对远端 latest 的事实源依赖，而不是把 `researcher_loader.py` 一并纳入本批。
3. `context_loader.py`、`news_scorer.py`、`pipeline.py` 正好覆盖当前仍在主动直连 Alienware latest 的 3 个实际消费控制点。
4. 若实施中证明必须同步修改 `services/decision/src/llm/researcher_loader.py` 才能完成 E3，则当前 E3 预审立即失效，必须回项目架构师补充预审或拆出 E3-SUP。

---

## 6. 明确排除项

以下文件或范围当前明确排除，不得混入本轮：

1. `services/data/src/main.py`
2. `services/data/tests/test_researcher_scheduler.py`
3. `services/decision/src/api/app.py`
4. `services/decision/src/llm/researcher_loader.py`
5. `services/decision/tests/test_researcher_integration.py`
6. `services/decision/.env.example`
7. `shared/contracts/**`
8. `shared/python-common/**`
9. `docker-compose.dev.yml`
10. `.github/**`
11. `runtime/**`
12. `logs/**`
13. 任一真实 `.env`
14. 任一部署、挂载、远端磁盘直读方案

特别裁定：

1. 不允许把 `services/data/src/main.py` 混进来；当前 researcher callback / stream 主链与 Decision 本地库存证收敛不需要它。
2. 不允许把 `shared/contracts/**` 混进来；当前最小闭环先按现有 researcher 批次字段和 Decision 内部收敛推进。
3. 不允许把 `services/decision/.env.example` 混进来；本轮并未形成必须新增配置样例的源码事实依据。
4. 不允许把任何 deploy / runtime / logs / 远端文件系统读取方案混进来；Decision 只能通过本地 store / query 或既有 API 消费 researcher 事实。

---

## 7. 验收标准

### 7.1 E1 验收

1. Mini callback 不再通过 `trigger_research() -> execute_hourly()` 回流旧 hourly 链。
2. callback 进入的必须是现役 stream / 事件语义，而不是再补一条独立旧链。
3. `execute_stream_cycle()` 主链仍可完成 Mini 上下文刷新、Mini news_api/rss 注入、分析和推送 Decision。
4. 本批最小验证应至少包含 callback 触发后的局部行为证据；若无合格窄测，不以旧 `test_researcher_scheduler.py` 代替。

### 7.2 E2 验收

1. Decision 本地 `ResearchStore` 中可稳定保留 researcher 三类事实的本地库存证，而不是只剩瞬时评分值。
2. 至少能通过本地统一查询面稳定读到：
   - 数据研报：以 `futures_report` 为主
   - 情报研报：以 `macro_report` 为主
   - 情绪研报：以 `news_report` 为主
3. `research_query.py` 提供的读取面足以被后续 LLM / scorer / pipeline 复用。
4. 最小验证应至少覆盖 `pytest services/decision/tests/test_research_extensions.py -q` 或等价窄测。

### 7.3 E3 验收

1. `context_loader.py` 不再把 Alienware `/reports/latest` 作为 researcher 主事实源。
2. `news_scorer.py` 不再把 Alienware `/reports/latest` 作为 researcher 主事实源。
3. `pipeline.py` 后段不再通过现有远端 latest 口径消费 researcher 主事实源。
4. Decision researcher 消费统一落回本地 `ResearchStore` / `research_query`。
5. 最小验证应至少通过：
   - `pytest services/decision/tests/test_llm_context.py -q`
   - `pytest services/decision/tests/test_llm_pipeline.py -q`

---

## 8. 进入签发裁定

是否允许进入 Jay.S 文件级 Token 签发：允许。

签发口径：

1. E1：`services/data/**` 单服务批次，执行 Agent 固定为数据。
2. E2：`services/decision/**` 单服务批次，执行 Agent 固定为决策。
3. E3：`services/decision/**` 单服务批次，执行 Agent 固定为决策。

进入签发的附加限制：

1. E1 / E2 / E3 只能按本预审冻结白名单签发，不得扩大。
2. E3 必须保持 5 文件上限；若要新增 `services/decision/src/llm/researcher_loader.py` 或其它第 6 个文件，必须补充预审。
3. 当前不需要 `shared/contracts/**` 预审；只有当 E2 明确证明现有批次字段无法承载 Decision 本地库存证目标时，才允许暂停实施并补做 contracts 预审。
4. 一旦实施中出现 `services/data/src/main.py`、`services/decision/.env.example`、`shared/contracts/**`、部署文件、`runtime/**`、`logs/**` 或任一真实 `.env` 的新增需求，当前 PRE 立即失效，必须回项目架构师补充预审。