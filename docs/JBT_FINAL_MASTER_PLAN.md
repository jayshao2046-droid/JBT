# JBT 终局总计划 — 全服务归属 · 任务分配 · 开发进度

【签名】Atlas
【时间】2026-04-09
【设备】MacBook
【状态】正式发布

> 本文件为 JBT 多服务工作区的最终收口计划。所有 Agent 在开始工作前必须读取本文件，确认自己的任务队列和衔接入口。

## ⚠️ 终局计划冲突管理规则（P0 最高优先级）

> **本章规则优先级高于本文件其余所有内容，高于任何单任务预审结论，高于任何 Agent 私有 prompt。**

1. **备注义务**：任何 Agent 在执行任务时，若实际变更与本计划任何细节不一致（包括但不限于：进度百分比、任务归属、Phase 顺序、文件白名单、依赖关系、验收标准），**必须在对应任务的 `docs/tasks/` 或 `docs/reviews/` 文件中显式备注差异**，格式为 `[PLAN-DELTA] 本批实际变更与终局计划第X章/X.X节不一致：{具体差异} → {本批实际口径}`。
2. **冲突确认**：遇到冲突时，**必须先暂停代码写入**，向 Jay.S 或 Atlas 提交冲突说明，确认"以哪个为准"后才可继续。不得自行裁决冲突、不得默认以本批实际口径覆盖计划。
3. **决定性变更**：若冲突涉及以下任一项，**必须立即停止执行，等待 Jay.S 确认并由 Atlas 修订本计划后才可继续**：
   - Phase 顺序变更（例如某 Phase 需要提前或推后）
   - 服务归属变更（例如某模块从 decision 移到 data）
   - 跨服务依赖链变更（例如新增或移除服务间 API 依赖）
   - 设备拓扑或端口变更
   - 新增未登记的 TASK 编号
   - 任何涉及 `shared/contracts/**` 的结构性变更
4. **计划修订流程**：本计划只能由 Atlas 在 Jay.S 确认后修订。修订时必须：(a) 在变更处标注 `[修订 YYYY-MM-DD]` 时间戳；(b) 同步更新所有受影响的 Phase、Agent 衔接矩阵和依赖链；(c) 通知所有相关 Agent 重新读取本计划。
5. **各服务临时看板（*_web）的变更**：各服务容器内临时看板（sim-trading_web/decision_web/backtest_web/data_web）跟随其后端 Agent 按后端变更配套调整即可，不视为计划冲突；但聚合看板（dashboard:8106）的变更必须走本章规则。

## [修订 2026-04-09] 3 天执行窗口总令

1. 自 Jay.S 于 2026-04-09 在当前窗口确认起，所有“已建档、已完成预审、白名单已冻结”的改造任务统一进入 3 天执行窗口，执行口径按 4320 分钟管理。
2. 当前 JBT 锁控仍只有“文件级 Token”能力，不存在目录级、服务级或整仓级“全局 Token”；任何“全局 Token”表述一律解释为“在 3 天窗口内，按任务 / 批次 / 文件白名单分别签发 4320 分钟 Token”，不得越权放大为整端解锁。
3. 每个批次完成后必须先完成最小验证并留存证据，再执行 lockback。证据至少包含以下之一并写入对应 `docs/reviews/**`、`docs/handoffs/**` 或任务留痕：测试结果、构建结果、运行日志摘要、诊断结果、远端验证摘要。
4. 禁止把多个批次连续开发后再统一补验证、统一补锁回。任何已完成批次若未留下验证证据并立即锁回，视为未完成，不得进入下一批。
5. 所有改造任务必须按依赖链倒排，在 3 天窗口内尽可能闭环；若存在开盘窗口、DNS/SSH、用户凭据、P0 保护区等外部阻塞，必须即时留痕为阻塞项，不得以赶工为由跳过预审、白名单、验证或锁回。

---

## 一、项目总览

JBT 是一个多服务量化交易系统工作区，包含 6 个核心服务 + 1 个治理层。目标是从 legacy J_BotQuant 单体系统迁移到完全隔离、可独立部署、API-first 的微服务架构。

### 设备拓扑（冻结）

| 设备 | 角色 | IP（内网） | IP（蒲公英） | 部署服务 |
|------|------|-----------|-------------|---------|
| MacBook | 开发/控制 | localhost | 172.16.3.136 | 全部开发环境 |
| Mini | 数据+模拟交易 | 192.168.31.74 | 172.16.0.49 | data:8105, sim-trading:8101, sim-trading-web:3002 |
| Air | 回测生产 | 192.168.31.245 | — | backtest:8103, backtest-web:3001 |
| Studio | 决策+看板 | 192.168.31.142 | 172.16.1.130 | decision:8104, decision-web:3003, dashboard:8106 |
| ECS | 云端（备用） | 47.103.36.144 | — | 暂停，待域名+SSH就绪 |

### 端口分配（冻结）

| 服务 | API端口 | Web端口 | 归属设备 |
|------|---------|---------|---------|
| sim-trading | 8101 | 3002 | Mini |
| live-trading | 8102 | 3006 | Studio（后置） |
| backtest | 8103 | 3001 | Air |
| decision | 8104 | 3003 | Studio |
| data | 8105 | 3004 | Mini |
| dashboard | 8106 | 3005 | Studio |

---

## 二、服务状态与归属矩阵

### 2.1 模拟交易 sim-trading — 27%

**负责 Agent：模拟交易**
**服务目录：`services/sim-trading/`**
**契约目录：`shared/contracts/sim-trading/`（5份已锁回）**

