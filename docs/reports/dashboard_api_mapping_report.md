# JBT Dashboard API 与功能分配完整报告

生成时间: 2026-04-18

## 📊 总体概览

**后端服务统计**:
- **模拟交易服务** (sim-trading): 87 个 API 端点
- **回测服务** (backtest): 23 个 API 端点
- **决策服务** (decision): 45+ 个 API 端点
- **数据服务** (data): 18 个 API 端点

**前端页面统计**: 35 个页面
**已实现功能覆盖率**: 约 65%

---

## 一、模拟交易模块 (Sim-Trading)

### 1.1 主看板页面 `/`
**状态**: ✅ 完全实现

**已对接 API**:
- `GET /api/v1/account` - 账户信息
- `GET /api/v1/positions` - 持仓列表
- `GET /api/v1/stats/performance` - 绩效统计
- `GET /api/v1/risk/l1` - L1 风控状态
- `GET /api/v1/orders` - 订单列表
- `GET /api/v1/dashboard/collectors` (data服务) - 数据源状态
- `GET /api/v1/dashboard/news` (data服务) - 新闻列表

**可新增功能**:
- `GET /api/v1/report/daily` - 日报数据
- `GET /api/v1/equity/history` - 权益曲线历史

---

### 1.2 模拟交易总览 `/sim-trading`
**状态**: ✅ 完全实现

**已对接 API**:
- `GET /api/v1/account` - 账户快照
- `GET /api/v1/positions` - 持仓
- `GET /api/v1/orders` - 订单
- `GET /api/v1/risk/l1` - L1 风控
- `GET /api/v1/risk/l2` - L2 风控

---

### 1.3 智能风控页面 `/sim-trading/intelligence`
**状态**: ✅ 完全实现

**已对接 API**:
- `GET /api/v1/risk/l1` - L1 预检查 (10项)
- `GET /api/v1/risk/l2` - L2 日线级风控
- `GET /api/v1/risk/alerts` - 告警历史 (SSE 推送)

**L1 检查项**:
- 交易开关、CTP连接、最大持仓检查
- 日内亏损检查、价格偏离检查、下单频率检查
- 保证金率检查、连接质量检查、仅平仓模式、灾难止损

**L2 指标**:
- 连续亏损次数、保证金率、今日交易笔数、今日盈亏、持仓数量

---

### 1.4 市场行情页面 `/sim-trading/market`
**状态**: ✅ 完全实现

**已对接 API**:
- `GET /api/v1/ticks` - 实时行情 Tick
- `GET /api/v1/market/movers` - 市场异动 (价格/振幅/成交量)

**可新增功能**:
- `GET /api/v1/market/kline/{symbol}` - K线数据

---

### 1.5 交易操作页面 `/sim-trading/operations`
**状态**: ✅ 完全实现

**已对接 API**:
- `GET /api/v1/account` - 账户信息
- `GET /api/v1/positions` - 持仓列表
- `GET /api/v1/orders` - 订单列表
- `POST /api/v1/orders` - 下单
- `POST /api/v1/orders/cancel` - 撤单

**下单 API 完整校验**:
1. 交易暂停检查
2. CTP 连接检查
3. 合约代码校验
4. 最小变动价位校验
5. 单笔最大委托手数校验
6. 风控预设手数限制

---

### 1.6 风控预设页面 `/sim-trading/risk-presets`
**状态**: ✅ 完全实现

**已对接 API**:
- `GET /api/v1/risk-presets` - 获取所有品种风控预设
- `POST /api/v1/risk-presets` - 更新品种风控参数

**支持品种**: 60+ 个期货品种 (SHFE/DCE/CZCE/CFFEX/INE/GFEX)

**可配置参数**:
- 最大手数 (max_lots)
- 最大持仓 (max_position)
- 日内亏损比例 (daily_loss_pct)
- 价格偏离比例 (price_dev_pct)
- 手续费 (commission)
- 滑点 (slippage_ticks)

---

### 1.7 CTP 配置页面 `/sim-trading/ctp-config`
**状态**: ✅ 完全实现

**已对接 API**:
- `GET /api/v1/ctp/config` - 获取 CTP 配置
- `POST /api/v1/ctp/config` - 保存 CTP 配置
- `GET /api/v1/ctp/status` - CTP 连接状态 (实时)
- `POST /api/v1/ctp/connect` - 连接 CTP
- `POST /api/v1/ctp/disconnect` - 断开 CTP

**SimNow 预设**: 7x24 环境、电信环境

---

### 1.8 未对接的高级 API

