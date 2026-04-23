# REVIEW-TASK-NOTIFY-20260423-PRE 通知体系重构 · 并行预审

- 审核人：项目架构师
- 审核时间：2026-04-23
- 父批次：TASK-NOTIFY-20260423
- 审核范围：A / B / C / D / E 五个子任务
- 审核口径：架构边界 / 服务隔离 / 文件白名单 / Token 需求 / 技术风险

---

## 0. 总体结论

| 子任务 | 服务 | 预审结论 | 文件数 | 含 P0 文件 | 实施顺序 |
|---|---|---|---|---|---|
| TASK-NOTIFY-20260423-A | sim-trading | ✅ 通过（带 1 项最小修正） | 11 | 1 | 第 1 |
| TASK-NOTIFY-20260423-B | data | ✅ 通过（带 2 项最小修正） | 12 | 1 | 第 2 |
| TASK-NOTIFY-20260423-C | decision | ✅ 通过 | 12 | 1 | 第 3 |
| TASK-NOTIFY-20260423-D | backtest | ✅ 通过（带 1 项必须澄清） | 10 | 1 | 第 4 |
| TASK-NOTIFY-20260423-E | live-trading | ✅ 通过（占位限定） | 8 | 1 | 第 5（可延后） |

**跨服务边界总裁定**：5 个子任务全部限制在各自 `services/{服务}/` 目录内，未触碰 `shared/contracts/**`、`shared/python-common/**`、`integrations/**`、`docker-compose.dev.yml`、`WORKFLOW.md`、`.github/**`、`runtime/**`、`logs/**`、其他服务目录及任一真实 `.env`。**符合 service-isolation 红线。**

**公共代码片段裁定**：✅ **同意 Atlas 的"各服务本地复制、不进 `shared/python-common`"方案**。

理由：
1. 静默窗口、标题前缀、落款 3 个片段总代码量 < 50 行，复制成本远低于跨服务依赖耦合成本。
2. 进 `shared/python-common` 会强制 5 个服务版本同步、共用回滚链、共用 Token，违背"服务独立部署、独立回滚"红线。
3. 5 个服务部署节奏不同（Mini/Alienware/Studio/Air），共享库变更会产生连锁部署风险。
4. 语义一致性通过项目架构师维护的 `docs/prompts/公共项目提示词.md` "通知规范" 章节集中约束，由终审环节人工核对。

**约束补充**（项目架构师在终审时强制核对）：
- 5 个服务的 `quiet_window._in_push_window()` 函数必须**字面级一致**（同一段代码 copy），任何分支/边界条件偏差视为终审不通过。
- 5 个服务的 `build_footer()` 落款时区固定 `Asia/Shanghai (+08:00)`，时间戳格式固定 `%Y-%m-%d %H:%M:%S`。
- 5 个服务的 `build_title()` 前缀字典必须使用同一份字面常量，新增前缀必须先更新公共 prompt 再各服务跟进。

---

## 1. TASK-NOTIFY-20260423-A · sim-trading

### 1.1 预审结论
✅ **通过**（带 1 项最小修正）

### 1.2 冻结后文件白名单（11 个）

| 序号 | 文件路径 | 类型 | 说明 |
|---|---|---|---|
| 1 | `services/sim-trading/src/notifier/__init__.py` | 改 | 暴露 dispatcher/trade_push |
| 2 | `services/sim-trading/src/notifier/dispatcher.py` | 改 | 三群路由 + 静默 + 反馈 |
| 3 | `services/sim-trading/src/notifier/feishu.py` | 改 | 标题/颜色/落款/中文化 |
| 4 | `services/sim-trading/src/notifier/email.py` | 改 | HTML 模板 + 中文化 |
| 5 | `services/sim-trading/src/notifier/trade_push.py` | **新建** | 成交/订单即时推送 |
| 6 | `services/sim-trading/src/notifier/quiet_window.py` | **新建** | 静默窗口工具（本地复制） |
| 7 | `services/sim-trading/src/health/heartbeat.py` | 改 | 4h 节奏 + 中文化 |
| 8 | `services/sim-trading/src/main.py` | 改 | 调度 + 反馈横幅 |
| 9 | `services/sim-trading/src/api/router.py` | 改 | CTP 回调接入 + `/notify/health` |
| 10 | `services/sim-trading/src/risk/guards.py` | 改 | 中文落款 |
| 11 | `services/sim-trading/.env.example` | 改 | **P0 文件，单独 Token** |

