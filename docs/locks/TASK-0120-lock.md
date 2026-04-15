# TASK-0120 锁控记录

【task-id】TASK-0120
【review-id】TASK-0120-review
【服务归属】services/data/ + services/decision/
【批次】总 Token

## Token

- token_id: tok-070a406a-4adb-4311-a640-e2923306c611
- agent: claude
- ttl: 480min
- status: active
- issued_at: 2026-04-15
- evidence: `python governance/jbt_lockctl.py issue --task TASK-0120 ...` 签发成功
- note: 同任务存在重复 active token `tok-29b461a5-7378-4783-8bc2-46db27e08dca`（由重复 issue 触发），当前以本 token 作为执行口径。
- files:
  - services/data/src/main.py
  - services/data/src/researcher_store.py
  - services/data/src/api/routes/researcher_route.py
  - services/data/src/researcher/config.py
  - services/data/src/researcher/summarizer.py
  - services/data/src/researcher/reporter.py
  - services/data/src/researcher/report_reviewer.py
  - services/data/src/researcher/scheduler.py
  - services/data/src/researcher/researcher_health.py
  - services/data/src/researcher/notifier.py
  - services/data/src/researcher/notify/card_templates.py
  - services/data/src/researcher/notify/feishu_sender.py
  - services/data/src/researcher/notify/email_sender.py
  - services/data/src/researcher/notify/daily_digest.py
  - services/data/src/researcher/staging.py
  - services/data/src/researcher/models.py
  - services/data/tests/test_researcher_api.py
  - services/data/tests/test_security.py
  - services/data/tests/test_main.py
  - services/decision/src/api/app.py
  - services/decision/src/api/routes/model.py
  - services/decision/src/api/routes/signal.py
  - services/decision/src/notifier/dispatcher.py
  - services/decision/src/notifier/feishu.py
  - services/decision/src/notifier/email.py
  - services/decision/src/reporting/daily.py
  - services/decision/src/core/signal_dispatcher.py
  - services/decision/src/llm/gate_reviewer.py
  - services/decision/src/research/factor_loader.py
  - services/decision/src/research/sandbox_engine.py
  - services/decision/tests/test_signal_dispatcher.py
  - services/decision/tests/test_llm_security.py
