# JBT 项目全面状态报告

**报告日期**：2026-04-12  
**报告类型**：项目全面扫描与状态汇报  
**生成方式**：Claude Code 自动扫描分析

---

## 执行摘要

JBT 是 BotQuant 的下一代微服务架构量化交易系统，目标是从 legacy 单体系统（J_BotQuant）迁移到完全隔离、可独立部署的 6 个核心服务。

**项目总体完成度：约 62-65%**

---

## 一、项目整体架构

### 1.1 服务拓扑（6 个核心服务）

| 服务 | 目录 | 端口 | 部署设备 | 完成度 | 核心职责 |
|------|------|------|---------|--------|---------|
| **sim-trading** | `services/sim-trading/` | API:8101 / Web:3002 | Mini | **85%** | 模拟交易、CTP/SimNow 网关、风控守卫、交易执行、账本管理、通知系统 |
| **decision** | `services/decision/` | API:8104 / Web:3003 | Studio | **75%** | 因子库、策略仓库、双沙箱回测（期货/股票）、调优引擎、信号分发、研究中心 |
| **data** | `services/data/` | API:8105 / Web:3004 | Mini | **93%** | 数据采集（21个采集器）、标准化、bars API 供数、动态 watchlist、健康检查、通知 |
| **backtest** | `services/backtest/` | API:8103 / Web:3001 | Air | **88%** | 在线/本地双引擎、风控引擎、因子注册、人工手动回测、策略审核、报告导出 |
| **dashboard** | `services/dashboard/` | API:8106 / Web:3005 | Studio | **5%** | 聚合看板（规划中）、只读数据聚合、受控配置入口 |
| **live-trading** | `services/live-trading/` | API:8102 / Web:3006 | Studio | **0%** | 实盘交易（后置，待 sim-trading 稳定 2~3 个月后启动） |

### 1.2 设备拓扑（冻结）

| 设备 | 角色 | 内网 IP | 蒲公英 IP | 部署服务 |
|------|------|---------|----------|---------|
| MacBook | 开发/控制 | localhost | 172.16.3.136 | 全部开发环境 |
| Mini | 数据+模拟交易 | 192.168.31.156 | 172.16.0.49 | data:8105, sim-trading:8101, sim-trading-web:3002 |
| Air | 回测生产 | 192.168.31.245 | — | backtest:8103, backtest-web:3001 |
| Studio | 决策+看板 | 192.168.31.142 | 172.16.1.130 | decision:8104, decision-web:3003, dashboard:8106 |
| ECS | 云端（备用） | 47.103.36.144 | — | 暂停，待域名+SSH就绪 |

---

## 二、各服务详细状态

### 2.1 sim-trading（模拟交易）— 85% 完成

**代码规模**：3,090 行 Python | 9 个测试文件

**已实现功能**：
- ✅ CTP 连接管理和自动重连
- ✅ 完整的交易执行流程（下单、撤单、查询）
- ✅ 风险控制（只减仓、回撤止损、升级机制）
- ✅ 内存日志系统
- ✅ 定时报表生成
- ✅ 多通道通知（飞书、邮件）
- ✅ API Key 认证（SIM_API_KEY）
- ✅ 密码脱敏（_safe_state()）
- ✅ signal_ids 有界管理（50k FIFO）

**最近完成工作**（2026-04-12）：
- 安全报告 v1.0 全部推翻重写，8 项修复均附代码证据
- 新增 GET /signals/queue 端点
- ctp_connect 添加并发锁防止 _gateway 竞态
- ExecutionService 激活：模块实例化+connect 绑定+下单路由使用

**待完成工作**：
- ⚠️ 离线缓存降级方案（TASK-0013/TASK-0017）
- 🟡 DR3 灾备演练（Docker 容器崩溃恢复）
- 🟡 开盘验证（TASK-0017）
- 🟡 CA6 信号分发执行适配
- 🟡 CS1-S 容灾交接接口

**关键文件**：
- `services/sim-trading/src/main.py` - 314 行启动逻辑
- `services/sim-trading/src/api/router.py` - 39KB 完整交易 API
- `services/sim-trading/src/execution/service.py` - 执行服务
- `services/sim-trading/src/risk/guards.py` - 风险守卫