| 模块 | 状态 | 说明 |
|------|------|------|
| CTP/SimNow 网关 | ✅ 已部署 | `src/gateway/simnow.py`，Mini 容器运行中 |
| API 路由 | ✅ 基本完成 | `src/api/router.py`，含 system_state/connect/disconnect/strategy/publish |
| 期货公司接通 | ❌ 未完成 | 当前尚未完成期货公司 sim-trading 的执行链路，需等待 decision Phase C 真闭环 |
| 风控守卫 | 🔶 骨架 | `src/risk/guards.py`，emit_alert 已接线，但规则引擎待完善 |
| 交易执行 | 🔶 骨架 | `src/execution/`，待调试 |
| 账本 | 🔶 骨架 | `src/ledger/service.py`，待调试 |
| 通知 | 🔶 部分 | A1 dispatcher/guards 已锁回；A2 系统事件接线待执行 |
| 发布接口 | ✅ 已锁回 | TASK-0023-A，`POST /api/v1/strategy/publish` |
| 运行态收口 | 🔶 A批完成 | TASK-0022-A locked；B批日志查看 pending |
| Docker/Mini | ✅ 已部署 | TASK-0017-A3，待开盘验证CTP |
| 临时看板 | ✅ 基本可用 | `sim-trading_web/`，operations+intelligence 页面 |

**已完成任务：** TASK-0002(契约), TASK-0009(治理闭环), TASK-0013(治理闭环), TASK-0014(A1~A4全锁回), TASK-0017-A3, TASK-0019(B1/B2锁回), TASK-0022-A, TASK-0023-A [修订 2026-04-10]
**当前活跃：** TASK-0017(待开盘验证)
**排队任务：** TASK-0010 → TASK-0022-B [修订 2026-04-10 TASK-0009/0013已闭环]

> **[修订 2026-04-10] 当前 sim-trading 只完成 SimNow 网关、发布接口、运行态基础与 Mini 部署，尚未接通期货公司 **

### 2.2 决策 decision — 90% [修订 2026-04-10 代码审计校正]

**负责 Agent：决策**
**服务目录：`services/decision/`**
**契约目录：`shared/contracts/decision/`（9份已锁回）**

| 模块 | 状态 | 说明 |
|------|------|------|
| API 骨架 | ✅ 已完成 | `src/api/routes/`（strategy/signal/model） |
| 策略仓库 | ✅ 已完成 | `src/strategy/repository.py`，8态生命周期完整 |
| 策略发布 | ✅ 已完成 | `src/publish/`（gate+sim_adapter+executor），H4闭环 |
| 研究中心 | ✅ 已完成 | `src/research/`（factor_loader真实data API接入/trainer/optuna/shap/onnx） |
| 模型路由 | 🔶 资格验证 | `src/model/router.py`，版本对齐+因子HASH校验，无实际推理加载（P2） |
| 门控 | ✅ 已完成 | `src/gating/`（backtest_gate/research_gate） |
| 持久化 | ✅ 已完成 | `src/persistence/`（FileStateStore） |
| 通知 | ✅ 已完成 | `src/notifier/`（飞书+邮件双通道投产，6级通知，JBT统一颜色） |
| 报告 | ✅ 已完成 | `src/reporting/`（daily+research_summary投产） |
| 临时看板 | ✅ 已完成 | `decision_web/` 7页面全部接真实数据（H6/H7完成去mock） |
| Dockerfile | ✅ 已修复 | TASK-0021-H0 |
| 测试 | ✅ 98用例 | `tests/` 全通过 |

**已完成任务：** TASK-0021(A契约+H0~H7全批次锁回), TASK-0024(部署审查) [修订 2026-04-10]
**剩余缺口（P2/P3）：** 模型路由无推理加载、Sharpe真实计算、ONNX存储路径、models-factors页数据绑定
**排队任务：** TASK-0025(SimNow备用方案) → TASK-0016(正式接入)

### 2.3 数据 data — 5%

**负责 Agent：数据**
**服务目录：`services/data/`**

| 模块 | 状态 | 说明 |
|------|------|------|
| 最小 bars API | ✅ 已完成 | `src/main.py`（health/version/symbols/bars） |
| 采集器 | ✅ 已部署(legacy) | `src/collectors/`（21个采集器文件），Mini 通过 cron 运行 |
| 调度器 | ✅ 已部署(legacy) | `src/scheduler/data_scheduler.py`，Mini 以 --daemon 运行 |
| 健康检查 | 🔶 有误报 | `src/health/health_check.py`，stock/news 判定有误报 |
| 通知 | 🔶 部分修复 | TASK-0028-B6 已修复通知体验，飞书/邮件恢复 |
| 新闻推送 | 🔶 部分修复 | `src/notify/news_pusher.py`，批量推送已恢复 |
| data_web | 🔶 部分 | 临时原型已导入，6页正式化与独立前端容器未完成 |
| Docker化 | 🔶 部分 | Mini 容器运行中(JBT-DATA-8105)，但调度仍为 legacy cron |
| 存储 | ✅ 已完成 | `src/data/storage.py`，Mini `~/jbt-data/` 目录体系 |

**已完成任务：** TASK-0018-B(bars API token active), TASK-0028-B6(通知修复locked)
**当前活跃：** TASK-0031(非夜盘热修 pending_token)
**排队任务：** TASK-0031 → TASK-0027(全量迁移) → data_web独立任务

> **[修订 2026-04-10] data 端仍要做“system 级迁移”的原因是：当前 Mini 现网真实 24h 采集、调度、健康检查和通知仍大量依赖 legacy collectors / scripts / crontab；JBT data 目前只承接最小供数 API、部分通知修复与 data_web 前端原型。若不完成 system 级迁移，JBT data 仍只是供数 API 壳层，无法满足无中断、可观测、可回滚的正式运行要求。**

### 2.4 回测 backtest — 95% [修订 2026-04-10 Phase E 全闭环，进入维护态]

**负责 Agent：回测**
**服务目录：`services/backtest/`**
**契约目录：`shared/contracts/backtest/`（4份已锁回）**

| 模块 | 状态 | 说明 |
|------|------|------|
| 在线引擎 | ✅ 已完成 | TqApi+TqSim+TqBacktest+TqAuth |
| 本地引擎 | ✅ 已完成 | `src/backtest/local_engine.py`，双引擎路由 |
| 风控引擎 | ✅ 已完成 | `src/backtest/risk_engine.py`，max_drawdown+daily_loss 双规则 |
| 因子注册 | ✅ 已完成 | `src/backtest/factor_registry.py`（MACD/RSI/VolumeRatio/ATR/ADX） |
| FC-224策略 | ✅ 已完成 | `src/backtest/fc_224_strategy.py`，total_trades=242 |
| 结果构建 | ✅ 已完成 | `src/backtest/result_builder.py` |
| 引擎选择器 | ✅ 已完成 | 前端+后端双路径 |
| 看板两页 | ✅ 已完成 | agent-network + operations |
| 泛化引擎 | ✅ 已完成 | TASK-0008 A/B/C/D 四批全锁回 [修订 2026-04-10] |
| 新增因子 | ✅ 已完成 | TASK-0026 A/B/C 三批全 locked_back [修订 2026-04-10] |
| 8004并回 | ✅ 已完成 | TASK-0007 A/B/C/D 全锁回 [修订 2026-04-10] |
| 容器命名 | ✅ 已完成 | TASK-0005 JBT-BACKTEST-8103/3001 [修订 2026-04-10] |

