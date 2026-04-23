# TASK-P1-20260423D — decision 直连 Alienware researcher 链路收敛

## 任务类型
- P1 标准流程
- 服务边界：`services/decision/**` + `services/data/run_researcher_server.py`
- 当前状态：预审已完成，需拆分为 D1 / D2 / D3 子批次后再进入签发

## 预审裁定摘要
- `docs/reviews/REVIEW-TASK-P1-20260423D-decision直连Alienware-researcher链路收敛-PRE.md` 已确认根因成立。
- 当前合单不允许直接进入 Jay.S 文件级 Token 签发。
- 必须拆分为 3 个子批次：
  1. D1：data 单文件修复 Alienware `/reports/latest` 语义
  2. D2：decision 代码链路解耦
  3. D3：decision `.env.example` 单文件配置样例更新

## 背景
- 用户要求缩短 researcher 报告消费链路：Alienware 研究员从 data 采数后在本地 `D:\researcher_reports` 生成研报，decision 侧不再通过 Mini data researcher 接口中转研报读取。
- 只读核对确认：Alienware 仍是 researcher 主落盘节点，Mini 当前 `report_rows=0`，不是本地产生研报。
- 同时确认现有实现仍存在双链路混用：
  1. `services/decision/src/llm/researcher_loader.py` 已按 Alienware `:8199/reports/latest` 风格读取。
  2. `services/decision/src/llm/context_loader.py` 和 `services/decision/src/research/news_scorer.py` 仍从 Mini `:8105/api/v1/researcher/report/latest` 读取研报摘要。
  3. `services/decision/src/llm/pipeline.py` 初始化 `ResearcherLoader` 时仍把 `DATA_SERVICE_URL` 传给 researcher loader，导致 data API 与 researcher API 口径混绑。

## 最新只读结论

### 1. 真实目标口径
- 按当前治理与服务隔离规则，decision **不能直接读取 Alienware 的 D 盘文件系统**。
- 本任务的合规技术落点应为：
  - Alienware researcher 服务继续以 `D:\researcher_reports` 为主落盘。
  - decision 统一直连 Alienware researcher API 读取研报。
  - Mini data 继续承担行情/上下文供数，不再承担 decision 的 researcher 研报中转口。

### 2. Alienware latest 端点当前存在真实阻塞
- 运行时探针：`GET http://192.168.31.187:8199/health` 返回 `status=ok`。
- 运行时探针：`GET http://192.168.31.187:8199/reports/latest` 返回 `404 报告文件不存在: D:\researcher_reports\2026-04-18\01-00.json`。
- 继续只读确认 `GET /queue/status` 后发现：
  - `pending_count=11`
  - `pending_reports[0].file_path = D:\researcher_reports\2026-04-18\01-00.json`
- 本地代码根因已定位：
  - `services/data/run_researcher_server.py` 的 `/reports/latest` 不是扫描 D 盘最新报告，而是直接调用 `queue_manager.get_pending(limit=1)`。
  - `services/data/src/researcher/queue_manager.py` 的 `get_pending()` 按 JSONL 文件写入顺序顺读返回，即 FIFO；因此 latest 实际取到的是最旧 pending 记录，而不是最新可读报告。

## 根因判断

### A. decision 侧根因
- 研报源没有独立配置，`DATA_SERVICE_URL` / `DATA_API_URL` 同时承担“行情 data API”和“researcher API”两种职责。
- 结果是：部分 decision 路径已接 Alienware researcher API，部分路径仍依赖 Mini researcher latest，形成混用。

### B. Alienware researcher 侧根因
- `/reports/latest` 的“latest”语义实现错误：当前返回最旧 pending 队列项，而不是最新且存在的报告文件。
- 结果是：即便 decision 改为直连 Alienware researcher API，当前 latest 端点也可能先被 stale queue path 阻塞。

## 任务目标
1. 修正 Alienware researcher `/reports/latest`，使其返回“最新且可读取”的报告，而不是 FIFO 队列第一条旧记录。
2. decision 侧 researcher 读取统一改为独立的 `RESEARCHER_SERVICE_URL`，不再复用 `DATA_SERVICE_URL`。
3. `context_loader.py` 与 `news_scorer.py` 不再请求 Mini `/api/v1/researcher/report/latest`。
4. `pipeline.py` 初始化 `ResearcherLoader` 时改为传入 researcher 专用 URL。
5. `.env.example` 补齐 researcher 专用配置说明。

## 预审候选白名单
- `services/data/run_researcher_server.py`
- `services/decision/src/llm/context_loader.py`
- `services/decision/src/research/news_scorer.py`
- `services/decision/src/llm/pipeline.py`
- `services/decision/.env.example`
- `services/decision/tests/test_researcher_integration.py`
- `services/decision/tests/test_llm_context.py`

## 明确排除
- 不允许让 decision 直接挂载、SMB 读取或跨设备读取 Alienware `D:\researcher_reports` 文件系统。
- 不允许改动 `services/data/src/main.py`、Mini `services/data/**` researcher_store 逻辑或 `shared/contracts/**`。
- 不允许改动 `docker-compose.dev.yml`、`.github/**`、`runtime/**`、`logs/**`、任一真实 `.env`。
- 若实施中证明必须修改 `services/data/src/researcher/queue_manager.py`、`services/decision/src/core/settings.py` 或新增白名单外文件，必须回项目架构师补充预审。

## 验收标准
1. `GET http://192.168.31.187:8199/reports/latest` 在存在有效待处理报告时返回 200，且不再被最旧 stale queue path 阻塞。
2. `services/decision/src/llm/context_loader.py` 拉取研报摘要时使用 researcher 专用 URL，不再命中 Mini researcher latest。
3. `services/decision/src/research/news_scorer.py` 拉取研报时使用 researcher 专用 URL，不再命中 Mini researcher latest。
4. `services/decision/src/llm/pipeline.py` 初始化 `ResearcherLoader` 时不再把 `DATA_SERVICE_URL` 当作 researcher 源。
5. decision 相关窄测通过，且不引入跨服务 import、跨目录文件读取或共享契约改动。

## 建议最小验证
- `curl http://192.168.31.187:8199/reports/latest`
- `cd services/decision && pytest tests/test_researcher_integration.py tests/test_llm_context.py -q`
- 如需 data 侧最小验证，补充针对 `/reports/latest` 的局部行为测试或远端探针说明。

## 风险说明
- 本任务是跨服务联调，不符合单服务热修；必须走标准流程预审 + 文件级白名单 + Token。
- 当前仓库仍有多处历史脏变更，实施时必须严格按白名单切片，避免混入无关 runtime/db/jsonl 文件。

## 拆分结果
- 子批次任务 1：`docs/tasks/TASK-P1-20260423D1-data-Alienware-latest语义修复.md`
- 子批次任务 2：`docs/tasks/TASK-P1-20260423D2-decision-researcher直连解耦.md`
- 子批次任务 3：`docs/tasks/TASK-P1-20260423D3-decision-env-example补齐researcher-url.md`