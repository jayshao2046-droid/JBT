# REVIEW-TASK-P1-20260423C-data-dashboard-snapshot-researcher-fallback-FINAL

- 审核人：项目架构师
- 审核时间：2026-04-23
- 对应任务：TASK-P1-20260423C
- 审核类型：标准流程终审（P1 / data 单服务）

---

## 1. 审核结论

**结论：通过终审，可以锁回并交付。**

本次终审以用户已确认的本地验证、Mini 同步重启结果、Mini 运行态接口返回与容器内只读检查事实为准；当前已可裁定本任务在冻结白名单内完成，且线上未发现 fallback 回归证据。

---

## 2. 任务信息与审查范围

### 2.1 任务归属

- 服务边界：仅 `services/data/**`
- 执行模式：标准流程
- 执行 Agent：数据
- Atlas 角色：仅终审 / 锁控裁定，不代写业务代码

### 2.2 本次唯一审查白名单

1. `services/data/src/health/health_check.py`
2. `services/data/src/scheduler/data_scheduler.py`
3. `services/data/src/researcher_store.py`
4. `services/data/src/api/routes/researcher_route.py`
5. `services/data/src/researcher/config.py`
6. `services/data/tests/test_scheduler.py`
7. `services/data/tests/test_researcher_api.py`
8. `services/data/tests/test_futures_sentiment.py`

### 2.3 范围裁定

- 本终审以预审文件与 lock 账本中的最终冻结白名单为准。
- 用户已确认本轮白名单内实际改动即为上述 8 文件，未纳入任何白名单外文件。
- 其他服务目录、共享契约、部署文件、运行态文件均不在本次终审范围内。

---

## 3. 实际改动范围

基于用户确认事实，本轮实际改动严格收敛在已冻结的 8 个白名单文件内，且与任务目标一致，未见跨服务或白名单外污染。

### 3.1 业务源码变更

1. `services/data/src/health/health_check.py`
   - 承担 collector snapshot 持久化相关修复，配合 scheduler 落盘逻辑保证看板读取的快照及时刷新。

2. `services/data/src/scheduler/data_scheduler.py`
   - 修复 heartbeat 路径对 collector snapshot 的刷新，使看板快照与调度心跳一致。

3. `services/data/src/researcher_store.py`
   - 修复 latest fallback 查询策略，支持在无当日报告时回退到最近历史报告。

4. `services/data/src/api/routes/researcher_route.py`
   - 修复 `/api/v1/researcher/status` 与 latest 相关接口口径，移除资源状态硬编码。

5. `services/data/src/researcher/config.py`
   - 修复导入期阻塞问题，使 `researcher.config` 可稳定导入。

### 3.2 测试变更

6. `services/data/tests/test_scheduler.py`
   - 覆盖 collector snapshot 写盘与 heartbeat 刷新行为。

7. `services/data/tests/test_researcher_api.py`
   - 覆盖 latest fallback、`/status` 资源状态与 `researcher.config` 导入稳定性。

8. `services/data/tests/test_futures_sentiment.py`
   - 覆盖历史研报 fallback 场景下 `stale=true` 的情绪接口行为。

---

## 4. 验收结果

### 4.1 白名单核验

用户已确认本轮白名单内实际改动为以下 8 文件，且与预审冻结白名单完全一致：

1. `services/data/src/health/health_check.py`
2. `services/data/src/scheduler/data_scheduler.py`
3. `services/data/src/researcher_store.py`
4. `services/data/src/api/routes/researcher_route.py`
5. `services/data/src/researcher/config.py`
6. `services/data/tests/test_scheduler.py`
7. `services/data/tests/test_researcher_api.py`
8. `services/data/tests/test_futures_sentiment.py`

结论：**白名单边界合规。**

### 4.2 本地验证结果

1. 本地执行命令：
   - `pytest services/data/tests/test_scheduler.py services/data/tests/test_researcher_api.py services/data/tests/test_futures_sentiment.py -q`
   - 结果：`50 passed, 3 skipped`

2. `researcher.config` 导入检查：
   - 输出：`CONFIG_IMPORT_OK`

结论：**本地窄测与导入验证通过。**

### 4.3 Mini 同步与运行验证

1. Mini 已同步本轮白名单文件并重启 `JBT-DATA-8105`。
2. Mini `GET /health` 返回 `ok`。
3. `docker top JBT-DATA-8105` 已确认以下进程同时在运行：
   - `python -m uvicorn main:app --host 0.0.0.0 --port 8105`
   - `python -m scheduler.data_scheduler`
4. 容器内只读检查确认 `collector_status_latest.json` 存在，且：
   - `ts=2026-04-23T13:19:30.161193+08:00`
   - `collector_sources=24`

结论：**Mini 运行态与 collectors snapshot 刷新链路正常。**

### 4.4 researcher 接口运行态判断

1. `/api/v1/researcher/status` 返回：
   - `alienware_reachable=True`
   - `ollama_available=True`
   - `last_run=None`

2. 容器内只读检查确认：
   - `report_rows:0`

3. 因当前无历史研报数据：
   - `/api/v1/researcher/report/latest` 当前返回 `404`
   - `/api/v1/context/futures_sentiment?symbol=rb` 当前返回 `symbol_count=0, stale=True, reason=no_report_available`

4. 上述现象的裁定：
   - 这是 **Mini 当前尚未产生 researcher 历史研报数据** 的结果，
   - **不是** latest fallback 回归，
   - 也 **不是** 本轮修复失效证据。

结论：**status 真实探测口径已生效；latest fallback 逻辑未见回归，但当前线上尚无历史研报可供真实命中。**

---

## 5. 风险与遗留项

本次终审仅保留 1 个观察项，不构成阻断：

1. 需要等待 Mini 后续真正产生 researcher 历史研报后，再继续观察 latest fallback 的线上真实命中情况；当前线上验证只能确认“无历史数据时不属于 fallback 回归”，尚不能以真实历史样本验证 fallback 命中路径。

---

## 6. Lockback 裁定

- 是否允许锁回：**是**
- 是否允许交付：**是**
- 裁定理由：
  1. 白名单内实际改动严格等于冻结的 8 文件
  2. 本地验证 `50 passed, 3 skipped`，且 `researcher.config` 导入输出 `CONFIG_IMPORT_OK`
  3. Mini 已同步白名单文件并重启 `JBT-DATA-8105`
  4. Mini `/health`、`docker top`、`collector_status_latest.json` 只读检查均符合预期
  5. `report_rows:0` 已解释当前 `404` 与 `no_report_available` 为“尚无历史研报数据”，不是 fallback 回归

建议锁回摘要：

`TASK-P1-20260423C 终审通过；8 文件白名单边界合规，本地验证通过，Mini 已同步重启并运行正常，当前无历史研报数据导致 latest/report 与 futures_sentiment 未命中，不构成 fallback 回归，允许 lockback 并交付。`