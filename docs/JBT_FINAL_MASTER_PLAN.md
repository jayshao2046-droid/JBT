# JBT 终局总计划 — 全服务归属 · 任务分配 · 开发进度

【签名】Atlas
【时间】2026-04-09
【设备】MacBook
【状态】正式发布

> 本文件为 JBT 多服务工作区的最终收口计划。所有 Agent 在开始工作前必须读取本文件，确认自己的任务队列和衔接入口。

---

## 📊 实时进度总览 [修订 2026-04-15]

| 服务 | 进度 | 状态 | 当前焦点 |
|------|------|------|---------|
| data | `████████████` **100%** | ✅ 生产运行中 | Round 1 收口完成；TASK-0104-D1 预读系统已部署；**TASK-0113 研究员子系统已完成（87/87测试通过，4 Token 全部锁回，Alienware qwen3:14b 部署运行中）** |
| backtest | `████████████` **100%** | ✅ 生产运行中 | Round 2 安全加固完成，维护态 |
| sim-trading | `████████████` **95%** | ✅ Alienware 裸 Python 运行中 | TASK-0107 迁移完成；schtasks 开盘/收盘自动调度已建立；待正式交易日 CTP 验证 |
| decision | `████████████` **100%** | ✅ Phase C + 精进改造全闭环 | TASK-0112(A/B/C)+0114+0115+0116+0117 全部完成并锁回；359 passed / 7 skipped；decision 进入维护态 |
| dashboard | `████████████` **100%** | ✅ Phase F 闭环 | TASK-0106 全部完成；.env.local 已配置 Alienware 代理；Studio 已同步 |
| live-trading | `░░░░░░░░░░░░` **0%** | ⏳ 后置 | 等待sim稳定运行2~3月后评估 |
| **整体** | `████████████` **~99%** | **Phase C+D+F 全闭环** | **TASK-0104/0107/0108 全部 locked；两地已同步；D1 今晚自动生效，D2 待 Studio 重启** |

> **更新规则：** 每次 Atlas 更新治理文件时同步刷新本表格和百分比。

---

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

### 设备拓扑（冻结）[修订 2026-04-15]

> **[修订 2026-04-14] 运行态四设备架构正式冻结为 Mini / Studio / Alienware / Air；MacBook 仅保留开发/控制，不计入运行态四设备。**

| 设备 | 角色 | IP（内网） | IP（蒲公英） | 部署服务 |
|------|------|-----------|-------------|---------|
| MacBook | 开发/控制 | localhost | 172.16.3.136 | 全部开发环境 |
| Mini | 纯数据采集 | 192.168.31.76 | 172.16.0.49 | data:8105 |
| Air | 回测生产 | 192.168.31.245 | — | backtest:8103, backtest-web:3001 |
| Studio | 决策/开发主控 | 192.168.31.142 | 172.16.1.130 | decision:8104, decision-web:3003, dashboard:8106 |
| Alienware | 交易执行+情报研究员节点 | 192.168.31.224 | — | sim-trading:8101、Windows 官方交易软件（24h）、qwen3:14b |
| ~~ECS~~ | ❌ 已永久停用 | 47.103.36.144 | — | [修订 2026-04-12] ECS永久停用，全部ECS相关任务取消 |

> **[修订 2026-04-15] TASK-0107 完成：** sim-trading API 已正式迁移至 Alienware（192.168.31.224:8101），验证通过（`curl /health` → 200，42 个端点可用）。Mini 不再承载 sim-trading，仅保留纯数据采集（data:8105）。本次迁移为裸 Python 部署；Docker 化部署待 BIOS 虚拟化开启后另行完成，不阻塞当前口径。

### 端口分配（冻结）

| 服务 | API端口 | Web端口 | 归属设备 |
|------|---------|---------|---------|
| sim-trading | 8101 | 3002 | Alienware |
| live-trading | 8102 | 3006 | Studio（后置） |
| backtest | 8103 | 3001 | Air |
| decision | 8104 | 3003 | Studio |
| data | 8105 | 3004 | Mini |
| dashboard | 8106 | 3005 | Studio |

---

## 二、服务状态与归属矩阵

### 2.1 模拟交易 sim-trading — 90% [修订 2026-04-12 SG API认证+二次核验通过]

**负责 Agent：模拟交易**
**服务目录：`services/sim-trading/`**
**契约目录：`shared/contracts/sim-trading/`（5份已锁回）**

| 模块 | 状态 | 说明 |
|------|------|------|
| CTP/SimNow 网关 | ✅ 已部署 | `src/gateway/simnow.py`，Mini 容器运行中 |
| API 路由 | ✅ 已完成 | `src/api/router.py`，28 个端点，含 API Key 认证、密码脱敏 |
| 期货公司接通 | ✅ 已完成 | 光大期货 CTP 已接通；MD/TD 基础链路可用，策略执行链仍待 decision Phase C 真闭环 |
| 风控守卫 | ✅ 已完成 | `src/risk/guards.py`，reduce_only + disaster_stop 真实实现，测试覆盖 |
| 交易执行 | ✅ 已完成 | `src/execution/service.py`，ExecutionService 真实委托 Gateway，已激活接入路由 |
| 账本 | ✅ 已完成 | `src/ledger/service.py`，record_trade 真实委托 add_trade，线程安全 |
| 通知 | ✅ 已完成 | dispatcher/guards 已接线，系统事件告警通道可用 |
| 发布接口 | ✅ 已锁回 | TASK-0023-A，`POST /api/v1/strategy/publish` |
| 安全加固 | ✅ 2026-04-12 | 9 项安全问题全部修复：API Key 认证、密码脱敏、并发锁、内存泄漏等 |
| 版本 | ✅ 1.0.0 | main.py 版本号已更新，/status stage 字段已修正 |
| 容灾交接接口 | ✅ 已完成 | `CS1-S` TASK-0077 commit 8afc8f5，接收 decision 本地 Sim / future live failover 的任务交接与账本同步 [2026-04-13] |
| 运行态收口 | 🔶 A批完成 | TASK-0022-A locked；B批日志查看 pending |
| Docker/Mini | ✅ 已部署 | TASK-0017-A3，待开盘验证CTP |
| 临时看板 | ✅ 基本可用 | `sim-trading_web/`，operations+intelligence 页面 |

**已完成任务：** TASK-0002(契约), TASK-0009(治理闭环), TASK-0010(骨架闭环), TASK-0013(治理闭环), TASK-0014(A1~A4全锁回), TASK-0017-A3, TASK-0019(B1/B2锁回), TASK-0022(A/B全锁回), TASK-0023-A, TASK-0041(A/B/C locked), TASK-0042(自动重连+状态同步 locked), TASK-0043(data_scheduler LaunchAgent守护 locked), TASK-0067(SG API认证+旧auth清理 locked), TASK-0077(CS1-S容灾交接接口 locked), TASK-0107(Alienware迁移 locked) [修订 2026-04-15]
**Phase B 状态：✅ 全闭环** [修订 2026-04-10]
**当前活跃：** TASK-0017(待开盘验证CTP — Alienware 裸 Python 运行中，schtasks 定时启停已建立)
**DR3 修复：** ✅ ISSUE-DR3-001 已由 TASK-0045 watchdog LaunchAgent 闭环 [2026-04-11]
**排队任务：** Phase H 前置容灾复用（CS1-S 已完成，CA6 已完成）

> **[修订 2026-04-15] sim-trading 已从 Mini Docker 迁移至 Alienware 裸 Python 部署（TASK-0107 locked）。schtasks 六组定时任务（早/午/夜开停）已建立。dashboard .env.local 代理已指向 Alienware:8101。仍未接通期货公式/策略公式执行链路。**

### 2.2 决策 decision — 100% [修订 2026-04-15 全任务闭环]

**负责 Agent：决策**
**服务目录：`services/decision/`**
**契约目录：`shared/contracts/decision/`（9份已锁回）**

| 模块 | 状态 | 说明 |
|------|------|------|
| API 骨架 | ✅ 已完成 | `src/api/routes/`（strategy/signal/model） |
| 策略仓库 | ✅ 已完成 | `src/strategy/repository.py`，8态生命周期完整；后续补 `manual_backtest_confirmed` 审核门槛 |
| 策略发布 | ✅ 已完成 | `src/publish/`（gate+sim_adapter+executor），H4闭环 |
| 研究中心骨架 | ✅ 已完成 | `src/research/`（factor_loader/trainer/optuna/shap/onnx）已投产为 Phase C 基线 |
| 期货沙箱回测 | ✅ 已完成 | `CA2'` TASK-0056 sandbox_engine.py 投产 [2026-04-12] |
| 股票沙箱回测 | ✅ 已完成 | `CB2'` TASK-0057 sandbox_engine.py T+1/涨跌停扩展 [2026-04-12] |
| 策略调优引擎 | ✅ 已完成 | `CA4` TASK-0061 trade_optimizer 网格搜索投产 [2026-04-12] |
| 导入通道 | ✅ 已完成 | `C0-3` TASK-0051 strategy_importer + `CF2` TASK-0063 邮件+看板YAML导入投产 [2026-04-12] |
| 股票研究中心 | ✅ 全闭环 | CB1~CB9全链路+CA7 PBO检验投产 (TASK-0069~0075)，200测试通过 [2026-04-13] |
| 本地 Sim 容灾 | ✅ 已完成 | `CS1` TASK-0076 LocalSimEngine commit 3c8be69，12测试通过 [2026-04-13] |
| LLM Pipeline | ✅ 已完成 | `CF1'` TASK-0083 LLM集成+研究中心auto_backtest, Atlas复核通过 [2026-04-13] |
| 因子同步 | ✅ 已完成 | `CK1~CK3` TASK-0084 双地同步+覆盖率+缺失通知，Claude执行+Atlas审核通过 [2026-04-13] |
| LLM 上下文注入 | ✅ 已完成 | `D2` TASK-0104-D2 context_loader TTL=8h + pipeline 三方法注入，commit d356511 [2026-04-15] |
| 模型路由 | 🔶 资格验证 | `src/model/router.py`，版本对齐+因子HASH校验，无实际推理加载（P2） |
| 门控（L1/L2/L3） | ✅ 已完成 | TASK-0112-A/B/C：phi4-reasoning L1(5日日线)/L2(20日+60分钟线+研报) 口径修正，gate_reviewer/context_loader 新建，full_pipeline() Optuna+SandboxEngine 串联，8+9+19=36测试通过 [2026-04-15 locked] |
| 持久化 | ✅ 已完成 | `src/persistence/`（FileStateStore） |
| 通知 | ✅ 已完成 | `src/notifier/`（飞书+邮件双通道投产，6级通知，JBT统一颜色） |
| 报告 | ✅ 基线完成 | `src/reporting/`（daily+research_summary投产）；后续补回测/荐股/盘后评估报告 |
| 临时看板 | ✅ 已扩容 | `decision_web/` 7+3+3 页面：股票池/盘中信号/期货研究面板+审批管理/研究报告/因子分析已上线 (TASK-0074+TASK-0079) [2026-04-14] |
| Dockerfile | ✅ 已修复 | TASK-0021-H0 |
| 测试 | ✅ 359用例 | `tests/` 全量通过 [修订 2026-04-15] |
| **35品种模型注册表** | ✅ 已完成 | TASK-0114：ModelRegistry 按品种×行情类型(5种：trend/oscillation/high_vol/compression/event_driven)存储 XGBClassifier，RegimeDetector 调 phi4 检测行情类型，trainer.py 品种级增量训练+真实 Sharpe，12测试通过 [2026-04-15 locked] |
| **信号失真监控（G8）** | ✅ 已完成 | TASK-0115：SignalValidator IC签名方向修正+30日滚动准确率监控；FactorMonitor IC衰减+分布漂移+零方差保护，14测试通过 [2026-04-15 locked] |
| **因子挖掘自动化** | ✅ 已完成 | TASK-0116：FactorMiner 四类因子(momentum/mean_reversion/vol_price/volatility)；FactorValidator IC_IR+t检验+多空收益；factor.py API路由(mine/validate/list)，26测试通过 [2026-04-15 locked] |
| **研究中心5项拓展** | ✅ 已完成 | TASK-0117：①spread_monitor Z-score 套利+空序列保护；②correlation_monitor 35品种相关矩阵偏离检测；③news_scorer deepcoder 评分+飞书推送；④spread_monitor/news_scorer/correlation_monitor 全测试覆盖，18测试通过 [2026-04-15 locked] |

