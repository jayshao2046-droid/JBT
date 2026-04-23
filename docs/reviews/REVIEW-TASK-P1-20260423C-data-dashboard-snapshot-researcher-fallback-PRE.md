# REVIEW-TASK-P1-20260423C-data-dashboard-snapshot-researcher-fallback-PRE

- 审核人：项目架构师
- 审核时间：2026-04-23
- 对应任务：TASK-P1-20260423C
- 审核类型：标准预审（P1 / data 单服务）

---

## 1. 审核结论

**结论：通过，允许进入 Jay.S 文件级 Token 签发。**

前置约束：

1. 执行 Agent 固定为**数据**，不得改派 Atlas 或其他服务 Agent。
2. Atlas 只负责预审、终审、白名单冻结与验收裁定，**不直接代写 `services/data/**` 业务代码**。
3. 本次仅批准 `services/data/**` 单服务范围；若实施中证明必须新增任一白名单外文件，当前预审立即失效，必须回到项目架构师补充预审。

---

## 2. 任务边界

### 2.1 批准范围

- 仅处理 `services/data/**` 内与以下三项直接相关的代码与测试：
  1. collectors 看板快照滞后
  2. researcher latest fallback
  3. researcher status 资源状态硬编码
- 仅允许在 MacBook 本地开发与验证，不得直接修改 Mini 文件系统。
- 仅允许修复现有行为，不得借机扩展 researcher 功能、通知链路、跨服务接口或部署配置。

### 2.2 明确排除

- 排除所有非 `services/data/**` 目录。
- 排除 `shared/contracts/**`、`shared/python-common/**`、`.github/**`、`docker-compose.dev.yml`、任一 `.env.example`、`runtime/**`、`logs/**`、任一真实 `.env`。
- 排除其他服务目录，包括但不限于 `services/dashboard/**`、`services/decision/**`、`services/sim-trading/**`。
- 排除 Mini 远端直写；本轮不得通过 ssh / scp / rsync 直接修改 Mini 的 `services/data/**`。

---

## 3. 根因判断

### 3.1 collectors 快照滞后

根因判断：**`collector_status_latest.json` 的持久化职责目前只落在 `health_check.py` 主执行路径中；`data_scheduler.py` 的 2h heartbeat 虽然已调用 `get_collector_freshness()`，但没有同步回写看板读取的 snapshot 文件。**

结果：调度仍在正常运行时，看板可能持续展示旧 `ts` / `last_run_time`，形成“采集空闲”的假象。

### 3.2 researcher latest fallback 缺失

根因判断：**`researcher_store.get_latest(date=None)` 当前把 `None` 固定解释为“仅查询今天”，没有回退到最近一份历史报告。**

结果：

1. `/api/v1/researcher/report/latest` 在当日无报告时返回空 / 404。
2. `/api/v1/context/futures_sentiment` 同样取不到历史最新报告。
3. 该缺陷属于 store 层查询策略问题，而不是情绪聚合算法本身的问题。

### 3.3 researcher status 口径失真

根因判断：**`/api/v1/researcher/status` 的 `alienware_reachable` 与 `ollama_available` 目前直接写死为 `true`，并非实时探测或基于状态文件推导。**

结果：监控面板会把未知状态错误展示为正常，削弱告警可信度。

### 3.4 架构补充判断

当前只读核对发现：`/api/v1/researcher/report/latest` 在 data 服务内存在**路由实现漂移风险**，但本任务的最小根因仍然是 store 层 fallback 缺失与 status 层硬编码。**本轮不批准借机扩展为 researcher 路由重构任务。**

### 3.5 researcher config 导入期阻塞

根因判断：**`services/data/src/researcher/config.py` 在类属性初始化阶段直接调用 `logger.warning(...)` 与 `logger.error(...)`，但文件内未先定义 `logger`。**

结果：

1. 只要该模块在导入路径上被加载，就可能在 import 阶段直接触发 `NameError: name 'logger' is not defined`。
2. 该问题属于 researcher 配置模块的导入期阻塞，优先级高于 status 接口口径修复；若不纳入本批白名单，执行 Agent 可能连最小导入校验与 API 测试都无法稳定完成。
3. 该问题仍然严格属于 `services/data/**` 单服务内部修复，不改变当前任务边界，也不构成 Atlas 代写 data 业务代码的例外。