**已完成任务：** TASK-0003(全锁回), TASK-0004(锁回), TASK-0005(锁回), TASK-0007(A/B/C/D全锁回), TASK-0008(A/B/C/D全锁回), TASK-0018(A/C/D/E锁回), TASK-0026(A/B/C全锁回) [修订 2026-04-10]
**Phase E 状态：全部闭环，回测进入维护态** [修订 2026-04-10]
**排队任务：** 无新排队

> **[修订 2026-04-09] 双回测分离原则：** Air 人工回测在 Phase E 完成后进入维护态（只修 bug、不加功能）。PBO/CPCV 等研究级能力归决策端内置研究回测引擎（Phase C / Section 5.4 沙箱），两端引擎代码不共享、职责不交叉。

### 2.5 看板 dashboard — 5%

**负责 Agent：看板**
**服务目录：`services/dashboard/`**

| 模块 | 状态 | 说明 |
|------|------|------|
| Dockerfile | ✅ 存在 | 基础骨架 |
| .env.example | ✅ 存在 | 基础配置 |
| src/ | ❌ 空目录 | 零代码 |
| 聚合看板 | ❌ 未开始 | 需聚合6个服务的只读数据 |

**当前状态：** 各服务使用自己容器内的临时看板（backtest_web/sim-trading_web/decision_web/data_web）
**定位：** 看板端为最后完成的服务。所有后端服务（sim-trading/decision/data/backtest）先完成 API 和数据能力，看板端最后纵观全局、一次性部署所有聚合功能。各服务容器内的临时看板跟随各自后端 Agent 配套更新，不受此顺序约束。
**排队任务：** TASK-0015(SimNow临时看板，已有参考前端) → 聚合看板独立任务（等所有后端 Phase 基本完成后启动）

> **[修订 2026-04-10] 聚合 dashboard 继续后置。当前 sim-trading / decision / data 三端临时看板均未全部收口，因此总看板不进入实施，只继续保留治理与信息架构冻结。**

### 2.6 实盘交易 live-trading — 0%

**负责 Agent：实盘交易**
**服务目录：`services/live-trading/`**

| 模块 | 状态 | 说明 |
|------|------|------|
| .env.example | ✅ 存在 | 占位 |
| README.md | ✅ 存在 | 占位 |
| src/ | ❌ 空目录 | 零代码 |

**前置条件：** 模拟交易契约稳定 + 统一风控核心(TASK-0013)完成 + sim-trading 连续稳定运行 2~3 个月并经 Jay.S 再次确认后启动 [修订 2026-04-10]
**排队任务：** 契约复用 → 骨架 → 网关 → 执行 → 风控 → 账本 → 通知

> **[修订 2026-04-10] live-trading 不进入当前执行窗口。当前明确后置，待 sim-trading 在 Mini 上连续稳定运行 2~3 个月后，再单独评估是否启动 Phase H。**

---

## 三、全量任务登记表（TASK-0001 ~ TASK-0031）

### 3.1 已完成/已锁回

| 任务编号 | 名称 | 服务 | 状态 |
|---------|------|------|------|
| TASK-0001 | 锁控器初始化 | 治理 | ✅ 闭环 |
| TASK-0002 | sim-trading Phase1 契约 | sim-trading | ✅ 阶段一闭环 |
| TASK-0003 | backtest Phase1 全开发 | backtest | ✅ R3锁回(75%) |
| TASK-0004 | backtest 看板两页收敛 | backtest | ✅ 语义修复锁回 |
| TASK-0017-A3 | Docker+Mini部署 | sim-trading | ✅ 部署完成 |
| TASK-0018-A | backtest 契约扩展 | backtest | ✅ 锁回 |
| TASK-0018-C | 双引擎执行编排 | backtest | ✅ 锁回 |
| TASK-0018-D | 系统级风控联动 | backtest | ✅ 锁回 |
| TASK-0018-E | 引擎选择控件 | backtest | ✅ 锁回 |
| TASK-0021-A | decision 契约冻结 | decision | ✅ 锁回 |
| TASK-0021-H0~H4 | decision 部署收口 | decision | ✅ 全锁回 |
| TASK-0022-A | sim-trading 运行态A | sim-trading | ✅ 锁回 |
| TASK-0023-A | sim-trading 发布接口 | sim-trading | ✅ 锁回 |
| TASK-0028-B6 | data 通知体验优化 | data | ✅ 锁回 |
| TASK-0029 | 极速维修V2制度 | 治理 | ✅ 锁回 |
| TASK-0030 | 终极维护U0制度 | 治理 | ✅ 锁回 |
| TASK-0014-A1 | 风控通知hooks | sim-trading | ✅ 锁回 |
| TASK-0007-A | backtest 契约补登 | backtest | ✅ 锁回 |
| TASK-0007-D | backtest Dockerfile修复 | backtest | ✅ 锁回 |
| TASK-0024 | 全平台部署审查 | 全局 | ✅ 完成 |

### 3.2 当前活跃/待执行

