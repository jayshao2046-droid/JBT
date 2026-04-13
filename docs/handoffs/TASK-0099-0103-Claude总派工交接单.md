# Claude 看板端全功能升级 — 总派工交接单

> 签发：Atlas（总项目经理）  
> 日期：2025-06-11  
> 状态：**全部 Token 已签发，等待 Claude 按序执行**

---

## 核心要求（Jay.S 原话）

1. **"看板端只能比临时看板端更好用功能更全，而不能不如临时看板"**
2. **"必须先在 MacBook 上把看板拉起来，我要看得到"** → `pnpm dev` 跑在 port 3005
3. **"完成一个收口一个"** → 每完成一个 TASK，Atlas 复核 → 架构师终审 → 锁回
4. **"打工的任务交给 Claude，必须要把所有工作落实到位"**

---

## 执行顺序（严格按序）

| 序号 | 任务 | Token | 文件数 | 比对文件（实施参考） |
|------|------|-------|--------|---------------------|
| 1 | TASK-0099：首页框架 + v0 模板替换 + API 层 | `tok-3e1c1970` | 47 | — |
| 2 | TASK-0100：sim-trading 端全功能升级 | `tok-279d4f99` | 24 | `docs/handoffs/TASK-0099-比对-sim-trading.md` |
| 3 | TASK-0101：backtest 端全功能升级 | `tok-92f7dce9` | 23 | `docs/handoffs/TASK-0099-比对-backtest.md` |
| 4 | TASK-0102：decision 端全功能升级 | `tok-1f25eea1` | 25 | `docs/handoffs/TASK-0099-比对-decision.md` |
| 5 | TASK-0103：data 端全功能升级 | `tok-bcdd740a` | 21 | `docs/handoffs/TASK-0099-比对-data.md` |

**总计：140 files across 5 tasks**

---

## TASK-0099 — 首页框架 + API（前置任务）

**目标**：用 v0-close 模板替换 TASK-0096 骨架，搭建完整的 layout / sidebar / 首页 / API client / auth

**验收要求**：
1. `pnpm install` → `pnpm build` → `pnpm lint` 全部通过
2. `pnpm dev` 在 port 3005 启动，浏览器可见首页
3. Sidebar 包含全部四端导航（sim-trading / backtest / decision / data）
4. API client 层已按四端创建基础文件
5. 清除全部 mock 数据硬编码

**Token**: `tok-3e1c1970`  
**白名单**: 47 files（详见 `docs/tasks/TASK-0099-dashboard-v0模板替换与API对接.md`）

---

## TASK-0100 — sim-trading 端全功能升级

**后端 API 基地址**：`http://localhost:8101`  
**临时看板参考**：`services/sim-trading/sim-trading_web/`（port 3001）  
**v0 模板参考**：`docs/portal-design/v0-close/app/(dashboard)/sim-trading/`

### 必须覆盖的功能（对标临时看板，只能更好不能更差）

**P0（必须对接 API）**：
- 模拟交易总览（KPI + 账户资金 + 持仓 + 最近成交）
- 交易终端（下单/撤单/平仓），对接 `/api/orders/`, `/api/positions/`
- 行情报价（实时报价表 + 行情图），对接 `/api/market/`, `/api/tick/`
- 风控监控（执行质量 + 风控状态），对接 `/api/risk-control/`

**P1（增强功能）**：
- 品种风控预设编辑器
- CTP 连接配置与状态监控
- 一键快捷下单面板

**P2（v0 增强组件）**：
- ExecutionQualityKPI、TechnicalChart、MarketMovers
- ConnectionQuality、OrderFlow、PositionAnalysis
- RiskConfigEditor、RiskTemplates、TradeHeatmap

### Token & 白名单

**Token**: `tok-279d4f99`

**路由 (7)**:
- `app/(dashboard)/sim-trading/layout.tsx`
- `app/(dashboard)/sim-trading/page.tsx`
- `app/(dashboard)/sim-trading/operations/page.tsx`
- `app/(dashboard)/sim-trading/market/page.tsx`
- `app/(dashboard)/sim-trading/intelligence/page.tsx`
- `app/(dashboard)/sim-trading/risk-presets/page.tsx`
- `app/(dashboard)/sim-trading/ctp-config/page.tsx`

