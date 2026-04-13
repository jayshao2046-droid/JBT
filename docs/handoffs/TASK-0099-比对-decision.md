# 决策端（decision）功能比对：临时看板 vs v0 看板

**比对日期**：2026-04-13  
**临时看板路径**：`services/decision/decision_web/`  
**v0 看板路径**：`docs/portal-design/v0-close/app/decision/` + `v0-close/decision/`  
**后端 API**：`services/decision/src/api/routes/` (port 8104)

---

## 页面级对比

| 页面 | 临时看板 | v0 统一门户路由 | v0 独立子应用 | 差异 |
|------|---------|--------------|------------|------|
| 首页/总览 | `app/page.tsx` ✅ **SPA + API** (7 模块导航) | `app/decision/page.tsx` 🔴 全 mock | `decision/app/page.tsx` | v0 信号/模型全 mock |
| 信号审查 | `components/decision/signal-review.tsx` ✅ **API** | `app/decision/signal/page.tsx` 🔴 mock | 无独立路由 | v0 信号页全 mock |
| 模型与因子 | `components/decision/models-factors.tsx` ✅ | `app/decision/models/page.tsx` 🔴 mock | 无独立路由 | v0 模型页全 mock |
| 策略仓库 | `components/decision/strategy-repository.tsx` ✅ | `app/decision/repository/page.tsx` 🔴 mock | 无独立路由 | v0 仓库页全 mock |
| 研究中心 | `components/decision/research-center.tsx` ✅ | `app/decision/research/page.tsx` 🔴 mock | `decision/app/research/page.tsx` | v0 研究页全 mock |
| 通知与日报 | `components/decision/notifications-report.tsx` ✅ | ❌ 无对应路由 | `decision/app/reports/page.tsx` | v0 统一门户无此页 |
| 配置与运行 | `components/decision/config-runtime.tsx` ✅ | ❌ 无对应路由 | 无 | v0 缺失 |
| 历史回放 | `app/history/page.tsx` ✅ | ❌ 无 | `decision/app/history/page.tsx` 🔴 mock | v0 统一门户无此页 |
| 策略导入 | `app/import/page.tsx` ✅ | ❌ 无 | `decision/app/import/page.tsx` | v0 统一门户无此页 |
| 参数优化 | `app/optimizer/page.tsx` ✅ | ❌ 无 | `decision/app/optimizer/page.tsx` 🔴 mock | v0 统一门户无此页 |
| 日报 | `app/reports/page.tsx` ✅ | ❌ 无 | `decision/app/reports/page.tsx` 🔴 mock | v0 统一门户无此页 |

---

## 组件级功能对比

### 总览 (overview)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 后端健康状态 | ✅ `fetchHealth()` 实时 | ❌ 无 | v0 缺失 |
| 模型运行时摘要 | ✅ `fetchRuntimeOverview()` | ❌ 无 | v0 缺失 |
| 在线/本地模型状态灯 | ✅ API 获取 | 🔴 mock `localModelsReady=true` | v0 需对接 |
| 研究窗口状态 | ✅ API | 🔴 mock `false` | v0 需对接 |
| 最后刷新时间 | ✅ 实时 | 🔴 mock | v0 需对接 |

### 信号审查 (signal)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 信号列表 | ✅ `/signals` + `/dashboard/signals` | 🔴 mock 5 条信号 | v0 需对接 `/dashboard/signals` |
| 信号审核 | ✅ POST `/signals/review` | ❌ 无审核操作 | v0 需对接 |
| 信号派发 | ✅ POST `/signals/dispatch` | ❌ 无 | v0 缺失 |
| 信号状态追踪 | ✅ `/signals/status/{id}` | ❌ 无 | v0 缺失 |
| 信号分布图 | ✅ API 数据 | 🔴 mock 6 个时段数据 | v0 需对接 |
| 信号通知 | ✅ `/dashboard/notifications` | ❌ 无 | v0 缺失 |
| 信号日报 | ✅ `/dashboard/reports` | ❌ 无 | v0 缺失 |

### 模型与因子 (models)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 模型性能数据 | ✅ API | 🔴 mock 5 条 modelPerformance | v0 需对接 |
| 因子分析 | ✅ `FactorAnalysis` 组件 | ❌ 无 | v0 缺失 |
| 信号分布图表 | ✅ `SignalDistributionChart` | 🔴 mock 图表数据 | v0 需对接 |

### 策略仓库 (repository)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 策略列表 | ✅ API | 🔴 mock | v0 需对接 |
| 策略模板回测 | ✅ `/templates/{name}/backtest` | ❌ 无 | v0 缺失 |
| 策略导入 | ✅ `StrategyImport` 组件 | ❌ 无 | v0 缺失 |
| 股票池管理 | ✅ `StockPoolTable` 组件 | ❌ 无 | v0 缺失 |

