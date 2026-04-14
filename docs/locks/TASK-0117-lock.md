# TASK-0117 锁控记录

【task-id】TASK-0117
【review-id】REVIEW-TASK-0117
【服务归属】services/decision/
【批次】A

## Batch A Token

- token_id: tok-f8d27abe-32ad-4b21-beae-fe03e6596ba7
- agent: 决策
- files: services/decision/src/research/spread_monitor.py, services/decision/src/research/news_scorer.py, services/decision/src/research/correlation_monitor.py, services/decision/src/reporting/daily.py, services/decision/src/api/routes/optimizer.py, services/decision/tests/test_research_extensions.py
- ttl: 480min
- status: locked
- locked_at: 2026-04-15
- evidence: 18/18 tests passed (test_research_extensions.py); spread_monitor空序列IndexError修复+correlation_monitor新建
