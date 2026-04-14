# TASK-0113 Token 签发记录

| 批次 | Token ID | 任务 | 文件数 | TTL | 状态 |
|------|----------|------|--------|-----|------|
| A | tok-d94404ab | TASK-0113-A | 5 | 480min | ✅ active |
| B | tok-bd0b218c | TASK-0113-B | 2 | 480min | ✅ active |
| C | tok-2fe77aed | TASK-0113-C | 3 | 480min | ✅ active |
| D | tok-1b948698 | TASK-0113-D | 3 | 480min | ✅ active |

签发时间：2026-04-15
预审：REVIEW-TASK-0113
Agent：数据
签发人：Jay.S (Atlas 执行)

## Batch A — 通知规范化（5 文件）
```
services/data/src/researcher/notifier.py
services/data/src/researcher/notify/card_templates.py
services/data/src/researcher/notify/daily_digest.py
services/data/src/researcher/notify/email_sender.py
services/data/src/researcher/notify/__init__.py
```

## Batch B — 调度与配置（2 文件）
```
services/data/src/researcher/config.py
services/data/src/researcher/scheduler.py
```

## Batch C — 国际采集源（3 文件）
```
services/data/configs/researcher_sources.yaml
services/data/src/researcher/crawler/parsers/international.py
services/data/src/researcher/crawler/parsers/__init__.py
```

## Batch D — 测试（3 文件）
```
services/data/tests/test_researcher_international.py
services/data/tests/test_researcher_daily_mail.py
services/data/tests/test_researcher_card_blue.py
```
