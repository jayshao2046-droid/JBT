# TASK-0035 data端 U0 新闻卡片排版与推送路由修复

## 文档信息

- 任务 ID：TASK-0035
- 文档类型：单服务 U0 事后审计
- 签名：Atlas
- 建档时间：2026-04-10 13:10
- 设备：MacBook
- 关联提交：`84e441f`

---

## 一、任务来源

1. 本任务来源于 Jay.S 在 data 单服务飞书通知观测排障中的 `U0` 直修指令。
2. 用户描述问题：新闻全部被路由到报警群（P0），半小时批量推送沉默不到达，卡片条目堆叠无间隔，标题前缀需改为 `JBQ`。
3. 本任务为 `TASK-0034` 的后续 U0 批次，独立承担本轮事后审计收口；`TASK-0034` 不改写。

---

## 二、U0 适用性确认

1. 直修全过程仅限 `services/data/src/notify/**` 三个文件，未触碰任何服务目录以外的路径。
2. 未触碰永久禁区：`shared/contracts/**`、`shared/python-common/**`、`WORKFLOW.md`、`.github/**`、`docker-compose.dev.yml`、任一 `.env.example`、任一真实 `.env`、`runtime/**`、`logs/**`。
3. 无跨服务写入、无目录新增、无 shared 代码改动、无部署编排改动。
4. 用户已确认运行态验证成功（`flush={'pushed':5, 'breaking_pushed':5, 'buffer_size':0}`），符合 U0 成功后一次性补齐审计材料的收口条件。

---

## 三、实际直修范围

| 文件 | 改动摘要 |
|------|---------|
| `services/data/src/notify/card_templates.py` | `SERVICE_NAME` 改为 `"BotQuant 资讯 \| JBT data-service"`（通过飞书关键词验证）；`alert_card` 标题前缀改为 `JBQ`，去除 `[DATA-LEVEL]` 标签 |
| `services/data/src/notify/news_pusher.py` | `dispatch_breaking` 改用 `NotifyType.NEWS`（原 `P0`），`bypass_quiet_hours→False`；精简 `BLACK_SWAN_KEYWORDS_ZH` 为高危词；单卡展示上限 20→50 条，标题截断 180→240；底部增加统计行（去重缓存/本卡/累计）|
| `services/data/src/notify/feishu.py` | 新增 `_build_news_card()` 静态方法，每条新闻独立 `div+hr`；`send()` 路由 `news_batch_summary`/`news_breaking` 至新方法，其他事件保留原 `alert_card` 路径 |

---

## 四、根本原因分析

| 故障现象 | 根本原因 |
|---------|---------|
| 新闻全部进报警群 | `dispatch_breaking` 使用 `NotifyType.P0`；同时黑天鹅关键词过宽（总统/主席/暴涨等），导致 200+ 条均被标记为 breaking |
| 半小时批量推送沉默 | 飞书 NEWS/INFO webhook 安全关键词要求 `BotQuant 资讯`，旧 `SERVICE_NAME="JBT data-service"` 不包含，返回 `code 19024 Key Words Not Found` |
| 卡片条目堆叠无间隔 | `_build_batch_body()` 返回单 Markdown 字符串，被包在单个 `_md()` div 内，无法生成逐条 hr 分隔 |

---

## 五、运行态验证摘要

1. 手动 flush 测试：`{'pushed': 5, 'breaking_pushed': 5, 'buffer_size': 0}` ✅
2. 调度器以 PID 82065 运行，`interval[0:03:00]` 确认 ✅
3. Mini notify/ 目录六文件大小与 MacBook 本地一致 ✅
4. Git 提交 `84e441f` 已推送至 `origin main` ✅

---

## 六、明确排除

1. 不反写 `TASK-0034` 的已锁回审计边界。
2. 不继续扩展 `services/data/src/scheduler/**`、`services/data/src/collectors/**`、`services/data/src/main.py`、`services/data/data_web/**`。
3. 不新增任何 `shared/**`、部署文件、`.env*`、运行态目录修改。
4. 本任务只负责补齐审计账本与远端备份，不追加新业务修复。

---

## 七、验收标准

1. `TASK-0035` 的 `task/review/lock/handoff` 四类账本文件补齐。✅
2. Git 提交 `84e441f` 推送至 `origin main`。✅
3. Mini 两地 notify/ 目录文件同步一致。✅
4. Atlas 同步 `ATLAS_PROMPT.md` 与私有 prompt。
5. 无超出 U0 已发生事实的新代码改动。✅
