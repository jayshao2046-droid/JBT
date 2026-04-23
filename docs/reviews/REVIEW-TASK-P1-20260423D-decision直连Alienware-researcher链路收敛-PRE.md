# REVIEW-TASK-P1-20260423D-decision直连Alienware-researcher链路收敛-PRE

- 审核人：项目架构师
- 审核时间：2026-04-23
- 对应任务：TASK-P1-20260423D
- 审核类型：标准预审（P1 / 跨服务）

---

## 1. 审核结论

结论：当前任务单按现状不允许直接进入 Jay.S 文件级 Token 签发。

裁定原因：

1. 本事项已由只读事实确认属于跨服务任务，同时涉及 services/data 和 services/decision，两端不能按单一服务任务直接签发。
2. 当前候选白名单把 data 修复、decision 解耦、decision 配置样例更新合并为一张清单，不符合一件事一审核一上锁和单服务优先拆批的治理要求。
3. 候选白名单内的 services/decision/tests/test_researcher_integration.py 已明显滞后于当前实现口径，直接沿用会把本批验证面做大且做偏。

当前预审结论不是否定根因，而是要求先拆分后签发。

允许进入后续签发的前提：

1. 先把当前任务拆为最小跨服务子批次。
2. 每个子批次分别冻结文件白名单。
3. decision 的 P0 文件 services/decision/.env.example 必须独立于 decision 代码批次单独签发。

---

## 2. 服务边界与模式裁定

### 2.1 是否跨服务

是，属于标准流程下的跨服务任务。

只读事实：

1. services/data/run_researcher_server.py 直接控制 Alienware researcher HTTP 端点 /reports/latest 和 /queue/status。
2. services/decision/src/llm/context_loader.py、services/decision/src/research/news_scorer.py、services/decision/src/llm/pipeline.py 分别控制 decision 侧 researcher 报告消费路径。
3. 上述两组控制点分别落在 data 和 decision 两个服务目录，不能按单服务热修处理。

### 2.2 适用模式

本事项只能走标准流程。

不适用原因：

1. 不是单服务事项，不能走 V2。
2. 不是 Jay.S 明确下达的单服务 U0 直修，不能走 U0。
3. 当前事项同时含 P1 服务文件和 decision 的 P0 文件 services/decision/.env.example，更不能按热修口径合并签发。

---

## 3. 只读事实核验

以下事实已在仓内实现与运行态上完成核验：

### 3.1 Alienware latest 端点当前实现

已核实 services/data/run_researcher_server.py 的 /reports/latest 当前直接执行：

1. queue_manager.get_pending(limit=1)
2. 取 pending[0]
3. 按该 file_path 直接读文件

因此它当前不是“找最新报告”，而是“找 pending 队列第一条记录”。

### 3.2 QueueManager 返回顺序

已核实 services/data/src/researcher/queue_manager.py 的 get_pending() 按 pending.jsonl 顺读追加到 records，读满 limit 即停止，没有倒序、没有按 added_at 排序、也没有跳过文件不存在记录。

因此 get_pending(limit=1) 的语义就是 FIFO 第一条，不是 latest。

### 3.3 运行态队列事实

已核实运行时 GET 192.168.31.187:8199/queue/status 返回：

1. pending_count = 11
2. pending_reports 第一条 file_path = D:\\researcher_reports\\2026-04-18\\01-00.json

### 3.4 运行态 latest 失败事实

已核实运行时 GET 192.168.31.187:8199/reports/latest 返回：

1. detail = 报告文件不存在: D:\\researcher_reports\\2026-04-18\\01-00.json

这与 3.3 的 FIFO 第一条完全对齐，证明 latest 当前确实被 stale pending 记录阻塞。

### 3.5 decision 侧仍走 Mini researcher 旧链路

已核实：

1. services/decision/src/llm/context_loader.py 仍请求 Mini :8105 的 /api/v1/researcher/report/latest。
2. services/decision/src/research/news_scorer.py 仍把 DATA_SERVICE_URL 当 researcher 报告源使用，并访问 /api/v1/researcher/report/latest。
3. services/decision/src/llm/pipeline.py 仍读取 DATA_SERVICE_URL 并传给 ResearcherLoader。

### 3.6 researcher_loader 当前实现状态

已核实 services/decision/src/llm/researcher_loader.py 已按 Alienware researcher API 风格实现：默认基址为 192.168.31.187:8199，并请求 /reports/latest。

因此 decision 侧问题不在 ResearcherLoader 本体，而在上游仍把 data URL 与 researcher URL 绑在一起。

---

## 4. 根因判断

### 4.1 根因一：Alienware latest 语义实现错误

根因成立。

当前 /reports/latest 实现并没有解析“最新且可读取的报告”，而是直接拿 pending 队列 FIFO 第一条记录。由于第一条记录已指向不存在的历史文件，端点稳定返回 404。

该根因由以下两项共同锁定：

1. run_researcher_server.py 中 /reports/latest 的控制逻辑。
2. queue_manager.py 中 get_pending() 的 FIFO 行为。

### 4.2 根因二：decision 侧 researcher 源与 data 源混绑

根因成立。

当前 decision 把 DATA_SERVICE_URL 同时承担两类职责：

1. data 行情和上下文供数
2. researcher 报告消费

这直接导致同一服务内出现两条 researcher 链路：

1. ResearcherLoader 已准备直连 Alienware :8199
2. context_loader 和 news_scorer 仍回到 Mini :8105 researcher API

因此即便修好 Alienware latest，若不同时解耦 decision 的 researcher URL，链路仍不会收敛。

### 4.3 非根因项裁定

以下项当前不构成本批必须改动的根因控制面：