**已完成任务：** TASK-0021(A契约+H0~H7全批次锁回), TASK-0024(部署审查), TASK-0050(C0-1), TASK-0051(C0-3), TASK-0052(CG1), TASK-0053(C0-2), TASK-0054(CB5), TASK-0055(CG2), TASK-0056(CA2'), TASK-0057(CB2'), TASK-0058(CG3), TASK-0059(CA6), TASK-0060(CA3), TASK-0061(CA4), TASK-0062(CB3), TASK-0063(CF2), TASK-0069(CB1), TASK-0070(CB4), TASK-0071(CB6), TASK-0072(CB7), TASK-0073(CB8), TASK-0074(CB9+CA1+CA5前端), TASK-0075(CA7), TASK-0076(CS1+路由注册), TASK-0079(看板3页扩容+Navbar), TASK-0080(Phase C全闭环审核), TASK-0083(LLM Pipeline+Factor Sync+Bug Fix Atlas复核通过), TASK-0084(CK2/CK3因子双地同步+缺失通知), TASK-0025(SimNow备用方案-仅平仓), TASK-0104-D2(LLM上下文注入 locked), TASK-0112(A/B/C三批门控精进 locked), TASK-0114(35品种模型注册表 locked), TASK-0115(信号失真+因子漂移 locked), TASK-0116(因子挖掘自动化 locked), TASK-0117(研究中心5项拓展 locked) [修订 2026-04-15]  
**剩余缺口：** 无（全部闭环，进入维护态）  
**当前活跃：** 无（全部 locked）[修订 2026-04-15]

### 2.3 数据 data — 100% [修订 2026-04-12 Round 1 收口完成]

**负责 Agent：数据**
**服务目录：`services/data/`**

| 模块 | 状态 | 说明 |
|------|------|------|
| 最小 bars API | ✅ 已完成 | `src/main.py`（health/version/symbols/bars） |
| 期货供数 | ✅ 已完成 | continuous/exact symbol + bars API 已投产 |
| 股票日线采集 | ✅ 已有能力 | `tushare_full_collector` / `akshare_backup` 已具备全 A 股日线采集能力 |
| 股票分钟K采集器 | ✅ 已完成 | `stock_minute_collector.py` 已支持 watchlist 动态模式 (TASK-0054) [2026-04-12] |
| 股票 bars API 路由 | ✅ 已完成 | `C0-1` TASK-0050 stock_bars 路由投产 [修订 2026-04-12] |
| 动态 watchlist 采集 | ✅ 已完成 | `CB5` TASK-0054 watchlist_client + pipeline + strategy.py watchlist 端点投产 [2026-04-12] |
| 采集器 | ✅ 已部署(legacy) | `src/collectors/`（21个采集器文件），Mini 通过 cron 运行 |
| 调度器 | ✅ 已部署(legacy) | `src/scheduler/data_scheduler.py`，Mini 以 --daemon / LaunchAgent 运行 |
| 健康检查 | ✅ 已修复 | `src/health/health_check.py`，FeishuNotifier 死代码已清理（TASK-0064）[2026-04-12] |
| 通知 | ✅ 已完成 | TASK-0028-B6 + TASK-0064 新增 FACTOR/WATCHLIST 通知类型及路由 [2026-04-12] |
| 新闻推送 | ✅ 已恢复 | `src/notify/news_pusher.py` 批量推送链路可用 |
| data_web | ✅ 基线完成 | 6 页临时看板已锁回，继续保持只读配套 |
| Docker化 | ✅ 基线完成 | Mini 容器运行中(JBT-DATA-8105)，system 迁移主线已闭环 |
| 存储 | ✅ 已完成 | `src/data/storage.py`，Mini `~/jbt-data/` 目录体系 |
| **研究员子系统** | ✅ 已部署运行 | TASK-0113：Alienware qwen3:14b + 飞书三类分流(blue/orange/red) + 11整点调度 + 国际7源 + 邮件日报 + Mini API 推送；87/87测试通过，4 Token 全部锁回；HTTP :8199 控制端口；last_run_ok=true [2026-04-15] |

**已完成任务：** TASK-0018(A~F全锁回), TASK-0027(A0~A7全锁回), TASK-0028(B1~B6全锁回), TASK-0031(锁回), TASK-0032/0033(锁回), TASK-0050(C0-1), TASK-0054(CB5), TASK-0064(Round 1 收口+SG) [修订 2026-04-12]
**已完成：** TASK-0113 数据研究员子系统（4批：A通知规范化 + B调度 + C国际爬虫 + D测试，共87/87测试通过）[完成 2026-04-15]
**Mini 股票 API 修复（U0 直修 2026-04-15）：** `_load_stock_frame` 路径修复为 `{root}/{code}/stock_minute/`；`_normalize_bar_frame` 增加 payload 展开（股票采集格式）；补 `open_interest=0`；验证：000001 返回 1329 条，期货 rb 主力 1605 条不受影响。
**Round 1 改动：** A2 STUB清除→延迟注入、因子通知器/SLA追踪器实现、健康检查修复、FACTOR/WATCHLIST通知路由、DATA_API_KEY认证中间件、11个测试扩充（77个测试全通过）[2026-04-12]

> **[修订 2026-04-11] data 端当前新增的 Phase C 职责不是重启 system 级迁移，而是在既有供数基线之上补足股票 bars 路由与动态 watchlist 分钟 K 采集。`stock_minute_collector` 与股票日线采集器已存在，当前主要缺口在路由层与调度模式切换。**

### 2.4 回测 backtest — 100% [修订 2026-04-12 Round 2 全部通过，Pow修复已合入]

**负责 Agent：回测**
**服务目录：`services/backtest/`**
**契约目录：`shared/contracts/backtest/`（4份已锁回）**

| 模块 | 状态 | 说明 |
|------|------|------|
| 在线引擎 | ✅ 已完成 | TqApi+TqSim+TqBacktest+TqAuth |
| 本地引擎 | ✅ 已完成 | `src/backtest/local_engine.py`，双引擎路由 |
| 风控引擎 | ✅ 已完成 | `src/backtest/risk_engine.py`，max_drawdown+daily_loss 双规则 |
| 因子注册 | ✅ 基线完成 | `src/backtest/factor_registry.py` 当前已覆盖基础技术因子；后续接入共享因子双地同步 |
| FC-224策略 | ✅ 已完成 | `src/backtest/fc_224_strategy.py`，total_trades=242 |
| 结果构建 | ✅ 已完成 | `src/backtest/result_builder.py` |
| 引擎选择器 | ✅ 已完成 | 前端+后端双路径 |
| 手动期货回测 | ✅ 基线完成 | Air 现网可用，继续承担人工最终复核 |
| 手动股票回测 | ✅ 已完成 | `CG3` TASK-0058 stock_runner + stock_approval T+1/涨跌停投产 [2026-04-12] |
| 策略导入审核 | ✅ 已完成 | `CG1` TASK-0052 strategy_queue + `CG2` TASK-0055 manual_runner + approval 投产 [2026-04-12] |
| 审核看板 | ✅ 已完成 | `backtest_web` manual review / stock review 页面已上线, TASK-0078 commit 9f1d9fb [2026-04-13] |
| 看板两页 | ✅ 基线完成 | agent-network + operations，后续扩容为人工审核入口 |
| 泛化引擎 | ✅ 已完成 | TASK-0008 A/B/C/D 四批全锁回 [修订 2026-04-10] |
| 新增因子 | ✅ 已完成 | TASK-0026 A/B/C 三批全 locked_back [修订 2026-04-10] |
| 8004并回 | ✅ 已完成 | TASK-0007 A/B/C/D 全锁回 [修订 2026-04-10] |
| 容器命名 | ✅ 已完成 | TASK-0005 JBT-BACKTEST-8103/3001 [修订 2026-04-10] |

**已完成任务：** TASK-0003(全锁回), TASK-0004(锁回), TASK-0005(锁回), TASK-0007(A/B/C/D全锁回), TASK-0008(A/B/C/D全锁回), TASK-0018(A/C/D/E锁回), TASK-0026(A/B/C全锁回), TASK-0052(CG1), TASK-0055(CG2), TASK-0058(CG3), TASK-0065(Round 2 F-001+API认证), TASK-0078(审核看板页面扩容 locked) [修订 2026-04-14]
**Phase E 状态：基线闭环 + CG 扩容已闭环 + 审核看板已上线 + Round 2 安全加固全部通过（F-001 eval三重限制+Pow非常量拒绝+BACKTEST_API_KEY认证）** [修订 2026-04-14]
**httpx 依赖修复：** requirements.txt 新增 `httpx>=0.27.0,<1.0.0`（U0 hotfix, commit 265344c）[2026-04-14]
**Air 同步状态：** ✅ rsync 同步 + 容器重启 + 远端验证通过 [2026-04-10]
**排队任务：** CK2/CK3 因子双地同步协同 + P3 Pow边界测试补充 [修订 2026-04-14]
**Studio 容器状态：** ✅ JBT-BACKTEST-8103 + JBT-BACKTEST-WEB-3001 健康运行中 [2026-04-14]

> **[修订 2026-04-11] 双回测分离原则：** decision 内部自动研究回测固定拆为“期货沙箱 / 股票沙箱”两条主路径，数据完全隔离、只共享因子；Air/backtest 继续承担人工手动回测与最终二次审核，不接管研究中心自动回测流程。

### 2.5 看板 dashboard — 98% [修订 2026-04-14 Phase F 全闭环]

**负责 Agent：Claude（看板实施）+ Atlas（逐任务审核）**
**服务目录：`services/dashboard/`**
**Web 目录：`services/dashboard/dashboard_web/`**
**部署设备：Studio (192.168.31.142)**
**端口：API 8106 / Web 3005**