| 任务编号 | 名称 | 服务 | Agent | 状态 | 优先级 |
|---------|------|------|-------|------|--------|
| TASK-0031 | data非夜盘热修 | data | 数据 | pending_token(6文件) | P1 紧急 |
| TASK-0018-B | backtest 数据API | data | 数据 | active | P1 |
| TASK-0018-C-SUP | 本地引擎补数据 | backtest | 回测 | active | P1 |
| TASK-0017 | Mini开盘验证 | sim-trading | 模拟交易 | 待开盘 | P1 |
| TASK-0014-A2 | 系统事件接线 | sim-trading | 模拟交易 | ✅ locked | P1 |
| TASK-0019 | 收盘统计邮件 | sim-trading | 模拟交易 | ✅ B1/B2 locked | P1 |
| TASK-0022-B | 只读日志查看 | sim-trading | 模拟交易 | pending_token | P2 |
| TASK-0009 | 严格风控验收 | sim-trading | 模拟交易 | ✅ 治理闭环 [2026-04-10] | P1 |
| TASK-0013 | 统一风控核心 | sim-trading+live | 项目架构师 | ✅ 治理闭环 [2026-04-10] | P1 |
| TASK-0010 | 服务骨架完善 | sim-trading | 模拟交易 | 前置已满足，待签发 [2026-04-10] | P1 |
| TASK-0025 | SimNow备用方案 | decision | 决策 | 预审 | P2 |
| TASK-0026 | 新增因子+别名 | backtest | 回测 | ✅ locked_back | P1 |
| TASK-0008 | 泛化引擎+报告导出 | backtest | 回测 | ✅ locked | P1 |
| TASK-0007-B | 正式后端并回 | backtest | 回测 | ✅ locked | P1 |
| TASK-0007-C | 前端8004收口 | backtest | 回测 | ✅ locked | P1 |
| TASK-0005 | 容器命名统一 | backtest | 回测 | ✅ locked | P2 |
| TASK-0027 | data全量采集迁移 | data | 数据 | 预审 | P1 |
| TASK-0015 | SimNow临时看板 | dashboard | 看板 | 预审 | P2 |
| TASK-0020 | ECS云部署 | 运维 | 运维 | 阻塞 | P2 |
| TASK-0011 | legacy清退 | sim-trading | 项目架构师 | 后置 | P2 |
| TASK-0012 | legacy信号桥接 | integrations | 项目架构师 | 后置 | P1 |
| TASK-0016 | 决策端正式接入 | decision | 决策 | 后置 | P1 |
| TASK-0036 | 灾备演练 | 全局 | 项目架构师 | 待Phase B完成 | P1 |
| TASK-0037 | PBO过拟合检验(决策端内置) | decision | 决策 | 待Phase C(C2) | P1 |

---

## 四、分阶段执行路线图

### Phase A — 基础稳定化（当前最高优先级）

**目标：** 确保当前已部署的服务稳定运行，修复已知问题

| 序号 | 任务 | Agent | 依赖 | 验收标准 |
|------|------|-------|------|---------|
| A1 | TASK-0031 data热修 | 数据 | Jay.S 签发6文件Token | A股停采不报错；health_check无误报；新闻推送恢复 |
| A2 | TASK-0017 开盘验证 | 模拟交易 | 开盘窗口 | CTP行情tick收到；成交回报正常；蒲公英可访 |
| A3 | TASK-0018-B data API实施 | 数据 | token已active | `services/data/src/main.py` 支持回测所需bars查询 |
| A4 | TASK-0018-C-SUP 本地引擎补数据 | 回测 | A3完成+token已active | local_engine 通过 data API 获取真实K线执行回测 |

**并行规则：** A1⊥A2⊥(A3→A4)，即数据热修、开盘验证、回测数据接入三条线可并行

### Phase B — SimNow 生产闭环

**目标：** 模拟交易达到"可日常运行+风控有效+通知畅通"的生产标准

| 序号 | 任务 | Agent | 依赖 | 验收标准 |
|------|------|-------|------|---------|
| B1 | TASK-0014 风控通知链路 | 模拟交易 | Phase A | ✅ A1~A4全锁回 [修订 2026-04-10] |
| B2 | TASK-0009 严格风控验收 | 项目架构师 | B1完成 | ✅ 治理闭环 [2026-04-10] |
| B3 | TASK-0013 统一风控核心 | 项目架构师 | B2完成 | ✅ 治理闭环 [2026-04-10] |
| B4 | TASK-0010 骨架完善 | 模拟交易 | B3完成 | 前置已满足，待签发 |
| B5 | TASK-0019 收盘报表 | 模拟交易 | B4完成 | ✅ B1/B2 locked [修订 2026-04-10] |
| B6 | TASK-0022-B 只读日志 | 模拟交易 | B4完成 | pending_token |

**并行规则：** B1→B2→B3→B4，之后 B5⊥B6

### Phase B+ — 灾备演练质量门禁 [修订 2026-04-09]

**目标：** 验证已部署服务在真实故障场景下的韧性，确保告警及时、服务自愈、数据完整

| 序号 | 场景 | 验证 Agent | 验收标准 |
|------|------|-----------|----------|
| DR1 | Mini 断网（拔网线/防火墙模拟） | 数据+模拟交易 | 飞书 P1 告警 ≤ 30s；data/sim-trading 自动重连；bars API 重连后数据连续 |
| DR2 | Studio 宕机（docker stop 全容器） | 决策+看板 | 飞书 P0 告警 ≤ 30s；docker restart policy 自动恢复；决策看板自动重连 |
| DR3 | Docker 容器崩溃（kill -9 主进程） | 各 Agent | restart: unless-stopped 策略生效；服务 ≤ 60s 内恢复响应 |
| DR4 | 数据端采集中断+恢复 | 数据 | 恢复后自动补采缺失区间；health_check 不误报 |

**任务编号：** TASK-0036
**时机：** Phase B 完成后、Phase C 开始前
**前置条件：** Phase B 全部闭环

### Phase C — 决策端核心能力

**目标：** 决策端具备"策略研发→内部回测→审批→发布→模拟交易"完整链路

