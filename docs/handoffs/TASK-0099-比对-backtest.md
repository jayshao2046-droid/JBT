# 回测端（backtest）功能比对：临时看板 vs v0 看板

**比对日期**：2026-04-13  
**临时看板路径**：`services/backtest/backtest_web/`  
**v0 看板路径**：`docs/portal-design/v0-close/app/backtest/` + `v0-close/backtest/`  
**后端 API**：`services/backtest/src/api/routes/` (port 8103)

---

## 页面级对比

| 页面 | 临时看板 | v0 统一门户路由 | v0 独立子应用 | 差异 |
|------|---------|--------------|------------|------|
| 首页/总览 | `app/page.tsx` ✅ **SPA + API** (系统状态/运行中任务) | `app/backtest/page.tsx` 🔴 全 mock | `backtest/app/page.tsx` | v0 首页策略列表全 mock |
| 操作台 | `app/operations/page.tsx` ✅ **对接 /run /enqueue** | `app/backtest/operations/page.tsx` 🔴 mock | `backtest/app/operations/page.tsx` | v0 操作台无法真正发起回测 |
| Agent 网络 | `app/agent-network/page.tsx` ✅ **API** | ❌ 无对应路由 | `backtest/app/agent-network/page.tsx` 🔴 mock | v0 统一门户无 agent 路由 |
| 智能监控 | `app/intelligence/page.tsx` ✅ **API** | ❌ 无 | `backtest/app/intelligence/page.tsx` 🔴 mock | v0 统一门户无此页 |
| 参数优化 | `app/optimizer/page.tsx` ✅ | ❌ 无 | `backtest/app/optimizer/page.tsx` 🔴 mock | v0 统一门户无此页 |
| 结果查看 | `app/results/page.tsx` ✅ **对接 /results** | ❌ 无 | `backtest/app/results/page.tsx` 🔴 mock | v0 统一门户无此页 |
| 审查面板 | `app/review/page.tsx` ✅ | ❌ 无 | `backtest/app/review/page.tsx` 🔴 mock | v0 统一门户无此页 |
| 系统管理 | `app/systems/page.tsx` ✅ | ❌ 无 | `backtest/app/systems/page.tsx` 🔴 mock | v0 统一门户无此页 |
| 指挥中心 | `app/command-center/page.tsx` ✅ | ❌ 无 | `backtest/app/command-center/page.tsx` 🔴 mock | v0 统一门户无此页 |

---

## 组件级功能对比

### 首页/总览

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 系统状态 (CPU/内存/延迟) | ✅ `/system/status` 5s轮询 | ❌ 无 | v0 缺失 |
| 运行中回测任务 | ✅ `/jobs` + 进度条 | 🔴 mock `Strategy[]` 数组 | v0 需对接 `/jobs` |
| 策略列表 | ✅ `/strategies` 真实 | 🔴 mock 5 条策略 | v0 需对接 `/strategies` |
| 服务运行时间 | ✅ uptime 显示 | ❌ 无 | v0 缺失 |
| 全局 loading 事件总线 | ✅ `backtest:loading` event | ❌ 无 | v0 缺失 |

### 操作台 (operations)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 发起回测 | ✅ POST `/run` + `/enqueue` | 🔴 mock 按钮（无 API） | v0 需对接 |
| 策略参数配置 | ✅ `/strategy/{name}/params` | 🔴 mock 参数 | v0 需对接 |
| 回测队列 | ✅ `/queue/status` | ❌ 无 | v0 缺失 |
| 回测进度 SSE | ✅ EventSource 进度流 | ❌ 无 | v0 缺失 |
| 策计验证 | ✅ POST `/validate` | ❌ 无 | v0 缺失 |

### 结果查看 (results)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 回测结果列表 | ✅ `/results` | ❌ 无此页面 | v0 缺失整个页面 |
| 权益曲线 | ✅ `/results/{id}/equity` | ❌ 无 | v0 缺失 |
| 成交明细 | ✅ `/results/{id}/trades` | ❌ 无 | v0 缺失 |
| 绩效指标 | ✅ `/results/{id}/performance` (Sharpe/MaxDD/WinRate/Return) | 🔴 mock 数据 | v0 需对接 |
| 任务详情 | ✅ `/jobs/{id}` | ❌ 无 | v0 缺失 |

### 回测业务组件