### 1.3 跨服务边界裁定
✅ 全部限制在 `services/sim-trading/` 内，无任何跨服务读写或 import。CTP 回调通过本服务 `gateway/` 已落地，新增 trade_push 仅消费本服务内部事件。

### 1.4 公共片段本地复制
✅ 同意 `quiet_window.py` 与 `dispatcher.py` 内的 title/footer helper 本地实现。

### 1.5 关键技术风险与最小修正建议

1. ⚠️ **修正 1（必改）**：成交即时推送声称 "<3s"，但 CTP `OnRtnTrade` 回调在 Alienware 端是同步线程，dispatcher 若被卡住会反向阻塞 CTP 主线程。**强制要求**：trade_push 必须使用 `ThreadPoolExecutor` 或 `asyncio.run_coroutine_threadsafe` 异步派发，CTP 回调线程禁止直接阻塞等待飞书 HTTP。
2. 风险（提示）：连续 5 笔拒单升级 P1 的窗口期需明确（建议 60s 滑窗），实施时在 dispatcher 内落注释。
3. 风险（提示）：`/api/v1/notify/health` 端点要复用现有 8101 端口，不得另起进程。

### 1.6 Token 需求
- 1 份**普通任务 Token**：覆盖文件 1–10。
- 1 份**P0 单独 Token**：`services/sim-trading/.env.example`（请 Jay.S 单独签发）。

---

## 2. TASK-NOTIFY-20260423-B · data

### 2.1 预审结论
✅ **通过**（带 2 项最小修正）

### 2.2 冻结后文件白名单（12 个）

| 序号 | 文件路径 | 类型 | 说明 |
|---|---|---|---|
| 1 | `services/data/src/notify/__init__.py` | 改 | 暴露新模块 |
| 2 | `services/data/src/notify/dispatcher.py` | 改 | 三群路由 + 静默 + 反馈 |
| 3 | `services/data/src/notify/feishu.py` | 改 | 标题/落款/中文化 |
| 4 | `services/data/src/notify/email_notify.py` | 改 | HTML + 中文化 |
| 5 | `services/data/src/notify/news_pusher.py` | 改 | 30→60min + 链接强校验 + 黑天鹅冷却 |
| 6 | `services/data/src/notify/card_templates.py` | 改 | 七色映射 + 标题前缀 |
| 7 | `services/data/src/notify/quiet_window.py` | **新建** | 静默窗口工具 |
| 8 | `services/data/src/notify/feedback.py` | **新建** | 失败横幅累计 |
| 9 | `services/data/src/scheduler/data_scheduler.py` | 改 | 心跳 4h + 节段对齐 + 邮件夜报 |
| 10 | `services/data/src/scheduler/pipeline.py` | **条件改** | 仅在采集摘要分流必须触达时纳入；否则实施时书面移除 |
| 11 | `services/data/src/main.py` | 改 | `/notify/health` 端点 |
| 12 | `services/data/.env.example` | 改 | **P0 文件，单独 Token** |

### 2.3 跨服务边界裁定
✅ 全部限制在 `services/data/` 内。新闻链接、采集摘要均为 data 服务内部事件，未触发跨服务调用。

### 2.4 公共片段本地复制
✅ 同意 `quiet_window.py` 本地实现，与 sim-trading 字面级一致。

### 2.5 关键技术风险与最小修正建议

1. ⚠️ **修正 1（必改）**：白名单第 10 项 `pipeline.py` 注释为 "如涉及"，含糊。**强制要求**：执行 Agent 在实施前 5 分钟内明确 `pipeline.py` 是否需改动；不需改动则**写入交接单并从白名单删除**，不得"先纳入再不动"。
2. ⚠️ **修正 2（必改）**：黑天鹅 10 分钟合并窗口需基于关键词 hash + 时间戳双键去重，避免 RSS 不同源 URL 但同事件被误合并丢弃。实施时在 `news_pusher._breaking_dedup` 落注释说明。
3. 风险（提示）：节段卡 cron `09:00 / 13:30 / 21:00` 的 timezone 必须是 `Asia/Shanghai`，scheduler 必须显式声明 tz，不能依赖容器默认。
4. 风险（提示）：60→30 条 + 30→60min 后单卡数据量翻倍，飞书卡 element 上限风险；实施时校验生成卡 element 数 < 50。