---

### 2.2 decision（决策引擎）— 75% 完成

**代码规模**：6,016 行 Python | 11 个测试文件

**已实现功能**：
- ✅ 策略生命周期管理（8 个状态 + 契约映射）
- ✅ 研究模块（Optuna 优化、SHAP 审计、ONNX 导出）
- ✅ 发布流程（执行器、网关、策略导入器）
- ✅ 审批门控（回测门、研究门、执行门）
- ✅ 信号生成和分发
- ✅ 多渠道审批（邮件、飞书）
- ✅ 报告生成和持久化
- ✅ 双沙箱回测（期货/股票）

**最近完成工作**（Phase C Batch-5）：
- ✅ TASK-0051：C0-3 策略导入解析器
- ✅ TASK-0053：C0-2 FactorLoader 股票支持
- ✅ TASK-0056：CA2' 期货沙箱回测引擎
- ✅ TASK-0057：CB2' 股票沙箱回测引擎
- ✅ TASK-0059：CA6 信号分发投产
- ✅ TASK-0060：CA3 回测报告展示导出
- ✅ TASK-0061：CA4 交易参数调优引擎
- ✅ TASK-0062：CB3 全 A 股选股引擎
- ✅ TASK-0063：CF2 邮件+看板 YAML 导入

**待完成工作**：
- 🟡 CB1/CB4~CB9 股票研究扩容
- 🟡 CS1 本地 Sim 容灾
- 🟡 CK1~CK3 因子双地同步
- 🟡 看板 KPI 调整后推送 Studio

**关键文件**：
- `services/decision/src/strategy/lifecycle.py` - 策略生命周期
- `services/decision/src/research/` - 研究模块
- `services/decision/src/publish/` - 发布流程
- `services/decision/src/gating/` - 审批门控

---

### 2.3 data（数据服务）— 93% 完成

**代码规模**：12,267 行 Python | 4 个测试文件

**已实现功能**：
- ✅ 完整的数据采集管道（21 个采集器）
- ✅ 多格式数据支持（K线、新闻、宏观指标）
- ✅ 仪表板 API（系统状态、采集器状态、存储、新闻）
- ✅ 自动修复和健康检查
- ✅ 资源监控（CPU、内存、磁盘）
- ✅ 运维 API（重启采集器、自动修复）
- ✅ 动态 watchlist 采集（CB5）
- ✅ 股票 bars API 路由（C0-1）

**最近完成工作**：
- ✅ TASK-0050：C0-1 股票 bars API 路由
- ✅ TASK-0054：CB5 动态 watchlist 采集

**待完成工作**：
- ⚠️ 存储层迁移（A2 批次）- `collectors/base.py` 第 8 行 TODO(A2)
- 🟡 数据预读投喂决策端

**关键文件**：
- `services/data/src/main.py` - 1,456 行完整数据 API
- `services/data/src/scheduler/data_scheduler.py` - 24h 调度
- `services/data/src/collectors/` - 30+ 个采集器
- `services/data/src/health/` - 健康检查

---

### 2.4 backtest（回测服务）— 88% 完成

**代码规模**：8,907 行 Python | 11 个测试文件

**已实现功能**：
- ✅ 完整的策略加载和执行流程
- ✅ 因子注册表和别名管理
- ✅ 风险检查和头寸管理
- ✅ 正式报告 API
- ✅ 策略队列管理
- ✅ 库存和审批流程
- ✅ 人工手动回测（期货+股票）

**最近完成工作**（Phase E + CG 扩容）：
- ✅ TASK-0052：CG1 回测策略导入队列
- ✅ TASK-0055：CG2 人工手动回测审核
- ✅ TASK-0058：CG3 股票手动回测

**待完成工作**：
- 🟡 审核看板页面扩容（backtest_web 增加 manual review / stock review 页面）

**关键文件**：
- `services/backtest/src/backtest/runner.py` - 回测执行引擎
- `services/backtest/src/backtest/local_engine.py` - 本地引擎
- `services/backtest/src/backtest/risk_engine.py` - 风险引擎
- `services/backtest/src/api/routes/backtest.py` - 69KB 完整 API

