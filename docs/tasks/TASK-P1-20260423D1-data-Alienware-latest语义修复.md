# TASK-P1-20260423D1 — data / Alienware latest 语义修复

## 任务类型
- P1 标准流程
- 服务边界：仅 `services/data/**`
- 当前状态：已完成，已锁回（2026-04-23）

## 任务来源
- 来源母任务：`TASK-P1-20260423D`
- 预审依据：`docs/reviews/REVIEW-TASK-P1-20260423D-decision直连Alienware-researcher链路收敛-PRE.md`

## 根因
- `services/data/run_researcher_server.py` 的 `/reports/latest` 当前直接调用 `queue_manager.get_pending(limit=1)`。
- `get_pending(limit=1)` 实际返回的是 pending JSONL 的 FIFO 第一条，而不是最新可读报告。
- 运行态表现为 `GET http://192.168.31.187:8199/reports/latest` 被 `D:\researcher_reports\2026-04-18\01-00.json` 这类 stale path 阻塞并返回 404。

## 目标
1. 修复 `/reports/latest` 的 latest 语义，使其返回最新且可读取的报告。
2. 当 pending 队列前部存在文件不存在记录时，端点应能跳过 stale 记录继续解析有效报告。
3. 本批不改 queue manager 本体，不改其他 data 文件。

## 冻结白名单
- `services/data/run_researcher_server.py`

## 明确排除
- `services/data/src/researcher/queue_manager.py`
- `services/data/src/main.py`
- 其他任意 `services/data/**` 文件

## 验收标准
1. `GET http://192.168.31.187:8199/reports/latest` 在存在有效报告时返回 200。
2. latest 结果不再被 FIFO 第一条 stale path 阻塞。
3. 即使 pending 队列前部有失效记录，也能返回最新可读报告。

## 建议验证
- `curl http://192.168.31.187:8199/reports/latest`
- `curl http://192.168.31.187:8199/queue/status`

## 约束
- 若实施中证明必须修改 `services/data/src/researcher/queue_manager.py`，本任务预审立即失效，必须回项目架构师补充预审。