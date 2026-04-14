# REVIEW-TASK-0104-PRE — 预审记录

| 字段 | 值 |
|------|------|
| **review-id** | REVIEW-TASK-0104-PRE |
| **任务** | TASK-0104 data 预读投喂决策端 |
| **审核人** | Atlas（快裁代行，Jay.S 委托） |
| **时间** | 2026-04-15 |
| **结论** | ✅ 预审通过，可签发 Token |

---

## 架构裁定

### 4 项前置问题裁定

| 问题 | 裁定 | 理由 |
|------|------|------|
| 文件共享方式 | data API 新路由 `GET /api/v1/context/daily` | data/decision 部署于不同容器，runtime 目录不同机；API 方式保持服务隔离 |
| 触发时机 | decision 启动时拉取到内存，TTL=8h，LLM 调用时校验新鲜度 | 避免每次 LLM 调用都触发 HTTP 请求；8h 覆盖交易日生命周期 |
| contracts 契约 | **不走 shared/contracts** | 预读摘要是 data 单向暴露的聚合端点，非 decision 与 data 双向交互的业务契约；response schema 在 data 服务内定义即可 |
| watchlist 范围 | 仅当前 watchlist 动态范围（~30只） | 全量 A 股数据量 10x，夜间生成摘要时间过长；watchlist 已覆盖决策端实际标的 |

---

## 文件白名单（分两批）

### D1 批次 — data 侧（先执行）

| 文件 | 操作 |
|------|------|
| `services/data/src/scheduler/data_scheduler.py` | 修改 — 添加夜间 21:00 预读钩子 |
| `services/data/src/scheduler/preread_generator.py` | 新建 — 四角色摘要生成器（researcher/l1/l2/analyst） |
| `services/data/src/api/routes/context_route.py` | 新建 — `GET /api/v1/context/daily` 路由 |
| `services/data/src/main.py` | 修改 — 注册 context_route |
| `services/data/src/notify/dispatcher.py` | 修改 — 添加 PREREAD_DONE / PREREAD_FAIL 通知类型 |
| `services/data/tests/test_preread.py` | 新建 — 基础测试（摘要生成 + API 响应格式） |

### D2 批次 — decision 侧（D1 完成后执行）

| 文件 | 操作 |
|------|------|
| `services/decision/src/llm/context_loader.py` | 新建 — TTL 缓存 + `GET /api/v1/context/daily` 拉取 |
| `services/decision/src/llm/pipeline.py` | 修改 — 按角色注入上下文到 prompt |
| `services/decision/src/llm/prompts.py` | 修改 — 新增上下文注入占位符（researcher/l1/l2/analyst 四角色模板） |
| `services/decision/tests/test_llm_context.py` | 新建 — 测试上下文注入逻辑 |

---

## 验收标准

**D1 验收：**
1. `pytest services/data/tests/test_preread.py -q` 通过
2. `GET /api/v1/context/daily` 返回 200，包含 `researcher_context / l1_briefing / l2_audit_context / analyst_dataset / ready_flag` 字段
3. 飞书 PREREAD_DONE 通知类型可正常路由

**D2 验收：**
1. `pytest services/decision/tests/test_llm_context.py -q` 通过
2. `POST /api/v1/llm/research` 调用时，pipeline 注入的 prompt 包含 researcher 上下文
3. 无 HTTP 调用失败时（data 服务不可用），LLM 调用可降级为无上下文模式

---

## 边界约束

1. `services/data/runtime/` 是永久禁改区，摘要文件由运行时生成，不进 Git
2. 不触及 `shared/contracts/**`（本轮不走契约）
3. D2 不修改 decision 的任何路由文件或 app.py（仅修改 llm/ 层）
4. 摘要不缓存在数据库，只存内存 + runtime 目录（data 侧生成，decision 侧只读）