### 2.6 Token 需求
- 1 份**普通任务 Token**：覆盖文件 1–11。
- 1 份**P0 单独 Token**：`services/data/.env.example`。

---

## 3. TASK-NOTIFY-20260423-C · decision

### 3.1 预审结论
✅ **通过**

### 3.2 冻结后文件白名单（12 个）

| 序号 | 文件路径 | 类型 | 说明 |
|---|---|---|---|
| 1 | `services/decision/src/notifier/__init__.py` | 改 | 暴露新模块 |
| 2 | `services/decision/src/notifier/dispatcher.py` | 改 | 三群路由 + 静默 + 反馈 |
| 3 | `services/decision/src/notifier/feishu.py` | 改 | 标题/颜色/落款 |
| 4 | `services/decision/src/notifier/email.py` | 改 | HTML 中文化 |
| 5 | `services/decision/src/notifier/daily_summary.py` | 改 | 5 节段对齐 |
| 6 | `services/decision/src/notifier/gate_notifications.py` | 改 | 强制交易群 |
| 7 | `services/decision/src/notifier/health_monitor.py` | 改 | 报警群路由 |
| 8 | `services/decision/src/notifier/quiet_window.py` | **新建** | 静默窗口 |
| 9 | `services/decision/src/notifier/feedback.py` | **新建** | 失败横幅 |
| 10 | `services/decision/src/llm/billing_notifier.py` | 改 | 1h → 4h |
| 11 | `services/decision/src/api/app.py` | 改 | 调度时点 + `/notify/health` |
| 12 | `services/decision/.env.example` | 改 | **P0 文件，单独 Token** |

### 3.3 跨服务边界裁定
✅ 全部限制在 `services/decision/` 内。`SIGNAL` 事件路由到飞书交易群属于通知层动作，与 sim-trading 之间仍走既有 HTTP API，未跨服务直读。

### 3.4 公共片段本地复制
✅ 同意。decision 的 `quiet_window` / footer / title 必须与 A/B 字面级一致。

### 3.5 关键技术风险与最小修正建议

1. 风险（提示）：`SIGNAL` 与 `GATE_*` 强制 `bypass_quiet_hours=True`，但夜间 02:00 无信号通常合理；建议在 dispatcher 实施时记录穿透次数，避免被滥用。
2. 风险（提示）：日报 cron 改为 5 节段后总频次翻倍，邮件夜报 23:30 与日报 23:05 间隔仅 25 分钟，需确认两者内容互补不重复（属于内容设计，不影响预审）。
3. 风险（提示）：`billing_notifier` 余额 <20% 走 P2，与既有报警等级阈值不冲突，但需要 dispatcher 知道这是 P2 而不是 INFO，实施时显式标注 `notify_level=NotifyLevel.P2`。

### 3.6 Token 需求
- 1 份**普通任务 Token**：覆盖文件 1–11。
- 1 份**P0 单独 Token**：`services/decision/.env.example`。

---

## 4. TASK-NOTIFY-20260423-D · backtest（新增）

### 4.1 预审结论
✅ **通过**（带 1 项必须澄清）

### 4.2 冻结后文件白名单（10 个）

| 序号 | 文件路径 | 类型 | 说明 |
|---|---|---|---|
| 1 | `services/backtest/src/notifier/__init__.py` | **新建** | 模块入口 |
| 2 | `services/backtest/src/notifier/dispatcher.py` | **新建** | 参考 sim-trading 模板 |
| 3 | `services/backtest/src/notifier/feishu.py` | **新建** | 飞书通道 |
| 4 | `services/backtest/src/notifier/email.py` | **新建** | 邮件通道 |
| 5 | `services/backtest/src/notifier/quiet_window.py` | **新建** | 静默窗口 |
| 6 | `services/backtest/src/notifier/feedback.py` | **新建** | 失败横幅 |
| 7 | `services/backtest/src/backtest/stock_runner.py` | 改 | 完成/失败钩子 |
| 8 | `services/backtest/src/backtest/manual_runner.py` | 改 | 完成/失败钩子 |
| 9 | `services/backtest/src/api/app.py` | 改 | 17:00 邮件调度 + `/notify/health` |
| 10 | `services/backtest/.env.example` | 改 | **P0 文件，单独 Token** |

