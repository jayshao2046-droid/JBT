# 📊 JBT Studio 看板 API 接入全面分析报告

**生成时间：** 2026-04-14  
**报告人：** Claude Code  
**审核对象：** Atlas 总项目经理  

---

## 一、各端看板现状总览

| 服务端 | 部署位置 | 端口 | 看板状态 | 后端 API 完整度 | 前端接入完整度 |
|--------|---------|------|---------|----------------|---------------|
| **data** | Mini | 8105/3004 | ✅ 已上线 | 95% | 85% |
| **backtest** | Studio | 8103/3001 | ✅ 已上线 | 90% | 75% |
| **decision** | Studio | 8104/3003 | ✅ 已上线 | 85% | 70% |
| **sim-trading** | Mini | 8101/3002 | ✅ 已上线 | 80% | 65% |
| **dashboard** | Studio | 8106/3005 | ❌ 未实施 | 0% | 0% |

---

## 二、各端详细缺失分析

### 🟠 **1. Data 端（Mini 8105/3004）**

#### 后端 API 已有（main.py）：
- ✅ `/health` - 健康检查
- ✅ `/api/v1/version` - 版本信息
- ✅ `/api/v1/symbols` - 可用合约列表
- ✅ `/api/v1/bars` - 期货分钟 K 线
- ✅ `/api/v1/stocks/bars` - 股票分钟 K 线
- ✅ `/api/v1/dashboard/system` - 系统资源监控
- ✅ `/api/v1/dashboard/collectors` - 采集器状态
- ✅ `/api/v1/dashboard/storage` - 存储目录树
- ✅ `/api/v1/dashboard/news` - 新闻聚合
- ✅ `/api/v1/ops/restart-collector` - 运维重启
- ✅ `/api/v1/ops/auto-remediate` - 自动修复

#### 前端页面已有（data_web/app/page.tsx）：
- ✅ 总览（overview）
- ✅ 采集器管理（collectors）
- ✅ 数据浏览（explorer）
- ✅ 新闻资讯（news）
- ✅ 硬件系统（system）
- ✅ 配置设置（settings）

#### ❌ 缺失功能：
1. **实时采集日志流** - 前端需要 WebSocket 或 SSE 推送最新采集日志
2. **采集器手动触发** - 缺少 `/api/v1/ops/trigger-collector` 端点
3. **数据质量检查报告** - 缺少数据完整性、异常值检测 API
4. **历史采集趋势图表** - 缺少时序统计 API（按天/周/月聚合）
5. **告警规则配置** - 缺少告警阈值设置与历史告警查询 API

**建议优先级：P2（data 端已基本完整，缺失为增强功能）**

---

### 🟡 **2. Backtest 端（Studio 8103/3001）**

#### 后端 API 已有（backtest/src/api/app.py）：
- ✅ `/api/health` - 健康检查
- ✅ `/api/v1/health` - 健康检查（v1）
- ✅ `/api/v1/version` - 版本信息
- ✅ `jobs_router` - 回测任务管理
- ✅ `backtest_router` - 回测执行
- ✅ `strategy_router` - 策略管理
- ✅ `support_router` - 支持工具
- ✅ `queue_router` - 队列管理
- ✅ `approval_router` - 审批流程
- ✅ `stock_approval_router` - 股票审批

#### 前端页面已有（backtest_web/app/）：
- ✅ 策略管理（agent-network/page.tsx）
- ✅ 回测详情（operations/page.tsx）
- ✅ 智能分析（intelligence/page.tsx）
- ✅ 参数优化（optimizer/page.tsx）
- ✅ 结果查看（results/page.tsx）
- ✅ 审核看板（review/page.tsx）
- ✅ 指挥中心（command-center/page.tsx）
- ✅ 系统监控（systems/page.tsx）

#### ❌ 缺失功能：
1. **回测进度实时推送** - 前端轮询 `/api/v1/backtest/{id}/progress`，缺少 WebSocket
2. **策略性能对比** - 缺少多策略横向对比 API（Sharpe、最大回撤、胜率对比）
3. **回测报告导出** - 缺少 PDF/Excel 导出端点
4. **历史回测记录查询** - 缺少分页、筛选、排序 API
5. **回测资源使用统计** - 缺少 CPU/内存/磁盘占用时序数据
6. **策略版本管理** - 缺少策略代码版本历史与 diff 查看 API