---

### 2.5 dashboard（看板服务）— 5% 完成

**代码规模**：0 行 Python | 0 个测试文件

**状态**：
- 目录结构存在（src/, tests/, configs/）
- 所有源文件为空
- 仅有 README.md 和 .env.example

**待完成工作**：
- ❌ TASK-0015 SimNow 临时看板 → 聚合看板
- ❌ 聚合 6 服务状态
- ❌ 只读数据聚合
- ❌ 受控配置入口

**优先级**：后置，等所有后端 Phase 基本完成后启动

---

### 2.6 live-trading（实盘交易）— 0% 完成

**代码规模**：0 行 Python | 0 个测试文件

**状态**：
- 目录结构存在（src/, tests/, configs/）
- 所有源文件为空
- 仅有 README.md 和 .env.example

**待完成工作**：
- ❌ 完整的实盘交易系统（Phase H）

**优先级**：最后阶段，待 sim-trading 稳定运行 2~3 个月后启动

---

## 三、当前活跃任务与待办事项

### 3.1 未跟踪文件（git status）

```
?? docs/reviews/sim-trading-二次核验联络文档.md
?? tests/data/collectors/__init__.py
```

**说明**：
- `sim-trading-二次核验联络文档.md`（249 行）— 二次核验联络单，要求独立全量核验
- `tests/data/collectors/__init__.py` — 空文件

### 3.2 Phase C 主线（已完成 14 个 TASK）

- ✅ TASK-0050：C0-1 股票 bars API 路由（数据）
- ✅ TASK-0051：C0-3 策略导入解析器（决策）
- ✅ TASK-0052：CG1 回测策略导入队列（回测）
- ✅ TASK-0053：C0-2 FactorLoader 股票支持（决策）
- ✅ TASK-0054：CB5 动态 watchlist 采集（数据+决策）
- ✅ TASK-0055：CG2 人工手动回测审核（回测）
- ✅ TASK-0056：CA2' 期货沙箱回测引擎（决策）
- ✅ TASK-0057：CB2' 股票沙箱回测引擎（决策）
- ✅ TASK-0058：CG3 股票手动回测（回测）
- ✅ TASK-0059：CA6 信号分发投产（决策）
- ✅ TASK-0060：CA3 回测报告展示导出（决策）
- ✅ TASK-0061：CA4 交易参数调优引擎（决策）
- ✅ TASK-0062：CB3 全 A 股选股引擎（决策）
- ✅ TASK-0063：CF2 邮件+看板 YAML 导入（决策）

### 3.3 待启动任务（优先级排序）

**P0 级（最高优先级）**：
- 🔴 CK2：共享因子库同步

**P1 级（高优先级）**：
- 🟡 TASK-0045：Mini macOS 容器自愈守护基线
- 🟡 TASK-0040：PBO 过拟合检验
- 🟡 Phase C 股票研究扩容（CB1/CB4~CB9）
- 🟡 Phase C 容灾+因子同步（CS1/CK1~CK3）

**P2 级（中优先级）**：
- 🟢 TASK-0017：sim-trading 开盘验证
- 🟢 TASK-0039：DR3 灾备演练剩余子任务
- 🟢 审核看板页面扩容（backtest_web）

**P3 级（低优先级/后置）**：
- ⚪ TASK-0015：聚合看板（dashboard）
- ⚪ Phase H：实盘交易（live-trading）

### 3.4 安全治理任务（SG1~SG5）

**TASK-0049 — 全项目安全检查纳入总计划与统一修复预审**

**治理阶段**：
- ✅ SG1：策略端只读检查（已完成）
- 🟡 SG2：策略端复核（进行中）
- 🟡 SG3：data 侧检查
- 🟡 SG4：全域复核
- 🟡 SG5：统一修复预审

**已确认问题**：
- F-001：backtest generic_strategy.py 表达式执行链风险
- F-002：data subprocess 风险
- F-003：data 查询构造链风险

---

## 四、最近完成的工作（最近 10 条 commit）