### 4.3 跨服务边界裁定
✅ 全部限制在 `services/backtest/` 内。回测任务 ID、结果 URL 指向本服务 backtest-web 端口，未跨服务直接读写。

### 4.4 公共片段本地复制
✅ 同意。

### 4.5 关键技术风险与最小修正建议

1. ⚠️ **澄清 1（必须）**：backtest 服务在 **Air (192.168.31.156) 与 Studio (192.168.31.142) 双节点同时部署**。同一回测任务若在两节点都触发完成钩子，会**双发飞书**。任务文档第 4 节 "Air 与 Studio 两节点都需部署" 明确双部署，但**未规定通知归属**。
   - **强制要求**：实施前由 Atlas 确认两节点中**仅一个开启 `BACKTEST_NOTIFY_ENABLED=true`**（建议 Studio，因 backtest-web 主入口在 Studio），另一节点 `.env` 设为 `false`。
   - 该开关必须在 `.env.example` 注释中标注："多节点部署下仅主节点开启，避免双发"。
2. 风险（提示）：完成钩子放在 `runner.run() finally` 块内，必须保证异常路径也走 finally；建议在 try/except/finally 三层都加 log，避免静默丢失。
3. 风险（提示）：Optuna 优化批次卡片包含 Top3 参数组，单卡内容较长，需校验飞书卡 4096 字符上限。

### 4.6 Token 需求
- 1 份**普通任务 Token**：覆盖文件 1–9。
- 1 份**P0 单独 Token**：`services/backtest/.env.example`。

---

## 5. TASK-NOTIFY-20260423-E · live-trading（占位）

### 5.1 预审结论
✅ **通过**（占位限定）

### 5.2 冻结后文件白名单（8 个）

| 序号 | 文件路径 | 类型 | 说明 |
|---|---|---|---|
| 1 | `services/live-trading/src/notifier/__init__.py` | **新建** | 模块入口 |
| 2 | `services/live-trading/src/notifier/dispatcher.py` | **新建** | 复制 sim 版本 + 双发约束 |
| 3 | `services/live-trading/src/notifier/feishu.py` | **新建** | 飞书通道 |
| 4 | `services/live-trading/src/notifier/email.py` | **新建** | 邮件通道（含 CC 列表） |
| 5 | `services/live-trading/src/notifier/trade_push.py` | **新建** | 占位，不接入 CTP |
| 6 | `services/live-trading/src/notifier/quiet_window.py` | **新建** | 静默窗口 |
| 7 | `services/live-trading/src/notifier/feedback.py` | **新建** | 失败横幅 |
| 8 | `services/live-trading/.env.example` | 改 | **P0 文件，单独 Token** |

### 5.3 跨服务边界裁定
✅ 全部限制在 `services/live-trading/` 内。**重要**：当前 `services/live-trading/src/` 为空目录，本任务将首次创建 `src/notifier/` 包。**强制要求**：
- 不得在本任务中新建 `src/__init__.py` 之外的任何业务模块（main / api / gateway 等）。
- `notifier/` 必须能独立 `python -c "from src.notifier import dispatcher"` 通过；为此允许新建 `services/live-trading/src/__init__.py` 一个空文件，但**该文件需追加进白名单**（共 9 个文件，请实施时同步报备）。

### 5.4 公共片段本地复制
✅ 同意。代码可直接从 sim-trading 完成版逐字 copy，仅替换标题前缀和落款字符串。

### 5.5 关键技术风险与最小修正建议

1. 风险（提示）：双发约束 "两通道同时成功才返回 True" 在 sim-trading 模板中不存在，是 live-trading 独有逻辑，dispatcher 中需用独立分支实现，不要污染 sim-trading 的单通道兜底链。
2. 风险（提示）：本任务为占位，实施完成后**禁止**任何调度器/服务进程注册（live-trading 还未上线），避免空跑。
3. 风险（提示）：依赖 TASK-A 完成后再启动，确保模板版本一致；若 TASK-A 后续二次修订，TASK-E 需联动同步。