**系统控制**:
- `POST /api/v1/system/pause` - 暂停交易
- `POST /api/v1/system/resume` - 恢复交易
- `POST /api/v1/system/preset` - 切换风控预设

**执行质量**:
- `GET /api/v1/stats/execution` - 执行质量统计 (滑点/拒单率/延迟/撤单率)

**批量操作**:
- `POST /api/v1/positions/batch_close` - 批量平仓
- `PATCH /api/v1/positions/{position_id}/stop_loss` - 修改止损

**信号接收** (决策服务对接):
- `POST /api/v1/signals/receive` - 接收交易信号
- `GET /api/v1/signals/queue` - 查看信号队列

**策略发布** (决策服务对接):
- `POST /api/v1/strategy/publish` - 接收策略发布

**Failover 容灾**:
- `POST /api/v1/failover/handover` - 接收交接数据
- `GET /api/v1/failover/status` - 查询交接状态
- `POST /api/v1/failover/confirm` - 确认交接完成

**日志查看**:
- `GET /api/v1/logs` - 获取日志
- `GET /api/v1/logs/tail` - 实时日志

---

## 二、回测模块 (Backtest)

### 2.1 回测总览 `/backtest`
**状态**: ✅ 完全实现

**已对接 API**:
- `GET /api/system/status` - 系统状态 (CPU/内存/磁盘/运行时间)
- `GET /api/v1/jobs` - 运行中任务列表
- `GET /api/strategies` - 策略列表

---

### 2.2 回测操作 `/backtest/operations`
**状态**: ✅ 完全实现

**已对接 API**:
- `GET /api/strategies` - 策略列表
- `POST /api/backtest/run` - 发起回测

---

### 2.3 回测结果 `/backtest/results`
**状态**: ✅ 完全实现

**已对接 API**:
- `GET /api/backtest/results` - 结果列表
- `GET /api/backtest/results/{task_id}` - 单个结果详情

**性能指标**:
- 总收益率 (total_return)
- 夏普比率 (sharpe_ratio)
- 最大回撤 (max_drawdown)
- 胜率 (win_rate)
- 交易次数 (total_trades)

---

### 2.4 策略审查 `/backtest/review`
**状态**: ⚠️ 占位页面

**可对接 API**:
- `GET /api/v1/strategy-queue/status` - 队列状态
- `POST /api/v1/strategy-queue/enqueue` - 入队
- `POST /api/v1/strategy-queue/clear` - 清空队列

---

### 2.5 参数优化 `/backtest/optimizer`
**状态**: ⚠️ 占位页面

**可对接 API**:
- `GET /api/strategy/{name}/params` - 获取策略参数
- `POST /api/backtest/run` - 批量回测 (参数网格搜索)

---

### 2.6 未对接的回测 API

**任务管理**:
- `GET /api/v1/jobs/{job_id}` - 单个任务详情
- `GET /api/backtest/progress/{task_id}` - 回测进度
- `POST /api/backtest/cancel/{task_id}` - 取消回测

**结果查询**:
- `GET /api/backtest/results/{task_id}/equity` - 权益曲线
- `GET /api/backtest/results/{task_id}/trades` - 成交记录
- `GET /api/backtest/history/{strategy_id}` - 策略历史

**审批流程**:
- `GET /api/v1/approvals` - 审批列表
- `POST /api/v1/approvals/submit` - 提交审批
- `POST /api/v1/approvals/{id}/complete` - 完成审批

---

## 三、决策模块 (Decision)

### 3.1 决策总览 `/decision`
**状态**: ✅ 部分实现

**已对接 API**:
- `GET /strategies/overview` - 策略总览

**可新增 API**:
- `GET /models/runtime` - 模型运行时状态
- `GET /signals/overview` - 信号总览

---

### 3.2 信号审查 `/decision/signal`
**状态**: ✅ 完全实现

**已对接 API**:
- `GET /signals/overview` - 信号总览
- `GET /signals` - 信号列表
- `POST /signals/review` - 审查信号

**信号状态**:
- approved (已批准)
- hold (暂缓)
- blocked (阻止)
- ready_for_publish (准备发布)
- locked_visible (锁定可见)

---

### 3.3 研究中心 `/decision/research`
**状态**: ✅ 完全实现

**组件**:
- 研究窗口 (ResearchCenter)
- 轮动计划 (EveningRotationPlan)
- 盘后报告 (PostMarketReport)