1. services/data/src/researcher/queue_manager.py 本身不是必须修改面，当前问题可在 run_researcher_server.py 内完成 latest 语义修正。
2. services/decision/src/llm/researcher_loader.py 已符合 Alienware API 风格，不是当前直接故障点。
3. services/decision/src/core/settings.py 不是当前最小改动必经面，若后续要统一进 settings，再另补预审。

---

## 5. 白名单裁定

### 5.1 对原候选白名单的裁定

原候选白名单不批准按单任务整体冻结。

理由：

1. 它跨了 data 与 decision 两个服务。
2. 它把 services/decision/.env.example 这个 P0 文件与 P1 代码文件混在同一签发集合。
3. 它纳入了 services/decision/tests/test_researcher_integration.py，但该文件当前仍写死 Mini 8105 口径，且 mock 的是 requests.get，而仓内 ResearcherLoader 实现使用 httpx.Client；它不是当前最小、最直接的验证面。

### 5.2 最终冻结方式

当前预审将白名单冻结为 3 个待拆分子批次；只有按下述拆分重建任务后，才允许进入签发。

#### 子批次 A：data 单服务批次

服务归属：services/data

冻结白名单：

1. services/data/run_researcher_server.py

裁定说明：

1. 当前 latest 语义错误的直接控制点就在该文件。
2. 不批准把 services/data/src/researcher/queue_manager.py 一并纳入；若实施中证明必须改 queue_manager.py，说明当前最小控制点判断被反证，必须回到项目架构师补充预审。
3. 当前仓内没有与该脚本完全同面的现成窄测文件，因此本批验收允许采用运行态 HTTP 探针作为最小验证主证据。

#### 子批次 B：decision 代码收敛批次

服务归属：services/decision

冻结白名单：

1. services/decision/src/llm/context_loader.py
2. services/decision/src/research/news_scorer.py
3. services/decision/src/llm/pipeline.py
4. services/decision/tests/test_llm_context.py
5. services/decision/tests/test_llm_pipeline.py

裁定说明：

1. 这 3 个源码文件正好覆盖用户点名的全部 decision 控制点。
2. test_llm_context.py 适合承接 context_loader 相关 researcher URL 断言。
3. test_llm_pipeline.py 适合承接 pipeline 初始化时 ResearcherLoader 基址解耦断言。
4. 不批准纳入 services/decision/tests/test_researcher_integration.py；它当前口径滞后，修它会把本批范围扩展为旧测试体系清理，不属于本批最小目标。

#### 子批次 C：decision 配置样例批次

服务归属：services/decision

冻结白名单：

1. services/decision/.env.example

裁定说明：

1. 该文件属于 P0 保护路径，必须独立于 decision 代码批次单独签发。
2. 本批仅允许补齐 researcher 专用 URL 配置说明，不得顺手改动其他环境变量语义。

---

## 6. 明确排除项

以下文件或范围当前明确排除：

1. services/data/src/researcher/queue_manager.py
2. services/decision/src/llm/researcher_loader.py
3. services/decision/src/core/settings.py
4. services/decision/tests/test_researcher_integration.py
5. services/data/src/main.py
6. shared/contracts/**
7. shared/python-common/**
8. docker-compose.dev.yml
9. .github/**
10. runtime/**
11. logs/**
12. 任一真实 .env
13. 任一跨设备文件系统直读方案，包括让 decision 直接读取 Alienware D 盘

特别裁定：

1. 不允许让 decision 直接挂载、SMB 读取、ssh 读取或其它形式跨设备读取 D:\\researcher_reports。
2. 不允许借本批顺手回头改 Mini researcher store、Mini data main 路由或跨服务契约。

---

## 7. 验收标准

### 7.1 data 子批次验收

1. GET 192.168.31.187:8199/reports/latest 在存在有效报告时返回 200。
2. latest 结果不得再被 D:\\researcher_reports\\2026-04-18\\01-00.json 这类 stale pending 第一条阻塞。
3. 即使 pending 队列中存在文件不存在记录，latest 也必须能跳过不可读旧记录，解析到最新且存在的报告。

### 7.2 decision 代码子批次验收

1. services/decision/src/llm/context_loader.py 不再请求 Mini researcher latest。
2. services/decision/src/research/news_scorer.py 不再把 DATA_SERVICE_URL 当 researcher 报告源。
3. services/decision/src/llm/pipeline.py 初始化 ResearcherLoader 时不再传入 DATA_SERVICE_URL。
4. DATA_SERVICE_URL 仍仅承担 data 行情与上下文供数职责，不得被 researcher 报告读取复用。
5. 窄测最少通过：
   - pytest services/decision/tests/test_llm_context.py -q
   - pytest services/decision/tests/test_llm_pipeline.py -q

### 7.3 decision 配置样例子批次验收

1. services/decision/.env.example 明确存在 researcher 专用 URL 配置说明。
2. researcher 专用 URL 默认值与当前运行态口径一致，指向 Alienware 8199。
3. 本批不得顺手修改与 researcher URL 无关的其他配置说明。

---

## 8. 进入签发裁定

### 8.1 当前任务单是否可直接签发

否。

### 8.2 拆分后是否可签发

可以，但仅限以下前提同时满足：

1. 先拆成子批次 A、B、C。
2. 每个子批次各自独立建单或至少独立冻结白名单。
3. services/decision/.env.example 继续按 P0 单文件单独签发。
4. 执行 Agent 严格遵守服务隔离，不得跨服务顺手修复。

最终裁定：

1. 根因判断成立。
2. 当前任务确属跨服务任务。
3. 原候选白名单不够小，也不够合理。
4. 只有按本预审冻结的 3 个子批次重建签发面后，才允许进入 Jay.S 文件级 Token 签发。