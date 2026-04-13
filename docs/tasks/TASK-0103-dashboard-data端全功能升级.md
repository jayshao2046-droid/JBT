# TASK-0103: 数据端统一看板全功能升级

**状态**：review_approved  
**服务**：services/dashboard/dashboard_web  
**前置**：TASK-0099 + TASK-0100 + TASK-0101 + TASK-0102  
**比对参考**：docs/handoffs/TASK-0099-比对-data.md  
**执行端**：Claude  
**目标**：统一看板 data 子页面必须覆盖临时看板全部功能并增强

---

## 任务范围

在 `services/dashboard/dashboard_web/` 中实现数据端完整功能：
- 6 个子页面（总览/采集器/数据浏览/新闻/系统/layout）
- 12 个业务组件（从临时看板移植 + 增强）
- 扩展 API client + 2 个 hooks

## 硬约束

1. 所有数据必须对接真实 API（port 8105），禁止 mock
2. 功能必须 ≥ 临时看板 `services/data/data_web/`
3. 路由组结构：`app/(dashboard)/data/`
4. 参考代码：临时看板 `data_web/components/pages/` 6 模块

## 文件白名单（21 files）

### 路由页面 (6)
- services/dashboard/dashboard_web/app/(dashboard)/data/layout.tsx
- services/dashboard/dashboard_web/app/(dashboard)/data/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/data/collectors/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/data/explorer/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/data/news/page.tsx
- services/dashboard/dashboard_web/app/(dashboard)/data/system/page.tsx

### 业务组件 (12)
- services/dashboard/dashboard_web/components/data/overview-page.tsx
- services/dashboard/dashboard_web/components/data/collectors-page.tsx
- services/dashboard/dashboard_web/components/data/data-explorer.tsx
- services/dashboard/dashboard_web/components/data/news-feed.tsx
- services/dashboard/dashboard_web/components/data/system-monitor.tsx
- services/dashboard/dashboard_web/components/data/collection-analysis.tsx
- services/dashboard/dashboard_web/components/data/collection-heatmap.tsx
- services/dashboard/dashboard_web/components/data/collection-queue.tsx
- services/dashboard/dashboard_web/components/data/collection-stats-chart.tsx
- services/dashboard/dashboard_web/components/data/data-quality-kpi.tsx
- services/dashboard/dashboard_web/components/data/data-source-health-kpi.tsx
- services/dashboard/dashboard_web/components/data/data-source-config-editor.tsx

### API/Hooks (3)
- services/dashboard/dashboard_web/lib/api/data.ts
- services/dashboard/dashboard_web/hooks/use-data-service.ts
- services/dashboard/dashboard_web/hooks/use-collectors.ts
