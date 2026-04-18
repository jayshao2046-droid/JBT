# TASK-DASHBOARD-001 最终执行方案

**任务编号**: TASK-DASHBOARD-001  
**创建时间**: 2026-04-18  
**修订版本**: v2.0 (基于 Atlas 评估修订)  
**优先级**: P0 (核心功能)  
**预计工期**: 6-8 个工作日

---

## 📋 Atlas 评估结论

**总体判断**: 计划基本可执行，但需收窄范围并调整优先级

**关键发现**:
1. ✅ **批次 3 (决策模块) 大部分已实现** - 工作量可缩减 60-70%
2. ✅ **批次 4 (数据模块) 核心功能已完成** - 只需增强而非重建
3. ⚠️ **批次 1 部分 API 客户端已存在** - 只需 UI 组件
4. ⚠️ **写操作需 Jay.S 确认** - 暂停/恢复/批量平仓等

---

## 🔍 代码核实结果

### 已实现组件确认

| 组件 | 路径 | 状态 | 说明 |
|------|------|------|------|
| Overview | `components/decision/overview.tsx` | ✅ 完整实现 | 已对接 strategyOverview + runtimeOverview，含 KPI、运行时状态、研究窗口 |
| ModelsFactors | `components/decision/models-factors.tsx` | ✅ 完整实现 | 已对接模型路由器、因子同步状态、本地/在线模型列表 |
| OverviewPage | `components/data/overview-page.tsx` | ✅ 完整实现 | 已对接采集器汇总、资源监控、日志展示 |
| CollectorsPage | `components/data/collectors-page.tsx` | ✅ 完整实现 | 已有分类筛选、搜索、重启功能 |

### API 客户端核实

| API 方法 | 文件 | 状态 | 说明 |
|---------|------|------|------|
| `pauseTrading` | `lib/api/sim-trading.ts:124` | ✅ 已实现 | POST /system/pause |
| `resumeTrading` | `lib/api/sim-trading.ts:130` | ✅ 已实现 | POST /system/resume |
| `batchClosePositions` | `lib/api/sim-trading.ts:212` | ✅ 已实现 | POST /positions/batch_close |
| `getExecutionStats` | `lib/api/sim-trading.ts:159` | ✅ 已实现 | GET /stats/execution |
| `getMarketKline` | `lib/api/sim-trading.ts:163` | ✅ 已实现 | GET /market/kline/{symbol} |

---

## 🎯 修订后的批次计划

### 批次 1: P0 核心交易功能增强 (2-3天)

#### 任务 1.1: 主看板权益曲线 ✅ 可执行
**工作量**: 0.5 天

**实施内容**:
- [ ] 对接 `GET /api/v1/equity/history` API
- [ ] 创建 `components/dashboard/equity-chart.tsx` 组件
- [ ] 在主看板嵌入权益曲线图表

**文件清单**:
- `app/(dashboard)/page.tsx` (修改)
- `lib/api/sim-trading.ts` (新增 API 方法)
- `components/dashboard/equity-chart.tsx` (新建)

**验收标准**:
- 显示最近 30 天权益曲线
- 支持时间范围切换
- 数据每 30 秒刷新

---

#### 任务 1.2: 市场行情 K 线图 ✅ 可执行
**工作量**: 1.5 天

**实施内容**:
- [ ] 创建 `components/market/kline-chart.tsx` K 线图组件
- [ ] 添加时间周期切换 (1m/5m/15m/30m/60m)
- [ ] 添加合约选择器
- [ ] 在市场行情页面嵌入

**文件清单**:
- `app/(dashboard)/sim-trading/market/page.tsx` (修改)
- `components/market/kline-chart.tsx` (新建)
- `components/market/symbol-selector.tsx` (新建)

**技术选型**: 使用 `lightweight-charts` 库

**验收标准**:
- K 线图正确显示 OHLC 数据
- 支持时间周期切换
- 支持合约切换
- 支持缩放和平移