**建议优先级：P1（回测报告导出、性能对比为高频需求）**

---

### 🔴 **3. Decision 端（Studio 8104/3003）**

#### 后端 API 已有（decision/src/api/app.py）：
- ✅ `/health` - 健康检查
- ✅ `/ready` - 就绪检查
- ✅ `strategy_router` - 策略管理
- ✅ `signal_router` - 信号管理
- ✅ `approval_router` - 审批流程
- ✅ `model_router` - 模型管理
- ✅ `strategy_import_router` - 策略导入
- ✅ `sandbox_router` - 沙箱执行
- ✅ `report_router` - 报告生成
- ✅ `optimizer_router` - 优化器
- ✅ `screener_router` - 选股器
- ✅ `import_channel_router` - 导入通道
- ✅ `stock_template_router` - 股票模板
- ✅ `stock_pool_router` - 股票池（Phase C）
- ✅ `intraday_router` - 盘中追踪（Phase C）
- ✅ `post_market_router` - 盘后评估（Phase C）
- ✅ `evening_rotation_router` - 晚间轮换（Phase C）
- ✅ `pbo_router` - PBO 过拟合检验（Phase C）
- ✅ `local_sim_router` - 本地 Sim 容灾（Phase C）
- ✅ `llm_router` - LLM 管道（CF1'）
- ✅ `decision_web_router` - 看板专用路由

#### 前端页面已有（decision_web/app/）：
- ✅ 总览（overview - page.tsx）
- ✅ 研究中心（research/page.tsx）
- ✅ 参数优化（optimizer/page.tsx）
- ✅ 历史记录（history/page.tsx）
- ✅ 策略导入（import/page.tsx）
- ✅ 报告查看（reports/page.tsx）

#### 前端 API 客户端已有（decision_web/lib/api.ts）：
- ✅ `fetchHealth()` - 健康检查
- ✅ `fetchStrategies()` - 策略列表
- ✅ `fetchSignals()` - 信号列表
- ✅ `fetchRuntimeOverview()` - 运行时总览

#### ❌ 缺失功能（严重）：

**1. 核心页面组件已开发但未挂载路由（5 个）：**
- ❌ 信号审查页面 - 前端有 `signal-review` 组件但未挂载路由
- ❌ 模型与因子页面 - 前端有 `models-factors` 组件但未挂载路由
- ❌ 策略仓库页面 - 前端有 `strategy-repository` 组件但未挂载路由
- ❌ 通知与日报页面 - 前端有 `notifications-report` 组件但未挂载路由
- ❌ 配置与运行页面 - 前端有 `config-runtime` 组件但未挂载路由

**2. Phase C 股票链路前端完全缺失（6 个后端 router 已完成）：**
- ❌ 股票池管理界面（对应 `stock_pool_router`）
- ❌ 盘中信号追踪界面（对应 `intraday_router`）
- ❌ 盘后评估界面（对应 `post_market_router`）
- ❌ 晚间轮换计划界面（对应 `evening_rotation_router`）
- ❌ PBO 过拟合检验界面（对应 `pbo_router`）
- ❌ 本地 Sim 容灾状态界面（对应 `local_sim_router`）

**3. 其他缺失功能：**
- ❌ LLM 管道监控界面 - CF1' 已有后端但无前端展示
- ❌ 实时信号推送 - 缺少 WebSocket 或 SSE 推送新信号
- ❌ 因子贡献度分析 - 缺少因子权重、SHAP 值可视化 API
- ❌ 策略性能实时监控 - 缺少策略收益曲线、回撤实时更新 API

**建议优先级：P0（decision 是核心决策端，缺失最严重）**

---

### 🟡 **4. Sim-Trading 端（Mini 8101/3002）**