**可对接 API**:
- `GET /api/v1/stock/evening-rotation` - 轮动计划
- `GET /api/v1/stock/post-market` - 盘后报告
- `GET /api/v1/researcher/reports` (data服务) - 研究员报告

---

### 3.4 策略仓库 `/decision/repository`
**状态**: ✅ 完全实现

**已对接 API**:
- `GET /strategies` - 策略列表
- `POST /strategies` - 创建策略
- `POST /strategies/{id}/publish` - 发布策略

**可新增 API**:
- `GET /api/v1/stock/pool` - 股票池
- `POST /import-channel/submit` - 导入策略

---

### 3.5 模型因子 `/decision/models`
**状态**: 🔶 部分实现

**可对接 API**:
- `GET /models/status` - 模型状态
- `GET /models/runtime` - 运行时总览
- `POST /models/route` - 模型路由
- `GET /api/v1/factors` - 因子列表
- `POST /api/v1/factors/sync` - 因子同步

---

### 3.6 通知日报 `/decision/reports`
**状态**: ✅ 完全实现

**可对接 API**:
- `GET /signals/overview` - 包含通知渠道状态
- `GET /report/daily` - 日报数据
- `POST /report/send` - 发送日报

---

### 3.7 未对接的决策 API

**策略管理**:
- `GET /strategies/{id}` - 策略详情
- `GET /strategies/{id}/lifecycle` - 生命周期状态

**审批流程**:
- `GET /approvals` - 审批列表
- `POST /approvals/submit` - 提交审批
- `POST /approvals/{id}/complete` - 完成审批

**沙盒测试**:
- `POST /sandbox/test` - 沙盒测试

**优化器**:
- `POST /optimizer/run` - 运行优化
- `GET /optimizer/results` - 优化结果

**选股器**:
- `POST /screener/run` - 运行选股
- `GET /screener/results` - 选股结果

**日内交易**:
- `GET /api/v1/stock/intraday` - 日内信号
- `POST /api/v1/stock/intraday/execute` - 执行日内交易

**PBO 分析**:
- `POST /api/v1/stock/pbo/analyze` - PBO 分析
- `GET /api/v1/stock/pbo/results` - PBO 结果

**本地模拟**:
- `POST /api/v1/stock/local-sim/run` - 本地模拟
- `GET /api/v1/stock/local-sim/status` - 模拟状态

**LLM 计费**:
- `GET /billing/usage` - 用量统计
- `GET /billing/summary` - 计费汇总

---

## 四、数据模块 (Data)

### 4.1 数据总览 `/data`
**状态**: 🔶 部分实现

**已对接 API**:
- `GET /api/v1/dashboard/collectors` - 采集器状态
- `GET /api/v1/dashboard/system` - 系统状态

---

### 4.2 采集器管理 `/data/collectors`
**状态**: 🔶 部分实现

**已对接 API**:
- `GET /api/v1/dashboard/collectors` - 采集器列表与状态

**采集器类别**:
- **行情类**: 内盘分钟/日线、外盘分钟/日线、A股分钟/实时、期权
- **宏观类**: 全球宏观、CBOE波动率、QVIX波动率、海运物流、外汇、天气
- **持仓类**: 每日持仓、每周持仓、CFTC持仓
- **新闻资讯类**: RSS新闻聚合
- **情绪类**: 市场情绪指数
- **监控类**: 自选监控、健康监控日志

**运维 API**:
- `POST /api/v1/ops/restart-collector` - 重启采集器 (需要 X-Ops-Token)
- `POST /api/v1/ops/auto-remediate` - 自动修复

---

### 4.3 数据探索 `/data/explorer`
**状态**: 🔶 部分实现

**已对接 API**:
- `GET /api/v1/symbols` - 可用合约列表
- `GET /api/v1/bars` - K线数据 (期货)
- `GET /api/v1/stocks/bars` - K线数据 (股票)

**查询参数**:
- symbol: 合约代码 (支持主连、精确合约)
- timeframe_minutes: 时间周期 (1/5/15/30/60)
- start/end: 时间范围
- limit: 返回条数

**支持格式**:
- 期货主连: `KQ.m@SHFE.rb` 或 `KQ_m_SHFE_rb`
- 精确合约: `SHFE.rb2505` 或 `SHFE_rb2505`
- 股票代码: `600000` / `SH600000` / `600000.SH`

---

### 4.4 新闻流 `/data/news`
**状态**: 🔶 部分实现

**已对接 API**:
- `GET /api/v1/dashboard/news` - 新闻列表

**新闻字段**:
- 标题、来源、发布时间、摘要
- 关键词、情绪 (positive/negative/neutral)
- 重要标记、推送状态