---

#### 任务 1.3: 系统控制 UI 组件 ⚠️ 需 Jay.S 确认写操作授权
**工作量**: 0.5 天

**实施内容**:
- [ ] 创建 `components/dashboard/emergency-stop-button.tsx` 紧急暂停按钮
- [ ] 添加暂停原因输入对话框
- [ ] 添加暂停状态全局横幅
- [ ] 在主看板嵌入

**文件清单**:
- `app/(dashboard)/page.tsx` (修改)
- `components/dashboard/emergency-stop-button.tsx` (新建)
- `components/dashboard/trading-status-banner.tsx` (新建)

**前置条件**: ⚠️ **需 Jay.S 确认 Dashboard 是否允许发起暂停/恢复交易**

**验收标准**:
- 暂停按钮醒目且需要二次确认
- 暂停后全局显示警告横幅
- 恢复交易需要确认操作

---

#### 任务 1.4: 批量操作 UI 组件 ⚠️ 需 Jay.S 确认写操作授权
**工作量**: 1 天

**实施内容**:
- [ ] 在持仓列表添加批量选择功能
- [ ] 创建 `components/trading/batch-close-dialog.tsx` 批量平仓对话框
- [ ] 创建 `components/trading/stop-loss-dialog.tsx` 止损修改对话框
- [ ] 对接 `PATCH /positions/{id}/stop_loss` API (需确认后端是否实现)

**文件清单**:
- `app/(dashboard)/sim-trading/operations/page.tsx` (修改)
- `lib/api/sim-trading.ts` (新增 updateStopLoss 方法)
- `components/trading/batch-close-dialog.tsx` (新建)
- `components/trading/stop-loss-dialog.tsx` (新建)

**前置条件**: ⚠️ **需 Jay.S 确认 Dashboard 是否允许发起批量平仓/止损修改**

**验收标准**:
- 支持多选持仓
- 批量平仓显示进度
- 止损修改实时生效

---

#### 任务 1.5: 执行质量统计卡片 ✅ 可执行
**工作量**: 0.5 天

**实施内容**:
- [ ] 创建 `components/trading/execution-quality-card.tsx` 组件
- [ ] 在模拟交易总览页面嵌入
- [ ] 显示滑点、拒单率、延迟、撤单率等指标

**文件清单**:
- `app/(dashboard)/sim-trading/page.tsx` (修改)
- `components/trading/execution-quality-card.tsx` (新建)

**验收标准**:
- 显示平均滑点、拒单率、平均延迟、撤单率
- 数据每分钟刷新

---

### 批次 2: 回测模块完善 (1.5-2天)

#### 任务 2.1: 策略审查页面 ✅ 可执行
**工作量**: 0.5 天

**实施内容**:
- [ ] 对接 `GET /api/v1/strategy-queue/status` API
- [ ] 对接 `POST /api/v1/strategy-queue/enqueue` API
- [ ] 对接 `POST /api/v1/strategy-queue/clear` API
- [ ] 实现队列管理界面

**文件清单**:
- `app/(dashboard)/backtest/review/page.tsx` (修改)
- `lib/api/backtest.ts` (已有方法，确认对接)

**验收标准**:
- 显示队列中的策略列表
- 支持添加策略到队列
- 支持清空队列

---

#### 任务 2.2: 参数优化器页面 (简化版) ✅ 可执行
**工作量**: 1 天

**实施内容**:
- [ ] 对接 `GET /api/strategy/{name}/params` API
- [ ] 实现参数网格配置界面
- [ ] 添加优化结果对比表格 (不含热力图)
- [ ] 支持按指标排序

**文件清单**:
- `app/(dashboard)/backtest/optimizer/page.tsx` (修改)
- `lib/api/backtest.ts` (确认 API 方法)
- `components/backtest/param-grid.tsx` (新建)
- `components/backtest/result-table.tsx` (新建)