| 序号 | 任务 | Agent | 依赖 | 验收标准 |
|------|------|-------|------|---------|
| C1 | TASK-0021续批 真实data接入 | 决策 | Phase A完成 | FactorLoader通过data API获取真实K线 |
| C2 | TASK-0021续批 研发中心UI | 决策 | C1完成 | research-center 页面可发起研究任务 |
| C3 | TASK-0021续批 信号真闭环 | 决策 | C1完成 | 因子信号生成→审批→publish→sim-trading 全链路 |
| C4 | TASK-0025 SimNow备用方案 | 决策 | C3完成 | SimNow异常时自动切换仅平仓模式 |
| C5 | TASK-0012 legacy信号桥接 | 项目架构师 | C3完成 | J_BotQuant决策端信号可桥接到JBT sim-trading |
| C6 | TASK-0016 决策端正式接入 | 决策 | C5测试闭环 | JBT原生决策链路取代legacy桥接 |
| C7 | TASK-0037 PBO过拟合检验 | 决策 | C2完成（研发中心） | 决策端内置研究回测引擎支持CPCV多折验证；PBO Score输出到研究报告JSON；decision_web模型因子页显示PBO≤0.5绿/>0.5红。不依赖Air回测端。 [修订 2026-04-09] |

**并行规则：** C1→(C2⊥C3)→C4，C5⊥C4后置，C7依赖C2（研发中心基础） [修订 2026-04-09]

### Phase D — 数据端全量迁移

**目标：** Mini数据端从legacy cron完全迁移到JBT Docker体系。当前必须做 system 级迁移，因为真实 24h 运行链路仍在 legacy system 上；若不迁移，JBT data 仍无法成为正式运行承载面。 [修订 2026-04-10]

| 序号 | 任务 | Agent | 依赖 | 验收标准 |
|------|------|-------|------|---------|
| D1 | TASK-0027 全量采集迁移 | 数据 | Phase A完成 | 21个采集器全部Docker化；cron全部替换为scheduler |
| D2 | 通知统一 | 数据 | D1完成 | 飞书+邮件按JBT统一卡片标准 |
| D3 | data_web 临时看板 | 数据 | D1完成 | 6页（总览/采集器/数据浏览/新闻/硬件/配置） |
| D4 | 健康检查修正 | 数据 | D1完成 | stock/news判定不再误报 |

**并行规则：** D1→(D2⊥D3⊥D4)

### Phase E — 回测系统稳定化（人工回测收口）

**目标：** 回测从"首轮验证完成"进入"多策略泛用+正式报告导出"。Phase E 完成后 Air 人工回测进入**维护态**——只修 bug，不加功能。PBO/CPCV 等研究级验证归决策端内置研究回测引擎（Phase C）。 [修订 2026-04-09]

| 序号 | 任务 | Agent | 依赖 | 验收标准 |
|------|------|-------|------|---------|
| E1 | TASK-0008 泛化引擎 | 回测 | Phase A完成 | generic_strategy模板，新策略只加YAML |
| E2 | TASK-0026 新增因子 | 回测 | E1完成 | Spread/Spread_RSI注册并可回测 |
| E3 | TASK-0007-B 正式后端并回 | 回测 | E1完成 | 5文件API与前端对齐 |
| E4 | TASK-0007-C 前端8004收口 | 回测 | E3完成 | 前端不再依赖8004端口 |
| E5 | TASK-0005 容器命名 | 回测 | E4完成 | 命名统一为JBT-BACKTEST-* |

### Phase F — 看板聚合与云部署（最后完成）

**目标：** 在所有后端服务基本就绪后，纵观全局一次性部署统一运维面板；开放公网访问

> **看板端定位：** 看板是所有后端能力的只读聚合层，不产生业务数据。因此看板端排在最后完成——等 sim-trading/decision/data/backtest 四端 API 稳定后，看板一次性对接全部后端，避免反复返工。各服务容器内临时看板（*_web）跟随后端配套更新，不受此顺序约束。

> **[修订 2026-04-10] 除后端 API 稳定外，还需等待 sim-trading / decision / data 三端临时看板先基本收口；在此前，总看板不启动实施。**

| 序号 | 任务 | Agent | 依赖 | 验收标准 |
|------|------|-------|------|---------|
| F1 | TASK-0015 SimNow临时看板 | 看板 | Phase B基本完成 | dashboard聚合sim-trading只读数据 |
| F2 | 聚合看板（新任务） | 看板 | Phase B/C/D/E基本完成 | 6服务状态聚合显示，一次性部署 |
| F3 | TASK-0020 ECS部署 | 运维 | DNS+SSH就绪 | sim.jbotquant.com 可访问 |

### Phase G — 收口与legacy清退

**目标：** JBT 完全独立运行，legacy J_BotQuant 退役

| 序号 | 任务 | Agent | 依赖 | 验收标准 |
|------|------|-------|------|---------|
| G1 | TASK-0011 legacy清退 | 项目架构师 | Phase C/D完成 | Mini/Studio legacy进程全部停止 |
| G2 | 数据目录迁移 | 数据 | G1完成 | ~/J_BotQuant/BotQuan_Data → ~/jbt-data 完全切换 |
| G3 | cron/launchctl 清退 | 运维 | G1完成 | 无legacy定时任务残留 |

### Phase H — 实盘交易（最终阶段，延后启动）

**目标：** 启用真实交易能力

> **[修订 2026-04-10] 本阶段不进入当前执行窗口；仅在 sim-trading 连续稳定运行 2~3 个月后，由 Jay.S 再次确认是否启动。**

| 序号 | 任务 | Agent | 依赖 | 验收标准 |
|------|------|-------|------|---------|
| H1 | live-trading 契约复用 | 项目架构师 | Phase B(TASK-0013)完成 | shared/contracts/live-trading/ 落地 |
| H2 | live-trading 骨架 | 实盘交易 | H1完成 | src/ 基础结构对齐sim-trading |
| H3 | live-trading 网关 | 实盘交易 | H2完成 | 真实CTP前置连接 |
| H4 | live-trading 执行+风控+账本 | 实盘交易 | H3完成 | 下单→成交→风控→账本全链路 |
| H5 | live-trading 通知+看板 | 实盘交易 | H4完成 | 报警+报表+Web面板 |

> **[修订 2026-04-09] 实盘安全硬约束：** 任何策略从模拟交易转实盘，必须经过人工飞书确认按钮 Approve。AI 自动研发的策略额外要求：代码经 flake8+bandit 扫描通过 + 沙箱容器资源限制验证通过 + **决策端内置研究回测引擎** PBO Score ≤ 0.5（非 Air 人工回测）。三项缺一不可。

---

## 五、战略能力规划（Jay.S 七大构想）

以下为 Jay.S 提出的七项战略构想，对应到已有服务和未来能力扩展：

