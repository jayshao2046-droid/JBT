# TASK-0028 — 数据端通知系统全量建设

| 字段 | 值 |
|------|-----|
| 任务 ID | TASK-0028 |
| 父任务 | TASK-0027 (数据端迁移) |
| 执行 Agent | 数据 |
| 审核 Agent | Atlas |
| 优先级 | P1 |
| 状态 | ✅ 主批次完成，✅ B6 通知体验优化完成并锁回 |
| 创建时间 | 2026-04-09 |
| 完成时间 | 2026-04-09 |
| Git 提交 | `1d8f262` |

## 目标

为 JBT 数据端构建完整通知系统：飞书三群路由（报警/交易/资讯）+ QQ 邮箱日报 + P0 按钮修复。

## 批次

| 批次 | 内容 | 状态 |
|------|------|------|
| B1 | dispatcher + card_templates + news_pusher (新建) | ✅ |
| B2 | feishu.py + email_notify.py + __init__.py (重写) | ✅ |
| B3 | scheduler / health_check / heartbeat 嵌入通知触发 | ✅ |
| B4 | main.py ops API + .env.example | ✅ |
| B5 | test_notify.py + 实测验证 | ✅ |
| B6 | 通知体验优化 + 0 产出策略收口 | ✅ locked |

## 实测结果（2026-04-09 02:26）

| 通道 | 发送数 | 结果 |
|------|--------|------|
| 报警群 | 4 张卡片（P0+P1+恢复+设备健康） | ✅ 全部成功 |
| 交易群 | 3 张卡片（启动+完成+批次） | ✅ 全部成功 |
| 资讯群 | 2 张卡片（新闻批量+突发） | ❌ `Key Words Not Found`（webhook 关键词安全校验） |
| 邮件日报 | 1 封 HTML | ✅ 成功 |

冒烟测试：13 卡片模板 + 导入 + HTML 日报 — 全部通过

### 剩余待处理

- 资讯群 webhook 配置了飞书自定义关键词安全校验，卡片标题/内容中需包含该关键词才能发送。需 Jay.S 提供关键词或在飞书后台修改安全设置。

## 补充批次 B6（已完成并锁回）

### 目标

收敛数据端当前通知噪音，冻结“同窗合并 + 单采集器仅飞书 + 新闻静默窗口修正 + 0 产出通知语义修正”四项范围。

### 已确认根因

- 外盘分钟 0 产出并非邮件误报，而是 Mini 运行态出现 `yfinance` 退避冷却，且 `Alpha Vantage` / `Twelve Data` API key 未配置，导致在退避窗口内 27 个品种直接 0 产出。
- 当前通知风暴主入口位于 `src/scheduler/data_scheduler.py` 的 `_safe_run()`：完成通知默认双通道，且 `bypass_quiet_hours=True`。
- 当前新闻静默窗口在 `src/notify/dispatcher.py` 中仍为 22:00-08:00，不符合当前口径。

### 白名单（预审冻结）

- `services/data/src/scheduler/data_scheduler.py`
- `services/data/src/notify/dispatcher.py`
- `services/data/src/notify/news_pusher.py`
- `services/data/tests/test_notify.py`

### 明确排除

- `services/data/src/scheduler/pipeline.py`
- `services/data/src/collectors/overseas_minute_collector.py`
- `services/data/src/main.py`
- `services/data/src/health/**`
- `services/data/.env.example`
- `shared/contracts/**`
- `runtime/`、`logs/`、Mini 线上配置与真实密钥

### 验收标准

1. 同一调度时间窗内的完成类通知合并为单条摘要通知。
2. 同一时间新闻推送合并为单条摘要通知。
3. 新闻静默窗口调整为 22:00-08:30，P0 与显式 bypass 语义不变。
4. 单独采集允许单独推送，但仅飞书，不发邮件。
5. 外盘分钟 0 产出不得继续按“采集完成”成功通知处理，本批只修通知语义，不修采集根因。

### 完成结果

- `services/data/src/scheduler/data_scheduler.py` 已接通 `sync_from_storage() -> flush()` 链路，并移除 `job_news_push_batch()` 尾部残留的未定义变量路径。
- `services/data/src/notify/dispatcher.py` 已完成同窗采集摘要合并、单采集器仅飞书、NEWS `22:00-08:30` 静默窗口与 `0产出` 语义收口。
- `services/data/src/notify/news_pusher.py` 已统一 `flush()` / `flush_batch()`，真实调度路径可汇总新闻摘要推送。
- `services/data/tests/test_notify.py` 当前自校验结果为 `11 passed`。
- 项目架构师复审结果：`REVIEW-TASK-0028-B6` 通过；B6 锁回 token：`tok-6fc51e92-756e-476d-8b43-7c35db059334`。

## 文件清单（13 文件，+2121/-322）

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/notify/card_templates.py` | 新建 | 13 种飞书卡片模板 |
| `src/notify/dispatcher.py` | 新建 | 双通道调度器 + 告警升级 + 去重 |
| `src/notify/news_pusher.py` | 新建 | 新闻推送器 + 黑天鹅检测 |
| `tests/test_notify.py` | 新建 | 冒烟测试 + 实测函数 |
| `src/notify/feishu.py` | 重写 | FeishuSender 类 |
| `src/notify/email_notify.py` | 重写 | EmailSender + HTML 日报 |
| `src/notify/__init__.py` | 重写 | 统一导出 |
| `src/scheduler/data_scheduler.py` | 修改 | 采集事件派发 + 日报/新闻定时 |
| `src/health/health_check.py` | 修改 | 4 个告警函数迁移新模板 |
| `src/health/heartbeat.py` | 修改 | DeviceHealthReporter |
| `src/main.py` | 修改 | v0.2.1 + OPS 端点 |
| `.env.example` | 修改 | 三 webhook + 邮件配置 |
| `docs/tasks/TASK-0028-*.md` | 新建 | 任务登记 |

## 约束

- 飞书 3 个独立 Webhook（报警/交易/资讯）
- 邮件：17621181300@qq.com → 17621181300@qq.com + ewangli@iCloud.com
- 使用 JBT 统一卡片颜色标准
- P0 告警支持飞书操作按钮