| 模块 | 状态 | 说明 |
|------|------|------|
| Dockerfile | ✅ 存在 | 基础骨架 |
| .env.example | ✅ 存在 | 基础配置 |
| dashboard_web | ✅ Next.js 15.2.6 | 统一聚合看板前端框架，TypeScript strict + shadcn/ui + Tailwind |
| 登录页 | ✅ 已完成 | /login，基础认证 |
| 总览首页 | ✅ 已完成 | /，KPI+持仓+信号+风控+新闻，对接 sim-trading 真实 API |
| 总配置页 | ✅ 已完成 | /settings |
| API 代理层 | ✅ 已完成 | next.config.ts 环境变量化，sim-trading/data→Mini(.76)，decision/backtest→Studio localhost |
| sim-trading 子页面 | ✅ 已完成 | /sim-trading（总览/交易终端/行情/风控/品种风控/CTP配置），7路由+11组件+6基础设施 |
| backtest 子页面 | ✅ 已完成 | /backtest（总览/结果/审查/优化器/运营），6路由+14组件+3 API/hooks |
| decision 子页面 | ✅ 已完成 | /decision（总览/信号/研究/仓库/模型/报告），6路由+12组件 |
| data 子页面 | ✅ 已完成 | /data（总览/采集器/数据探索/新闻/系统），5路由+10组件 |
| Studio 生产部署 | ✅ 已部署 | pnpm build 28/28 ✅，Next.js 运行于 :3005，4端 API proxy 全通 |
| 功能强化 | ✅ 已完成 | TASK-0106：全端 API 路由对齐+strategy-import YAML 导入修复+optimizer 注释，pnpm 28/28 [2026-04-15]|

**已完成任务 [修订 2026-04-14]：**
- ✅ TASK-0099：统一看板首页框架（47 files，commit bee35c9，tok-3e1c1970 locked）
- ✅ TASK-0100：sim-trading 全功能升级（24 files，commit 4969642，tok-279d4f99 locked）
- ✅ TASK-0101：backtest 全功能升级（40 files，commit af0981c，tok-92f7dce9 locked）
- ✅ TASK-0102：decision 全功能升级（45 files，架构 MainLayout 提升，commit 2ff4cda，tok-1f25eea1 locked）
- ✅ TASK-0103：data 全功能升级（24 files，commit 65b5f40，tok-bcdd740a locked）
- ✅ TASK-F5：sidebar 补全 + Studio 部署（1 file，commit 463bb0c，tok-16dffac3 locked）
- ✅ TASK-0105：next.config.ts 环境变量化（commit 66a1b2f，tok-642d8752 locked）

**当前活跃：**
- 🟡 TASK-0106：全端功能强化（API 对齐检查、显示完整性修复、空状态处理、API 路由对齐）

**TASK-0106 子任务清单 [修订 2026-04-15]：**

| 子任务 | 内容 | 文件 | 状态 |
|-------|------|------|------|
| A | decision/backtest API路由对齐+兼容层 | decision.ts/backtest.ts/evening-rotation-plan.tsx/hooks | ✅ commit a741ed3 |
| B | strategy-import.tsx 全量重写（YAML导入表单，调 `/api/v1/import/dashboard`） | strategy-import.tsx | ✅ commit 4ec5b6a |
| C | optimizer-panel.tsx 路径注释清理，确认路由正确 | optimizer-panel.tsx | ✅ commit 28b3227 |
| D | pnpm build 28/28 验证 + ATLAS_PROMPT/总计划更新 + TASK-0106 lockback | ATLAS_PROMPT.md + 本文件 | ✅ 完成（本次 commit）|
| E | git push → origin/main + Studio SSH 同步 + 容器重启验证 | — | ⏳ 待 Jay.S 确认 |

> **[修订 2026-04-15] TASK-0106 B~D 全部完成，dashboard 100% 收口，Phase F 正式闭环。pnpm build 28/28 ✅。剩余 TASK-0106-E（push+Studio同步）待 Jay.S 确认后执行。token: tok-49b26cc4（lockback 后归档）**

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

## 三、全量任务登记表（TASK-0001 ~ TASK-0049）

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

### 3.2 当前活跃/待执行 [修订 2026-04-12]

| 任务编号 | 名称 | 服务 | Agent | 状态 | 优先级 |
|---------|------|------|-------|------|--------|
| TASK-0031 | data非夜盘热修 | data | 数据 | ✅ locked [2026-04-09] | P1 紧急 |
| TASK-0018 | backtest 数据API全批次 | data+backtest | 数据+回测 | ✅ A~F全locked [2026-04-10] | P1 |
| TASK-0017 | Mini开盘验证 | sim-trading | 模拟交易 | ✅ A1-A4全locked [2026-04-10] | P1 |
| TASK-0014 | 风控通知链路 | sim-trading | 模拟交易 | ✅ A1-A4全locked | P1 |
| TASK-0019 | 收盘统计邮件 | sim-trading | 模拟交易 | ✅ 整体闭环 [2026-04-10] B0确认不需要 | P1 |
| TASK-0022-B | 只读日志查看 | sim-trading | 模拟交易 | ✅ locked [2026-04-10] | P2 |
| TASK-0009 | 严格风控验收 | sim-trading | 模拟交易 | ✅ 治理闭环 [2026-04-10] | P1 |
| TASK-0013 | 统一风控核心 | sim-trading+live | 项目架构师 | ✅ 治理闭环 [2026-04-10] | P1 |
| TASK-0010 | 服务骨架完善 | sim-trading | 模拟交易 | ✅ 闭环 [2026-04-10] | P1 |
| TASK-0041 | CTP前端下单与密码脱敏 | sim-trading | 模拟交易 | ✅ A/B/C全locked [2026-04-10] | P1/P0 |
| TASK-0042 | CTP自动重连与状态同步 | sim-trading | 模拟交易 | ✅ locked [2026-04-11] | P1 |
| TASK-0021 | 决策端迁移 | decision | 决策 | ✅ A+H0~H7全locked [2026-04-10] | P1 |
| TASK-0048 | Phase C扩展与总计划修订 | 治理 | Atlas | A0/A1已完成；A2 prompt同步已完成 [2026-04-11] | P1 |
| TASK-0049 | 全项目安全检查纳入总计划与统一修复预审 | 治理 | Atlas | A0已完成；A1总计划/Atlas状态已同步；当前冻结 SG1→SG5，先检查后修复 [2026-04-11] | P1 |
| TASK-0050 | C0-1 股票bars API路由 | data | 数据 | ✅ locked [2026-04-12] | P1 |
| TASK-0051 | C0-3 策略导入解析器 | decision | 决策 | ✅ locked [2026-04-12] | P1 |
| TASK-0052 | CG1 回测策略导入队列 | backtest | 回测 | ✅ locked [2026-04-12] | P1 |
| TASK-0053 | C0-2 FactorLoader股票支持 | decision | 决策 | ✅ locked [2026-04-12] | P1 |
| TASK-0054 | CB5 动态watchlist采集 | data+decision | 数据+决策 | ✅ locked [2026-04-12] | P1 |
| TASK-0055 | CG2 人工手动回测审核 | backtest | 回测 | ✅ locked [2026-04-12] | P1 |
| TASK-0056 | CA2' 期货沙箱回测引擎 | decision | 决策 | ✅ locked [2026-04-12] | P1 |
| TASK-0057 | CB2' 股票沙箱回测引擎 | decision | 决策 | ✅ locked [2026-04-12] | P1 |
| TASK-0058 | CG3 股票手动回测 | backtest | 回测 | ✅ locked [2026-04-12] | P1 |
| TASK-0059 | CA6 信号分发投产 | decision | 决策 | ✅ locked [2026-04-12] | P1 |
| TASK-0060 | CA3 回测报告展示导出 | decision | 决策 | ✅ locked [2026-04-12] | P1 |
| TASK-0061 | CA4 交易参数调优引擎 | decision | 决策 | ✅ locked [2026-04-12] | P1 |
| TASK-0062 | CB3 全A股选股引擎 | decision | 决策 | ✅ locked [2026-04-12] | P1 |
| TASK-0063 | CF2 邮件+看板YAML导入 | decision | 决策 | ✅ locked [2026-04-12] | P1 |
| TASK-0023-A | 发布接口对接 | sim-trading | 模拟交易 | ✅ locked | P1 |
| TASK-0026 | 新增因子+别名 | backtest | 回测 | ✅ locked_back | P1 |
| TASK-0008 | 泛化引擎+报告导出 | backtest | 回测 | ✅ A~D全locked | P1 |
| TASK-0007 | 正式后端并回+前端收口 | backtest | 回测 | ✅ A~D全locked | P1 |
| TASK-0005 | 容器命名统一 | backtest | 回测 | ✅ locked [2026-04-10] | P2 |
| TASK-0027 | data全量采集迁移 | data | 数据 | ✅ 整体闭环 [2026-04-10] A0~A7全locked | P1 |
| TASK-0028 | data通知系统全量 | data | 数据 | ✅ B1-B6全locked [2026-04-09] | P1 |
| TASK-0029 | 极速维修V2制度 | 治理 | Atlas | ✅ locked | P1 |
| TASK-0030 | 终极维护U0制度 | 治理 | Atlas | ✅ locked | P1 |
| TASK-0032 | data_web临时看板导入 | data | 数据 | ✅ locked | P1 |
| TASK-0033 | data_web正式化联调 | data | 数据 | ✅ locked | P1 |
| TASK-0034 | data端U0审计 | data | Atlas | ✅ locked | P1 |
| TASK-0035 | data端新闻卡片修复 | data | Atlas | ✅ locked (U0) | P1 |
| TASK-0036 | ~~灾备演练~~ → 实际为U0外盘K线修复 | data | Atlas | ✅ locked (U0) [编号冲突] | P1 |
| TASK-0037 | ~~PBO检验~~ → 实际为U0通知降噪 | data | Atlas | ✅ locked (U0) [编号冲突] | P1 |
| TASK-0038 | data端国内K线降噪 | data | Atlas | ✅ locked (U0) | P1 |
| TASK-0025 | SimNow备用方案 | decision | 决策 | 预审(待Phase C) | P2 |
| TASK-0015 | SimNow临时看板 | dashboard | 看板 | 预审(待各端临时看板收口) | P2 |
| ~~TASK-0020~~ | ~~ECS云部署~~ | ~~运维~~ | ~~运维~~ | ❌ 已取消（[修订 2026-04-12] ECS永久停用） | ~~P2~~ |
| TASK-0011 | legacy清退 | sim-trading | 项目架构师 | 后置(待Phase C/D) | P2 |
| TASK-0012 | legacy信号桥接 | integrations | 项目架构师 | 后置(待Phase C-C3) | P1 |
| TASK-0016 | 决策端正式接入 | decision | 决策 | 后置(待Phase C-C5) | P1 |
| ~~TASK-0036~~ | 灾备演练(原定编号冲突) | 全局 | 项目架构师 | ✅ 已重编号→TASK-0039; A0建档完成 [2026-04-10] | P1 |
| ~~TASK-0037~~ → TASK-0040 | PBO过拟合检验 | decision | 决策 | ✅ 已重编号→TASK-0040; A0建档完成 [2026-04-10]; 待Phase C(C2) | P1 |
| TASK-0099 | 统一看板首页框架（Phase F-F0） | dashboard | Claude | ✅ locked (commit bee35c9, tok-3e1c1970) [2026-04-14] | P1 |
| TASK-0100 | sim-trading 全功能升级（Phase F-F1） | dashboard | Claude | ✅ locked (commit 4969642, tok-279d4f99) [2026-04-14] | P1 |
| TASK-0101 | backtest 全功能升级（Phase F-F2） | dashboard | Claude | 🟡 执行中 (tok-92f7dce9 active) [2026-04-14] | P1 |
| TASK-0102 | decision 全功能升级（Phase F-F3） | dashboard | Claude | ⏳ 待 TASK-0101 locked (tok-1f25eea1 active) | P1 |
| TASK-0103 | data 全功能升级（Phase F-F4） | dashboard | Claude | ⏳ 待 TASK-0102 locked (tok-bcdd740a active) | P1 |
| TASK-0112-A | 决策端 LLM 口径修正 + phi4 L1/L2 门控实装 | decision | Claude | 🟡 Token active (tok-0a2faa03) | P1 |
| TASK-0112-B | 决策端 deepcoder 夜间策略调优 + 沙箱回测 | decision | Claude | 🟡 Token active (tok-08de1aff)，依赖 A | P1 |
| TASK-0112-C | 决策端 full_pipeline() 串联 + Optuna 调度 | decision | Claude | 🟡 Token active (tok-370db4de)，依赖 B | P1 |
| TASK-0114 | 决策端 35 品种自适应模型注册表 | decision | Claude | 🟡 Token active (tok-d0112f40)，依赖 0112-C | P1 |
| TASK-0115 | 决策端信号失真检测 + 因子漂移监控（G8） | decision | Claude | 🟡 Token active (tok-48fd42a7)，可并行 | P1 |
| TASK-0116 | 决策端因子挖掘自动化 | decision | Claude | 🟡 Token active (tok-bc3f9282)，可并行 | P1 |
| TASK-0117 | 决策端研究中心 5 项拓展 | decision | Claude | 🟡 Token active (tok-f8d27abe)，依赖 0112-C | P1 |

