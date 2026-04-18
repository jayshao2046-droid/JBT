# Dashboard 页面完成任务拆分计划

**任务编号**: TASK-DASHBOARD-001  
**创建时间**: 2026-04-18  
**优先级**: P0 (核心功能)  
**预计工期**: 5-7 个工作日

---

## 📋 任务总览

**目标**: 完成 Dashboard 所有页面的 API 对接与功能实现

**当前状态**:
- ✅ 已完成: 18/35 页面 (51%)
- 🔶 部分完成: 10/35 页面 (29%)
- ⚠️ 待开发: 7/35 页面 (20%)

---

## 🎯 批次划分

### 批次 1: P0 核心交易功能增强 (1-2天)
**目标**: 完善模拟交易模块的高级功能

#### 任务 1.1: 主看板增强
- [ ] 对接 `GET /api/v1/equity/history` - 权益曲线历史
- [ ] 对接 `GET /api/v1/report/daily` - 日报数据
- [ ] 添加权益曲线图表组件
- [ ] 添加日报摘要卡片

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/page.tsx`
- `services/dashboard/dashboard_web/lib/api/sim-trading.ts`
- `services/dashboard/dashboard_web/components/dashboard/equity-chart.tsx` (新建)
- `services/dashboard/dashboard_web/components/dashboard/daily-report-card.tsx` (新建)

**验收标准**:
- 权益曲线正确显示最近30天数据
- 日报卡片显示当日交易汇总
- 数据刷新间隔 30 秒

---

#### 任务 1.2: 市场行情 K 线图
- [ ] 对接 `GET /api/v1/market/kline/{symbol}` - K线数据
- [ ] 实现 K 线图表组件 (使用 recharts 或 lightweight-charts)
- [ ] 添加时间周期切换 (1m/5m/15m/30m/60m)
- [ ] 添加合约选择器

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/sim-trading/market/page.tsx`
- `services/dashboard/dashboard_web/lib/api/sim-trading.ts`
- `services/dashboard/dashboard_web/components/market/kline-chart.tsx` (新建)

**验收标准**:
- K 线图正确显示 OHLC 数据
- 支持时间周期切换
- 支持合约切换

---

#### 任务 1.3: 系统控制功能
- [ ] 对接 `POST /api/v1/system/pause` - 暂停交易
- [ ] 对接 `POST /api/v1/system/resume` - 恢复交易
- [ ] 在主看板添加紧急暂停按钮
- [ ] 添加暂停原因输入对话框
- [ ] 添加暂停状态全局提示

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/page.tsx`
- `services/dashboard/dashboard_web/lib/api/sim-trading.ts`
- `services/dashboard/dashboard_web/components/dashboard/emergency-stop-button.tsx` (新建)

**验收标准**:
- 暂停按钮醒目且需要二次确认
- 暂停后全局显示警告横幅
- 恢复交易需要确认操作

---

#### 任务 1.4: 批量操作功能
- [ ] 对接 `POST /api/v1/positions/batch_close` - 批量平仓
- [ ] 对接 `PATCH /api/v1/positions/{position_id}/stop_loss` - 修改止损
- [ ] 在持仓列表添加批量选择功能
- [ ] 添加批量平仓确认对话框
- [ ] 添加止损修改对话框

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/sim-trading/operations/page.tsx`
- `services/dashboard/dashboard_web/lib/api/sim-trading.ts`
- `services/dashboard/dashboard_web/components/trading/batch-close-dialog.tsx` (新建)
- `services/dashboard/dashboard_web/components/trading/stop-loss-dialog.tsx` (新建)

**验收标准**:
- 支持多选持仓
- 批量平仓显示进度
- 止损修改实时生效

---

#### 任务 1.5: 执行质量统计
- [ ] 对接 `GET /api/v1/stats/execution` - 执行质量统计
- [ ] 创建执行质量页面或卡片
- [ ] 显示滑点、拒单率、延迟、撤单率等指标
- [ ] 添加趋势图表

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/sim-trading/page.tsx`
- `services/dashboard/dashboard_web/lib/api/sim-trading.ts`
- `services/dashboard/dashboard_web/components/trading/execution-quality-card.tsx` (新建)

**验收标准**:
- 显示平均滑点、拒单率、平均延迟、撤单率
- 数据每分钟刷新

---

### 批次 2: 回测模块完善 (1天)

#### 任务 2.1: 策略审查页面
- [ ] 对接 `GET /api/v1/strategy-queue/status` - 队列状态
- [ ] 对接 `POST /api/v1/strategy-queue/enqueue` - 入队
- [ ] 对接 `POST /api/v1/strategy-queue/clear` - 清空队列
- [ ] 实现队列管理界面
- [ ] 添加策略入队表单

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/backtest/review/page.tsx`
- `services/dashboard/dashboard_web/lib/api/backtest.ts`

**验收标准**:
- 显示队列中的策略列表
- 支持添加策略到队列
- 支持清空队列

---