### 5.6 Token 需求
- 1 份**普通任务 Token**：覆盖文件 1–7（外加可能新增的 `src/__init__.py`）。
- 1 份**P0 单独 Token**：`services/live-trading/.env.example`。

---

## 6. 跨任务统一校核

### 6.1 不会产生跨服务 import
所有 5 个任务的"公共代码片段"均**本地复制**，不引入 `from shared.python_common.notify import ...` 之类的依赖；service-isolation 红线保持。

### 6.2 不会触碰契约
本批次**不涉及** `shared/contracts/**`。三群分流是各服务**对外通知**层逻辑，不涉及任何跨服务 API 字段，因此**不需要契约预审**。

### 6.3 不会触碰其他 P0/P2 区域
除每个任务的 `.env.example` 外，本批次**不触及** `WORKFLOW.md`、`.github/**`、`shared/contracts/**`、`shared/python-common/**`、`integrations/**`、`docker-compose.dev.yml`、`runtime/**`、`logs/**`。

### 6.4 实施顺序（强制串行）
```
A (sim-trading) → B (data) → C (decision) → D (backtest) → E (live-trading 占位)
```
每子任务**独立预审 / 独立 Token / 独立实施 / 独立终审 / 独立锁回 / 独立 commit**，禁止合批。

### 6.5 公共项目提示词联动
本批次终审通过后，由项目架构师在 `docs/prompts/公共项目提示词.md` 新增"通知规范"章节，沉淀以下 5 项标准（独立预审、独立 Token）：
1. 三群边界与 webhook 环境变量名约定
2. 标题前缀字典（`[等级-类型]`）
3. 落款规范（`JBT-{服务中文名}`）
4. 静默窗口语义（08:00–24:10）
5. 通道失败反馈机制

---

## 7. 给 Atlas 的汇报摘要

### 7.1 预审结论
- **5 个子任务全部预审通过**。
- A / B / D 各带 1–2 项**最小必改修正**（已在各子任务 §x.5 标注 ⚠️）。
- 公共代码片段**同意各服务本地复制**，不进 `shared/python-common`。
- 跨服务边界**全部合规**，未触碰 `shared/contracts/**` 与其他服务目录。

### 7.2 冻结后文件白名单总数
| 子任务 | 文件数 | 含新建数 | 含 P0 数 |
|---|---|---|---|
| A | 11 | 2 | 1 |
| B | 12 | 2 | 1 |
| C | 12 | 2 | 1 |
| D | 10 | 6 | 1 |
| E | 8（可能 +1） | 7（可能 +1） | 1 |
| **合计** | **53–54** | **19–20** | **5** |

### 7.3 需 Jay.S 关注的 Token 项（共 5 份 P0 单独 Token）
| 子任务 | P0 文件 | 说明 |
|---|---|---|
| A | `services/sim-trading/.env.example` | 新增 ALERT/TRADE/INFO 三 webhook key |
| B | `services/data/.env.example` | 复核三 webhook key 文档 |
| C | `services/decision/.env.example` | 新增三 webhook key |
| D | `services/backtest/.env.example` | 新增三 webhook + SMTP + 多节点开关 |
| E | `services/live-trading/.env.example` | 新增三 webhook + SMTP + 灰度 CC 列表 |

**特殊提示**：
1. **TASK-D 必须在签 Token 前由 Atlas 明确"Air/Studio 双节点中由哪一节点负责通知"**（建议 Studio），并在 `.env.example` 注释固化。
2. **TASK-E 实施时如需新建 `services/live-trading/src/__init__.py`，需要 Atlas 同步把该文件追加进 Token 范围**（共 9 文件）。
3. 5 份 P0 Token 建议**分子任务串行签发**，与实施顺序对齐，避免并行解锁带来的窗口期暴露。

### 7.4 后置项
- 终审通过后，项目架构师独立预审 + Token 修订 `docs/prompts/公共项目提示词.md` 的"通知规范"新章节。
- 5 个执行 Agent 私有 prompt（`docs/prompts/agents/{服务}提示词.md`）由各 Agent 在终审锁回后自行更新。

---

**审核签字**：项目架构师  
**结论**：✅ 全部通过，等待 Atlas 调度 + Jay.S 签发首批 Token（建议从 TASK-A 启动）。