#### 后端 API 已有（sim-trading/src/api/router.py）：
- ✅ `/health` - 健康检查
- ✅ `/api/v1/health` - 健康检查（v1）
- ✅ `/api/v1/version` - 版本信息
- ✅ `/api/v1/system/state` - 系统状态
- ✅ `/api/v1/system/pause` - 暂停交易
- ✅ `/api/v1/system/resume` - 恢复交易
- ✅ `/api/v1/ctp/connect` - CTP 连接
- ✅ `/api/v1/ctp/disconnect` - CTP 断开
- ✅ `/api/v1/ctp/config` - CTP 配置
- ✅ `/api/v1/positions` - 持仓查询
- ✅ `/api/v1/orders` - 委托查询
- ✅ `/api/v1/orders/submit` - 下单
- ✅ `/api/v1/orders/cancel` - 撤单
- ✅ `/api/v1/risk/presets` - 风控预设
- ✅ `/api/v1/risk/presets/{symbol}` - 更新风控
- ✅ `/api/v1/market/quote` - 行情查询
- ✅ `/api/v1/market/subscribe` - 订阅行情
- ✅ `/api/v1/ledger/summary` - 账本摘要
- ✅ `/api/v1/ledger/trades` - 成交记录
- ✅ `/api/v1/ledger/daily-report` - 日报

#### 前端页面已有（sim-trading_web/app/）：
- ✅ 风控监控（intelligence/page.tsx）
- ✅ 交易终端（operations/page.tsx）
- ✅ 行情报价（market/page.tsx）
- ✅ 品种风控（risk-presets/page.tsx）
- ✅ CTP 配置（ctp-config/page.tsx）

#### ❌ 缺失功能：
1. **实时持仓 PnL 推送** - 前端轮询 `/api/v1/positions`，缺少 WebSocket
2. **成交明细查询** - 缺少分页、筛选、导出 API
3. **风控事件历史** - 缺少风控拒单、熔断历史记录 API
4. **账户资金曲线** - 缺少净值、权益时序数据 API
5. **策略归因分析** - 缺少按策略分组的盈亏统计 API
6. **行情深度数据** - 缺少五档盘口、逐笔成交 API
7. **CTP 连接日志** - 缺少连接/断开事件历史查询 API

**建议优先级：P1（实时推送、成交明细为高频需求）**

---

### ⚫ **5. Dashboard 统一看板（Studio 8106/3005）**

#### 现状：完全未实施

#### 规划中的功能（来自 ATLAS_PROMPT.md）：
- ❌ 四端服务健康聚合
- ❌ 全局 KPI 仪表盘
- ❌ 跨服务数据流监控
- ❌ 统一告警中心
- ❌ 系统拓扑图
- ❌ 性能瓶颈分析
- ❌ 容量规划建议

**建议优先级：P2（当前各端临时看板已基本满足需求，统一看板可后置）**

---

## 三、各端 KPI 与 API 对比表

### **Data 端 KPI**
| KPI 指标 | 前端展示 | 后端 API | 缺失 |
|---------|---------|---------|------|
| 采集器总数 | ✅ | ✅ `/api/v1/dashboard/collectors` | - |
| 采集成功率 | ✅ | ✅ 同上 | - |
| 数据新鲜度 | ✅ | ✅ 同上 | - |
| 存储占用 | ✅ | ✅ `/api/v1/dashboard/storage` | - |
| CPU/内存 | ✅ | ✅ `/api/v1/dashboard/system` | - |
| 新闻条数 | ✅ | ✅ `/api/v1/dashboard/news` | - |
| 实时日志流 | ❌ | ❌ | WebSocket/SSE |
| 数据质量分数 | ❌ | ❌ | 质量检查 API |

### **Backtest 端 KPI**
| KPI 指标 | 前端展示 | 后端 API | 缺失 |
|---------|---------|---------|------|
| 运行中回测数 | ✅ | ✅ `/api/v1/jobs` | - |
| 回测进度 | ✅ | ✅ `/api/v1/backtest/{id}/progress` | WebSocket 推送 |
| 策略总数 | ✅ | ✅ `/api/v1/strategies` | - |
| 系统资源 | ✅ | ✅ `/api/v1/system/status` | - |
| 策略性能对比 | ❌ | ❌ | 多策略对比 API |
| 回测报告导出 | ❌ | ❌ | PDF/Excel 导出 |
| 历史回测记录 | ⚠️ | ⚠️ | 分页/筛选不完整 |