#### 任务 2.2: 参数优化器页面
- [ ] 对接 `GET /api/strategy/{name}/params` - 获取策略参数
- [ ] 对接 `POST /api/backtest/run` - 批量回测
- [ ] 实现参数网格配置界面
- [ ] 添加优化结果对比表格
- [ ] 添加参数热力图

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/backtest/optimizer/page.tsx`
- `services/dashboard/dashboard_web/lib/api/backtest.ts`
- `services/dashboard/dashboard_web/components/backtest/param-grid.tsx` (新建)
- `services/dashboard/dashboard_web/components/backtest/result-heatmap.tsx` (新建)

**验收标准**:
- 支持配置参数范围和步长
- 显示所有参数组合的回测结果
- 支持按指标排序

---

#### 任务 2.3: 回测详情增强
- [ ] 对接 `GET /api/backtest/results/{task_id}/equity` - 权益曲线
- [ ] 对接 `GET /api/backtest/results/{task_id}/trades` - 成交记录
- [ ] 对接 `GET /api/backtest/progress/{task_id}` - 回测进度
- [ ] 对接 `POST /api/backtest/cancel/{task_id}` - 取消回测
- [ ] 在结果页面添加详情查看功能

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/backtest/results/page.tsx`
- `services/dashboard/dashboard_web/lib/api/backtest.ts`
- `services/dashboard/dashboard_web/components/backtest/result-detail-dialog.tsx` (新建)

**验收标准**:
- 点击结果可查看详情
- 显示权益曲线和成交记录
- 支持取消运行中的回测

---

### 批次 3: 决策模块集成 (1-2天)

#### 任务 3.1: 决策总览完善
- [ ] 对接 `GET /models/runtime` - 模型运行时状态
- [ ] 对接 `GET /signals/overview` - 信号总览
- [ ] 完善 Overview 组件
- [ ] 添加模型状态卡片
- [ ] 添加信号统计卡片

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/decision/page.tsx`
- `services/dashboard/dashboard_web/lib/api/decision.ts`
- `services/dashboard/dashboard_web/components/decision/overview.tsx`

**验收标准**:
- 显示策略总数、信号总数、模型状态
- 显示待审批数量
- 数据实时刷新

---

#### 任务 3.2: 模型因子页面完善
- [ ] 对接 `GET /models/status` - 模型状态
- [ ] 对接 `GET /models/runtime` - 运行时总览
- [ ] 对接 `POST /models/route` - 模型路由
- [ ] 对接 `GET /api/v1/factors` - 因子列表
- [ ] 对接 `POST /api/v1/factors/sync` - 因子同步
- [ ] 完善 ModelsFactors 和 FactorAnalysis 组件

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/decision/models/page.tsx`
- `services/dashboard/dashboard_web/lib/api/decision.ts`
- `services/dashboard/dashboard_web/components/decision/models-factors.tsx`
- `services/dashboard/dashboard_web/components/decision/factor-analysis.tsx`

**验收标准**:
- 显示所有模型状态
- 显示因子列表和同步状态
- 支持手动触发因子同步

---

#### 任务 3.3: 研究中心集成
- [ ] 对接 `GET /api/v1/stock/evening-rotation` - 轮动计划
- [ ] 对接 `GET /api/v1/stock/post-market` - 盘后报告
- [ ] 对接 `GET /api/v1/researcher/reports` (data服务) - 研究员报告
- [ ] 完善 ResearchCenter、EveningRotationPlan、PostMarketReport 组件

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/decision/research/page.tsx`
- `services/dashboard/dashboard_web/lib/api/decision.ts`
- `services/dashboard/dashboard_web/components/decision/research-center.tsx`
- `services/dashboard/dashboard_web/components/decision/evening-rotation-plan.tsx`
- `services/dashboard/dashboard_web/components/decision/post-market-report.tsx`

**验收标准**:
- 显示研究员最新报告
- 显示轮动计划
- 显示盘后报告

---

#### 任务 3.4: 策略仓库完善
- [ ] 对接 `GET /api/v1/stock/pool` - 股票池
- [ ] 对接 `POST /import-channel/submit` - 导入策略
- [ ] 完善 StrategyRepository、StrategyImport、StockPoolTable 组件

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/decision/repository/page.tsx`
- `services/dashboard/dashboard_web/lib/api/decision.ts`
- `services/dashboard/dashboard_web/components/decision/strategy-repository.tsx`
- `services/dashboard/dashboard_web/components/decision/strategy-import.tsx`
- `services/dashboard/dashboard_web/components/decision/stock-pool-table.tsx`

**验收标准**:
- 显示股票池列表
- 支持导入策略
- 显示策略详情

---

### 批次 4: 数据模块完善 (1天)

#### 任务 4.1: 数据总览页面
- [ ] 完善 OverviewPage 组件
- [ ] 显示采集器汇总统计
- [ ] 显示系统资源使用情况
- [ ] 添加快速操作入口

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/data/page.tsx`
- `services/dashboard/dashboard_web/components/data/overview-page.tsx`

**验收标准**:
- 显示采集器成功/失败/延迟/空闲数量
- 显示 CPU/内存/磁盘使用率
- 提供快速跳转链接

---

#### 任务 4.2: 采集器管理完善
- [ ] 完善 CollectorsPage 组件
- [ ] 添加采集器分类筛选
- [ ] 添加采集器搜索功能
- [ ] 添加批量重启功能

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/data/collectors/page.tsx`
- `services/dashboard/dashboard_web/components/data/collectors-page.tsx`