**组件 (11)**:
- `components/sim-trading/performance-kpi.tsx`
- `components/sim-trading/execution-quality-kpi.tsx`
- `components/sim-trading/quick-order-presets.tsx`
- `components/sim-trading/technical-chart.tsx`
- `components/sim-trading/market-movers.tsx`
- `components/sim-trading/connection-quality.tsx`
- `components/sim-trading/order-flow.tsx`
- `components/sim-trading/position-analysis.tsx`
- `components/sim-trading/risk-config-editor.tsx`
- `components/sim-trading/risk-templates.tsx`
- `components/sim-trading/trade-heatmap.tsx`

**Lib (3)**:
- `lib/api/sim-trading.ts`（扩展 TASK-0099 创建的基础版本）
- `lib/contracts.ts`
- `lib/holidays-cn.ts`

**Hooks (3)**:
- `hooks/use-sim-trading.ts`
- `hooks/use-market-data.ts`
- `hooks/use-risk-control.ts`

---

## TASK-0101 — backtest 端全功能升级

**后端 API 基地址**：`http://localhost:8103`  
**临时看板参考**：`services/backtest/backtest_web/`（port 3002）  
**v0 模板参考**：`docs/portal-design/v0-close/app/(dashboard)/backtest/`

### 必须覆盖的功能

**P0**：
- 策略列表 + 状态（对接 `/api/strategies/`）
- 回测任务管理（创建/删除/运行，对接 `/api/backtest/jobs/`）
- 回测结果查看（收益曲线/交易记录/月度分析，对接 `/api/backtest/results/`）

**P1**：
- 系统状态、引擎健康
- 策略参数在线编辑
- 回测队列与进度追踪

**P2**：
- 参数优化热力图
- 多策略对比分析
- SSE 实时进度条

### Token & 白名单

**Token**: `tok-92f7dce9`

**路由 (6)**:
- `app/(dashboard)/backtest/layout.tsx`
- `app/(dashboard)/backtest/page.tsx`
- `app/(dashboard)/backtest/operations/page.tsx`
- `app/(dashboard)/backtest/results/page.tsx`
- `app/(dashboard)/backtest/review/page.tsx`
- `app/(dashboard)/backtest/optimizer/page.tsx`

**组件 (14)**:
- `components/backtest/backtest-analysis.tsx`
- `components/backtest/backtest-comparison.tsx`
- `components/backtest/backtest-config-editor.tsx`
- `components/backtest/backtest-heatmap.tsx`
- `components/backtest/backtest-quality-kpi.tsx`
- `components/backtest/backtest-queue.tsx`
- `components/backtest/backtest-templates.tsx`
- `components/backtest/equity-curve-chart.tsx`
- `components/backtest/parameter-optimizer.tsx`
- `components/backtest/performance-kpi.tsx`
- `components/backtest/progress-tracker.tsx`
- `components/backtest/review-panel.tsx`
- `components/backtest/stock-review-table.tsx`
- `components/backtest/trade-detail-analysis.tsx`

**Lib (1)**:
- `lib/api/backtest.ts`

**Hooks (2)**:
- `hooks/use-backtest.ts`
- `hooks/use-backtest-results.ts`

---

## TASK-0102 — decision 端全功能升级

**后端 API 基地址**：`http://localhost:8104`  
**临时看板参考**：`services/decision/decision_web/`（port 3003）  
**v0 模板参考**：`docs/portal-design/v0-close/app/(dashboard)/decision/`

### 必须覆盖的功能

**P0**：
- 信号审查与分发（对接 `/api/signals/`）
- 决策总览（当日信号统计 + 持仓建议，对接 `/api/decision/overview/`）
- 模型与因子管理（对接 `/api/factor-models/`）

**P1**：
- 策略调度与分发
- 通知管理与日报
- 策略模板配置

**P2**：
- 因子分析工具箱
- 盘中信号实时刷新
- 盘后复盘报告
- 股票池筛选器

### Token & 白名单

**Token**: `tok-1f25eea1`