### **Decision 端 KPI**
| KPI 指标 | 前端展示 | 后端 API | 缺失 |
|---------|---------|---------|------|
| 策略总数 | ✅ | ✅ `/api/v1/strategies` | - |
| 信号总数 | ✅ | ✅ `/api/v1/signals` | - |
| 审批待办 | ✅ | ✅ `/api/v1/approvals` | - |
| 本地模型状态 | ✅ | ✅ `/api/v1/models/runtime` | - |
| 在线模型状态 | ✅ | ✅ 同上 | - |
| 研究窗口状态 | ✅ | ✅ 同上 | - |
| **股票池管理** | ❌ | ✅ `/api/v1/stock/pool` | **前端完全缺失** |
| **盘中信号** | ❌ | ✅ `/api/v1/stock/intraday` | **前端完全缺失** |
| **盘后评估** | ❌ | ✅ `/api/v1/stock/post-market` | **前端完全缺失** |
| **晚间轮换** | ❌ | ✅ `/api/v1/stock/evening-rotation` | **前端完全缺失** |
| **PBO 检验** | ❌ | ✅ `/api/v1/stock/pbo` | **前端完全缺失** |
| **本地 Sim 容灾** | ❌ | ✅ `/api/v1/stock/local-sim` | **前端完全缺失** |
| LLM 管道监控 | ❌ | ✅ `/api/v1/llm` | 前端缺失 |
| 因子贡献度 | ❌ | ❌ | 因子分析 API |
| 实时信号推送 | ❌ | ❌ | WebSocket/SSE |

### **Sim-Trading 端 KPI**
| KPI 指标 | 前端展示 | 后端 API | 缺失 |
|---------|---------|---------|------|
| 持仓数量 | ✅ | ✅ `/api/v1/positions` | - |
| 浮动盈亏 | ✅ | ✅ 同上 | WebSocket 推送 |
| 今日成交笔数 | ✅ | ✅ `/api/v1/ledger/summary` | - |
| 今日盈亏 | ✅ | ✅ 同上 | - |
| CTP 连接状态 | ✅ | ✅ `/api/v1/system/state` | - |
| 全局交易开关 | ✅ | ✅ 同上 | - |
| 风控预设数量 | ✅ | ✅ `/api/v1/risk/presets` | - |
| 成交明细查询 | ❌ | ⚠️ | 分页/筛选不完整 |
| 账户资金曲线 | ❌ | ❌ | 净值时序 API |
| 策略归因分析 | ❌ | ❌ | 按策略分组 API |
| 风控事件历史 | ❌ | ❌ | 风控日志 API |

---

## 四、优先级修复建议

### **P0 - 立即修复（Decision 端）**

#### 1. 挂载缺失的 5 个核心页面路由
在 `decision_web/app/layout.tsx` 或路由配置中添加：
- `/signal-review` → `signal-review` 组件
- `/models-factors` → `models-factors` 组件
- `/strategy-repository` → `strategy-repository` 组件
- `/notifications` → `notifications-report` 组件
- `/config-runtime` → `config-runtime` 组件

**预计工时：1-2 小时**

#### 2. Phase C 股票链路前端全面补齐
创建以下 6 个页面（对接已完成的后端 router）：
- `/stock-pool` 页面（对接 `stock_pool_router`）
  - 显示股票池列表、添加/移除股票、轮换计划
- `/intraday-signals` 页面（对接 `intraday_router`）
  - 显示盘中突破信号、成交量异动、实时追踪
- `/post-market-eval` 页面（对接 `post_market_router`）
  - 显示盘后评级（A-E）、批量评估结果
- `/evening-rotation` 页面（对接 `evening_rotation_router`）
  - 显示多因子打分、轮换计划、执行状态
- `/pbo-validation` 页面（对接 `pbo_router`）
  - 显示 PBO 过拟合检验结果、CSCV 分布图