---

## 4. 冻结白名单

本次最终冻结为 **8 个文件**，不得扩大：

| 序号 | 文件路径 | 说明 |
|---|---|---|
| 1 | `services/data/src/health/health_check.py` | 抽取/复用 collectors snapshot 持久化逻辑，保持快照格式一致 |
| 2 | `services/data/src/scheduler/data_scheduler.py` | 在 2h heartbeat 路径刷新 snapshot，消除看板读取旧快照问题 |
| 3 | `services/data/src/researcher_store.py` | 修复 latest 查询的历史回退策略 |
| 4 | `services/data/src/researcher/config.py` | 修复 researcher 配置模块导入期 `logger` 未定义导致的 `NameError` 阻塞 |
| 5 | `services/data/src/api/routes/researcher_route.py` | 修复 `/api/v1/researcher/status` 的资源状态硬编码 |
| 6 | `services/data/tests/test_scheduler.py` | 覆盖 scheduler/health_check 的 snapshot 刷新行为 |
| 7 | `services/data/tests/test_researcher_api.py` | 覆盖 latest fallback、researcher status 与 config 导入稳定性 |
| 8 | `services/data/tests/test_futures_sentiment.py` | 覆盖历史报告回退后 `stale=true` 的情绪接口行为 |

---

## 5. 排除项

以下文件**明确不在本轮白名单内**：

- `services/data/src/main.py`
- `services/data/src/api/routes/context_route.py`
- `services/data/src/data/futures_sentiment.py`
- `services/data/tests/test_main.py`
- 其他任意 `services/data/**` 文件

裁定说明：

1. `futures_sentiment` 现有 stale 判定已经基于报告日期完成；本轮优先在 `researcher_store.py` 修正 fallback，不批准扩大到聚合层重写。
2. `context_route.py` 当前只是转发到 `data.futures_sentiment`，不是根因控制点。
3. `main.py` 不在本轮最小修复面内；若执行 Agent 证明必须改动 `main.py` 才能满足验收，说明当前局部根因判断被反证，必须回交补充预审。
4. `test_main.py` 不是本次最直接的行为验证面，优先使用 `test_scheduler.py`、`test_researcher_api.py`、`test_futures_sentiment.py` 三个窄测文件收口。

---

## 6. 验收标准

### 6.1 行为验收

1. `dashboard/collectors` 读取的 snapshot 不再长期滞后；scheduler 正常运行时，`collector_status_latest.json` 的 `ts` 与 `sources` 能被周期性刷新。
2. `/api/v1/researcher/report/latest` 在“当日无报告、历史有报告”时返回最近一份历史报告，而不是空 / 404。
3. `/api/v1/context/futures_sentiment` 在存在历史报告时返回真实数据，并以 `stale=true` 明确暴露“非当日报告”事实。
4. `/api/v1/researcher/status` 的 `alienware_reachable` / `ollama_available` 不得继续硬编码为 `true`；必须来自可解释的实际判定。
5. `services/data/src/researcher/config.py` 不得再在 import 阶段因 `logger` 未定义触发 `NameError`。
6. 不得引入跨服务 import、共享契约改动、部署文件改动或 Mini 远端直写。

### 6.2 自校验要求

执行 Agent 至少完成以下最小验证：

1. `pytest services/data/tests/test_scheduler.py -q`
2. `pytest services/data/tests/test_researcher_api.py -q`
3. `pytest services/data/tests/test_futures_sentiment.py -q`
4. 至少补做一次 researcher 配置导入校验，确保 `services/data/src/researcher/config.py` 不再在模块加载阶段抛出 `NameError`。

若新增验证命令超出本 3 个窄测文件，需在 handoff 中说明原因，但不得据此扩大白名单。

---

## 7. 进入签发结论

**是否批准进入签发：是。**

签发口径：

- 任务类型：P1 单服务标准流程
- 服务归属：`services/data/**`
- 执行 Agent：**数据**
- Atlas 角色：**仅预审 / 终审 / 锁控，不代写业务代码**
- Token 范围：仅限本 review 冻结的 8 文件
