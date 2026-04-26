# TASK-P1-20260424E1 — data callback 接管 stream 主链

## 任务类型
- P1 标准流程
- 服务归属：services/data
- 母任务：TASK-P1-20260424E
- 预审依据：REVIEW-TASK-P1-20260424E-researcher-decision两地联调闭环-PRE
- 当前状态：可进入 Jay.S 文件级 Token 签发与实施

## 目标
1. 让 Mini callback 不再通过 trigger_research() 回流 execute_hourly() 旧链。
2. 让 callback 进入现役 stream / 事件语义，与后台 execute_stream_cycle() 主链收敛。
3. 保持 researcher 现役主链对 Decision 的推送能力不被破坏。

## 冻结白名单
1. services/data/run_researcher_server.py
2. services/data/src/researcher/scheduler.py

## 明确排除
1. services/data/src/main.py
2. services/data/src/researcher/queue_manager.py
3. services/data/tests/test_researcher_scheduler.py
4. shared/contracts/**
5. 任意 Mini 主服务、部署、runtime、logs、真实 .env 文件

## 验收标准
1. callback 不再进入 execute_hourly() 旧链。
2. callback 触发后可驱动现役 stream / 事件语义完成联动。
3. execute_stream_cycle() 主链仍能正常完成 Mini 上下文刷新、分析和推送 Decision。

## 建议最小验证
- 针对 callback -> stream 主链的局部行为断言
- 必要时补充最小 HTTP 探针说明