| 组件 | 临时看板 | v0 看板 | 差距 |
|------|---------|--------|------|
| BacktestAnalysis | ✅ API 对接 | 🔴 mock | v0 需对接 |
| BacktestComparison | ✅ 多策略对比 | 🔴 mock | v0 需对接 |
| BacktestConfigEditor | ✅ 配置编辑 | 🔴 mock | v0 需对接 |
| BacktestHeatmap | ✅ 参数热力图 | 🔴 mock | v0 需对接 |
| BacktestQualityKPI | ✅ 质量指标 | 🔴 mock | v0 需对接 |
| BacktestQueue | ✅ 队列管理 | 🔴 mock | v0 需对接 |
| BacktestTemplates | ✅ 策略模板 | 🔴 mock | v0 需对接 |
| EquityCurveChart | ✅ 权益曲线 | 🔴 mock | v0 需对接 |
| ParameterOptimizer | ✅ 参数优化器 | 🔴 mock | v0 需对接 |
| PerformanceKPI | ✅ Sharpe/MaxDD/WinRate | 🔴 mock | v0 需对接 |
| ProgressTracker | ✅ 进度追踪 | 🔴 mock | v0 需对接 |
| ReviewPanel | ✅ 审查面板 | 🔴 mock | v0 需对接 |
| StockReviewTable | ✅ 个股审查 | 🔴 mock | v0 需对接 |
| TradeDetailAnalysis | ✅ 成交分析 | 🔴 mock | v0 需对接 |

---

## 后端 API 清单（backtest:8103 已有，v0 需对接）

| API | 方法 | 用途 | v0 当前状态 |
|-----|------|------|-----------|
| `/api/health` | GET | 健康检查 | ❌ 未用 |
| `/system/status` | GET | CPU/内存/延迟 | ❌ 未用 |
| `/system/logs` | GET | 系统日志 | ❌ 未用 |
| `/strategies` | GET | 策略列表 | ❌ 未用 |
| `/strategy/{name}` | GET | 策略详情 | ❌ 未用 |
| `/strategy/{name}/params` | GET | 策略参数 | ❌ 未用 |
| `/strategy/import` | POST | 导入策略 | ❌ 未用 |
| `/strategy/export/{name}` | GET | 导出策略 | ❌ 未用 |
| `/strategy/list` | GET | 策略清单 | ❌ 未用 |
| `/run` | POST | 发起回测 | ❌ 未用 |
| `/validate` | POST | 验证策略 | ❌ 未用 |
| `/adjust` | POST | 调整参数 | ❌ 未用 |
| `/summary` | GET | 摘要 | ❌ 未用 |
| `/results` | GET | 结果列表 | ❌ 未用 |
| `/results/{task_id}` | GET | 任务结果 | ❌ 未用 |
| `/results/{task_id}/equity` | GET | 权益曲线 | ❌ 未用 |
| `/results/{task_id}/trades` | GET | 成交明细 | ❌ 未用 |
| `/results/{task_id}/performance` | GET | 绩效指标 | ❌ 未用 |
| `/history` | GET | 历史回测 | ❌ 未用 |
| `/history/{strategy_id}` | GET | 策略历史 | ❌ 未用 |
| `/jobs` | GET/POST | 任务管理 | ❌ 未用 |
| `/jobs/{job_id}` | GET | 任务详情 | ❌ 未用 |
| `/enqueue` | POST | 入队 | ❌ 未用 |
| `/queue/status` | GET | 队列状态 | ❌ 未用 |
| `/market/quotes` | GET | 行情 | ❌ 未用 |
| `/market/main-contracts` | GET | 主力合约 | ❌ 未用 |
| `/market/list` | GET | 品种列表 | ❌ 未用 |
| `/v1/factors` | GET | 因子列表 | ❌ 未用 |

---

## 升级要求（Claude 实施清单）

### 优先级 P0（核心链路）
1. **backtest/page.tsx 首页**：对接 `/strategies` + `/jobs`，显示策略列表和运行中任务
2. **operations/page.tsx**：对接 `/run` POST 发起回测、`/enqueue` 入队、`/validate` 验证
3. **results 页面**：新建或对接 `/results` `/results/{id}/equity` `/results/{id}/performance`

### 优先级 P1（完善体验）
4. 系统状态 KPI：对接 `/system/status` (CPU/内存/延迟)
5. 策略参数配置：对接 `/strategy/{name}/params`
6. 回测队列管理：对接 `/queue/status` + `/enqueue`
7. 策略导入导出：对接 `/strategy/import` POST + `/strategy/export/{name}` GET

### 优先级 P2（增强功能 - 从临时看板回补）
8. BacktestHeatmap 参数热力图（对接 API）
9. BacktestComparison 多策略对比
10. ProgressTracker 进度追踪（SSE）
11. ReviewPanel 审查面板
12. TradeDetailAnalysis 成交分析
13. Agent Network 页面（目前统一门户无此路由）

### 参考代码来源
- 临时看板 `services/backtest/backtest_web/src/utils/api.ts`（完整 API client）
- 临时看板各业务组件（BacktestAnalysis, BacktestQueue 等）
- 临时看板 `backtest_web/src/components/` 下的 ReportPanel, ErrorBoundary
