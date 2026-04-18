# TASK-DASHBOARD-001-B4：数据模块增强

## 任务信息

- 任务 ID：TASK-DASHBOARD-001-B4
- 上级任务：TASK-DASHBOARD-001（Dashboard 页面完成计划）
- 所属服务：dashboard
- 执行 Agent：Livis（Claude-Code）
- 复核人：Atlas
- 优先级：P2
- 预计工期：0.5-1 天
- 前置依赖：TASK-DASHBOARD-001-B3 完成并锁回
- 当前状态：待执行

## 任务目标

**以增强为主**。Atlas 评估发现数据模块核心功能（总览、采集器管理）已完整实现，本批次任务为：
1. 数据探索器增强 — 补充 K 线图表和数据导出功能
2. 新闻流增强 — 补充筛选和搜索功能
3. 系统监控增强 — 补充资源使用趋势图

## 现状评估（Atlas 已核实）

| 组件 | 状态 | 说明 |
|------|------|------|
| OverviewPage | ✅ 已完成 | 采集器汇总+资源监控+日志全部对接 |
| CollectorsPage | ✅ 已完成 | 分类筛选+搜索+自动刷新+单个重启全部完成 |
| DataExplorer | ⚠️ 可增强 | 基础功能存在，K 线图和导出可补充 |
| NewsFeed | ⚠️ 可增强 | 新闻列表存在，高级筛选可补充 |
| SystemMonitor | ⚠️ 可增强 | 基础监控存在，趋势图可补充 |

## 文件白名单（7 个）

**修改文件（7 个）**：
1. `services/dashboard/dashboard_web/app/(dashboard)/data/explorer/page.tsx`
2. `services/dashboard/dashboard_web/app/(dashboard)/data/news/page.tsx`
3. `services/dashboard/dashboard_web/app/(dashboard)/data/system/page.tsx`
4. `services/dashboard/dashboard_web/lib/api/data.ts`
5. `services/dashboard/dashboard_web/components/data/data-explorer.tsx`
6. `services/dashboard/dashboard_web/components/data/news-feed.tsx`
7. `services/dashboard/dashboard_web/components/data/system-monitor.tsx`

## 验收标准

1. 数据探索器支持合约搜索和简单 K 线图表展示
2. 新闻流支持按来源/情绪/重要性筛选和关键词搜索
3. 系统监控显示资源使用趋势（近 1h/6h/24h）
4. `pnpm build` 通过

## 执行要求

- 增强功能优先使用已有组件库（recharts / shadcn/ui）
- 不引入新的重型依赖
- 若某项增强需要后端 API 不存在，标记降级并跳过

## 执行记录

- [ ] 数据探索器增强完成
- [ ] 新闻流增强完成
- [ ] 系统监控增强完成
- [ ] pnpm build 通过
- [ ] Atlas 复核通过

---
**创建人**：Atlas  
**创建时间**：2026-04-18
