# TASK-DASHBOARD-001-B3：决策模块验证与补缺

## 任务信息

- 任务 ID：TASK-DASHBOARD-001-B3
- 上级任务：TASK-DASHBOARD-001（Dashboard 页面完成计划）
- 所属服务：dashboard
- 执行 Agent：Livis（Claude-Code）
- 复核人：Atlas
- 优先级：P1
- 预计工期：0.5-1 天
- 前置依赖：TASK-DASHBOARD-001-B2 完成并锁回
- 当前状态：待执行

## 任务目标

**以验证为主、补缺为辅**。Atlas 评估发现决策模块大部分组件已完整实现，本批次任务为：
1. 逐组件核实 API 连接状态，标记已通/未通
2. 补缺未连接的 API 调用（如有）
3. 增强组件数据展示（如有明确缺失）

## 现状评估（Atlas 已核实）

| 组件 | 状态 | 说明 |
|------|------|------|
| Overview | ✅ 已实现 | strategyOverview + runtimeOverview 已对接 |
| SignalReview | ✅ 已实现 | signals/overview + signals + signals/review 已对接 |
| ModelsFactors | ✅ 已实现 | 模型路由器 + 因子同步状态已对接 |
| FactorAnalysis | ✅ 已实现 | 已有组件 |
| ResearchCenter | ✅ 部分实现 | 研究窗口已对接，轮动/盘后组件存在但需验证数据源 |
| StrategyRepository | ✅ 已实现 | strategies CRUD 已对接 |
| StrategyImport | ✅ 已实现 | import-channel 已有组件 |
| StockPoolTable | ⚠️ 待验证 | 组件存在，需验证 stock/pool API |

## 文件白名单（15 个）

**修改文件（15 个，含验证后可能的小修改）**：
1. `services/dashboard/dashboard_web/app/(dashboard)/decision/page.tsx`
2. `services/dashboard/dashboard_web/app/(dashboard)/decision/models/page.tsx`
3. `services/dashboard/dashboard_web/app/(dashboard)/decision/research/page.tsx`
4. `services/dashboard/dashboard_web/app/(dashboard)/decision/repository/page.tsx`
5. `services/dashboard/dashboard_web/lib/api/decision.ts`
6. `services/dashboard/dashboard_web/hooks/use-decision.ts`
7. `services/dashboard/dashboard_web/components/decision/overview.tsx`
8. `services/dashboard/dashboard_web/components/decision/models-factors.tsx`
9. `services/dashboard/dashboard_web/components/decision/factor-analysis.tsx`
10. `services/dashboard/dashboard_web/components/decision/research-center.tsx`
11. `services/dashboard/dashboard_web/components/decision/evening-rotation-plan.tsx`
12. `services/dashboard/dashboard_web/components/decision/post-market-report.tsx`
13. `services/dashboard/dashboard_web/components/decision/strategy-repository.tsx`
14. `services/dashboard/dashboard_web/components/decision/strategy-import.tsx`
15. `services/dashboard/dashboard_web/components/decision/stock-pool-table.tsx`

## 验收标准

1. 所有决策模块组件的 API 连接状态已逐一核实并留记录
2. 未连接的 API 已补缺（如有）
3. 组件无硬编码 mock 数据（除后端 API 不存在的情况）
4. `pnpm build` 通过

## 执行要求

- Livis 先做只读核实（curl 各 API、检查组件是否真正调用了 hook），产出核实报告
- 只在确认有缺失时才修改代码
- 若核实结果为"全部已通"，本批次可快速收口

## 执行记录

- [ ] 逐组件 API 连接核实完成
- [ ] 补缺修改完成（如有）
- [ ] pnpm build 通过
- [ ] Atlas 复核通过

---
**创建人**：Atlas  
**创建时间**：2026-04-18
