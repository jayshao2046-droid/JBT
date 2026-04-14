# TASK-0116 锁控记录

【task-id】TASK-0116
【review-id】REVIEW-TASK-0116
【服务归属】services/decision/
【批次】A

## Batch A Token

- token_id: tok-bc3f9282-fb3e-4c90-8484-680d6be0e752
- agent: 决策
- files: services/decision/src/research/factor_miner.py, services/decision/src/research/factor_validator.py, services/decision/src/api/routes/factor.py, services/decision/tests/test_factor_mining.py
- ttl: 480min
- status: locked
- locked_at: 2026-04-15
- evidence: 26/26 tests passed (test_factor_mining.py); _momentum边界保护+ic_ir/t_test零方差处理