### 5.1 多策略按品种按时间桶并行

- **归属服务：** decision + backtest
- **前置条件：** TASK-0008(泛化引擎) + TASK-0021续批(策略仓库)
- **实施路径：** 决策端策略仓库管理多FC → 按品种+时间桶(5m/15m/30m/60m)分桶执行 → 每个桶独立进程 → 结果汇总
- **legacy资产可复用：** `J_BotQuant/scripts/unified_strategy_runner.py`（StrategyWorker线程模型）、`factor_live_trader.py`（--symbols/--group 品种分组）
- **实施阶段：** Phase C + Phase E

### 5.2 完整策略自动淘汰制度

- **归属服务：** decision
- **前置条件：** TASK-0021续批(策略生命周期完善)
- **实施路径：** 定时评估运行中策略绩效 → 触发淘汰规则(连亏/PnL/Sharpe/胜率) → 淘汰策略回退到"研发中心"重新优化 → 飞书通知
- **legacy资产可复用：** `J_BotQuant/scripts/strategy_retirement_check.py`（4规则+feishu报警+YAML移到retired/）
- **实施阶段：** Phase C（独立任务，建议 TASK-0032+）

### 5.3 研发中心开发

- **归属服务：** decision
- **前置条件：** Phase C(C1+C2)
- **实施路径：** research 模块完善 → optuna参数搜索 → shap因子解释 → onnx模型导出 → decision_web research-center 页面
- **现有资产：** `src/research/`（factor_loader/trainer/optuna_search/shap_audit/onnx_export）已有骨架
- **实施阶段：** Phase C

### 5.4 决策端封闭沙箱

- **归属服务：** decision
- **前置条件：** 研发中心基础完成
- **实施路径：** decision内部 sandbox 环境 → 策略在沙箱内训练/回测 → 不依赖外部backtest服务 → 数据通过data API获取不出沙箱 → 结果审批后才可发布
- **内置研究回测引擎：** [修订 2026-04-09] 沙箱内包含独立的研究回测引擎（非 Air 人工回测引擎的复制品）。该引擎面向 CPCV（组合净化交叉验证）统计验证，核心职责是判断"策略绩效是否为过拟合噪声"，而非"策略历史盈亏多少"。依赖 mlfinlab 的 `combinatorial_purged_cross_val` + `probability_of_backtest_overfitting`。输出物为 PBO Score + CPCV 报告，供研究中心 UI 展示和策略发布门禁检查。
- **与 Air 人工回测的分界：** Air 回测（backtest:8103）负责研究员手动发起的逐 bar 成交仿真，关注"策略在历史上赚了多少"；决策端研究回测关注"策略的绩效是否统计可靠"。两端引擎代码不共享，职责不交叉。
- **关键约束：** 策略进、策略出，数据不出沙箱边界
- **安全围栏（硬性验收条件）：** [修订 2026-04-09]
  1. **代码静态扫描**：AI 生成的代码必须经过 flake8 + bandit（安全扫描）才能进入沙箱执行，扫描不通过则拒绝入箱
  2. **资源硬限制**：沙箱容器必须在 docker-compose 中限制 CPU（≤2核）/ Memory（≤4GB）/ Network（禁止外网出站），防止死循环或网络风暴
  3. **人工最终审批**：即使 AI 全自动研发，策略从沙箱发布到模拟交易/实盘前必须经过人工 Approve（飞书确认按钮），无人工确认不得进入 `pending_execution` 状态
- **实施阶段：** Phase C 后续（独立任务，建议 TASK-0033+）

### 5.5 飞书/看板控制面

- **归属服务：** dashboard + decision
- **前置条件：** Phase F
- **实施路径：** dashboard聚合各服务 → 飞书机器人接收控制指令 → 策略启停/风控参数调整/定时任务管理 → 看板展示
- **实施阶段：** Phase F

### 5.6 本地模型集成（DeepSeek14b + Qwen7b coder）

- **归属服务：** decision（model router）
- **前置条件：** Phase C(研发中心)
- **实施路径：** DeepSeek14b 负责市场解读/策略评分/自然语言到策略转译 → Qwen7b coder 负责模板填充/规则改写/参数生成 → model_router 路由到对应模型
- **现有资产：** `src/model/router.py` 骨架已存在
- **实施阶段：** Phase C 后续（独立任务，建议 TASK-0034+）

### 5.7 数据端预读投喂决策端

- **归属服务：** data → decision
- **前置条件：** Phase D(数据全量迁移) + DeepSeek14b 已接入
- **实施路径：** data服务在非交易时段用DeepSeek14b预读K线/新闻/宏观 → 生成摘要JSON → decision在开盘前拉取摘要 → L1/L2快速预判，减少盘中计算延迟
- **实施阶段：** Phase D 后续（独立任务，建议 TASK-0035+）

---

## 六、Agent 衔接矩阵

### 6.1 模拟交易 Agent

**当前状态：** 3项已锁回，1项待开盘验证
**开工前必读：**
1. `WORKFLOW.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/模拟交易提示词.md`
4. `docs/tasks/TASK-0014-sim-trading-风控通知链路预审.md`
5. `docs/handoffs/` 中 sim-trading 相关交接单

**任务队列（按优先级）：**

```
┌─ TASK-0017  待开盘验证CTP        ← 等开盘窗口
├─ TASK-0014-A2  系统事件接线      ← 等Jay.S Token
├─ TASK-0009  严格风控验收          ← 等Jay.S Token
├─ TASK-0010  服务骨架完善          ← 依赖TASK-0013
├─ TASK-0019  收盘统计邮件          ← 等Jay.S确认时间窗
└─ TASK-0022-B  只读日志查看        ← 等Jay.S Token
```

**交接要点：**
- SimNow 凭证只通过 `.env` 运行时注入，绝不写入 Git
- Mini 是模拟交易主机(172.16.0.49:8101)，ECS 暂停
- 所有 API 调用只通过 Mini 蒲公英，不通过 ECS
- MD 24h 保活，TD 仅交易时段
- 风控规则必须从 guards.py emit_alert 走 dispatcher → feishu/email

### 6.2 决策 Agent