---

## 四、分阶段执行路线图

### Phase A — 基础稳定化 ✅ [2026-04-10 全闭环]

**目标：** 确保当前已部署的服务稳定运行，修复已知问题

| 序号 | 任务 | Agent | 依赖 | 验收标准 | 状态 |
|------|------|-------|------|---------|------|
| A1 | TASK-0031 data热修 | 数据 | Jay.S 签发6文件Token | A股停采不报错；health_check无误报；新闻推送恢复 | ✅ locked |
| A2 | TASK-0017 开盘验证 | 模拟交易 | 开盘窗口 | CTP行情tick收到；成交回报正常；蒲公英可访 | ✅ A1-A4全locked [2026-04-10] |
| A3 | TASK-0018-B data API实施 | 数据 | token已active | `services/data/src/main.py` 支持回测所需bars查询 | ✅ locked |
| A4 | TASK-0018-C-SUP 本地引擎补数据 | 回测 | A3完成+token已active | local_engine 通过 data API 获取真实K线执行回测 | ✅ locked |

**并行规则：** A1⊥A2⊥(A3→A4)，即数据热修、开盘验证、回测数据接入三条线可并行

### Phase B — SimNow 生产闭环 ✅ [2026-04-10 全闭环]

**目标：** 模拟交易达到"可日常运行+风控有效+通知畅通"的生产标准

| 序号 | 任务 | Agent | 依赖 | 验收标准 |
|------|------|-------|------|---------|
| B1 | TASK-0014 风控通知链路 | 模拟交易 | Phase A | ✅ A1~A4全锁回 [修订 2026-04-10] |
| B2 | TASK-0009 严格风控验收 | 项目架构师 | B1完成 | ✅ 治理闭环 [2026-04-10] |
| B3 | TASK-0013 统一风控核心 | 项目架构师 | B2完成 | ✅ 治理闭环 [2026-04-10] |
| B4 | TASK-0010 骨架完善 | 模拟交易 | B3完成 | ✅ 已闭环，15文件全就绪 [2026-04-10] |
| B5 | TASK-0019 收盘报表 | 模拟交易 | B4完成 | ✅ B1/B2 locked [修订 2026-04-10] |
| B6 | TASK-0022-B 只读日志 | 模拟交易 | B4完成 | ✅ locked [2026-04-10] |

**并行规则：** B1→B2→B3→B4，之后 B5⊥B6

### Phase B+ — 灾备演练质量门禁 [修订 2026-04-09]

**目标：** 验证已部署服务在真实故障场景下的韧性，确保告警及时、服务自愈、数据完整

| 序号 | 场景 | 验证 Agent | 验收标准 |
|------|------|-----------|----------|
| DR1 | Mini 断网（拔网线/防火墙模拟） | 数据+模拟交易 | 飞书 P1 告警 ≤ 30s；data/sim-trading 自动重连；bars API 重连后数据连续 |
| DR2 | Studio 宕机（docker stop 全容器） | 决策+看板 | 飞书 P0 告警 ≤ 30s；docker restart policy 自动恢复；决策看板自动重连 |
| DR3 | Docker 容器崩溃（kill -9 主进程） | 各 Agent | restart: unless-stopped 策略生效；服务 ≤ 60s 内恢复响应 |
| DR4 | 数据端采集中断+恢复 | 数据 | 恢复后自动补采缺失区间；health_check 不误报 |

**任务编号：** ~~TASK-0036~~ → **TASK-0039**（原 TASK-0036 编号已被 U0 外盘 K 线修复占用）[修订 2026-04-11]
**时机：** Phase B 完成后、Phase C 开始前
**前置条件：** Phase B 全部闭环 ✅ 已满足 [2026-04-10]

### Phase C — 决策端核心能力

**目标：** 决策端与数据端、回测端、模拟交易端形成“策略导入 → 双沙箱研究/回测 → 调优 → 回测端人工二次回测 → 审批 → 进入策略池 → 执行/荐股”的完整链路。

**Phase C 硬约束：**

1. 期货自动回测只在 decision 内部期货沙箱执行；股票自动回测只在 decision 内部股票沙箱执行；两者数据不互通，只共享因子定义。
2. 所有策略调优完成后，必须导出到 backtest 端进行人工二次手动回测与审核确认；未经人工确认，不得进入各自策略池。
3. 飞书不接收 YAML 策略导入，只接收口头策略需求；正式 YAML 仅允许看板上传或标准格式邮件导入。
4. 研究中心若自研因子，必须与 backtest 端双地同步；研究中心与回测端的因子实现和版本必须保持一致。

#### C0 共享前置

| 编号 | 任务 | 主责 | 协同 | 验收标准 |
|------|------|------|------|---------|
| C0-1 | 股票 bars API 路由扩展 | 数据 | 决策 | `services/data/src/main.py` 支持股票代码解析与 `stock_daily/stock_minute` 供数 |
| C0-2 | FactorLoader 股票代码支持 | 决策 | 数据 | `factor_loader.py` 可通过 data API 拉取股票日线/分钟K |
| C0-3 | 策略导入解析器 | 决策 | 无 | 统一支持看板 YAML / 邮件 YAML / 内部生成策略的入库与校验 |

> **[修订 2026-04-12] Phase C C0 实施情况：**
> - **C0-1**：✅ 已完成 → TASK-0050 commit `73f1634` [2026-04-12]
> - **C0-2**：✅ 已完成 → TASK-0053 stock_data_client + factor_loader 股票支持 [2026-04-12]
> - **C0-3**：✅ 已完成 → TASK-0051 strategy_importer + yaml_importer [2026-04-12]

#### CA 期货研究链路

| 编号 | 任务 | 主责 | 协同 | 验收标准 |
|------|------|------|------|---------|
| CA1 | 看板导入与研究入口 | 决策 | 无 | `research-center` 可导入期货策略并登记到策略仓库 |
| CA2' | 期货沙箱回测引擎 | 决策 | 数据 | decision 内部完成期货逐 bar 回测与绩效统计，不依赖 backtest API |
| CA3 | 回测报告展示与导出 | 决策 | 无 | 研究中心页面可展示并导出期货回测报告 |
| CA4 | 交易参数调优引擎 | 决策 | 无 | 基于真实 Sharpe / 回撤等指标调优期货交易参数 |
| CA5 | 期货研究中心全流程 UI | 决策 | 无 | 页面闭环覆盖导入、回测、调优、报告、提交人工复核 |
| CA6 | 信号真闭环 → sim-trading | 决策 | 模拟交易 | 通过人工二次回测确认后，策略可进入 sim-trading 执行 |
| CA7 | ~~TASK-0037~~ → TASK-0040 PBO过拟合检验 | 决策 | 无 | 研究报告输出 PBO/CPCV，作为自动研发门禁的一部分 |

> **[修订 2026-04-12] CA 实施情况：**
> - **CA2'**：✅ 已完成 → TASK-0056 sandbox_engine.py 投产 [2026-04-12]
> - **CA3**：✅ 已完成 → TASK-0060 report_builder + report 路由投产 [2026-04-12]
> - **CA4**：✅ 已完成 → TASK-0061 trade_optimizer 网格搜索投产 [2026-04-12]
> - **CA6**：✅ 已完成 → TASK-0059 signal_dispatcher 投产 [2026-04-12]
> - **CA1**：✅ 已完成 → TASK-0074 期货研究入口页面+FuturesResearchPanel 投产 [2026-04-13]
> - **CA5**：✅ 已完成 → TASK-0074 期货研究中心 UI 投产 [2026-04-13]
> - **CA7**：✅ 已完成 → TASK-0075 PBOValidator CSCV实现 commit eb33055，11测试通过 [2026-04-13]

#### CB 股票研究链路

| 编号 | 任务 | 主责 | 协同 | 验收标准 |
|------|------|------|------|---------|
| CB1 | 股票策略模板（短/中/长期） | 决策 | 无 | 形成面向日线的 short/mid/long 三类模板 |
| CB2' | 股票沙箱回测引擎 | 决策 | 数据 | decision 内部完成股票日线回测，不依赖 backtest 自动引擎 |
| CB3 | 全 A 股选股引擎 + benchmark | 决策 | 数据 | 先完成全量跑分 benchmark，再冻结每日固定选股时间 |
| CB4 | 股票池管理器 | 决策 | 无 | 白天/晚间轮换后池内常驻 30 只股票，保留淘汰理由 |
| CB5 | 动态 watchlist 分钟K采集 | 数据 | 决策 | data 端按 20 只 watchlist 动态采集分钟 K，替代全量轮询 |

> **[修订 2026-04-12] CB5**：✅ 已完成 → TASK-0054 watchlist_client + stock_minute_collector 动态模式 + strategy.py watchlist 端点 [2026-04-12]

