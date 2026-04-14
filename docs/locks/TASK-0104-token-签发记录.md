# TASK-0104 Token 签发记录

【签名】Atlas  
【时间】2026-04-15  
【设备】MacBook  
【预审报告】docs/reviews/REVIEW-TASK-0104-PRE.md  

---

## 签发总览（2026-04-15 重签 — 原始 token 文件字段为空，已替换）

> ⚠️ 旧 token（tok-97335b68 / tok-54f501ef）文件字段为空，validate 会失败。已重新签发含完整文件列表的替代 token，Claude 必须使用下表新 token。

| # | Token ID | 批次 | Agent | 文件数 | 状态 |
|---|----------|------|-------|--------|------|
| 1（旧） | ~~`tok-97335b68-9929-4633-b938-0049a205f869`~~ | D1（data 侧） | Claude-Code | 0 | ⚠️ 已替代 |
| 2（旧） | ~~`tok-54f501ef-db44-404d-8fc5-ab5d81c99685`~~ | D2（decision 侧） | Claude-Code | 0 | ⚠️ 已替代 |
| 3 | `tok-d8f23d88-c183-45ba-8a59-8ad5700bfdb3` | D1（data 侧）**新** | Claude-Code | 6 | 🔒 已锁回 |
| 4 | `tok-6f298133-7364-44dd-a69c-1cebc10402e5` | D2（decision 侧）**新** | Claude-Code | 4 | 🔒 已锁回 |

---

## Token-1: D1 — data 侧夜间预读 + context API

| 字段 | 值 |
|------|-----|
| token_id | `tok-97335b68-9929-4633-b938-0049a205f869` |
| task_id | TASK-0104 |
| agent | Claude-Code |
| action | edit |
| review_id | REVIEW-TASK-0104-PRE |
| ttl | 4320 分钟（3天） |
| issued_at | 2026-04-15 |
| 状态 | 🔒 locked（approved，2026-04-15） |

**白名单（6 文件）：**

| 文件 | 操作 |
|------|------|
| `services/data/src/scheduler/data_scheduler.py` | 修改 — 添加 21:00 夜间预读钩子 |
| `services/data/src/scheduler/preread_generator.py` | 新建 — 四角色摘要生成器 |
| `services/data/src/api/routes/context_route.py` | 新建 — `GET /api/v1/context/daily` 路由 |
| `services/data/src/main.py` | 修改 — 注册 context_route |
| `services/data/src/notify/dispatcher.py` | 修改 — 添加 PREREAD_DONE/PREREAD_FAIL |
| `services/data/tests/test_preread.py` | 新建 — 基础测试 |

> ⚠️ **Claude 注意**：`check_token_access` 调用时 agent 必须填 `Claude-Code`，文件路径为 `services/data/src/main.py`（不是 `src/api/main.py`），模块名为 `src/notify/dispatcher.py`（不是 `src/notifications/`） — 2026-04-15 已确认验证失败原因为路径错误，Token 本身完全有效。

**执行结果：** commit `802c1f7`；`pytest services/data/tests/test_preread.py -q` 通过；Mini 已同步，`preread_generator` 将于 21:00 自动首次运行。

---

## Token-2: D2 — decision 侧 LLM 上下文注入

| 字段 | 值 |
|------|-----|
| token_id | `tok-54f501ef-db44-404d-8fc5-ab5d81c99685` |
| task_id | TASK-0104 |
| agent | Claude-Code |
| action | edit |
| review_id | REVIEW-TASK-0104-PRE |
| ttl | 4320 分钟（3天） |
| issued_at | 2026-04-15 |
| 状态 | 🔒 locked（approved，2026-04-15） |

**白名单（4 文件）：**

| 文件 | 操作 |
|------|------|
| `services/decision/src/llm/context_loader.py` | 新建 — TTL 缓存 + HTTP 拉取 |
| `services/decision/src/llm/pipeline.py` | 修改 — 按角色注入上下文 |
| `services/decision/src/llm/prompts.py` | 修改 — 四角色模板加上下文占位符 |
| `services/decision/tests/test_llm_context.py` | 新建 — 上下文注入测试 |

**执行结果：** commit `d356511`；`pytest services/decision/tests/test_llm_context.py -q` 通过；Studio 已同步，待服务重启后生效。

---

## 架构裁定备忘（来自 REVIEW-TASK-0104-PRE）

| 决策点 | 裁定 |
|--------|------|
| 文件共享 | data API 暴露 `GET /api/v1/context/daily`，decision HTTP 拉取 |
| 缓存策略 | decision 启动时拉取一次，内存缓存，TTL=8h |
| contracts | 不走 shared/contracts，data 单向暴露聚合摘要 |
| watchlist 范围 | 仅当前 watchlist（~30 只），非全量 A 股 |
| 降级策略 | data 不可用时 LLM 调用降级为无上下文模式 |
