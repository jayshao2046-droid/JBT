# TASK-P1-20260424E — researcher / decision 两地联调闭环

## 任务类型
- P1 标准流程
- 服务边界：services/data + services/decision
- 当前状态：待项目架构师预审

## 背景
- 用户已确认本轮目标不是继续做 researcher 局部优化，而是把 Mini -> Alienware researcher -> Decision -> 实操判断 的主链真正打通。
- 业务目标已明确收敛为 3 点：
  1. Mini 采集的数据必须被 researcher 实际消费。
  2. Alienware researcher 必须稳定产出三类研报：数据研报、情报研报、情绪研报。
  3. Decision 必须把 researcher 研报消化为最终判断依据并实际参与门控、仓位、风控或排序，而不是读完即丢。
- 用户进一步确认的运行原则：
  1. Alienware 自身期货分钟分析适合流式。
  2. Mini 定时采集完成后，应通过通知方式触发 researcher 拉取增量，而不是 researcher 主动轮询问询。
  3. 除“流式分钟触发 + Mini 完成事件触发”外，其余不必要定时、旧轮询、旧链路应收敛或下线。

## 已完成只读核查结论

### 1. researcher 现役主链已存在
- services/data/src/researcher/scheduler.py 的 execute_stream_cycle() 已包含：
  1. 刷新 Mini 上下文
  2. 注入 Mini news_api / news_rss
  3. 流式文章分析
  4. 日 K 级补充分析
  5. _push_rich_report_to_decision() 推送 news_report / futures_report / macro_report 到 Decision
- 结论：researcher 主链无需推倒重来，可直接作为本轮联调主干。

### 2. Mini callback 仍然打到旧 hourly 链
- services/data/run_researcher_server.py 的 /callback 当前收到 Mini 采集通知后，仍通过 trigger_research() 调用 execute_hourly()。
- trigger_research() 当前不是现役 stream 主链入口，而是旧整点兼容链入口。
- 结论：这与“采完即通知、事件驱动、砍旧轮询”的目标直接冲突，是 data 侧第一控制点。

### 3. Decision 当前仍是双消费混合
- Decision 已具备本地 ResearchStore 与 research query 查询面：
  1. services/decision/src/research/research_store.py
  2. services/decision/src/api/routes/research_query.py
- 但仍存在多处旧链直连 Alienware /reports/latest：
  1. services/decision/src/llm/context_loader.py
  2. services/decision/src/research/news_scorer.py
  3. services/decision/src/llm/researcher_loader.py
  4. services/decision/src/llm/pipeline.py
- 结论：Decision 尚未真正统一以本地研究库为 researcher 事实源。

### 4. 本轮可以先不触碰 shared/contracts
- 当前 researcher -> Decision 推送载荷已具备 news_report / futures_report / macro_report / rss_report / sentiment_report 等字段。
- 若本轮以“复用现有批次字段 + 在 Decision 本地研究库保留原始研报事实”为方案，则当前不需要先改 shared/contracts。
- 结论：本轮优先目标应是主链收敛，不应先扩展 shared/contracts。

## 根因判断

### A. data 侧根因
- Mini 完成采集后的通知还没有接入现役 stream 主链，而是回流到旧 execute_hourly()。
- 因此 researcher 仍同时存在：
  1. 后台 stream 主链
  2. callback 触发的 hourly 旧链
- 两条链并存，导致事件驱动语义不成立，旧定时链也无法真正下线。

### B. decision 侧根因
- Decision 一部分逻辑已经具备本地 ResearchStore 消费基础，另一部分逻辑仍把 Alienware /reports/latest 当作直接事实源。
- 结果是：
  1. researcher 报告被推送入库
  2. 但 context / scorer / pipeline 后段仍可能绕回 latest 旧链
  3. Decision 仍没有形成单一 researcher 事实源

### C. 联调层根因
- “三类研报”在业务目标上已明确，但在现有主链里仍没有形成一个统一的本地消费口径：
  1. 数据研报：以 futures_report 为主
  2. 情报研报：以 macro_report 及 Mini 各类上下文事实为主
  3. 情绪研报：以 news_report / rss_report / sentiment_report 为主
- 现状不是没有内容，而是这些内容没有在 Decision 本地研究库中形成统一引用面。

## 本轮任务目标
1. 把 Mini callback 从旧 hourly 链切换为现役 stream / 事件语义，不再让“采完即通知”绕回旧链。
2. 保持 researcher 现役 stream 主链不推倒重来，在原主干上稳定产出三类研报事实。
3. 把 researcher 推送到 Decision 的现有批次内容稳定写入本地 ResearchStore，保留足够的原始研报事实供后续消费。
4. 让 Decision 内所有 researcher 消费统一收敛到本地研究库 / research query，而不是继续直接拉取 Alienware /reports/latest。
5. 收敛或下线不必要的旧轮询、旧直连、旧 fallback 依赖，但不扩大到 shared/contracts、Mini data 主服务或部署文件。