**验收标准**:
- 支持按类别筛选
- 支持搜索采集器
- 支持批量重启

---

#### 任务 4.3: 数据探索器完善
- [ ] 完善 DataExplorer 组件
- [ ] 添加合约搜索功能
- [ ] 添加 K 线图表
- [ ] 添加数据导出功能

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/data/explorer/page.tsx`
- `services/dashboard/dashboard_web/components/data/data-explorer.tsx`

**验收标准**:
- 支持搜索合约
- 显示 K 线图表
- 支持导出 CSV

---

#### 任务 4.4: 新闻流完善
- [ ] 完善 NewsFeed 组件
- [ ] 添加新闻筛选功能 (来源/情绪/重要性)
- [ ] 添加新闻搜索功能
- [ ] 添加新闻详情查看

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/data/news/page.tsx`
- `services/dashboard/dashboard_web/components/data/news-feed.tsx`

**验收标准**:
- 支持按来源/情绪/重要性筛选
- 支持搜索新闻
- 点击可查看详情

---

#### 任务 4.5: 系统监控完善
- [ ] 完善 SystemMonitor 组件
- [ ] 添加资源使用趋势图
- [ ] 添加进程管理功能
- [ ] 添加日志实时查看

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/data/system/page.tsx`
- `services/dashboard/dashboard_web/components/data/system-monitor.tsx`

**验收标准**:
- 显示资源使用趋势
- 支持重启进程
- 实时显示日志

---

### 批次 5: 系统设置与高级功能 (1天)

#### 任务 5.1: 系统设置后端对接
- [ ] 创建设置 API 客户端
- [ ] 对接账户信息管理
- [ ] 对接交易时段控制
- [ ] 对接通知配置
- [ ] 对接服务管理

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/settings/page.tsx`
- `services/dashboard/dashboard_web/lib/api/settings.ts` (新建)

**验收标准**:
- 支持修改账户信息
- 支持配置交易时段
- 支持配置通知渠道
- 支持重启服务

---

#### 任务 5.2: 日志查看功能
- [ ] 对接 `GET /api/v1/logs` - 获取日志
- [ ] 对接 `GET /api/v1/logs/tail` - 实时日志
- [ ] 创建日志查看页面或组件
- [ ] 添加日志筛选功能 (级别/来源)
- [ ] 添加日志搜索功能

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/logs/page.tsx` (新建)
- `services/dashboard/dashboard_web/lib/api/sim-trading.ts`
- `services/dashboard/dashboard_web/components/logs/log-viewer.tsx` (新建)

**验收标准**:
- 显示最近日志
- 支持按级别/来源筛选
- 支持搜索日志
- 支持实时刷新

---

#### 任务 5.3: 信号接收队列
- [ ] 对接 `POST /api/v1/signals/receive` - 接收交易信号
- [ ] 对接 `GET /api/v1/signals/queue` - 查看信号队列
- [ ] 创建信号队列页面
- [ ] 添加信号详情查看
- [ ] 添加手动执行功能

**文件清单**:
- `services/dashboard/dashboard_web/app/(dashboard)/signals/page.tsx` (新建)
- `services/dashboard/dashboard_web/lib/api/sim-trading.ts`
- `services/dashboard/dashboard_web/components/signals/signal-queue.tsx` (新建)

**验收标准**:
- 显示信号队列
- 显示信号详情
- 支持手动执行信号

---

## 📊 进度跟踪

### 批次完成情况
- [ ] 批次 1: P0 核心交易功能增强 (0/5)
- [ ] 批次 2: 回测模块完善 (0/3)
- [ ] 批次 3: 决策模块集成 (0/4)
- [ ] 批次 4: 数据模块完善 (0/5)
- [ ] 批次 5: 系统设置与高级功能 (0/3)

### 总体进度
- **总任务数**: 20 个子任务
- **已完成**: 0
- **进行中**: 0
- **待开始**: 20

---

## 🔒 治理规则

**执行前置条件**:
1. 每个批次需要在 `docs/tasks/` 创建独立任务文件
2. 每个批次需要项目架构师预审
3. 每个批次需要 Jay.S 签发文件级 Token
4. 只读诊断可以先行,写操作必须等待 Token

**批次收口流程**:
1. 完成后调用 `append_atlas_log` 写入批次摘要
2. 停止,等待 Atlas 复审
3. Atlas 确认 → 项目架构师终审 → 独立 commit

---

## 📝 备注

1. **优先级**: 按批次顺序执行,P0 批次优先
2. **依赖关系**: 批次 3 依赖批次 1 的部分功能
3. **测试要求**: 每个批次完成后需要手动测试所有新增功能
4. **文档更新**: 完成后更新 API 映射报告

---

**创建人**: Claude (Kiro)  
**审批人**: 待 Atlas 分配  
**预计开始时间**: 待 Token 签发
