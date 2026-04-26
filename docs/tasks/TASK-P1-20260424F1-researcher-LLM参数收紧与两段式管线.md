# TASK-P1-20260424F1 — researcher LLM 参数收紧与两段式管线

## 任务类型
- P1 标准流程
- 服务归属：services/data
- 母任务（评估溯源）：2026-04-24 Atlas 对 researcher 24h 工作 ROI 只读评估
- 当前状态：项目架构师预审通过（REVIEW-PRE-20260424-TASK-P1-20260424F1.md）→ 待 Jay.S 签发 Token-A
- 注意：F1 完成后 Alienware researcher 将切换为 qwen3:14b-q4_K_M（量化版），与 Studio decision 统一

## 背景与根因
2026-04-24 只读体检发现 researcher 当前实际瓶颈不在抓取，而在 LLM 深分析阶段：

1. 单条新闻分析平均耗时 ≈ 120 秒（=单条 timeout 上限），日志大量 `[ANALYZE] LLM 超时/失败 [jin10] / [mini_news_api]`。
2. 单轮 stream cycle 入分析队列 19–37 条新闻，全部串行进 14B 深分析。
3. qwen3:14b 默认会输出 `<think>...</think>` 长推理段，2070 8GB 上推理 ~10 token/s，单条想 800–2000 token 正好等于 120s 超时。
4. Ollama 调用未显式设置 `num_predict` / `keep_alive`，且未在 prompt 层关闭 think 链（仅事后 strip）。
5. 当前所有新闻无前置筛选，绝大多数为重复转载或非品种相关噪声。
6. macro 报告 source_report.data_coverage 实际很厚，但下游 Decision 给 25 分，受 LLM 失败 / 字段稀疏拖累。

## 目标
1. 收紧三个 LLM 调用入口（新闻分析、K线分析、宏观分析）的 Ollama options：关闭 think 链、固定 num_predict、固定 num_ctx、设置 keep_alive、收紧单条 timeout。
2. 在 stream cycle 的新闻分析阶段引入"小模型前置筛选 + 14B 深分析"两段式管线：
   - 前置打分模型：qwen2.5:7b-instruct-q4_K_M（Alienware 本地，新增）
   - 深分析模型：保持 qwen3:14b
   - 评分阈值由配置控制，默认 ≥7/10 才进入深分析
3. 单轮 LLM 总耗时（37 条样本）从 ~50 分钟降到 ≤10 分钟。
4. 不破坏现有 Decision 消费链路（三类 fact 仍按 BATCH-YYYYMMDD-HH 入库）。

## 冻结白名单（最小必要）
1. `services/data/src/researcher/llm_analyzer.py` — 新闻分析 Ollama 调用参数收紧 + 接入前置筛选结果
2. `services/data/src/researcher/kline_analyzer.py` — K线分析 Ollama 调用参数收紧（num_predict/keep_alive/no_think）
3. `services/data/src/researcher/scheduler.py` — `_call_macro_llm` 内联 Ollama 调用参数收紧；stream cycle 接前置筛选钩子
4. `services/data/src/researcher/config.py` — 新增配置项：`OLLAMA_PREFILTER_MODEL`、`OLLAMA_PREFILTER_THRESHOLD`、`OLLAMA_NUM_PREDICT`、`OLLAMA_KEEP_ALIVE`、`OLLAMA_NEWS_TIMEOUT`
5. `services/data/src/researcher/prompts.py` — 新增前置筛选 prompt 模板；现有 prompt 增加 `/no_think` 指令
6. **新增文件**：`services/data/src/researcher/news_prefilter.py` — 两段式管线第一段实现（小模型 0–10 分打分器）
7. `services/data/.env.example` — 新增上述环境变量样例

## 明确排除（本批次不动）
1. `shared/contracts/**`（fact schema 不变）
2. `services/decision/**`（消费侧不动）
3. `services/data/src/researcher/daily_stats.py`（stream cycle 接回 daily_stats 走另一单 F2）
4. `services/data/run_researcher_server.py`（服务入口不改）
5. `services/data/src/researcher/queue_manager.py`、`shared_queue.py`、`memory_db.py`
6. 任何 `runtime/`、`logs/`、真实 `.env`、Mini 上的文件

## 验收标准
1. 单条 14B 深分析平均耗时 ≤ 25 秒（从 ~120s 降下来）。
2. 单轮 stream cycle 中进入 14B 深分析的新闻条数 ≤ 全量的 30%（其余被前置筛选过滤）。
3. `[ANALYZE] LLM 超时/失败` 日志条数下降 ≥ 80%。
4. researcher /reports/latest 返回的 NEWS / MACRO / FUTURES 报告字段完整性不低于改造前。
5. Decision /api/v1/research/facts/latest 三类 fact 仍能正常入库（BATCH-YYYYMMDD-HH 命名）。
6. 新增 qwen2.5:7b-instruct-q4_K_M 已在 Alienware 本地 Ollama 可用（`ollama list` 可见）。

## 建议最小验证
- 在 Alienware 上对比同一条新闻在改造前后的 LLM 调用耗时（curl `/api/generate` 时间戳对照）。
- 抓取改造后第一轮 stream cycle 的 task_stdout.log，统计 `[PREFILTER]` 与 `[ANALYZE]` 日志条数比例。
- Studio 端 curl `http://192.168.31.142:8104/api/v1/research/facts/latest` 验证 fact 仍按时入库。

## 执行顺序与责任
1. **PRE（本单）**：Atlas 完成 → 项目架构师预审 → Jay.S 签 Token
2. **拉模型**：后台已在 Alienware 启动 `ollama pull qwen2.5:7b-instruct-q4_K_M`（无代码变更，无需 Token）
3. **实施**：执行 Agent = `数据`（services/data 归属）
4. **复核**：Atlas 复核 → 项目架构师终审 → Lockback → 独立提交 → rsync 同步 Alienware

## 风险与回滚
- **风险**：前置筛选阈值过严会丢真信号。**对策**：阈值走 env，默认 7，先观察 24h 再调。
- **风险**：qwen2.5:7b 与 qwen3:14b 在 8GB 显存上同时常驻可能 OOM。**对策**：用 keep_alive 错峰；如不可行，降级为按需 load+1m keep_alive。
- **回滚**：保留 `OLLAMA_PREFILTER_ENABLED=false` 开关，一键退回单段式。

## 关联后续任务
- TASK-P1-20260424F2：stream cycle 接回 daily_stats（解决评估盲区）
- TASK-P1-20260424F3：Decision macro 评分识别 source_report.data_coverage（解决评分失真）
- TASK-P1-20260424F4：Studio QLoRA 微调 qwen3:14b 固化 JSON schema（依赖本单完成 + 2 周生产数据积累）