> **[修订 2026-04-12] CB2'**：✅ 已完成 → TASK-0057 sandbox_engine T+1/涨跌停扩展 [2026-04-12]

> **[修订 2026-04-12] CB3**：✅ 已完成 → TASK-0062 stock_screener 多因子打分 + benchmark 投产 [2026-04-12]

> **[修订 2026-04-13] CB1**：✅ 已完成 → TASK-0069 短/中/长期三类模板 + 回测路由 commit e80e74b [2026-04-12]

> **[修订 2026-04-13] CB4**：✅ 已完成 → TASK-0070 StockPool管理器 add/remove/rotate commit 94fedbc [2026-04-13]

> **[修订 2026-04-13] CB6**：✅ 已完成 → TASK-0071 IntradayTracker breakout/volume_spike信号 commit 0568ec2 [2026-04-13]

> **[修订 2026-04-13] CB7**：✅ 已完成 → TASK-0072 PostMarketEvaluator 5级评级+批量评估 commit cfd2998 [2026-04-13]

> **[修订 2026-04-13] CB8**：✅ 已完成 → TASK-0073 EveningRotator 多因子打分+轮换计划 commit 96bc534 [2026-04-13]

> **[修订 2026-04-13] CB9**：✅ 已完成 → TASK-0074 股票研究中心页面(StockPoolTable+IntradaySignal+盘后报啄) commit aec3dae [2026-04-13]

| CB6 | 盘中跟踪与飞书入离场提醒 | 决策 | 数据 | 盘中基于分钟 K 给出入场/离场提醒 |
| CB7 | 盘后评估与未来预判 | 决策 | 无 | 对 30 只股票输出走势评估、目标价位、止盈止损与预判 |
| CB8 | 晚间再选 + 淘汰 + 报告 | 决策 | 无 | 每晚新增 20、淘汰 10、保留 10，并输出完整报告 |
| CB9 | 股票研究中心页面 | 决策 | 无 | 看板显示股票池、入离场时间线、选股排行与盘后评估 |

#### CG 人工二次回测关卡

| 编号 | 任务 | 主责 | 协同 | 验收标准 |
|------|------|------|------|---------|
| CG1 | 回测端策略导入队列 | 回测 | 决策 | backtest 端可导入“原始策略 / 研究中心优化后策略” |
| CG2 | 人工手动回测 + 审核确认 | 回测 | 决策 | 人工点选回测、审阅结果、确认是否启用，回写 decision 状态 |
| CG3 | 回测端股票手动回测与看板调整 | 回测 | 数据 | 回测端新增股票回测与对应看板页面 |
> **[修订 2026-04-12] CG 实施情况：**
> - **CG1**：✅ 已完成 → TASK-0052 strategy_queue 投产 [2026-04-12]
> - **CG2**：✅ 已完成 → TASK-0055 manual_runner + approval 投产 [2026-04-12]
> - **CG3**：✅ 已完成 → TASK-0058 stock_runner + stock_approval T+1/涨跌停投产 [2026-04-12]

#### CF 导入通道

| 编号 | 任务 | 主责 | 协同 | 验收标准 |
|------|------|------|------|---------|
| CF1' | 飞书口头策略通道 | 决策 | 无 | 用户可用自然语言提出策略想法，研究中心自动生成策略并反馈结果 |
| CF2 | 邮件 + 看板 YAML 导入 | 决策 | 无 | YAML 仅允许标准格式邮件或看板上传；导入成功/失败通过飞书通知 |

> **[修订 2026-04-12] CF 实施情况：**
> - **CF2**：✅ 已完成 → TASK-0063 EmailImporter + import_channel 路由投产 [2026-04-12]

> **[修订 2026-04-13] CF1' LLM Pipeline：**
> - **CF1'**：✅ 已完成 → TASK-0083 LLM Pipeline集成+研究中心auto_backtest+Bug Fix, Atlas复核通过 [2026-04-13]
> - 架构：Mini 同源投喂 + Alienware 研究员报告 + Studio 决策/开发主控 的协同链路
> - 本地模型冻结：Studio = deepcoder:14b（策略开发 / 因子挖掘）+ phi4-reasoning:14b（盘中门控 / 快速分析）；Alienware = qwen3:14b（研究报告生成）
> - 约束：不再沿用“Studio 3×14B 串行流水线”口径；Alienware 负责输出两份格式化报告（Studio / Jay.S），Studio 消费 Mini 投喂数据与研究报告继续进入双沙箱 / 人工复核链路

#### CS 容灾与断联接管

| 编号 | 任务 | 主责 | 协同 | 验收标准 |
|------|------|------|------|---------|
| CS1 | decision 本地 Sim 容灾引擎 | 决策 | 模拟交易/实盘交易 | 平时 standby；一旦与正式交易端断联，即可本地接管任务与临时账本 |
| CS1-S | 交易端交接接口 | 模拟交易 | 决策/实盘交易 | 正式交易端恢复后可接收订单/持仓/账本差异并完成任务回切 |

> **[修订 2026-04-13] CS1**：✅ 已完成 → TASK-0076 LocalSimEngine failover 引擎 commit 3c8be69，12测试通过 [2026-04-13]

> **[修订 2026-04-14] CS1-S**：✅ 已完成 → TASK-0077 交易端容灾交接接口 commit 8afc8f5 [2026-04-13]

#### CK 因子体系

| 编号 | 任务 | 主责 | 协同 | 验收标准 |
|------|------|------|------|---------|
| CK1 | 共享因子库覆盖率扩充 | 决策+回测 | 项目架构师 | 共享因子覆盖率达到 90%+，大多数导入策略无需单独补因子 |
| CK2 | 因子双地同步与版本校验 | 项目架构师 | 决策+回测 | 研究中心与回测端因子实现、版本、hash 保持一致 |
| CK3 | 因子缺失/新增通知 | 决策+回测 | 无 | 导入缺失因子或研究中心新增因子时，双端都能通知并留痕 |

**股票链路日程冻结：**

1. 每日 09:00 输出前一晚选股报告，说明去除的 10 只、原因以及新增 20 只的选股逻辑。
2. 09:30-15:00 盘中基于分钟 K 做入离场提醒。
3. 15:30 后进行 30 只股票盘后评估、目标价位与未来走势预判。
4. 晚间再跑一轮选股，完成 20 只新增、10 只淘汰、30 只常驻池的闭环。

**并行规则：** `C0-1 ⊥ C0-3 -> C0-2`；`CA2' ⊥ CB2'`；`CA/CB` 的自动研究结果统一汇入 `CG1/CG2/CG3` 人工二次回测关卡；`CK1 -> CK2 -> CK3` 贯穿决策与回测两端；`CS1/CS1-S` 与双沙箱可并行推进。 [修订 2026-04-11]

### Phase D — 数据端全量迁移 [修订 2026-04-11: ~85% 完成]

**目标：** Mini数据端从legacy cron完全迁移到JBT Docker体系。当前必须做 system 级迁移，因为真实 24h 运行链路仍在 legacy system 上；若不迁移，JBT data 仍无法成为正式运行承载面。 [修订 2026-04-10]

| 序号 | 任务 | Agent | 依赖 | 验收标准 | 状态 |
|------|------|-------|------|---------|------|
| D1 | TASK-0027 全量采集迁移 | 数据 | Phase A完成 | 21个采集器全部Docker化；cron全部替换为scheduler | ✅ 整体闭环 A0~A7全locked |
| D2 | 通知统一(TASK-0028) | 数据 | D1完成 | 飞书+邮件按JBT统一卡片标准 | ✅ B1-B6全locked |
| D3 | data_web 临时看板(TASK-0032+0033) | 数据 | D1完成 | 6页（总览/采集器/数据浏览/新闻/硬件/配置） | ✅ locked |
| D4 | 健康检查修正(TASK-0031) | 数据 | D1完成 | stock/news判定不再误报 | ✅ locked |

**剩余缺口：** 无。TASK-0027 整体闭环，Phase D D1 完成 [2026-04-10]

**并行规则：** D1→(D2⊥D3⊥D4)

### Phase E — 回测系统稳定化 ✅ [2026-04-10 全闭环]

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
| ~~F3~~ | ~~TASK-0020 ECS部署~~ | ~~运维~~ | ~~DNS+SSH就绪~~ | ❌ 已取消（[修订 2026-04-12] ECS永久停用，公网访问不再纳入计划） |

### Phase G — 收口与legacy清退

**目标：** JBT 完全独立运行，legacy J_BotQuant 退役并从工作区切割

> **[修订 2026-04-12] Phase C完成后立即执行 G0（J_BotQuant工作区切割）；G1~G3随后跟进。**

| 序号 | 任务 | Agent | 依赖 | 验收标准 |
|------|------|-------|------|----------|
| G0 | J_BotQuant工作区切割 | Atlas | Phase C完成 | 1. 停止Mini/Studio所有legacy J_BotQuant容器；2. 将J_BotQuant从VS Code工作区（.code-workspace）移除；3. J_BotQuant目录保留只读归档，不再承接任何开发 |
| G1 | TASK-0011 legacy清退 | 项目架构师 | G0完成 | Mini/Studio legacy进程全部停止，cron/LaunchAgent清退 |
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

### 安全治理横线 SG — 全项目安全检查与统一修复预审 [修订 2026-04-11]

**说明：** SG 不是新的功能 Phase，也不改写 Phase A~H 的功能顺序；它是覆盖当前主线的横向治理约束，用于冻结“先安全检查、再统一修复”的执行口径。

**SG 硬约束：**

1. 当前阶段只允许只读安全检查、复核与修复预审，不进入任何即时代码修复。
2. 本轮“策略端”固定为 `decision + backtest`；首批主落点先以 `backtest` 已确认的 `F-001` 为主，`decision` 作为补充复核范围。
3. data 侧 `F-002`、`F-003` 以及其余范围当前只允许做可达性与影响面复核，不得误写成已批准实施。
4. 任一真正代码修复，仍必须在 SG4 完成后独立建档、冻结白名单、签发 Token，并重新进入标准实施流程。

| 编号 | 任务 | 主责 | 协同 | 验收标准 |
|------|------|------|------|---------|
| SG1 | 策略端只读安全检查 | Atlas | 决策+回测 | ✅ 完成 [2026-04-11] |
| SG2 | 策略端复核冻结 | 项目架构师 | Atlas | ✅ Round 0 全域扫描完成 [2026-04-12] |
| SG3 | 全域只读安全检查 | Atlas | 数据+模拟交易+看板+实盘交易+项目架构师 | ✅ Round 0 全域扫描完成 [2026-04-12] |
| SG4 | 全域安全复核冻结 | 项目架构师 | Atlas | ✅ Round 0 报告 + 架构师 Round 2 终审完成 [2026-04-12] |
| SG5 | 统一修复预审与实施 | Claude-Code | Atlas+项目架构师 | 🟡 进行中：data Round 1 ✅、backtest Round 2 ✅（含Pow补丁）、decision Round 3 ✅、sim-trading Round 4 ✅（3 commits, 架构师终审通过） |

---