## 拟拆分子批次

### 子批次 E1：data / Alienware 事件主链接管
- 服务归属：services/data
- 目标：
  1. callback 改为接入现役 stream / 事件语义
  2. 避免继续走 execute_hourly() 旧链
  3. 确保 researcher 三类研报主干仍由现役 stream 主链统一推送到 Decision
- 预审候选白名单：
  1. services/data/run_researcher_server.py
  2. services/data/src/researcher/scheduler.py
  3. services/data/tests/test_researcher_scheduler.py

### 子批次 E2：decision 本地研究库存证收敛
- 服务归属：services/decision
- 目标：
  1. 把 researcher 推送批次稳定写入本地 ResearchStore
  2. 保留 Decision 后续消费所需的三类研报原始事实或摘要事实
  3. 通过 research query 形成统一读取面
- 预审候选白名单：
  1. services/decision/src/api/routes/researcher_evaluate.py
  2. services/decision/src/research/research_store.py
  3. services/decision/src/api/routes/research_query.py
  4. services/decision/tests/test_research_extensions.py

### 子批次 E3：decision researcher 消费全面切库
- 服务归属：services/decision
- 目标：
  1. context_loader 不再直拉 /reports/latest
  2. news_scorer 不再直拉 /reports/latest
  3. ResearcherLoader / pipeline 后段不再把 Alienware latest 当作事实源
  4. Decision researcher 消费统一转向本地研究库 / research query
- 预审候选白名单：
  1. services/decision/src/llm/context_loader.py
  2. services/decision/src/research/news_scorer.py
  3. services/decision/src/llm/researcher_loader.py
  4. services/decision/src/llm/pipeline.py
  5. services/decision/tests/test_llm_context.py
  6. services/decision/tests/test_llm_pipeline.py

## 明确排除项
1. 不改 shared/contracts/**。
2. 不改 shared/python-common/**。
3. 不改 services/data/src/main.py 与 Mini data 主服务 researcher_store 旧中转逻辑。
4. 不改 docker-compose.dev.yml、.github/**、runtime/**、logs/**、任一真实 .env。
5. 不让 Decision 直接挂载、SMB 读取、ssh 读取或以其他方式跨设备读取 Alienware 磁盘文件。
6. 若实施中证明必须新增 shared/contracts/**、services/decision/.env.example、services/data/src/researcher/queue_manager.py 或其它白名单外文件，必须回项目架构师补充预审。

## 验收标准

### E1 验收
1. Mini callback 不再通过 trigger_research() 回流到 execute_hourly() 旧链。
2. researcher 现役 stream 主链仍可正常完成 Mini 上下文刷新、内容分析和推送 Decision。
3. callback 事件触发后，researcher 不再依赖额外的旧整点链才能完成联动。

### E2 验收
1. Decision 本地 ResearchStore 中可稳定看到最新 researcher 事实。
2. 至少能在本地统一查询到数据研报、情报研报、情绪研报对应事实源或聚合摘要。
3. 本地研究库存证保留足够字段供后续 LLM / scorer / pipeline 读取，而不是只留一份瞬时评分结果。

### E3 验收
1. context_loader 不再请求 Alienware /reports/latest。
2. news_scorer 不再请求 Alienware /reports/latest。
3. ResearcherLoader / pipeline 后段不再把 latest 直连当作 researcher 主事实源。
4. Decision researcher 相关窄测通过，且 researcher 消费统一落到本地研究库 / query 面。

## 建议最小验证
- services/data：pytest services/data/tests/test_researcher_scheduler.py -q
- services/decision：pytest services/decision/tests/test_research_extensions.py services/decision/tests/test_llm_context.py services/decision/tests/test_llm_pipeline.py -q
- 必要时补充最小 HTTP 探针或局部行为断言，证明 callback -> stream 与 Decision 切库已生效。

## 风险说明
1. 本事项是跨服务联调，不符合 U0 / V2，必须走标准流程。
2. 当前仓内存在其它未提交改动，实施时必须严格按白名单切片，避免混入无关变更。
3. 若 E2 证明现有 researcher -> Decision 批次字段无法承载本地库存证目标，必须暂停实施并回到项目架构师补充“是否需要 shared/contracts 预审”的裁定。

## 请求项目架构师裁定事项
1. 是否批准按 E1 / E2 / E3 三子批次冻结白名单。
2. 是否认可本轮先不触碰 shared/contracts，以“复用现有 researcher 批次字段 + Decision 本地库存证收敛”为最小闭环方案。
3. Decision 本地库存证批次是否允许把 services/decision/src/api/routes/research_query.py 与 services/decision/tests/test_research_extensions.py 一并纳入同一批次。