**简化说明**: Atlas 建议将热力图降为 P1，先用表格展示

**验收标准**:
- 支持配置参数范围和步长
- 显示所有参数组合的回测结果
- 支持按指标排序

---

#### 任务 2.3: 回测详情增强 ✅ 可执行
**工作量**: 0.5 天

**实施内容**:
- [ ] 对接 `GET /api/backtest/results/{task_id}/equity` API
- [ ] 对接 `GET /api/backtest/results/{task_id}/trades` API
- [ ] 对接 `GET /api/backtest/progress/{task_id}` API
- [ ] 对接 `POST /api/backtest/cancel/{task_id}` API
- [ ] 创建详情查看对话框

**文件清单**:
- `app/(dashboard)/backtest/results/page.tsx` (修改)
- `lib/api/backtest.ts` (确认 API 方法)
- `components/backtest/result-detail-dialog.tsx` (新建)

**验收标准**:
- 点击结果可查看详情
- 显示权益曲线和成交记录
- 支持取消运行中的回测

---

### 批次 3: 决策模块补缺 (0.5-1天) ⚠️ 大幅缩减

**Atlas 评估**: 决策模块大部分已实现，只需补缺和验证

#### 任务 3.1: 决策模块验证与补缺 ✅ 可执行
**工作量**: 0.5 天

**实施内容**:
- [ ] 验证 Overview 组件数据连接
- [ ] 验证 ModelsFactors 组件数据连接
- [ ] 验证 ResearchCenter 组件数据连接
- [ ] 验证 StrategyRepository 组件数据连接
- [ ] 补充缺失的错误处理和加载状态

**文件清单**:
- `components/decision/overview.tsx` (验证)
- `components/decision/models-factors.tsx` (验证)
- `components/decision/research-center.tsx` (验证)
- `components/decision/strategy-repository.tsx` (验证)

**验收标准**:
- 所有组件正确显示数据
- 错误处理完善
- 加载状态友好

---

### 批次 4: 数据模块增强 (0.5-1天) ⚠️ 大幅缩减

**Atlas 评估**: 数据模块核心功能已完成，只需增强

#### 任务 4.1: 数据探索器 K 线图增强 ✅ 可执行
**工作量**: 0.5 天

**实施内容**:
- [ ] 在 DataExplorer 组件添加 K 线图
- [ ] 添加数据导出功能 (CSV)

**文件清单**:
- `components/data/data-explorer.tsx` (修改)
- `components/data/kline-chart.tsx` (复用 market 组件)

**验收标准**:
- 显示 K 线图表
- 支持导出 CSV

---

### 批次 5: 系统设置对接 (0.5-1天)

#### 任务 5.1: 系统设置后端对接 ✅ 可执行
**工作量**: 0.5 天

**实施内容**:
- [ ] 创建 `lib/api/settings.ts` API 客户端
- [ ] 对接账户信息管理
- [ ] 对接交易时段控制
- [ ] 对接通知配置

**文件清单**:
- `app/(dashboard)/settings/page.tsx` (修改)
- `lib/api/settings.ts` (新建)

**验收标准**:
- 支持修改账户信息
- 支持配置交易时段
- 支持配置通知渠道

---

## 📊 修订后的工作量估算

| 批次 | 原估算 | 修订后 | 变化 | 说明 |
|------|--------|--------|------|------|
| 批次 1 | 3 天 | 2-3 天 | 持平 | API 客户端已有，只需 UI 组件 |
| 批次 2 | 2 天 | 1.5-2 天 | -0.5 天 | 简化参数优化器 |
| 批次 3 | 2 天 | 0.5-1 天 | **-1 天** | 大部分已实现，只需验证 |
| 批次 4 | 1 天 | 0.5-1 天 | -0.5 天 | 核心功能已完成 |
| 批次 5 | 1 天 | 0.5-1 天 | -0.5 天 | 简化范围 |
| **总计** | **9 天** | **6-8 天** | **-2 天** | 更符合实际 |