## 五、战略能力规划（Jay.S 七大构想）

以下为 Jay.S 提出的七项战略构想，对应到已冻结的服务边界与未来扩展路径：

### 5.1 多策略按品种按时间桶并行

- **归属服务：** decision 主导，backtest 承接人工最终复核
- **前置条件：** `C0` 前置完成 + `CA2'`/`CB2'` 双沙箱就绪 + `CG1/CG2` 人工二次回测关卡就绪
- **实施路径：**
  1. 期货侧：在 decision 期货沙箱内按品种 + 时间桶（5m/15m/30m/60m）并行执行研究与调优。
  2. 股票侧：在 decision 股票沙箱内按短/中/长期三类日线模板并行研究与选股。
  3. 所有优化后策略统一导出到 backtest 端进行人工手动回测与审核确认。
- **legacy资产可复用：** `J_BotQuant/scripts/unified_strategy_runner.py`、`factor_live_trader.py`
- **实施阶段：** Phase C + CG

### 5.2 完整策略自动淘汰制度

- **归属服务：** decision + backtest（人工复核）
- **前置条件：** 策略仓库、双沙箱、人工二次回测关卡完成
- **实施路径：**
  1. 期货/股票策略在运行中持续按连亏、PnL、Sharpe、胜率等规则评估。
  2. 股票池每日晚间执行“新增 20 / 淘汰 10 / 常驻 30”轮换，淘汰理由进入报告。
  3. 被淘汰策略回退到研究中心重新优化，再次进入人工复核。
- **legacy资产可复用：** `J_BotQuant/scripts/strategy_retirement_check.py`
- **实施阶段：** Phase C 后续独立任务

### 5.3 研发中心开发

- **归属服务：** decision
- **前置条件：** `C0` 共享前置 + `CA` / `CB` 研究链路启动
- **实施路径：**
  1. 看板导入 YAML、标准格式邮件导入 YAML、飞书口头策略三通道统一进入策略导入解析器。
  2. research-center 页面覆盖导入、回测、调优、报告、提交人工复核的全流程。
  3. 研究中心允许通过 SHAP 发现组合因子、口头策略衍生因子、手动定义因子三种方式自研因子。
  4. 研究中心自研因子必须同步到回测端并通过版本/hash 校验后才能正式使用。
- **现有资产：** `src/research/` 现有骨架 + `decision_web` 真数据基线
- **实施阶段：** Phase C

### 5.4 决策端封闭双沙箱

- **归属服务：** decision
- **前置条件：** 研发中心基础 + `CK1/CK2/CK3` 因子体系就绪
- **实施路径：**
  1. 在 decision 内部建立 `futures_sandbox` 与 `stock_sandbox` 两条自动研究主路径。
  2. 两个沙箱数据完全隔离，只共享 `shared/python-common` 中的因子定义与版本元数据。
  3. 期货沙箱负责自动期货回测、调优、PBO/CPCV 验证；股票沙箱负责日线回测、选股、盘中跟踪与盘后评估。
  4. 沙箱结果不得直接发布到交易端，必须先导出到 backtest 端做人为手动回测与审核确认。
- **自研因子同步规则：** 新因子创建后，必须完成“注册到共享因子库 → 双端同步 → bit-exact 校验 → 回测端可用”的流水线。
- **安全围栏（硬性验收条件）：**
  1. AI 生成代码或因子必须经过 `flake8 + bandit` 静态扫描。
  2. 沙箱容器必须限制 CPU（≤2核）/ Memory（≤4GB）/ Network（默认禁止外网出站）。
  3. 所有策略必须经过人工二次回测与 Approve，方可进入策略池。
- **实施阶段：** Phase C 主线

### 5.5 飞书/看板控制面

- **归属服务：** decision + dashboard + backtest
- **前置条件：** Phase C 研究链路可用；聚合 dashboard 仍后置到 Phase F
- **实施路径：**
  1. 飞书负责接收口头策略需求、盘中入离场提醒、09:00 选股摘要、导入成功/失败通知。
  2. 邮件负责承载完整 YAML 导入、详细回测报告、盘后评估与股票池轮换长报告。
  3. 各服务临时看板优先在 decision_web / backtest_web 内落地扩容页面；聚合 dashboard 最后统一收口。
- **实施阶段：** Phase C + Phase F

### 5.6 本地模型集成（Studio + Alienware 协同架构）[修订 2026-04-14]

- **归属服务：** decision（LLM Pipeline）+ Alienware 研究协同节点
- **前置条件：** 研究中心与口头策略通道完成基础接线
- **运行态冻结：** 四设备架构固定为 Mini / Studio / Alienware / Air；MacBook 仅保留开发/控制，不计入运行态四设备。
- **Studio 定位：** 决策/开发主控节点；本地常驻模型冻结为：
  1. **deepcoder:14b**：策略开发 / 因子挖掘 / 研究结果结构化转译。
  2. **phi4-reasoning:14b**：盘中门控 / 快速分析 / 读取 Mini 投喂数据与 Alienware 研究报告。
  3. 不再把 `qwen3:14b` 记为 Studio 本地常驻模型。
- **Alienware 定位：** 交易执行 + 情报研究员节点（192.168.31.224）；sim-trading:8101 已正式部署（TASK-0107，2026-04-15）；本地模型 `qwen3:14b`，不再记录 deepcoder / phi4。
- **Mini 定位：** 纯数据采集节点；仅负责采集与数据供数（data:8105），不再承载 sim-trading 或研究投喂存储职责。
- **Alienware 承担：**
  1. 运行 sim-trading:8101 API，承接 CTP 交易执行（光大期货）。
  2. 读取 Mini 的采集数据，生成两份格式化研究报告：一份给 Studio，一份给 Jay.S。
  3. 承载期货公司官方 Windows 交易软件，作为 24h 在线主机。
- **[修订 2026-04-15] TASK-0107 已完成**：sim-trading 服务已迁移至 Alienware 并验证通过，原过渡说明不再适用。Docker 化部署待 BIOS 虚拟化开启后另行完成。
- **实施阶段：** 基础迁移已完成；后续若需调整 decision 本地模型装载、研究路由，均需独立任务。

### 5.7 数据端预读投喂决策端 [修订 2026-04-14]

- **任务编号：** TASK-0104（已建档，2026-04-14）
- **归属服务：** data → decision；Alienware 为研究协同节点，不改写服务边界
- **前置条件：** `C0-1` 股票 bars 路由扩展 + `CB5` 动态 watchlist 分钟 K 已落地
- **Mini 节点职责：** 作为“数据源 + 情报落库存储 + 快速投喂节点”，负责采集、预读、存放研究员报告和投喂包，并向 Studio 与 Alienware 提供同源数据。
- **实施路径：**
  1. Mini 在非交易时段（21:00）预读 K 线、新闻、宏观、情绪和股票池 watchlist 数据，生成统一投喂包并落库。
  2. Mini 在开盘前与盘中同时向 Alienware 与 Studio 提供同源数据；Studio 不再假定自己本地承担完整三模型串行研究。
  3. Alienware 读取 Mini 的采集 / 预读 / 研究投喂数据，由 `qwen3:14b` 生成两份格式化研究报告：一份给 Studio，一份给 Jay.S。
  4. Studio 读取 Mini 投喂包与 Alienware 报告，由 `phi4-reasoning:14b` 承担盘中门控 / 快速分析，由 `deepcoder:14b` 承担策略开发 / 因子挖掘与结构化落地。
- **研究范围冻结：**
  1. 期货优先，只跟踪当前已有策略覆盖的品种，重点关注内外盘突发和实时关联消息。
  2. 股票只分析策略筛出的 30 只股票池，不在池内的不分析。
  3. 搜索 / 外部信息在研究环节中主要作为“排除项增强”，负面或不确定信息权重提高，不作为无条件加分项。
- **数据资产清单（15 个 collector）：**
  - 市场：TushareDailyCollector、StockMinuteCollector、OverseasMinuteCollector
  - 宏观/情绪：MacroCollector、SentimentCollector、CftcCollector、VolatilityCollector
  - 新闻：NewsAPICollector、RSSCollector
  - 衍生品：OptionsCollector、ForexCollector、ShippingCollector
  - 深度：TqSdkCollector、TushareFullCollector、TushareFuturesCollector
- **节点模型映射（治理冻结）：**
  - Mini 投喂包 → Alienware `qwen3:14b` → Studio / Jay.S 双报告
  - Mini 投喂包 → Studio `phi4-reasoning:14b` → 盘中门控 / 快速分析
  - Mini 投喂包 + 研究报告 → Studio `deepcoder:14b` → 策略开发 / 因子挖掘
  - 在线模型 `qwen-plus-latest / qwen-max-latest` 只作为上层扩展能力，不改变本地模型冻结口径
- **Studio + Alienware 节点模型冻结（规划口径，2026-04-14）：**
  - Studio：`OLLAMA_RESEARCHER_MODEL=deepcoder:14b`
  - Studio：`OLLAMA_ANALYST_MODEL=phi4-reasoning:14b`
  - Alienware：`OLLAMA_AUDITOR_MODEL=qwen3:14b`
- **在线模型配置（扩展能力，2026-04-14）：**
  - `ONLINE_MODEL_DEFAULT=qwen-plus-latest`（DashScope，¥2/百万输入 token）
  - `ONLINE_MODEL_UPGRADE=qwen-max-latest`（DashScope，¥2.5/百万输入 token）
  - `ONLINE_MODEL_BACKUP=qwen-plus-latest`
  - `ONLINE_MODEL_DISPUTE=qwen-max-latest`
- **费用基准（DashScope 官方定价 2026-04-14）：** TASK-0104 上线后约 ¥1.6/天 / ¥35/月（20 信号/天场景），高频满载约 ¥115/月，成本可控。
- **分批实施（D0-D5）：**
  - D0 数据结构设计（Architect 预审）
  - D1 data 夜间调度器扩展
  - D2 Mini → Studio / Alienware 双投喂接口
  - D3 Alienware 研究报告模板与排除项增强
  - D4 Studio 消费双报告 + Jay.S 报告通知
  - D5 健康检查与 SLA 告警
- **当前状态：** ✅ D1+D2 全部完成（2026-04-15）。D1 commit 802c1f7（tok-d8f23d88 locked），D2 commit d356511（tok-6f298133 locked）。Mini 已同步（D1 今晚 21:00 preread 自动首次运行），Studio 已同步（D2 待重启生效）。
- **实施阶段：** Phase D — D1/D2 已闭环；D3~D5 后续按需推进

---

## 六、Agent 衔接矩阵

### 6.1 模拟交易 Agent

**当前状态：** Phase B 基线闭环；当前等待开盘验证，并冻结“Mini 现网部署 + Alienware 目标承载面”过渡口径
**开工前必读：**
1. `WORKFLOW.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/模拟交易提示词.md`
4. `docs/tasks/TASK-0014-sim-trading-风控通知链路预审.md`
5. `docs/handoffs/` 中 sim-trading 相关交接单

**任务队列（按优先级）：**