**路由 (7)**:
- `app/(dashboard)/decision/layout.tsx`
- `app/(dashboard)/decision/page.tsx`
- `app/(dashboard)/decision/signal/page.tsx`
- `app/(dashboard)/decision/models/page.tsx`
- `app/(dashboard)/decision/repository/page.tsx`
- `app/(dashboard)/decision/research/page.tsx`
- `app/(dashboard)/decision/reports/page.tsx`

**组件 (15)**:
- `components/decision/overview.tsx`
- `components/decision/signal-review.tsx`
- `components/decision/models-factors.tsx`
- `components/decision/strategy-repository.tsx`
- `components/decision/research-center.tsx`
- `components/decision/notifications-report.tsx`
- `components/decision/config-runtime.tsx`
- `components/decision/factor-analysis.tsx`
- `components/decision/intraday-signal.tsx`
- `components/decision/evening-rotation-plan.tsx`
- `components/decision/post-market-report.tsx`
- `components/decision/signal-distribution-chart.tsx`
- `components/decision/stock-pool-table.tsx`
- `components/decision/strategy-import.tsx`
- `components/decision/optimizer-panel.tsx`

**Lib (1)**:
- `lib/api/decision.ts`

**Hooks (2)**:
- `hooks/use-decision.ts`
- `hooks/use-signals.ts`

---

## TASK-0103 — data 端全功能升级

**后端 API 基地址**：`http://localhost:8105`  
**临时看板参考**：`services/data/data_web/`（port 3004）  
**v0 模板参考**：无独立 v0 子应用，参考 v0-close 首页数据板块

### 必须覆盖的功能

**P0**：
- 采集器状态管理（各采集器运行/暂停/出错，对接 `/api/collectors/`）
- 系统健康监控（Mini 硬件 + 服务进程，对接 `/api/system/`）
- 新闻资讯流（实时新闻展示，对接 `/api/news/`）

**P1**：
- 存储用量分析
- 数据浏览器（按标的/日期查询）
- 自动修复机制状态

**P2**：
- 采集热力图（按时段/品种显示数量密度）
- 数据质量 KPI
- SSE 采集进度

### Token & 白名单

**Token**: `tok-bcdd740a`

**路由 (6)**:
- `app/(dashboard)/data/layout.tsx`
- `app/(dashboard)/data/page.tsx`
- `app/(dashboard)/data/collectors/page.tsx`
- `app/(dashboard)/data/explorer/page.tsx`
- `app/(dashboard)/data/news/page.tsx`
- `app/(dashboard)/data/system/page.tsx`

**组件 (12)**:
- `components/data/overview-page.tsx`
- `components/data/collectors-page.tsx`
- `components/data/data-explorer.tsx`
- `components/data/news-feed.tsx`
- `components/data/system-monitor.tsx`
- `components/data/collection-analysis.tsx`
- `components/data/collection-heatmap.tsx`
- `components/data/collection-queue.tsx`
- `components/data/collection-stats-chart.tsx`
- `components/data/data-quality-kpi.tsx`
- `components/data/data-source-health-kpi.tsx`
- `components/data/data-source-config-editor.tsx`

**Lib (1)**:
- `lib/api/data.ts`

**Hooks (2)**:
- `hooks/use-data-service.ts`
- `hooks/use-collectors.ts`

---

## 技术约束

1. **所有路径前缀**：`services/dashboard/dashboard_web/`（白名单中省略了前缀）
2. **框架**：Next.js 15.2.6 + React 19 + TypeScript + Tailwind + shadcn/ui
3. **UI 主题**：orange-500 暗色主题（继承 v0-close 模板设计语言）
4. **API 调用**：使用 TASK-0099 创建的 `lib/api-client.ts` 统一 fetch wrapper
5. **认证**：使用 TASK-0099 创建的 auth 中间件
6. **不允许**：跨服务 import / 读取非 dashboard_web 目录 / 复制临时看板代码（需重写 + 增强）

## 验收流程

每完成一个 TASK：
1. `pnpm lint` + `pnpm build` 必须通过
2. `pnpm dev` 可见对应端页面
3. API 对接真实后端（后端不启动时显示优雅降级，不 crash）
4. Atlas 复核 → 架构师终审 → 锁回 → 独立提交
