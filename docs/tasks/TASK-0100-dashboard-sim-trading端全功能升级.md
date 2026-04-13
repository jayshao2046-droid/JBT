# TASK-0100: 模拟交易端统一看板全功能升级

**状态**：review_approved  
**服务**：services/dashboard/dashboard_web  
**前置**：TASK-0099（首页框架 + API 对接）  
**比对参考**：docs/handoffs/TASK-0099-比对-sim-trading.md  
**执行端**：Claude  
**目标**：统一看板 sim-trading 子页面必须覆盖临时看板全部功能并增强

---

## 任务范围

在 `services/dashboard/dashboard_web/` 中实现模拟交易端完整功能：
- 6 个子页面（总览/交易终端/行情报价/风控监控/品种风控/CTP配置）
- 11 个业务组件（从临时看板移植 + 增强）
- 扩展 API client + 3 个 hooks
- 工具库（合约列表/交易日历）

## 硬约束

1. 所有数据必须对接真实 API（port 8101），禁止 mock
2. 功能必须 ≥ 临时看板 `services/sim-trading/sim-trading_web/`
3. 路由组结构：`app/(dashboard)/sim-trading/`
4. 参考代码：临时看板 `sim-trading_web/lib/sim-api.ts` + 各组件

## 文件白名单（24 files）

### 路由页面 (7)
- services/dashboard/dashboard_web/app/(dashboard)/sim-trading/layout.tsx
- services/dashboard/dashboard_web/app/(dashboard)/sim-trading/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/sim-trading/operations/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/sim-trading/market/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/sim-trading/intelligence/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/sim-trading/risk-presets/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/sim-trading/ctp-config/page.tsx

### 业务组件 (11)
- services/dashboard/dashboard_web/components/sim-trading/performance-kpi.tsx
- services/dashboard/dashboard_web/components/sim-trading/execution-quality-kpi.tsx
- services/dashboard/dashboard_web/components/sim-trading/quick-order-presets.tsx
- services/dashboard/dashboard_web/components/sim-trading/technical-chart.tsx
- services/dashboard/dashboard_web/components/sim-trading/market-movers.tsx
- services/dashboard/dashboard_web/components/sim-trading/connection-quality.tsx
- services/dashboard/dashboard_web/components/sim-trading/order-flow.tsx
- services/dashboard/dashboard_web/components/sim-trading/position-analysis.tsx
- services/dashboard/dashboard_web/components/sim-trading/risk-config-editor.tsx
- services/dashboard/dashboard_web/components/sim-trading/risk-templates.tsx
- services/dashboard/dashboard_web/components/sim-trading/trade-heatmap.tsx

### API/Hooks/Lib (6)
- services/dashboard/dashboard_web/lib/api/sim-trading.ts
- services/dashboard/dashboard_web/lib/contracts.ts
- services/dashboard/dashboard_web/lib/holidays-cn.ts
- services/dashboard/dashboard_web/hooks/use-sim-trading.ts
- services/dashboard/dashboard_web/hooks/use-market-data.ts
- services/dashboard/dashboard_web/hooks/use-risk-control.ts