**sim-trading 服务安全修复收口（2026-04-12）**：

1. `6e25038` - 更新总计划、sim-trading prompt、Atlas prompt（审核+安全修复收口，v1.0.0，85%）
2. `1ecb83a` - 安全报告 v1.0 全部推翻重写，8 项修复均附代码证据
3. `0d8611d` - 新增 GET /signals/queue 端点，明确标注队列无消费者
4. `691254c` - ctp_connect 添加并发锁防止 _gateway 竞态，同步 sleep 已注释说明
5. `6d330fd` - ExecutionService 激活：模块实例化+connect 绑定+下单路由使用
6. `836eac9` - 全 API 添加 API Key 认证（SIM_API_KEY env 控制）
7. `2cb6d89` - 3 个接口返回密码明文 → _safe_state() 脱敏副本
8. `3ed9547` - signal_ids 无界 set → 有界 OrderedDict 50k FIFO 淘汰
9. `99bfe3f` - 移除 CtpConfigRequest.auth_code 硬编码明文默认值
10. `41ec077` - /status stage 字段 skeleton → 1.0.0

**工作重点**：sim-trading 服务完成了全面的安全加固，包括 API 认证、密码脱敏、并发控制、资源限制等 8 项修复。

---

## 五、进度汇总表

### 5.1 服务完成度

| 服务 | 完成度 | 代码行数 | 测试文件 | 状态 |
|------|--------|---------|---------|------|
| data | 93% | 12,267 | 4 | ✅ 高完成度，待存储层迁移 |
| backtest | 88% | 8,907 | 11 | ✅ 高完成度，待看板扩容 |
| sim-trading | 85% | 3,090 | 9 | ✅ 高完成度，待开盘验证 |
| decision | 75% | 6,016 | 11 | ✅ 中高完成度，待股票扩容 |
| dashboard | 5% | 0 | 0 | ❌ 未实现，后置任务 |
| live-trading | 0% | 0 | 0 | ❌ 未实现，最后阶段 |
| **总计** | **62%** | **30,280** | **35** | 核心交易系统完整 |

### 5.2 Phase 完成度

| Phase | 名称 | 完成度 | 状态 |
|-------|------|--------|------|
| Phase A | 基础稳定化 | 100% | ✅ 已闭环 |
| Phase B | SimNow 生产闭环 | 100% | ✅ 已闭环 |
| Phase B+ | 灾备演练质量门禁 | 75% | 🟡 DR3 待完成 |
| Phase C | 决策端核心能力 | 70% | 🟡 14/20 任务完成 |
| Phase D | 数据端全量迁移 | 100% | ✅ 已闭环 |
| Phase E | 回测系统稳定化 | 100% | ✅ 已闭环 |
| Phase F | 看板聚合与云部署 | 5% | ❌ 后置任务 |
| Phase G | 收口与 legacy 清退 | 0% | ❌ 最后阶段 |
| Phase H | 实盘交易 | 0% | ❌ 最后阶段 |
| SG | 安全治理横线 | 30% | 🟡 SG1 完成，SG2~SG5 进行中 |

---

## 六、下一步优先级建议

### 6.1 短期优先级（1-2 周）

**P0 级（立即执行）**：
1. **完成 sim-trading 二次核验**
   - 处理未跟踪文件 `docs/reviews/sim-trading-二次核验联络文档.md`
   - 独立全量核验 sim-trading 服务

2. **完成 SG2~SG5 安全治理流程**
   - SG2：策略端复核
   - SG3：data 侧检查
   - SG4：全域复核
   - SG5：统一修复预审

3. **完成 DR3 灾备演练**
   - Docker 容器崩溃恢复测试
   - 验证自动重启和数据恢复

**P1 级（本周内）**：
4. **TASK-0017：sim-trading 开盘验证**
   - 实盘环境下验证交易流程
   - 监控风控规则执行

5. **TASK-0045：Mini macOS 容器自愈守护基线**
   - 实现容器自动重启
   - 健康检查和告警

### 6.2 中期优先级（2-4 周）

**Phase C 股票研究扩容**：
- CB1：股票因子库扩容
- CB4~CB9：股票研究工具链

