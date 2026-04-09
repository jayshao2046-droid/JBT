# TASK-0034 data端 U0 直修事后审计与远端备份

## 文档信息

- 任务 ID：TASK-0034
- 文档类型：单服务 U0 事后审计 / 远端备份收口
- 签名：Atlas
- 建档时间：2026-04-09 23:17
- 设备：MacBook

---

## 一、任务来源

1. 本任务来源于 Jay.S 在 data 单服务运行态排障中的明确 `U0` 直修指令。
2. 用户在直修成功后进一步要求：“完成 U0 后补审计，同步 git 远端备份。”
3. 为避免反向改写 `TASK-0031` 已锁回的 6 文件标准热修边界，本任务单独承担后续 U0 直修的事后审计与备份收口；`TASK-0031` 仅保留为前情引用。

## 二、U0 适用性确认

1. 直修全过程仅限 `services/data/**` 单服务。
2. 未触碰 `shared/contracts/**`、`shared/python-common/**`、`WORKFLOW.md`、`.github/**`、`docker-compose.dev.yml`、任一 `.env.example`、任一真实 `.env`、`runtime/**`、`logs/**` 等永久禁区。
3. 未发生跨服务写入、目录新增、shared 代码改动或部署编排改动。
4. 用户已确认运行态成功，符合 `U0` 在成功后一次性补齐 `task/review/lock/handoff/prompt` 与独立提交的收口条件。

## 三、实际直修范围

1. 实际写入文件共 5 个，且全部位于 `services/data/**`：
   - `services/data/src/notify/dispatcher.py`
   - `services/data/src/notify/heartbeat.py`
   - `services/data/src/notify/news_pusher.py`
   - `services/data/src/scheduler/data_scheduler.py`
   - `services/data/src/health/health_check.py`
2. 相关代码提交链为：`bd108b3` -> `f221773` -> `c9b5790`。
3. Mini 实际部署版本为 `c9b5790`。

## 四、实际收口问题

1. 移除 `heartbeat.py` 对 Studio SSH / legacy `launchctl` 的依赖，使 Mini 心跳只关注 JBT data 自身运行态。
2. 恢复 `NEWS/TRADING` 与 `INFO/TRADE` 双口径 webhook 兼容，避免现网必须依赖运行态别名注入。
3. 停止 A 股分钟采集任务，消除当前设计下的重复堆积与误报。
4. 修正 `news_pusher.py` 的 storage base_dir，使新闻批量推送能够从 `~/jbt-data` 的真实落盘目录读取数据，不再稳定读到 0 条。
5. 修正 `health_check.py` 对国内期货分钟 / 日线新目录结构的 freshness 判定，消除采集正常但仍按 legacy 路径报警的 false alarm。

## 五、运行态验证摘要

1. Mini 已完成 `c9b5790` 部署验证。
2. 飞书心跳链路恢复到 JBT 自身口径，不再引用 Studio / legacy 服务。
3. 新闻 / RSS 批量推送已恢复可读真实存储数据。
4. 期货分钟健康检查已切换到 `EXCHANGE.contract/1min` 与 `daily` 新目录结构。
5. 最终目录审计确认：核心采集与落档目录整体正确；`CFTC` 目录为空属于周六任务未触发的正常状态。

## 六、明确排除

1. 不反写 `TASK-0031` 的原始 6 文件标准热修边界。
2. 不继续扩展 `services/data/src/scheduler/pipeline.py`、`services/data/src/collectors/**`、`services/data/src/main.py`、`services/data/data_web/**`。
3. 不新增任何 `shared/**`、部署文件、`.env*`、运行态目录修改。
4. 本任务只负责补齐审计账本、prompt 同步与独立远端备份，不继续追加新的业务修复。

## 七、验收标准

1. `TASK-0034` 的 `task/review/lock/handoff` 四类账本补齐。
2. 项目架构师完成 `REVIEW-TASK-0034`，并同步公共项目提示词与其私有 prompt。
3. Atlas 同步总项目经理 prompt、私有 prompt 与 `ATLAS_PROMPT.md`。
4. 账本以独立文档提交方式同步到 `origin` 与 `local` 两个远端。
5. 本轮无任何超出 U0 已发生事实的新代码改动。

## 八、当前结论

1. `TASK-0034` 是 `TASK-0031` 后续 data 单服务 U0 直修的独立事后审计锚点。
2. `TASK-0031` 继续保留为原 6 文件标准热修与 lockback 记录，不做边界改写。
3. 本轮收口完成后，data 端本次 U0 仅剩历史审计与备份事实，不再自动延伸为新一轮代码任务。