# TASK-0114 锁控记录

【task-id】TASK-0114
【review-id】REVIEW-TASK-0114
【服务归属】services/decision/
【批次】A

## Batch A Token

- token_id: tok-d0112f40-fa4d-4368-9f4b-12e20952d6e7
- agent: 决策
- files: services/decision/src/research/model_registry.py, services/decision/src/research/regime_detector.py, services/decision/src/research/trainer.py, services/decision/tests/test_model_registry.py
- ttl: 480min
- status: locked
- locked_at: 2026-04-15
- evidence: 12/12 tests passed (test_model_registry.py); Regime扩展至5类(trend/oscillation/high_vol/compression/event_driven)