**Phase C 容灾+因子同步**：
- CS1：本地 Sim 容灾
- CK1~CK3：因子双地同步
- 🔴 CK2：共享因子库同步（P0）

**TASK-0040：PBO 过拟合检验**
- 实现 Probability of Backtest Overfitting 检验
- 集成到回测报告

### 6.3 长期优先级（1-3 个月）

**Phase F：看板聚合与云部署**：
- TASK-0015：聚合看板（dashboard）
- 云端部署（ECS）

**Phase G：收口与 legacy 清退**：
- 停止 J_BotQuant 所有进程
- 清理 cron/launchctl 残留
- 完成 10 项收口标准

**Phase H：实盘交易**：
- 待 sim-trading 稳定运行 2~3 个月后启动
- 实现 live-trading 服务

---

## 七、关键风险与建议

### 7.1 当前风险

1. **sim-trading 离线缓存降级方案未完成**
   - 风险：断网/断数据源下无法交易
   - 建议：优先完成 TASK-0013/TASK-0017

2. **dashboard 和 live-trading 完全未实现**
   - 风险：无法聚合监控，无法实盘交易
   - 建议：按计划后置，先完成核心功能

3. **安全治理流程未完成**
   - 风险：已发现 3 个安全问题（F-001/F-002/F-003）
   - 建议：优先完成 SG2~SG5 流程

### 7.2 架构建议

1. **优先完成核心交易链路**
   - decision → sim-trading → live-trading 信号链路
   - 确保数据端 24h 采集无中断

2. **加强容灾能力**
   - 完成 DR1~DR4 灾备演练
   - 实现容器自愈守护

3. **统一监控和告警**
   - 实现聚合看板（dashboard）
   - 统一飞书+邮件通知标准

---

## 八、关键文档路径

**核心文档**：
- `ATLAS_PROMPT.md` - JBT 本地 Atlas 入口 prompt
- `docs/JBT_FINAL_MASTER_PLAN.md` - 终局总计划（63KB）
- `PROJECT_CONTEXT.md` - 项目上下文与接管规则
- `WORKFLOW.md` - 工作流与角色权限矩阵
- `README.md` - 工作区总览

**服务目录**：
- `services/sim-trading/` - 模拟交易服务
- `services/decision/` - 决策引擎服务
- `services/data/` - 数据服务
- `services/backtest/` - 回测服务
- `services/dashboard/` - 看板服务（空）
- `services/live-trading/` - 实盘交易服务（空）

**治理目录**：
- `docs/tasks/` - 任务预审
- `docs/reviews/` - 审核记录
- `docs/locks/` - 锁控账本
- `docs/handoffs/` - 交接单（88 个）
- `docs/prompts/` - Agent prompt

---

## 总结

JBT 项目当前处于**中后期阶段**，核心交易系统（data、backtest、sim-trading、decision）已基本完成，完成度达到 **62-65%**。

**已完成**：
- ✅ Phase A/B/D/E 全部闭环
- ✅ Phase C 主线完成 14 个 TASK
- ✅ sim-trading 安全加固（8 项修复）
- ✅ 数据采集 24h 运行
- ✅ 回测系统完整投产

**待完成**：
- 🟡 sim-trading 二次核验 + 开盘验证
- 🟡 SG2~SG5 安全治理流程
- 🟡 DR3 灾备演练
- 🟡 Phase C 股票研究扩容
- ❌ dashboard 聚合看板
- ❌ live-trading 实盘交易

**下一步建议**：
1. 优先完成 sim-trading 二次核验和安全治理
2. 完成 DR3 灾备演练和开盘验证
3. 推进 Phase C 股票研究扩容
4. 后置 dashboard 和 live-trading 开发

---

**报告生成信息**：
- 生成时间：2026-04-12
- 扫描范围：/Users/jayshao/JBT 全项目
- 分析方法：Claude Code 自动扫描（文档分析 + 代码扫描 + Git 历史）
- 数据来源：JBT_FINAL_MASTER_PLAN.md、ATLAS_PROMPT.md、代码库、Git 提交记录