```
┌─ TASK-0017  待开盘验证CTP               ← 等开盘窗口
├─ CA6  决策端信号真闭环执行适配          ← 依赖 decision 人工二次回测关卡
├─ CS1-S  本地Sim容灾交接API             ← 待 TASK-0048 后续拆批
└─ Phase H 前保持观察，不主动扩新范围
```

**交接要点：**
- SimNow 凭证只通过 `.env` 运行时注入，绝不写入 Git
- Mini 是模拟交易主机(172.16.0.49:8101)，ECS 暂停
- 当前 JBT 已部署的 sim-trading 容器/API 仍在 Mini，这是现网事实
- Alienware 承载期货公司官方 Windows 交易软件与研究员节点，但不等于 sim-trading 服务已迁移
- 若后续要把交易执行正式切到 Alienware，必须另建任务、预审、白名单、Token
- 所有 API 调用只通过 Mini 蒲公英，不通过 ECS
- MD 24h 保活，TD 仅交易时段
- 风控规则必须从 guards.py emit_alert 走 dispatcher → feishu/email
- 正式执行面仍固定为 sim-trading；decision 本地 Sim 只作为断联容灾备用面，不得常态替代 sim-trading
- 正式交易端恢复后，sim-trading 必须接收 decision 推送的订单/持仓/账本差异并完成回切

### 6.2 决策 Agent

**当前状态：** Phase C 全闭环 + TASK-0083 LLM集成/因子同步/Bug修复 Atlas复核通过；Studio + Alienware 协同研究/决策口径已冻结
**开工前必读：**
1. `WORKFLOW.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/决策提示词.md`
4. `docs/tasks/TASK-0021-decision-旧决策域清洗升级迁移预审.md`
5. `docs/handoffs/TASK-0021-*` 系列交接单

**任务队列（按优先级）：**

```
┌─ CK1 / CK2 / CK3  因子覆盖率与双地同步  ← 与 backtest 协同
└─ TASK-0016  正式接入                       ← 依赖人工二次回测关卡稳定
```

**已完成（Phase C 本轮 [2026-04-13]）：**
- ✅ C0-2 FactorLoader股票支持、C0-3 策略导入解析器
- ✅ CA1~CA7 期货研究全链路（沙箱/报告/调优/信号分发/UI/PBO检验）
- ✅ CB1~CB9 股票研究全链路（模板/股票池/盘中跟踪/盘后评估/晚间译股/研究页面）
- ✅ CB5 watchlist、CF2 邮件+看板 YAML 导入
- ✅ CS1 本地 Sim 容灾引擎 (TASK-0076)
- ✅ 看板扩容 7+3+3 页面 (TASK-0074+TASK-0079)
- ✅ TASK-0040/CA7 PBO CSCV 实现 (TASK-0075)
- ✅ CF1' LLM Pipeline 基线已完成（TASK-0083, Atlas复核通过）；2026-04-14 起按“Studio=deepcoder+phi4 / Alienware=qwen3 双报告”口径运行
- ✅ Factor Sync 共享因子基础框架 (TASK-0083, shared/python-common/factors/)
- ✅ Bug Fix: SignalDispatcher FIFO + ctp_disconnect lock (TASK-0083)

**交接要点：**
- 自动研究主路径固定在 decision 双沙箱内部完成；backtest 端只承担人工二次回测与审核确认
- Studio 本地常驻模型冻结为 `deepcoder:14b` + `phi4-reasoning:14b`；`qwen3:14b` 改记 Alienware 研究员节点，不再记为 Studio 本地常驻
- decision 侧默认读取 Mini 同源投喂数据 + Alienware 双报告；Studio 本地主要承担门控、快速分析、策略开发与因子挖掘
- 研究范围冻结：期货只跟踪已有策略覆盖品种；股票只分析 30 只股票池；搜索/外部信息只作排除项增强
- 策略调优完成后必须先进入 backtest 人工复核，再允许进入 `pending_execution`
- 飞书只接收口头策略需求；正式 YAML 仅允许邮件标准格式或看板导入
- 研究中心若自研因子，必须同步到 backtest 端并通过版本/hash 校验后方可正式使用
- SimTradingAdapter 继续 POST 到 `http://{SIM_TRADING_SERVICE_URL}/api/v1/strategy/publish`；但断联场景下先切到 decision 本地 Sim 备用面

### 6.3 数据 Agent

**当前状态：** system 级迁移基线已闭环 + Phase C 股票供数协同已完成（C0-1 + CB5 投产）；Mini → Studio / Alienware 同源投喂口径已冻结
**开工前必读：**
1. `WORKFLOW.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/数据提示词.md`
4. `docs/tasks/TASK-0031-data端非夜盘热修与新闻推送恢复.md`
5. `docs/tasks/TASK-0027-data端全量采集体系迁移.md`

**任务队列（按优先级）：**

```
┌─ 数据预读投喂决策端（后续独立任务）     ← 依赖本地模型与股票池稳定
└─ 维持现网供数稳定，不因 Phase C 打断生产
```

**已完成（Phase C 本轮 [2026-04-12]）：**
- ✅ C0-1 股票 bars API 路由扩展（TASK-0050）
- ✅ CB5 动态 watchlist 分钟K采集（TASK-0054）

**交接要点：**
- Mini 是数据主机（172.16.0.49:8105），`~/jbt-data/` 为数据根目录
- Mini 当前固定为“数据源 + 情报落库存储 + 快速投喂节点”，除供数外还负责存放研究员报告与投喂包
- Mini 需向 Studio 与 Alienware 提供同源数据，避免两端各自形成第二套研究输入源
- 21 个采集器文件在 `src/collectors/`，涵盖 tqsdk/tushare/akshare/rss/news_api/macro/sentiment 等
- `stock_minute_collector.py` 已存在，当前 `STOCK_MINUTE_ENABLED` 默认关闭；Phase C 要求切到“按 watchlist 动态采集”而非全量轮询
- 股票日线采集与 stock_basic 能力已存在，当前缺的是 bars API 路由层和调度模式切换
- 全量迁移要求"无中断"：不得先停旧 cron 再补救
- 飞书 webhook 命名兼容：`FEISHU_NEWS_WEBHOOK_URL` → `FEISHU_INFO_WEBHOOK_URL`
- 35 个期货品种 + 260 symbols + 63 KQ连续合约

### 6.4 回测 Agent

**当前状态：** Phase E 基线闭环 + CG 扩容已完成（CG1/CG2/CG3 全投产）+ 审核看板已上线（TASK-0078）
**开工前必读：**
1. `WORKFLOW.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/回测提示词.md`
4. `docs/tasks/TASK-0018-backtest-API化重建-Phase1.md`
5. `docs/tasks/TASK-0008-backtest-泛化正式引擎与正式报告导出预审.md`

**任务队列（按优先级）：**

```
┌─ CK2 / CK3  因子双地同步与缺失通知协同  ← 与 decision 共线
└─ 保持 Air 手动回测主机稳定，不接管自动研究回测
```

**已完成（Phase C 本轮 [2026-04-14]）：**
- ✅ CG1 策略导入队列（TASK-0052）
- ✅ CG2 人工手动回测 + 审核确认（TASK-0055）
- ✅ CG3 股票手动回测（TASK-0058）
- ✅ 审核看板 manual review / stock review 页面（TASK-0078）

**交接要点：**
- 双引擎架构：tqsdk(在线) + local(离线)，由 engine_router 路由
- Air 通过 Tailscale 访问 Mini data API (100.82.139.52:8105)
- 本地通过蒲公英访问 Mini data API (172.16.0.49:8105)
- FC-224 策略已验证 total_trades=242，final_equity 可追溯
- 风控引擎 risk_engine.py 执行 max_drawdown + daily_loss_limit 双规则
- 结果 report.json 包含完整元数据（策略/品种/区间/资金/手续费/滑点/status）
- backtest 不再承担 research-center 的自动回测主路径，而是承担“人工最终复核 + 是否启用策略”的确认责任
- 回测端后续必须支持 stock 策略导入、股票手动回测和人工审核页面

### 6.5 看板 Agent

**当前状态：** 空目录，待启动
**开工前必读：**
1. `WORKFLOW.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/看板提示词.md`
4. `docs/tasks/TASK-0015-dashboard-SimNow-临时Next.js看板预审.md`

**任务队列（按顺序）：**

```
├─ TASK-0099  首页框架                ✅ locked (commit bee35c9)
├─ TASK-0100  sim-trading全功能升级   ✅ locked (commit 4969642)
├─ TASK-0101  backtest全功能升级      🟡 Claude 执行中
├─ TASK-0102  decision全功能升级      ⏳ token active，待 0101 locked
├─ TASK-0103  data全功能升级          ⏳ token active，待 0102 locked
└─ F5 整合收口                        ⏳ 待 0099~0103 全部 locked
```

**交接要点：**
- 看板只做只读聚合，不得绕过 API 直接读服务内部数据
- API 代理路径：`/api/sim-trading → 8101`、`/api/backtest → 8103`、`/api/decision → 8104`、`/api/data → 8105`
- BASE 前缀规则：`/api/{service}/api/v1`（因各后端均使用 `/api/v1` 路由前缀）
- TypeScript strict：无 any、无 unused imports；pnpm build + pnpm lint 必须双通过才可锁回
- Claude 完成一个端后向 Atlas 报结果，Atlas 独立运行 pnpm build 验证通过才 locked 发下一个
- 4 份功能比对报告已建档（`docs/handoffs/TASK-0099-比对-*.md`），Claude 按原始报告执行，不引入任何虚构 API 或组件
- 前端技术栈：Next.js 15.2.6 + React 19 + TypeScript + shadcn/ui + Tailwind

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
- Phase H 启动时需直接复用 decision `CS1` 容灾框架与交接协议，形成 sim/live 两端一致的断联接管口径

### 6.7 项目架构师

**当前状态：** 全局治理 + 预审为主
**职责范围：**

