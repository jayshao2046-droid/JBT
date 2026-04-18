# TASK-DASHBOARD-001-B2：回测模块完善

## 任务信息

- 任务 ID：TASK-DASHBOARD-001-B2
- 上级任务：TASK-DASHBOARD-001（Dashboard 页面完成计划）
- 所属服务：dashboard
- 执行 Agent：Livis（Claude-Code）
- 复核人：Atlas
- 优先级：P1
- 预计工期：1.5-2 天
- 前置依赖：TASK-DASHBOARD-001-B1 完成并锁回
- 当前状态：待执行

## 任务目标

完善 Dashboard 回测模块的三个占位页面：
1. 策略审查页面 — 对接策略队列管理 API
2. 参数优化器页面 — 实现参数网格配置与结果表格（简化版，热力图后置）
3. 回测详情增强 — 添加权益曲线、成交记录、进度跟踪、取消功能

## 现状评估

- `backtest/review/page.tsx` — 当前为占位页面（"审查功能开发中..."）
- `backtest/optimizer/page.tsx` — 当前为占位页面（"参数优化功能开发中..."）
- `backtest/results/page.tsx` — 已有结果列表，缺详情弹窗
- `components/backtest/` 已有 14 个组件文件，部分可复用

## 文件白名单（10 个）

**修改文件（6 个）**：
1. `services/dashboard/dashboard_web/app/(dashboard)/backtest/review/page.tsx`
2. `services/dashboard/dashboard_web/app/(dashboard)/backtest/optimizer/page.tsx`
3. `services/dashboard/dashboard_web/app/(dashboard)/backtest/results/page.tsx`
4. `services/dashboard/dashboard_web/lib/api/backtest.ts`
5. `services/dashboard/dashboard_web/hooks/use-backtest.ts`
6. `services/dashboard/dashboard_web/hooks/use-backtest-results.ts`

**可修改的已有组件（2 个）**：
7. `services/dashboard/dashboard_web/components/backtest/parameter-optimizer.tsx`
8. `services/dashboard/dashboard_web/components/backtest/review-panel.tsx`

**新建文件（2 个）**：
9. `services/dashboard/dashboard_web/components/backtest/result-detail-dialog.tsx`
10. `services/dashboard/dashboard_web/components/backtest/param-grid.tsx`

## 验收标准

1. 策略审查页面显示队列中的策略列表，支持入队/清空
2. 参数优化器支持配置参数范围和步长，结果按表格展示（热力图后置为 P2）
3. 回测结果页面点击可查看详情弹窗（权益曲线+成交记录）
4. 运行中的回测显示进度，支持取消
5. `pnpm build` 通过

## 前置检查

- [ ] Livis 先 curl 验证以下后端 API 可用性：
  - `GET /api/v1/strategy-queue/status`
  - `GET /api/backtest/results/{task_id}/equity`
  - `GET /api/backtest/results/{task_id}/trades`
  - `GET /api/backtest/progress/{task_id}`
  - `POST /api/backtest/cancel/{task_id}`

## 执行记录

- [ ] API 可用性扫描完成
- [ ] 策略审查页面完成
- [ ] 参数优化器页面完成
- [ ] 回测详情弹窗完成
- [ ] pnpm build 通过
- [ ] Atlas 复核通过

---
**创建人**：Atlas  
**创建时间**：2026-04-18