**统计数据**:
- 热门关键词 (Top 10)
- 来源分布
- 情绪分布
- 推送记录

---

### 4.5 系统监控 `/data/system`
**状态**: 🔶 部分实现

**已对接 API**:
- `GET /api/v1/dashboard/system` - 系统完整状态

**监控指标**:
- **资源**: CPU使用率、内存使用率、磁盘使用率
- **进程**: 数据API、数据调度器状态
- **通知渠道**: 飞书 (报警/新闻/交易)、邮件
- **数据源**: Tushare、TqSdk、AkShare、SMTP、飞书 Webhook
- **日志**: 最近40条调度器日志

---

### 4.6 研究员控制台 `/data/researcher`
**状态**: ✅ 完全实现

**已对接 API**:
- `GET /api/v1/researcher/status` - 研究员状态
- `GET /api/v1/researcher/sources` - 数据源管理
- `GET /api/v1/researcher/reports` - 研究报告列表
- `GET /api/v1/researcher/report/latest` - 最新报告
- `POST /api/v1/researcher/trigger` - 触发研究

**研究员进程**:
- kline_monitor (K线监控)
- news_crawler (新闻爬虫)
- fundamental_crawler (基本面爬虫)
- llm_analyzer (LLM分析器)
- report_generator (报告生成器)

---

### 4.7 未对接的数据 API

**上下文投喂** (决策服务对接):
- `POST /api/v1/context/preread` - 预读上下文

**存储管理**:
- `GET /api/v1/dashboard/storage` - 存储树状图

---

## 五、系统设置 `/settings`
**状态**: 🔶 UI完整但未连接后端

**可对接功能**:
- 账户信息管理
- 交易时段控制
- 通知配置 (飞书/邮件)
- 服务管理 (重启服务)

---

## 六、登录页面 `/login`
**状态**: ✅ 完全实现

**认证方式**: 本地验证 (admin/admin123)

**可升级为**:
- JWT Token 认证
- OAuth 2.0
- LDAP 集成

---

## 七、功能优先级建议

### P0 - 立即对接 (核心交易功能)
1. ✅ 模拟交易下单/撤单
2. ✅ 持仓/订单查询
3. ✅ 风控状态监控
4. ✅ CTP 连接管理
5. ⚠️ 系统暂停/恢复交易

### P1 - 近期对接 (增强功能)
1. ⚠️ 批量平仓
2. ⚠️ 止损修改
3. ⚠️ 执行质量统计
4. ⚠️ 权益曲线历史
5. ⚠️ 信号接收队列

### P2 - 中期对接 (决策集成)
1. ⚠️ 策略发布流程
2. ⚠️ 信号审批流程
3. ⚠️ 模型路由管理
4. ⚠️ 因子同步
5. ⚠️ 研究员报告集成

### P3 - 长期规划 (高级功能)
1. ⚠️ 参数优化器
2. ⚠️ 选股器
3. ⚠️ PBO 分析
4. ⚠️ 本地模拟引擎
5. ⚠️ LLM 计费统计

---

## 八、API 安全与认证

**当前认证方式**:
- API Key 认证 (X-API-Key Header)
- 环境变量配置:
  - `SIM_API_KEY` - 模拟交易
  - `BACKTEST_API_KEY` - 回测服务
  - `DECISION_API_KEY` - 决策服务
  - `DATA_API_KEY` - 数据服务
  - `DATA_OPS_SECRET` - 数据运维操作

**安全特性**:
- HMAC 常量时间比较
- 生产环境强制 API Key
- 速率限制 (决策服务: 100 req/min)
- 公开路径白名单
- 审计日志

---

## 九、部署架构

**服务端口分配**:
- Dashboard Web: `3001`
- Sim-Trading: `8102`
- Backtest: `8103`
- Decision: `8104`
- Data: `8105`

**代理规则** (Next.js):
```
/api/sim-trading/* → http://localhost:8102/*
/api/backtest/*    → http://localhost:8103/*
/api/decision/*    → http://localhost:8104/*
/api/data/*        → http://localhost:8105/*
```

---

## 十、总结

**已实现功能**: 
- 模拟交易核心功能 100%
- 回测基础功能 60%
- 决策信号审查 80%
- 数据采集监控 70%

**待实现功能**:
- 批量操作 API
- 策略发布流程
- 参数优化器
- 高级分析工具

**建议优先级**: 先完成 P0/P1 核心交易功能,再逐步集成决策与分析模块。