**当前状态：** H0~H4全锁回，契约9份完成
**开工前必读：**
1. `WORKFLOW.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/决策提示词.md`
4. `docs/tasks/TASK-0021-decision-旧决策域清洗升级迁移预审.md`
5. `docs/handoffs/TASK-0021-*` 系列交接单

**任务队列（按优先级）：**

```
┌─ TASK-0021续批 真实data接入      ← 依赖Phase A
├─ TASK-0021续批 研发中心UI        ← 依赖data接入
├─ TASK-0021续批 信号真闭环        ← 依赖data接入
├─ TASK-0025  SimNow备用方案        ← 依赖信号闭环
├─ TASK-0016  正式接入              ← 依赖C5测试闭环
├─ 策略淘汰制度（新任务）          ← 依赖策略仓库
├─ TASK-0037 PBO过拟合检验          ← 依赖C2(研发中心) [修订 2026-04-09]
├─ 封闭沙箱（新任务）              ← 依赖研发中心（含内置研究回测引擎）
└─ 本地模型集成（新任务）          ← 依赖沙箱
```

**交接要点：**
- 决策端不连回测端；内部回测通过 data API 获取 K 线，在 decision 内自行计算
- 策略仓库 8 态生命周期：imported → draft → backtesting → backtest_confirmed → pending_execution → sim_running → live_running → retired
- PublishGate 只放行 `backtest_confirmed → pending_execution` 和 `pending_execution retry`
- SimTradingAdapter POST 到 `http://{SIM_TRADING_SERVICE_URL}/api/v1/strategy/publish`
- research 模块已有 optuna/shap/onnx 骨架，待接入真实数据

### 6.3 数据 Agent

**当前状态：** Mini bars API运行中，通知B6修复完成
**开工前必读：**
1. `WORKFLOW.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/数据提示词.md`
4. `docs/tasks/TASK-0031-data端非夜盘热修与新闻推送恢复.md`
5. `docs/tasks/TASK-0027-data端全量采集体系迁移.md`

**任务队列（按优先级）：**

```
┌─ TASK-0031  非夜盘热修            ← 等Jay.S 6文件Token
├─ TASK-0018-B  bars API实施        ← token已active
├─ TASK-0027  全量Docker化迁移      ← 预审阶段
├─ 通知统一（新任务）               ← 依赖D1
├─ data_web 临时看板（新任务）      ← 依赖D1
├─ 健康检查修正（新任务）           ← 依赖D1
└─ 数据预读投喂（新任务）           ← 依赖本地模型
```

**交接要点：**
- Mini 是数据主机（172.16.0.49:8105），`~/jbt-data/` 为数据根目录
- 21 个采集器文件在 `src/collectors/`，涵盖 tqsdk/tushare/akshare/rss/news_api/macro/sentiment 等
- 当前 Mini 仍通过 legacy cron + `data_scheduler --daemon` 运行
- 全量迁移要求"无中断"：不得先停旧 cron 再补救
- 飞书 webhook 命名兼容：`FEISHU_NEWS_WEBHOOK_URL` → `FEISHU_INFO_WEBHOOK_URL`
- 35 个期货品种 + 260 symbols + 63 KQ连续合约

### 6.4 回测 Agent

**当前状态：** 75%阶段性结案，双引擎运行，批次B/C-SUP active
**开工前必读：**
1. `WORKFLOW.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/回测提示词.md`
4. `docs/tasks/TASK-0018-backtest-API化重建-Phase1.md`
5. `docs/tasks/TASK-0008-backtest-泛化正式引擎与正式报告导出预审.md`

**任务队列（按优先级）：**

```
┌─ TASK-0018-C-SUP  本地引擎补数据  ← token已active
├─ TASK-0008  泛化引擎+报告导出     ← 等Jay.S Token
├─ TASK-0026  新增因子(Spread/RSI)  ← 等Jay.S Token
├─ TASK-0007-B  正式后端并回        ← 等Jay.S Token
├─ TASK-0007-C  前端8004收口        ← 依赖B完成
└─ TASK-0005  容器命名统一          ← 低优先级
```

**交接要点：**
- 双引擎架构：tqsdk(在线) + local(离线)，由 engine_router 路由
- Air 通过 Tailscale 访问 Mini data API (100.82.139.52:8105)
- 本地通过蒲公英访问 Mini data API (172.16.0.49:8105)
- FC-224 策略已验证 total_trades=242，final_equity 可追溯
- 风控引擎 risk_engine.py 执行 max_drawdown + daily_loss_limit 双规则
- 结果 report.json 包含完整元数据（策略/品种/区间/资金/手续费/滑点/status）

### 6.5 看板 Agent

**当前状态：** 空目录，待启动
**开工前必读：**
1. `WORKFLOW.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/看板提示词.md`
4. `docs/tasks/TASK-0015-dashboard-SimNow-临时Next.js看板预审.md`

**任务队列：**

```
┌─ TASK-0015  SimNow临时看板        ← 等 sim-trading 临时看板链路再收口 + 白名单
└─ 聚合看板（新任务）               ← 等各服务临时看板基本收口 + Phase B/C/D/E基本完成后一次性启动
```

**交接要点：**
- 聚合看板(dashboard:8106)是最后完成的服务——纵观全局后一次性部署所有功能
- 各服务临时看板(*_web)跟随后端配套更新，看板Agent不负责
- 参考前端已在 `services/sim-trading/参考文件/V0-模拟交易端 0406/`
- 看板只做只读聚合，不得绕过 API 直接读服务内部数据
- 前端技术栈：Next.js 15 + React 19

### 6.6 实盘交易 Agent

**当前状态：** 空目录，待命
**开工前必读：**
1. `WORKFLOW.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/实盘交易提示词.md`

**任务队列：**

```
等待 sim-trading 连续稳定运行 2~3 个月 + Phase B(TASK-0013 统一风控核心) 完成 + Jay.S 再确认后启动
```

**交接要点：**
- 与 sim-trading 共用风控核心，不共用账本和配置
- 契约可复用 sim-trading 范式，但以 `shared/contracts/live-trading/` 独立维护
- 真实 CTP 前置地址与 SimNow 不同，需独立配置
- 部署在 Studio，不在 Mini

### 6.7 项目架构师