- `/local-sim-failover` 页面（对接 `local_sim_router`）
  - 显示本地 Sim 容灾状态（STANDBY/ACTIVE/ERROR）

**预计工时：2-3 天**

#### 3. LLM 管道监控页面
创建 `/llm-pipeline` 页面（对接 `llm_router`）：
- 显示 LLM 调用统计、成功率、延迟分布
- 显示本地模型（Ollama）与在线模型（DashScope）状态
- 显示 L1/L2/分析师/研究员四角色调用记录

**预计工时：1 天**

---

### **P1 - 高优先级（Backtest + Sim-Trading）**

#### 1. Backtest 端
- 实现策略性能对比 API（`/api/v1/backtest/compare`）
  - 支持多策略横向对比（Sharpe、最大回撤、胜率、收益曲线）
- 实现回测报告导出 API（`/api/v1/backtest/{id}/export`）
  - 支持 PDF/Excel 格式导出
- 完善历史回测记录分页/筛选 API
  - 支持按策略、时间范围、状态筛选

**预计工时：2-3 天**

#### 2. Sim-Trading 端
- 实现 WebSocket 实时持仓推送（`/ws/positions`）
  - 推送持仓变化、浮动盈亏更新
- 实现成交明细分页查询 API（`/api/v1/ledger/trades?page=&size=`）
  - 支持按时间、合约、方向筛选
- 实现账户资金曲线 API（`/api/v1/ledger/equity-curve`）
  - 返回净值、权益时序数据

**预计工时：2 天**

---

### **P2 - 中优先级（增强功能）**

#### 1. Data 端
- 实现实时日志流 WebSocket（`/ws/logs`）
- 实现数据质量检查 API（`/api/v1/dashboard/data-quality`）

#### 2. Decision 端
- 实现因子贡献度分析 API（`/api/v1/factors/attribution`）
- 实现实时信号推送 WebSocket（`/ws/signals`）

#### 3. Sim-Trading 端
- 实现策略归因分析 API（`/api/v1/ledger/attribution`）
- 实现风控事件历史 API（`/api/v1/risk/events`）

**预计工时：3-4 天**

---

### **P3 - 低优先级（Dashboard 统一看板）**
等待各端临时看板基本收口后再启动

---

## 五、总结与建议

### 当前最严重的问题：Decision 端（Studio 8104/3003）

1. **5 个核心页面组件已开发但未挂载路由**，导致用户无法访问
2. **Phase C 股票链路后端已完成（6 个 router），但前端完全缺失**
3. **LLM 管道（CF1'）后端已完成，但前端无监控界面**

### 建议立即行动：

#### 第一步：快速修复（1-2 小时）
挂载 Decision 端 5 个缺失页面路由，立即恢复用户访问能力

#### 第二步：Phase C 补齐（2-3 天）
完成 Phase C 股票链路 6 个前端页面开发，打通后端已完成的功能

#### 第三步：LLM 监控（1 天）
完成 LLM 管道监控页面，可视化 CF1' 运行状态

#### 预期效果：
完成以上工作后，Decision 端看板完整度可从 **70% → 95%**，成为四端中最完整的看板。

---

## 附录：文件路径参考

### Decision 端关键文件
- 后端路由：`services/decision/src/api/app.py`
- 前端主页：`services/decision/decision_web/app/page.tsx`
- 前端组件：`services/decision/decision_web/components/decision/`
- API 客户端：`services/decision/decision_web/lib/api.ts`
- 侧边栏配置：`services/decision/decision_web/components/layout/sidebar.tsx`

### Phase C 后端路由
- 股票池：`services/decision/src/api/routes/stock_pool.py`
- 盘中追踪：`services/decision/src/api/routes/intraday.py`
- 盘后评估：`services/decision/src/api/routes/post_market.py`
- 晚间轮换：`services/decision/src/api/routes/evening_rotation.py`
- PBO 检验：`services/decision/src/api/routes/pbo.py`
- 本地 Sim：`services/decision/src/api/routes/local_sim.py`
- LLM 管道：`services/decision/src/api/routes/llm.py`

---

**报告结束**
