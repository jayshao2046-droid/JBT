# TASK-0101: 回测端统一看板全功能升级

**状态**：review_approved  
**服务**：services/dashboard/dashboard_web  
**前置**：TASK-0099 + TASK-0100  
**比对参考**：docs/handoffs/TASK-0099-比对-backtest.md  
**执行端**：Claude  
**目标**：统一看板 backtest 子页面必须覆盖临时看板全部功能并增强

---

## 任务范围

在 `services/dashboard/dashboard_web/` 中实现回测端完整功能：
- 6 个子页面（总览/操作台/结果查看/审查/参数优化/layout）
- 14 个业务组件（从临时看板移植 + 增强）
- 扩展 API client + 2 个 hooks

## 硬约束

1. 所有数据必须对接真实 API（port 8103），禁止 mock
2. 功能必须 ≥ 临时看板 `services/backtest/backtest_web/`
3. 路由组结构：`app/(dashboard)/backtest/`
4. 参考代码：临时看板 `backtest_web/src/utils/api.ts` + 各组件

## 文件白名单（23 files）

### 路由页面 (6)
- services/dashboard/dashboard_web/app/(dashboard)/backtest/layout.tsx
- services/dashboard/dashboard_web/app/(dashboard)/backtest/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/backtest/operations/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/backtest/results/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/backtest/review/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/backtest/optimizer/page.tsx

### 业务组件 (14)
- services/dashboard/dashboard_web/components/backtest/backtest-analysis.tsx
- services/dashboard/dashboard_web/components/backtest/backtest-comparison.tsx
- services/dashboard/dashboard_web/components/backtest/backtest-config-editor.tsx
- services/dashboard/dashboard_web/components/backtest/backtest-heatmap.tsx
- services/dashboard/dashboard_web/components/backtest/backtest-quality-kpi.tsx
- services/dashboard/dashboard_web/components/backtest/backtest-queue.tsx
- services/dashboard/dashboard_web/components/backtest/backtest-templates.tsx
- services/dashboard/dashboard_web/components/backtest/equity-curve-chart.tsx
- services/dashboard/dashboard_web/components/backtest/parameter-optimizer.tsx
- services/dashboard/dashboard_web/components/backtest/performance-kpi.tsx
- services/dashboard/dashboard_web/components/backtest/progress-tracker.tsx
- services/dashboard/dashboard_web/components/backtest/review-panel.tsx
- services/dashboard/dashboard_web/components/backtest/stock-review-table.tsx
- services/dashboard/dashboard_web/components/backtest/trade-detail-analysis.tsx

### API/Hooks (3)
- services/dashboard/dashboard_web/lib/api/backtest.ts
- services/dashboard/dashboard_web/hooks/use-backtest.ts
- services/dashboard/dashboard_web/hooks/use-backtest-results.ts
