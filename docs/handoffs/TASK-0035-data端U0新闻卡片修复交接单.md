# HANDOFF-TASK-0035 data端 U0 新闻卡片排版与推送路由修复

## 文档信息

- 任务 ID：TASK-0035
- 交接类型：U0 事后审计收口
- 签名：Atlas
- 时间：2026-04-10 13:10
- 设备：MacBook

---

## 一、本轮 U0 修复问题清单

| # | 问题 | 修复文件 |
|---|------|---------|
| 1 | 新闻全部进报警群（NotifyType.P0 误用） | `news_pusher.py` |
| 2 | 半小时批量推送静默失败（飞书关键词 19024） | `card_templates.py` |
| 3 | 黑天鹅词过宽导致几乎全量标记为 breaking | `news_pusher.py` |
| 4 | 卡片条目堆叠无间隔（单 Markdown 字符串） | `feishu.py` |
| 5 | 卡片标题前缀含 `[DATA-LEVEL]` 需改为 `JBQ` | `card_templates.py` |
| 6 | 单卡展示项数 20 条不足，缺少统计行 | `news_pusher.py` |

---

## 二、运行态状态

- Mini 调度器：PID 82065，`interval[0:03:00]` 运行中
- 新闻推送：批次消化正常，breaking 进资讯群
- Git：`84e441f` → origin main 已推送

---

## 三、接口与部署说明

- Mini data 服务路径：`jaybot@172.16.0.49:~/jbt/`
- API 端口：8105
- 重启调度器：`ssh jaybot@172.16.0.49 'cd ~/jbt && pkill -f data_scheduler && nohup .venv/bin/python -m services.data.src.scheduler.data_scheduler > /tmp/scheduler.log 2>&1 &'`

---

## 四、后继注意事项

1. 飞书 NEWS/INFO webhook 的关键词安全过滤要求 `SERVICE_NAME` 必须含 `BotQuant 资讯`，不得删改。
2. `BLACK_SWAN_KEYWORDS_ZH` 仅保留高精度词，如需新增须谨慎评估泛义风险。
3. `_build_news_card()` 只处理 `news_batch_summary` 和 `news_breaking`，其他事件仍走 `alert_card`。
4. 若飞书批量推送再次出现 19024，优先排查 `SERVICE_NAME` 是否被修改。

---

## 五、关联文档

- 任务：`docs/tasks/TASK-0035-data端U0新闻卡片排版与推送路由修复.md`
- 审查：`docs/reviews/TASK-0035-review.md`
- 锁回：`docs/locks/TASK-0035-lock.md`
- 前情：`TASK-0034`（data端U0直修事后审计与远端备份）
