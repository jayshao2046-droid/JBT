# TASK-P1-20260423C Lock Record

- task_id: TASK-P1-20260423C
- service: data
- agent: 数据
- review_id: REVIEW-TASK-P1-20260423C-data-dashboard-snapshot-researcher-fallback-PRE
- final_review_id: REVIEW-TASK-P1-20260423C-data-dashboard-snapshot-researcher-fallback-FINAL
- token_id: tok-3670abb9-26a0-4331-9970-380f9b5e4f73
- status: locked
- issued_at: 2026-04-23
- locked_at: 2026-04-23
- reason: data 看板快照滞后 + researcher latest fallback / status 口径修复 + researcher.config 导入阻塞

## Allowed Files
- services/data/src/health/health_check.py
- services/data/src/scheduler/data_scheduler.py
- services/data/src/researcher_store.py
- services/data/src/api/routes/researcher_route.py
- services/data/src/researcher/config.py
- services/data/tests/test_scheduler.py
- services/data/tests/test_researcher_api.py
- services/data/tests/test_futures_sentiment.py

## Notes
- 本 token 依据本地 lockctl 状态补发，并已通过 `governance/jbt_lockctl.py validate` 语义校验。
- Atlas 仅负责预审、锁控、验收与锁回；实际代码修改由“数据”代理执行。
- 本地验证结果：`cd services/data && pytest tests/test_scheduler.py tests/test_researcher_api.py tests/test_futures_sentiment.py -q` => `51 passed, 3 skipped`；5 个 runtime 源码 `py_compile` 通过；8 文件 `Problems=0`。
- Mini 备份目录：`/Users/jaybot/JBT/backups/TASK-P1-20260423C-20260423-132539`
- Mini 部署范围：仅同步 5 个 runtime 文件到 `/Users/jaybot/JBT/services/data/`，未携带测试文件或其他脏变更。
- Mini 运行验证：`JBT-DATA-8105` 已重启并恢复 `healthy`；`/health=ok`；`/api/v1/researcher/report/latest?date=bad-date` 返回 `400 Invalid date format`，证明新 researcher 路由已生效。
- Mini 容器内只读检查：`report_rows=0`，因此当前 `/api/v1/researcher/report/latest=404` 与 `futures_sentiment=no_report_available` 属于无历史数据，不是回归。
- `collector_status_latest.json` 存在，`ts=2026-04-23T13:19:30.161193+08:00`，`sources=24`。
- 治理说明：本批 recovered JWT 可用于 `validate`，但未在 `.jbt/lockctl/tokens.json` 中形成可枚举状态条目，因此官方 `jbt_lockctl.py lockback` 无法再次接管；当前以项目架构师终审 + 本 lock 记录完成审计锁回留痕。