```
┌─ TASK-0013  统一风控核心设计      ← ✅ 治理闭环
├─ TASK-0012  legacy信号桥接        ← 跨 integrations (待Phase C)
├─ TASK-0011  legacy清退            ← 跨服务清退 (待Phase C/D)
├─ TASK-0039 灾备演练设计+验收      ← ✅ DR1/DR4 已修复; 仅剩 ISSUE-DR3-001 1个P1 Issue [2026-04-11]
├─ TASK-0048 Phase C扩展与总计划修订 ← A0/A1/A2已完成，后续进入服务级拆批
├─ TASK-0049 安全治理横线与统一修复预审 ← A0完成；SG1→SG5 顺序已纳入总计划
├─ CK2 因子双地同步治理             ← `shared/python-common/**` 的后续 P0 预审入口
├─ Phase H1  live-trading 契约      ← shared/contracts (延后)
├─ 所有新任务预审                   ← 持续
└─ 公共项目提示词维护               ← 持续
```

---

## 七、总进度仪表盘 [修订 2026-04-14]

| 模块 | 完成 | 目标 | 当前Phase | 下一里程碑 |
|------|------|------|----------|----------|
| 治理 | 100% | 100% | ✅ 完成 | 维护 |
| sim-trading | 90% | 100% | Phase B ✅ + v1.0.0 安全收口 + SG API认证 ✅ + CS1-S 已完成 | 开盘验证CTP（周一）|  
| decision | **99%** | 100% | Phase C 全闭环 + CK因子同步+SimNow备用 Claude执行+Atlas审核通过 | 维护态；PBO/CPCV 待启动 |
| data | **100%** | 100% | ✅ Phase D + Round 1 收口 + 看板上线 ✅ | **完成** [2026-04-12] |
| backtest | **100%** | 100% | ✅ Phase E + Round 2 安全加固 + 看板上线 ✅ + 审核看板已上线 | **完成** [2026-04-14] |
| dashboard | **25%→100%** | 100% | ✅ Phase F 全闭环 | TASK-0099/0100/0101/0102/0103/F5/0105/0106 全部完成 [2026-04-15] |
| live-trading | 0% | 100% | Phase H | 待 sim-trading 稳定运行 2~3 个月 |
| **总体** | **~98%** | **100%** | **data 100% / backtest 100% / sim-trading 90% / decision 99% / dashboard 100%** | **Phase F 全闭环 ✅ → 待 Studio 同步确认，后续 sim-trading 开盘验证** |

---

## 八、Token 签发待办清单 [修订 2026-04-14]

以下为当前真正需要 Jay.S 签发的批次（已完成项已移除，或已冻结为待拆批）：

> `TASK-0049` 的 A1 两文件最小 Token 已于 2026-04-11 签发并 validate，通过范围仅限 `docs/JBT_FINAL_MASTER_PLAN.md` 与 `ATLAS_PROMPT.md`；后续 SG5 若要进入任何实际修复，必须另起独立任务、白名单与 Token。

| 优先级 | 任务 | 文件数 | Agent | 白名单概要 | 说明 |
|--------|------|--------|-------|-----------|------|
| 🟡 P1 | TASK-0101 | 23 | Claude | dashboard/backtest 6路由+14组件+3 API/hooks | 🟡 执行中（Claude）；Atlas 验证后锁回，发 TASK-0102 |
| ⏳ P1 | TASK-0102 | 25 | Claude | dashboard/decision 6路由+15组件+4 API/hooks | ⏳ tok-1f25eea1 active；待 TASK-0101 locked 后发 |
| ⏳ P1 | TASK-0103 | 21 | Claude | dashboard/data 5路由+12组件+4 API/hooks | ⏳ tok-bcdd740a active；待 TASK-0102 locked 后发 |
| 🟡 P1 | TASK-0039 | 0 | 架构师 | 灾备演练场景脚本 | ✅ DR1~DR4执行完成[2026-04-10]; ISSUE-DR1-001 已由 TASK-0042 修复, ISSUE-DR4-001 已由 TASK-0043 修复, ISSUE-DR3-001 已独立建档为 TASK-0045 |
| 🟡 P1 | TASK-0045 | 3~4 | 架构师 | Mini macOS容器自愈守护基线 | A0建档完成[2026-04-11]; 待A1白名单签发 |
| 🟡 P1 | TASK-0040 | TBD | 决策 | PBO+CPCV+mlfinlab | A0建档完成[2026-04-10]; 待Phase C(C2)启动实施 |
| 🟡 P1 | Phase C 股票研究扩容（CB1/CB4~CB9） | TBD | 决策 | 股票模板/池管理/盘中跟踪/盘后评估/晚间选股/研究页面 | C0/CA/CB/CG/CF 主线已完成；下一步扩容 |
| ✅ 完成 | Phase C 容灾+因子同步（CS1/CK1~CK3） | 13 | 决策+回测+Claude | decision 本地Sim + 因子双地同步 | CS1-S(TASK-0077)+CK1(TASK-0083)+CK2/CK3(TASK-0084) 全部完成 [2026-04-13] |
| ✅ 完成 | TASK-0081/0083 CF1' LLM Pipeline | 7+12 | Claude-Code | decision llm+pipeline+prompts+routes+test+factor_sync+bugfix | TASK-0083 Atlas复核通过; TASK-0081 由TASK-0083完全覆盖 [2026-04-13] |
| ✅ 完成 | TASK-0084 CK2/CK3 因子双地同步 | 7 | Claude | shared/python-common/factors + decision/backtest接线 | Claude执行+Atlas审核通过 [2026-04-13] |
| ✅ 完成 | TASK-0025 SimNow备用方案 | 6 | Claude | decision/publish/failover + executor + dispatcher + tests | Claude执行+Atlas审核通过; 10测试全通过 [2026-04-13] |

### 已完成存档（2026-04-14 清理）

| 状态 | 任务 | 说明 |
|------|------|------|
| ✅ | TASK-0031 | data热修 locked |
| ✅ | TASK-0014 A1-A4 | 风控通知全批locked |
| ✅ | TASK-0009 | 治理闭环 |
| ✅ | TASK-0013 | 治理闭环 |
| ✅ | TASK-0010 | 骨架闭环 |
| ✅ | TASK-0019 B1/B2 | 报表locked |
| ✅ | TASK-0022-B | 只读日志locked |
| ✅ | TASK-0008 A~D | 泛化引擎全批locked |
| ✅ | TASK-0026 A~C | 因子全批locked |
| ✅ | TASK-0007 A~D | 后端并回全批locked |
| ✅ | TASK-0005 | 容器命名locked |
| ✅ | TASK-0018 A~F | 数据API全批locked |
| ✅ | TASK-0028 B1~B6 | 通知系统全批locked |
| ✅ | TASK-0021 A+H0~H7 | 决策迁移全批locked |
| ✅ | TASK-0023-A | 发布接口locked |
| ✅ | TASK-0029/0030 | 治理制度locked |
| ✅ | TASK-0032/0033 | data_web locked |
| ✅ | TASK-0034~0038 | data端U0全部locked |
| ✅ | TASK-0041/0042/0043 | sim/data 运行态收口 locked |
| ✅ | TASK-0048 | Phase C 扩展总计划、ATLAS 与 prompt 口径已同步 |
| ✅ | TASK-0050 | C0-1 股票bars API locked [2026-04-12] |
| ✅ | TASK-0051 | C0-3 策略导入解析器 locked [2026-04-12] |
| ✅ | TASK-0052 | CG1 回测策略导入队列 locked [2026-04-12] |
| ✅ | TASK-0053 | C0-2 FactorLoader股票支持 locked [2026-04-12] |
| ✅ | TASK-0054 | CB5 动态watchlist采集 locked [2026-04-12] |
| ✅ | TASK-0055 | CG2 人工手动回测审核 locked [2026-04-12] |
| ✅ | TASK-0056 | CA2' 期货沙箱回测引擎 locked [2026-04-12] |
| ✅ | TASK-0057 | CB2' 股票沙箱回测引擎 locked [2026-04-12] |
| ✅ | TASK-0058 | CG3 股票手动回测 locked [2026-04-12] |
| ✅ | TASK-0059 | CA6 信号分发投产 locked [2026-04-12] |
| ✅ | TASK-0060 | CA3 回测报告展示导出 locked [2026-04-12] |
| ✅ | TASK-0061 | CA4 交易参数调优引擎 locked [2026-04-12] |
| ✅ | TASK-0062 | CB3 全A股选股引擎 locked [2026-04-12] |
| ✅ | TASK-0063 | CF2 邮件+看板YAML导入 locked [2026-04-12] |
| ✅ | TASK-0083 | 决策端全闭环收尾(LLM Pipeline+Factor Sync+Bug Fix) Atlas复核通过 [2026-04-13] |
| ✅ | TASK-0081 | CF1' LLM Pipeline — 由TASK-0083完全覆盖实现 [2026-04-13] |
| ✅ | TASK-0080 | G0 J_BotQuant工作区切割 — workspace已仅含JBT, legacy容器已清除 [2026-04-13] |
| ✅ | TASK-0082 | Atlas Agent新建 — .github/agents/atlas.agent.md已存在 [2026-04-13] |
| ✅ | TASK-0084 | CK2/CK3 因子双地同步+覆盖率+缺失通知 — Claude执行+Atlas审核通过 [2026-04-13] |
| ✅ | TASK-0025 | SimNow备用方案-仅平仓模式 — Claude执行+Atlas审核通过; 10测试全通过 [2026-04-13] |
| ✅ | TASK-0099 | 统一看板首页框架（47 files）— build+lint ✅，commit bee35c9，tok-3e1c1970 locked [2026-04-14] |
| ✅ | TASK-0100 | sim-trading全功能升级（24 files）— Atlas修复3轮ESLint+类型错误，build+lint ✅，commit 4969642，tok-279d4f99 locked [2026-04-14] |

---

## 九、关键依赖链 [修订 2026-04-11]

```
TASK-0049(安全治理横线) ──> SG1(策略端只读安全检查) ──> SG2(策略端复核冻结) ──> SG3(全域只读安全检查) ──> SG4(全域复核冻结) ──> SG5(统一修复预审与拆批)

TASK-0048(总计划修订) ────────────────┐
                                      ├─> C0-1(data 股票 bars 路由) ──┐
                                      ├─> C0-3(decision 导入解析器) ──┤
                                      └─> C0-2(FactorLoader股票支持) ─┘

C0 前置完成 ────────────────┬─> CA2'(期货沙箱) ──┬─> CA3(报告) ──> CA4(调优) ──> CA5(UI) ──┐
                           │                    │                                             │
                           │                    └─> TASK-0040(PBO) ───────────────────────────┤
                           │                                                                  ├─> CG1/CG2/CG3 人工二次回测关卡 ──> CA6 执行链闭环
                           └─> CB2'(股票沙箱) ──┬─> CB3(选股 benchmark) ──> CB4(股票池) ────┤
                                                ├─> CB5(data watchlist 分钟K) ──────────────┤
                                                ├─> CB6(盘中提醒) ──> CB7(盘后评估) ───────┤
                                                └─> CB8(晚间再选) ──> CB9(股票研究页面) ───┘

CF1'(飞书口头策略) ──┐
                     ├─> C0-3 导入解析器 ──> 双沙箱主链
CF2(邮件/看板 YAML) ─┘

CK1(因子覆盖率 90%+) ──> CK2(双地同步/hash校验) ──> CK3(因子缺失/新增通知)

CS1(decision 本地Sim容灾) ──> CS1-S(sim/live 交接接口) ──> Phase H 复用

TASK-0017(开盘验证) + TASK-0039/0045(DR3 自愈) ──> sim-trading 基线稳定 ──> Phase H 延后启动

dashboard 聚合看板 ──> 继续后置，待 decision/backtest/data 的 Phase C 页面在各自服务内先闭环
```

---

## 十、完成定义（项目收口标准）

当以下条件全部满足时，JBT 项目视为完成收口：

1. **6 个服务全部可独立启动、构建、部署**
2. **6 个服务全部有完整契约在 `shared/contracts/`**
3. **Mini / Studio / Air 三个 JBT 服务部署节点通过 docker-compose.dev.yml 部署，Alienware 作为 Windows 交易端 / 研究节点保持独立在线**
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
