# TASK-P1-20260423C — data 看板快照滞后 + researcher latest fallback / status 口径修复

## 任务类型
- P1 单服务修复
- 服务边界：仅 `services/data/**`
- 执行模式：标准流程（禁止 U0 直修 Mini data）
- 当前状态：已完成本地修复、通过终审，并已同步 Mini

## 背景
- 2026-04-23 全量只读检查确认 data 实际采集健康，但发现 2 条真实修复项和 1 条监控口径项。
- 本任务只修复 data 服务本地代码，不直接修改 Mini 文件系统；Mini 仅允许后续在本地开发完成并获得 Token 后再按标准同步。

## 问题清单
1. `dashboard/collectors` 读取 `collector_status_latest.json`，但该快照仅在独立执行 `health_check.py` 主程序时回写，`data_scheduler` 的 2h heartbeat 只计算 freshness 不落盘，导致看板可长期显示旧快照，出现“国内期货分钟 idle，但调度日志持续正常”的假象。
2. `researcher_store.get_latest()` 在 `date=None` 时默认只查“今天”的报告；当天无报告时，`/api/v1/researcher/report/latest` 和 `/api/v1/context/futures_sentiment` 都返回空/404，即使前一日已有最新有效报告。
3. `/api/v1/researcher/status` 中 `alienware_reachable` / `ollama_available` 目前硬编码为 `true`，监控口径失真。
4. 本地验证发现 `services/data/src/researcher/config.py` 在类定义阶段直接调用未定义的 `logger`，导致 `main.py` / `researcher_route.py` 导入时可触发 `NameError`，阻塞本批次修复验证。

## 目标
- 修复 collectors 看板快照滞后，保证看板状态与实际调度心跳一致。
- 修复 researcher latest / futures_sentiment 的 latest fallback 行为：无当日报告时应回退到最新一份历史报告，并正确标记 stale。
- 修复 researcher status 资源状态字段，移除硬编码口径。

## 冻结白名单（预审候选）
- `services/data/src/health/health_check.py`
- `services/data/src/scheduler/data_scheduler.py`
- `services/data/src/researcher_store.py`
- `services/data/src/api/routes/researcher_route.py`
- `services/data/src/researcher/config.py`
- `services/data/tests/test_scheduler.py`
- `services/data/tests/test_researcher_api.py`
- `services/data/tests/test_futures_sentiment.py`

## 验收标准
1. `dashboard/collectors` 不再长期引用陈旧 `last_run_time`；在 scheduler 正常运行时，不应出现由旧 snapshot 导致的错误 idle 展示。
2. `/api/v1/researcher/report/latest` 在存在历史报告但当日无报告时返回最新历史报告。
3. `/api/v1/context/futures_sentiment` 在存在历史报告时返回数据，并通过 `stale=true` 暴露“不是当日报告”的事实。
4. `/api/v1/researcher/status` 的资源状态不再硬编码为 `true`。
5. 相关单测通过，且不扩展到 `services/data/**` 之外。

## 风险与约束
- 禁止直接修改 Mini `services/data/**`；只能在 MacBook 本地开发，后续由标准流程同步。
- 本任务不处理 researcher 内容生成策略本身，只修 latest fallback / status 口径。
- 本任务不修改共享契约、不修改其他服务。

## 实际修改范围
- `services/data/src/health/health_check.py`：复用 `persist_collector_status_snapshot()`，统一 collectors snapshot 持久化格式。
- `services/data/src/scheduler/data_scheduler.py`：在 2h heartbeat 路径刷新 `collector_status_latest.json`。
- `services/data/src/researcher_store.py`：`get_latest(date=None)` 改为回退到最近一份历史研报。
- `services/data/src/api/routes/researcher_route.py`：`/report/latest` 改为走 store；`/status` 改为真实资源探测，不再硬编码 true。
- `services/data/src/researcher/config.py`：保留并验证模块级 logger 修复，解除导入期阻塞。
- `services/data/tests/test_scheduler.py`：覆盖 snapshot 持久化与 heartbeat 刷新。
- `services/data/tests/test_researcher_api.py`：覆盖 latest fallback、status 真实探测与 config 导入稳定性。
- `services/data/tests/test_futures_sentiment.py`：覆盖历史研报回退后的 stale 行为。

## 本地验证
- `cd services/data && pytest tests/test_scheduler.py tests/test_researcher_api.py tests/test_futures_sentiment.py -q`
	- 结果：`51 passed, 3 skipped`
- `python -c "import researcher.config; print('CONFIG_IMPORT_OK')"`
	- 结果：`CONFIG_IMPORT_OK`

## Mini 同步与运行验证
- 远端备份目录：`/Users/jaybot/JBT/backups/TASK-P1-20260423C-20260423-132539`
- 已按白名单内 runtime 切片精确同步 5 个文件到 `/Users/jaybot/JBT/services/data/`
- 已重启容器：`JBT-DATA-8105`
- `GET /health`：`status=ok, service=jbt-data`
- `GET /api/v1/researcher/report/latest?date=bad-date`：`400 Invalid date format`，证明新 researcher 路由已在 Mini 生效
- `GET /api/v1/researcher/status`：`alienware_reachable=True`, `ollama_available=True`, `last_run=None`
- 容器内只读检查：
	- `report_rows=0`
	- `collector_status_latest.json` 存在
	- `collector_snapshot_ts=2026-04-23T13:19:30.161193+08:00`
	- `collector_sources=24`

## 线上观察结论
- Mini 当前没有历史 researcher 研报数据（`report_rows=0`），因此：
	- `/api/v1/researcher/report/latest` 当前返回 `404`
	- `/api/v1/context/futures_sentiment?symbol=rb` 当前返回 `symbol_count=0, stale=true, reason=no_report_available`
- 上述现象与本次 fallback 修复不冲突，当前属于“线上无历史数据”，不是“fallback 回归失效”。

## 收口结论
- 本任务已通过项目架构师终审：`REVIEW-TASK-P1-20260423C-data-dashboard-snapshot-researcher-fallback-FINAL`
- 当前按 FINAL review + lock 账本完成审计锁回并交付。
- 唯一剩余观察项：等待 Mini 后续真正产生 researcher 历史研报后，再观察 latest fallback 的线上真实命中。
- 治理补充：本批 recovered JWT 已用于 `validate` 与实施，但未写回 `.jbt/lockctl/tokens.json` 状态表，因此官方 `jbt_lockctl.py lockback` 无法再次接管；相关事实已记录在 lock/handoff 中。