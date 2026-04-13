# TASK-0102: 决策端统一看板全功能升级

**状态**：review_approved  
**服务**：services/dashboard/dashboard_web  
**前置**：TASK-0099 + TASK-0100 + TASK-0101  
**比对参考**：docs/handoffs/TASK-0099-比对-decision.md  
**执行端**：Claude  
**目标**：统一看板 decision 子页面必须覆盖临时看板全部功能并增强

---

## 任务范围

在 `services/dashboard/dashboard_web/` 中实现决策端完整功能：
- 7 个子页面（总览/信号审查/模型因子/策略仓库/研究中心/通知日报/layout）
- 15 个业务组件（从临时看板移植 + 增强）
- 扩展 API client + 2 个 hooks

## 硬约束

1. 所有数据必须对接真实 API（port 8104），禁止 mock
2. 功能必须 ≥ 临时看板 `services/decision/decision_web/`
3. 路由组结构：`app/(dashboard)/decision/`
4. 参考代码：临时看板 `decision_web/lib/api.ts` + `components/decision/` 7 模块

## 文件白名单（25 files）

### 路由页面 (7)
- services/dashboard/dashboard_web/app/(dashboard)/decision/layout.tsx
- services/dashboard/dashboard_web/app/(dashboard)/decision/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/decision/signal/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/decision/models/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/decision/repository/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/decision/research/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/decision/reports/page.tsx

### 业务组件 (15)
- services/dashboard/dashboard_web/components/decision/overview.tsx
- services/dashboard/dashboard_web/components/decision/signal-review.tsx
- services/dashboard/dashboard_web/components/decision/models-factors.tsx
- services/dashboard/dashboard_web/components/decision/strategy-repository.tsx
- services/dashboard/dashboard_web/components/decision/research-center.tsx
- services/dashboard/dashboard_web/components/decision/notifications-report.tsx
- services/dashboard/dashboard_web/components/decision/config-runtime.tsx
- services/dashboard/dashboard_web/components/decision/factor-analysis.tsx
- services/dashboard/dashboard_web/components/decision/intraday-signal.tsx
- services/dashboard/dashboard_web/components/decision/evening-rotation-plan.tsx
- services/dashboard/dashboard_web/components/decision/post-market-report.tsx
- services/dashboard/dashboard_web/components/decision/signal-distribution-chart.tsx
- services/dashboard/dashboard_web/components/decision/stock-pool-table.tsx
- services/dashboard/dashboard_web/components/decision/strategy-import.tsx
- services/dashboard/dashboard_web/components/decision/optimizer-panel.tsx

### API/Hooks (3)
- services/dashboard/dashboard_web/lib/api/decision.ts
- services/dashboard/dashboard_web/hooks/use-decision.ts
- services/dashboard/dashboard_web/hooks/use-signals.ts