---

## ⚠️ 执行前置条件

### 必须完成的确认事项

- [ ] **Jay.S 确认写操作授权** - Dashboard 是否允许发起暂停/恢复/批量平仓等写操作
- [ ] **后端 API 可用性扫描** - 验证所有计划中的 API 端点是否已实现
- [ ] **批次独立建档** - 为每个批次创建独立任务文件 (TASK-DASHBOARD-001-B1.md 等)
- [ ] **项目架构师预审** - 审查技术方案并冻结白名单
- [ ] **Jay.S 按批次签发 Token** - 文件级白名单 Token

### 后端 API 待验证清单

需要通过 curl/httpie 验证以下 API 是否已实现：

**Sim-Trading**:
- [ ] `GET /api/v1/equity/history` - 权益曲线历史
- [ ] `PATCH /api/v1/positions/{id}/stop_loss` - 修改止损

**Decision**:
- [ ] `GET /models/status` - 模型状态
- [ ] `GET /api/v1/factors` - 因子列表
- [ ] `POST /api/v1/factors/sync` - 因子同步
- [ ] `GET /api/v1/stock/evening-rotation` - 轮动计划
- [ ] `GET /api/v1/stock/post-market` - 盘后报告
- [ ] `GET /api/v1/stock/pool` - 股票池

**Data**:
- [ ] `GET /api/v1/context/preread` - 上下文投喂

---

## 🔒 治理约束

### Dashboard 定位铁律

**调度提示词明确**: "dashboard 定位为最终只读聚合控制面，不直接承担交易写操作"

**写操作清单** (需 Jay.S 明确授权):
1. 暂停/恢复交易 (批次 1.3)
2. 批量平仓 (批次 1.4)
3. 修改止损 (批次 1.4)

**建议**: 如果 Jay.S 不授权写操作，则批次 1.3 和 1.4 改为"只读查看"模式，不提供操作按钮。

### 文件级 Token 要求

每个批次需要独立签发 Token，不得合并：

**批次 1 文件清单** (~10 个文件):
- `app/(dashboard)/page.tsx`
- `app/(dashboard)/sim-trading/market/page.tsx`
- `app/(dashboard)/sim-trading/operations/page.tsx`
- `lib/api/sim-trading.ts`
- `components/dashboard/equity-chart.tsx` (新建)
- `components/dashboard/emergency-stop-button.tsx` (新建)
- `components/dashboard/trading-status-banner.tsx` (新建)
- `components/market/kline-chart.tsx` (新建)
- `components/market/symbol-selector.tsx` (新建)
- `components/trading/batch-close-dialog.tsx` (新建)
- `components/trading/stop-loss-dialog.tsx` (新建)
- `components/trading/execution-quality-card.tsx` (新建)

**批次 2 文件清单** (~6 个文件):
- `app/(dashboard)/backtest/review/page.tsx`
- `app/(dashboard)/backtest/optimizer/page.tsx`
- `app/(dashboard)/backtest/results/page.tsx`
- `lib/api/backtest.ts`
- `components/backtest/param-grid.tsx` (新建)
- `components/backtest/result-table.tsx` (新建)
- `components/backtest/result-detail-dialog.tsx` (新建)

**批次 3 文件清单** (~4 个文件):
- `components/decision/overview.tsx`
- `components/decision/models-factors.tsx`
- `components/decision/research-center.tsx`
- `components/decision/strategy-repository.tsx`

**批次 4 文件清单** (~2 个文件):
- `components/data/data-explorer.tsx`
- `components/data/kline-chart.tsx` (新建)

**批次 5 文件清单** (~2 个文件):
- `app/(dashboard)/settings/page.tsx`
- `lib/api/settings.ts` (新建)

---

## 📝 批次收口流程

每个批次完成后：

