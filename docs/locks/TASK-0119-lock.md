# TASK-0119 锁控记录

【锁控】Atlas  
【日期】2026-04-15  
【task-id】TASK-0119  
【review-id】TASK-0119-review  
【服务归属】services/data/ + services/decision/  
【批次】总 Token  
【Token ID】tok-9111c220-98e3-4b35-a179-7f54c46fc89f  
【状态】active（有效期 480 分钟）

## 白名单文件（16 个）

### data 服务（7 个）
- `services/data/src/main.py`
- `services/data/src/notify/card_templates.py`
- `services/data/src/collectors/tushare_full_collector.py`
- `services/data/tests/test_main.py`
- `services/data/tests/test_security.py`
- `services/data/src/researcher/crawler/parsers/futures.py`
- `services/data/src/researcher/scheduler.py`

### decision 服务（9 个）
- `services/decision/src/llm/gate_reviewer.py`
- `services/decision/src/core/signal_dispatcher.py`
- `services/decision/src/notifier/email.py`
- `services/decision/src/persistence/state_store.py`
- `services/decision/tests/test_llm_security.py`
- `services/decision/tests/test_signal_dispatcher.py`
- `services/decision/src/research/factor_loader.py`
- `services/decision/src/api/app.py`
- `services/decision/src/research/sandbox_engine.py`

## 签发流程

1. ✅ 任务建档：`docs/tasks/TASK-0119-全服务安全漏洞修复.md`
2. ✅ 架构师预审：`docs/reviews/TASK-0119-review.md`
3. ✅ Token 签发：`tok-9111c220-98e3-4b35-a179-7f54c46fc89f`
4. ✅ 锁控记录：本文件
5. ⬜ Claude 执行修复
6. ⬜ 验收测试通过
7. ⬜ 终审收口
8. ⬜ lockback（锁回）

## 关联文档

- 派工单：`docs/handoffs/TASK-0119-Claude-安全漏洞修复派工单.md`
- 体检报告：`docs/reports/20260415-风控常规体检报告.md`

## 白名单文件（16 个）

### data 服务（7 个）
- `services/data/src/main.py`
- `services/data/src/notify/card_templates.py`
- `services/data/src/collectors/tushare_full_collector.py`
- `services/data/tests/test_main.py`
- `services/data/tests/test_security.py`
- `services/data/src/researcher/crawler/parsers/futures.py`
- `services/data/src/researcher/scheduler.py`

### decision 服务（9 个）
- `services/decision/src/llm/gate_reviewer.py`
- `services/decision/src/core/signal_dispatcher.py`
- `services/decision/src/notifier/email.py`
- `services/decision/src/persistence/state_store.py`
- `services/decision/tests/test_llm_security.py`
- `services/decision/tests/test_signal_dispatcher.py`
- `services/decision/src/research/factor_loader.py`
- `services/decision/src/api/app.py`
- `services/decision/src/research/sandbox_engine.py`

## 证据

- `python governance/jbt_lockctl.py issue --task TASK-0119 ...` 签发成功