**当前状态：** 全局治理 + 预审为主
**职责范围：**

```
┌─ TASK-0013  统一风控核心设计      ← 跨 sim/live 服务
├─ TASK-0012  legacy信号桥接        ← 跨 integrations
├─ TASK-0011  legacy清退            ← 跨服务清退
├─ TASK-0036 灾备演练设计+验收      ← Phase B完成后 [修订 2026-04-09]
├─ Phase H1  live-trading 契约      ← shared/contracts
├─ 所有新任务预审                   ← 持续
└─ 公共项目提示词维护               ← 持续
```

---

## 七、总进度仪表盘

| 模块 | 完成 | 目标 | 当前Phase | 下一里程碑 |
|------|------|------|----------|-----------|
| 治理 | 100% | 100% | ✅ 完成 | 维护 |
| sim-trading | 27% | 100% | Phase A→B | 开盘验证通过 + 期货公式接通 |
| decision | 10% | 100% | Phase A→C | data API真实接入 |
| data | 5% | 100% | Phase A→D | 热修完成+Docker化 |
| backtest | 75% | 100% | Phase A→E | 本地引擎补真实数据 |
| dashboard | 5% | 100% | Phase F | 待各服务临时看板基本收口 |
| live-trading | 0% | 100% | Phase H | 待 sim-trading 稳定运行 2~3 个月 |
| **总体** | **~30%** | **100%** | **Phase A** | **基础稳定化** |

---

## 八、Token 签发待办清单（按紧急度排序）

以下为当前所有处于 `pending_token` 状态需 Jay.S 签发的批次：

| 优先级 | 任务 | 文件数 | Agent | 白名单概要 |
|--------|------|--------|-------|-----------|
| 🔴 P1紧急 | TASK-0031 | 6 | 数据 | data_scheduler/health_check/dispatcher/news_pusher + 2 tests |
| 🟡 P1 | TASK-0014-A2 | 2 | 模拟交易 | router.py + main.py (系统事件接线) |
| 🟡 P1 | TASK-0009 | TBD | 模拟交易 | guards/risk相关 (风控规则引擎) |
| 🟡 P1 | TASK-0019 | ~5 | 模拟交易 | main.py/email.py/ledger/service.py + tests |
| ✅ P1 | TASK-0008 | ~12 | 回测 | A/B/C/D四批全锁回 [2026-04-10] |
| ✅ P1 | TASK-0026 | TBD | 回测 | A/B/C三批全locked_back [2026-04-10] |
| ✅ P1 | TASK-0007-B | 5 | 回测 | 正式后端API并回 locked [2026-04-10] |
| ✅ P1 | TASK-0007-C | 2 | 回测 | 前端8004收口 locked [2026-04-10] |
| 🟢 P2 | TASK-0022-B | 4 | 模拟交易 | main.py/router.py/intelligence/page.tsx + test |
| ✅ P2 | TASK-0005 | 1 | 回测 | docker-compose.yml locked [2026-04-10] |
| ✅ P2 | TASK-0013 | N/A | 架构师 | 纯治理闭环(无代码Token) [2026-04-10] |
| 🟢 P2 | TASK-0036 | TBD | 架构师 | 灾备演练场景脚本(待Phase B) [修订 2026-04-09] |
| 🟢 P2 | TASK-0037 | TBD | 决策 | PBO检验+CPCV+mlfinlab(决策端内置，待Phase C) [修订 2026-04-09] |

---

## 九、关键依赖链（冻结）

```
TASK-0031(data热修) ─────────────────────────────────┐
TASK-0017(开盘验证) ─────────────────────────────────┤
TASK-0018-B/C-SUP(回测数据) ─────────────────────────┤
                                                      ├── Phase A 完成
TASK-0014-A2(事件接线) ──┐                            │
TASK-0009(风控验收) ─────┤                            │
TASK-0013(统一风控) ─────┤── Phase B 完成 ────────────┤
TASK-0010(SimNow骨架) ──┤                            │
TASK-0019(报表) ─────────┘                            │
                                                      │
TASK-0036(灾备演练) ──────── Phase B+ 质量门禁 ──────┤  [修订 2026-04-09]
                                                      │
TASK-0021续(data接入) ──┐                             │
TASK-0021续(研发中心) ──┤── Phase C 完成 ────────────┤
TASK-0021续(信号闭环) ──┤                            │
TASK-0037(PBO·决策内置) ┤  [修订 2026-04-09]         │
TASK-0012(桥接) ────────┤                            │
TASK-0016(正式接入) ────┘                            │
                                                      │
TASK-0027(data迁移) ────┐                            │
通知统一 ───────────────┤── Phase D 完成 ────────────┤
data_web ───────────────┘                            │
                                                      │
TASK-0008(泛化引擎) ────┐                            │
TASK-0026(新增因子) ────┤── Phase E 完成            │
TASK-0007-B/C(并回) ────┘                            │
                                                      │
TASK-0015(临时看板) ────┐                            │
聚合看板 ───────────────┤── Phase F 完成            │
TASK-0020(ECS) ─────────┘                            │
                                                      │
TASK-0011(legacy清退) ──── Phase G 完成              │
                                                      │
live-trading 全线 ──────── Phase H 完成 ← 依赖B+C   │
                                                      │
战略规划(多策略/淘汰/沙箱+安全围栏/模型/预读) ←── 依赖C+D │
```

---

## 十、完成定义（项目收口标准）

当以下条件全部满足时，JBT 项目视为完成收口：

1. **6 个服务全部可独立启动、构建、部署**
2. **6 个服务全部有完整契约在 `shared/contracts/`**
3. **Mini/Studio/Air 三端全部通过 docker-compose.dev.yml 部署**
4. **legacy J_BotQuant 全部进程停止，无 cron/launchctl 残留**
5. **决策→模拟交易→实盘交易 信号链路完整闭环**
6. **数据端 24h 采集无中断**
7. **看板聚合 6 服务状态**
8. **飞书+邮件通知按统一卡片标准输出**
9. **风控规则在 sim/live 双端统一执行**
10. **所有治理账本（task/review/lock/handoff）完整闭环**

---

【签名】Atlas
【时间】2026-04-09
【设备】MacBook
