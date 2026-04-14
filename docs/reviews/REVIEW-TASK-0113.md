# REVIEW-TASK-0113 预审记录

| 字段 | 值 |
|------|-----|
| 预审ID | REVIEW-TASK-0113 |
| 任务 | TASK-0113 |
| 审核人 | Atlas（项目架构师代审） |
| 日期 | 2026-04-15 |
| 结论 | ✅ 通过 |

## 审核要点

### 1. 服务边界

- 所有修改限于 `services/data/` 内部，不跨服务
- 不涉及 `shared/contracts/**` 或 `shared/python-common/**`
- 不涉及 P0 保护区

### 2. 通知规范

- 飞书卡片由 `turquoise` 改为 `blue`（资讯类），符合 JBT 统一通知颜色标准
- 失败告警保持 `orange`（P1 报警），合规
- 邮件 HTML Card 格式，符合 JBT 卡片标准
- footer 含服务名 + 时间戳，合规

### 3. 爬虫安全

- 所有爬虫使用 UA 轮换 + 请求间隔 + 指数退避
- 默认 code 模式（httpx），不触发 JavaScript
- timeout 保护（30~60s）
- 国际源均为公开数据页面

### 4. 文件变更范围

- 10 个修改 + 3 个新建 = 13 文件
- 所有文件在 `services/data/` 路径下
- 无目录结构变更（`parsers/` 下新增文件不算目录变更）

### 5. 风险评估

- 低风险：仅 data 服务内部改动
- 不影响 sim-trading / decision / backtest / dashboard
- 解析器失败只影响单源采集，不影响整体调度
- 邮件发送失败有本地日志兜底

## 文件白名单（13 文件）

```
services/data/src/researcher/notifier.py
services/data/src/researcher/notify/card_templates.py
services/data/src/researcher/notify/daily_digest.py
services/data/src/researcher/notify/email_sender.py
services/data/src/researcher/notify/__init__.py
services/data/src/researcher/config.py
services/data/src/researcher/scheduler.py
services/data/configs/researcher_sources.yaml
services/data/src/researcher/crawler/parsers/international.py
services/data/src/researcher/crawler/parsers/__init__.py
services/data/tests/test_researcher_international.py
services/data/tests/test_researcher_daily_mail.py
services/data/tests/test_researcher_card_blue.py
```