1. ✅ 调用 `append_atlas_log` 写入批次摘要到 `ATLAS_PROMPT.md`
2. ⏸️ 停止，等待 Atlas 复审
3. ✅ Atlas 确认 → 项目架构师终审 → 锁回
4. ✅ 独立 commit (格式: `feat(dashboard): 批次 N - 功能描述`)
5. ✅ 同步到 Mini/Studio (如需要)

---

## 🎯 优先级调整建议

### P0 - 立即执行 (必须完成)
1. ✅ 批次 1.1 - 主看板权益曲线
2. ✅ 批次 1.2 - 市场行情 K 线图
3. ✅ 批次 1.5 - 执行质量统计
4. ✅ 批次 2.1 - 策略审查页面
5. ✅ 批次 2.3 - 回测详情增强

### P1 - 近期执行 (重要但非紧急)
1. ⚠️ 批次 1.3 - 系统控制 (需授权)
2. ⚠️ 批次 1.4 - 批量操作 (需授权)
3. ✅ 批次 2.2 - 参数优化器
4. ✅ 批次 3.1 - 决策模块验证
5. ✅ 批次 5.1 - 系统设置对接

### P2 - 后续优化 (可延后)
1. 批次 4.1 - 数据探索器增强
2. 参数优化器热力图
3. 日志查看独立页面
4. 信号接收队列页面 (建议删除)

---

## 📌 关键风险提示

### 1. 后端 API 存在性未验证
**风险**: 部分 API 端点可能尚未在后端实现  
**缓解**: 执行前先做 API 可用性扫描，标记 404 的端点

### 2. 写操作授权未明确
**风险**: Dashboard 写操作可能违反"只读聚合"定位  
**缓解**: 等待 Jay.S 明确授权后再执行批次 1.3 和 1.4

### 3. 组件实现状态不明确
**风险**: 部分组件可能已部分实现但未完全连接  
**缓解**: 批次 3 和 4 先做验证，再决定是否需要补充

### 4. K 线图组件复杂度高
**风险**: K 线图是批次 1 最耗时的任务  
**缓解**: 使用成熟的 `lightweight-charts` 库，减少自研工作量

---

## ✅ 执行准备清单

### Atlas 需要完成
- [ ] 审查本方案并确认可执行
- [ ] 为每个批次创建独立任务文件
- [ ] 协调 Jay.S 确认写操作授权
- [ ] 协调项目架构师预审

### Livis (我) 需要完成
- [ ] 后端 API 可用性扫描 (生成 API 可用性矩阵)
- [ ] 批次 3 和 4 的代码验证 (确认实际工作量)
- [ ] 技术方案细化 (K 线图组件设计)
- [ ] 依赖库调研 (lightweight-charts 使用方案)

### Jay.S 需要确认
- [ ] Dashboard 是否允许发起暂停/恢复交易
- [ ] Dashboard 是否允许发起批量平仓
- [ ] Dashboard 是否允许修改持仓止损
- [ ] 按批次签发文件级 Token

---

## 📅 建议执行顺序

### 第一阶段 (2-3天) - P0 核心功能
1. 批次 1.1 - 主看板权益曲线
2. 批次 1.2 - 市场行情 K 线图
3. 批次 1.5 - 执行质量统计

### 第二阶段 (1.5-2天) - 回测完善
4. 批次 2.1 - 策略审查页面
5. 批次 2.3 - 回测详情增强
6. 批次 2.2 - 参数优化器

### 第三阶段 (1-2天) - 验证与补缺
7. 批次 3.1 - 决策模块验证
8. 批次 5.1 - 系统设置对接
9. 批次 4.1 - 数据探索器增强

### 第四阶段 (待授权) - 写操作功能
10. 批次 1.3 - 系统控制 (需授权)
11. 批次 1.4 - 批量操作 (需授权)

---

**创建人**: Livis (Claude/Kiro)  
**审批人**: Atlas  
**最终确认**: Jay.S  
**预计开始时间**: 待前置条件完成后立即启动
