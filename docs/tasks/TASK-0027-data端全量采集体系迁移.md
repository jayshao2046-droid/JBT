# TASK-0027：data 端全量采集体系迁移到 JBT

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0027 |
| 任务标题 | data 端全量采集体系迁移到 JBT |
| 服务归属 | `services/data/**`（单服务） |
| 发起人 | Jay.S |
| 预审人 | 项目架构师 |
| 创建日期 | 2026-04-08 |
| 状态 | A0 治理建档中 |
| 关联任务 | 独立任务，不并入 TASK-0018-B |

---

## 背景

JBT `services/data/` 当前仅有最小 4 文件骨架（README.md、.env.example、src/main.py、tests/test_main.py），提供 `/health`、`/api/v1/version`、`/api/v1/symbols`、`/api/v1/bars` 只读 API。

Mini 现网数据采集体系由以下组成：

- **17 个 collector 模块**（collectors/ 目录）
- **主调度器** data_scheduler.py（APScheduler，11 个调度管道）
- **18 个独立 scheduler** 脚本（futures_minute_scheduler.py、macro_scheduler.py、news_scheduler.py 等）
- **30 个 LaunchAgent plist**（com.botquant.*）
- **6 个 crontab job**（数据完整性检查、VPN 健康检查、系统心跳、盘前检查、RSS 采集、整点健康检查）
- **Docker 容器** botquant-data:latest（运行旧版 src.api.data_api:app 于 8001，挂载 BotQuan_Data 只读）
- **依赖模块**：src/utils/（config、logger、proxy、exceptions）、src/monitor/（collection_notifier、飞书系列、邮件通知）
- **运维脚本**：健康检查、备份、清理、NAS 同步、存储告警

---

## Jay.S 硬约束（4 条）

1. Mini 上 data 服务继续在 Mini Docker，不迁到本地
2. 只迁程序段到 JBT，在未接入 Mini Docker data 前不停 Mini 原采集器
3. 本地全量采集测试通过 + Jay.S 签确认单后才推 Mini Docker；飞书和邮件禁止迁移，必须本地重做
4. 100% 全量迁移，除飞书和邮件外无一遗漏

---

## 迁移范围

### 纳入迁移

| 类别 | 内容 |
|------|------|
| 采集器 | Mini 现网 collectors/（全部 17 个模块） |
| 主调度器 | data_scheduler.py（APScheduler，11 个调度管道） |
| 独立 scheduler | 18 个独立 scheduler 脚本 |
| 公共依赖 | utils/config、utils/logger、utils/proxy、utils/exceptions |
| 健康与心跳 | 健康检查、心跳、掉线检测、自动重连 |
| 运维脚本 | 备份、清理、NAS 同步、数据完整性检查、存储告警 |

### 明确排除

| 类别 | 内容 |
|------|------|
| 飞书相关 | feishu_bot、feishu_card_templates、feishu_client、feishu_command_handler、feishu_command_listener、feishu_config、feishu_offline_queue、feishu_webhook_server、feishu_ws_client、notify_feishu |
| 邮件相关 | notify_email、send_email_alert、send_email_card |
| 脚本 | 所有 send_feishu_* / send_email_* 脚本 |

### 通知系统

本地全新设计，不迁移旧代码。需 Jay.S 签单后才嵌入。

---

## 迁移策略

```
inventory → 本地实现 → 本地全量采集测试 → Jay.S 签确认单 → 推送 Mini Docker → 灰度切换 → 观察 → 全量切换
```

## 回滚方案

Mini 旧 cron/plist/scheduler 在全量切换验证通过前持续运行。任何批次出现问题可独立回滚该批次，不影响 Mini 现网采集。

## 可靠性要求

- 掉线自动重连
- 重连失败人工干预
- 心跳监控
- 故障检测与告警

---

## 分批计划

| 批次 | 内容 | 保护级别 | 依赖 |
|------|------|----------|------|
| **A0** | 治理建档 + inventory 冻结 | — | 无（本批） |
| **A1** | 采集器本体 + 公共依赖迁移（17 collectors + base + utils/config + utils/logger + utils/proxy + utils/exceptions + 数据模型） | P1 | A0 完成 |
| **A2** | 主调度器 + 独立 scheduler 迁移（data_scheduler + 18 个子 scheduler + 交易时段判断 + APScheduler 编排） | P1 | A0 完成 |
| **A3** | 健康检查 + 心跳 + 掉线检测 + 自动重连 + 人工接管（health_check、heartbeat、check_and_restart_collector、health_remediate） | P1 | A0 完成 |
| **A4** | 备份 + 清理 + NAS 同步 + 数据完整性（backup_to_nas、mini_data_backup、cleanup、check_data_completeness、storage_alert） | P1 | A0 完成 |
| **A5** | 本地全量采集联调 + 逐项对账 | P1 | A1~A4 全部完成 |
| **A6** | 通知系统本地重做设计（飞书 + 邮件），需 Jay.S 签单 | P0 | 独立于 A1~A5，可并行设计，嵌入需签单 |
| **A7** | 接入 Mini Docker + 灰度切换 + 24h 验证 | P0 | A5 通过 + A6 签单 |

### 批次执行约束

- A1~A4 可按序执行，也可 A1/A2 并行
- A5 必须在 A1~A4 全部完成后执行
- A6 独立于 A1~A5，可并行设计，但嵌入必须等 Jay.S 签单
- A7 必须在 A5 通过 + A6 签单后才能执行

---

## 预审结论

1. 本任务独立成立，不借用 TASK-0018-B
2. 保护级别：A1~A4 为 P1，A6 为 P0（涉及通知系统设计），A7 包含 P0（docker-compose / .env.example 等）
3. 批次执行顺序已冻结，见上方约束

---

【签名】项目架构师
【时间】2026-04-08
【设备】MacBook