### 研究中心 (research)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 期货研究面板 | ✅ `FuturesResearchPanel` | 🔴 mock | v0 需对接 |
| 盘中信号 | ✅ `IntradaySignal` | ❌ 无 | v0 缺失 |
| 晚间换仓计划 | ✅ `EveningRotationPlan` + `/evening-rotation/plan` | ❌ 无 | v0 缺失 |
| 盘后总结 | ✅ `PostMarketReport` | ❌ 无 | v0 缺失 |
| 选股器 | ✅ `/screener/run` + `/screener/results` | ❌ 无 | v0 缺失 |

### 决策独特组件

| 组件 | 临时看板 | v0 看板 | 差距 |
|------|---------|--------|------|
| DecisionAnalysis | ✅ | 🔴 mock | v0 需对接 |
| DecisionComparison | ✅ | 🔴 mock | v0 需对接 |
| DecisionConfigEditor | ✅ | 🔴 mock | v0 需对接 |
| DecisionHeatmap | ✅ | 🔴 mock | v0 需对接 |
| DecisionQualityKPI | ✅ | 🔴 mock | v0 需对接 |
| DecisionQueue | ✅ | 🔴 mock | v0 需对接 |
| DecisionTemplates | ✅ | 🔴 mock | v0 需对接 |
| OptimizerPanel | ✅ | 🔴 mock | v0 需对接 |
| ReportViewer | ✅ | 🔴 mock | v0 需对接 |
| Navbar (侧边导航) | ✅ 7 模块 | ❌ 无独立侧边栏 | v0 用统一 AppSidebar |

---

## 后端 API 清单（decision:8104 已有，v0 需对接）

| API | 方法 | 用途 | v0 当前状态 |
|-----|------|------|-----------|
| `/api/health` | GET | 健康检查 | ❌ 未用 |
| `/api/ready` | GET | 就绪检查 | ❌ 未用 |
| `/signals` | GET | 信号列表 | ❌ 未用 |
| `/signals/{decision_id}` | GET | 信号详情 | ❌ 未用 |
| `/signals/review` | POST | 信号审核 | ❌ 未用 |
| `/signals/dispatch` | POST | 信号派发 | ❌ 未用 |
| `/signals/status/{signal_id}` | GET | 信号状态 | ❌ 未用 |
| `/signals/overview` | GET | 信号总览 | ❌ 未用 |
| `/dashboard/signals` | GET | 看板信号 | ❌ 未用 |
| `/dashboard/notifications` | GET | 通知列表 | ❌ 未用 |
| `/dashboard/reports` | GET | 日报列表 | ❌ 未用 |
| `/history` | GET | 决策历史 | ❌ 未用 |
| `/validate` | POST | 决策验证 | ❌ 未用 |
| `/batch` | POST | 批量决策 | ❌ 未用 |
| `/{decision_id}/performance` | GET | 绩效 | ❌ 未用 |
| `/{decision_id}/quality` | GET | 质量指标 | ❌ 未用 |
| `/progress/{decision_id}/stream` | GET (SSE) | 进度流 | ❌ 未用 |
| `/evening-rotation/run` | POST | 晚间换仓 | ❌ 未用 |
| `/evening-rotation/plan` | GET | 换仓计划 | ❌ 未用 |
| `/templates` | GET | 策略模板 | ❌ 未用 |
| `/templates/{name}/backtest` | POST | 模板回测 | ❌ 未用 |
| `/screener/run` | POST | 选股器运行 | ❌ 未用 |
| `/screener/results` | GET | 选股结果 | ❌ 未用 |
| `/strategy/import` | POST | 策略导入 | ❌ 未用 |
| `/local-sim/order` | POST | 本地模拟下单 | ❌ 未用 |
| `/local-sim/positions` | GET | 模拟持仓 | ❌ 未用 |
| `/local-sim/health` | GET | 模拟器健康 | ❌ 未用 |

---

## 升级要求（Claude 实施清单）

### 优先级 P0（核心链路）
1. **decision/page.tsx 首页**：对接 `/api/health` + `/signals/overview`，显示模型状态和信号摘要
2. **signal 页面**：对接 `/dashboard/signals` 显示信号列表，实现 `/signals/review` POST 审核操作
3. **models 页面**：对接模型性能数据（从 `/signals/overview` 或扩展 API）

### 优先级 P1（完善体验）
4. 信号派发：对接 `/signals/dispatch`
5. 通知与日报：对接 `/dashboard/notifications` + `/dashboard/reports`
6. 策略仓库：对接 `/templates` 列表
7. 研究中心：对接 `/evening-rotation/plan`

### 优先级 P2（增强功能 - 从临时看板回补）
8. FactorAnalysis 因子分析组件
9. IntradaySignal 盘中信号
10. EveningRotationPlan 晚间换仓计划
11. PostMarketReport 盘后总结
12. StockPoolTable 股票池管理
13. StrategyImport 策略导入
14. DecisionHeatmap 决策热力图
15. OptimizerPanel 参数优化面板
16. 选股器 screener 集成

### 参考代码来源
- 临时看板 `services/decision/decision_web/lib/api.ts`（完整 API client）
- 临时看板 `components/decision/` 下 7 个模块组件
- 临时看板各独立业务组件（DecisionAnalysis, FactorAnalysis 等）
