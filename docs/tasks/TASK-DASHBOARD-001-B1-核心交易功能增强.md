# TASK-DASHBOARD-001-B1：P0 核心交易功能增强

## 任务信息

- 任务 ID：TASK-DASHBOARD-001-B1
- 上级任务：TASK-DASHBOARD-001（Dashboard 页面完成计划）
- 所属服务：dashboard
- 执行 Agent：Livis（Claude-Code）
- 复核人：Atlas
- 优先级：P0
- 预计工期：2-3 天
- 当前状态：待执行

## 任务目标

完善 Dashboard 主看板和模拟交易模块的核心功能，包括：
1. 主看板权益曲线图表 + 日报摘要卡片
2. 市场行情 K 线图组件（lightweight-charts 或 recharts）
3. 紧急暂停/恢复按钮（写操作已授权，需二次确认 UI）
4. 批量平仓对话框（写操作已授权，需弹窗+密码确认）
5. 执行质量统计卡片

## 写操作授权说明（Jay.S 2026-04-18 确认）

| 功能 | 授权 | 约束 |
|------|------|------|
| 暂停/恢复交易 | ✅ 已授权 | 需二次确认弹窗 |
| 批量平仓 | ✅ 已授权 | 需弹窗+二次确认 |
| 修改止损 | ❌ 暂不授权 | 本批次不实现 |

## API 客户端现状

以下 API 客户端方法 **已存在于** `lib/api/sim-trading.ts`，无需重写：
- `pauseTrading()` / `resumeTrading()` — 系统暂停/恢复
- `batchClosePositions()` — 批量平仓
- `getExecutionStats()` — 执行质量统计
- `getMarketKline()` — K 线数据
- `getDailyReport()` — 日报数据

需要新增的 API 客户端方法：
- `getEquityHistory()` — 权益曲线历史 (`GET /api/v1/equity/history`)

## 文件白名单（13 个）

**修改文件（7 个）**：
1. `services/dashboard/dashboard_web/app/(dashboard)/page.tsx` — 嵌入权益曲线+日报+紧急暂停
2. `services/dashboard/dashboard_web/app/(dashboard)/sim-trading/market/page.tsx` — 嵌入 K 线图
3. `services/dashboard/dashboard_web/app/(dashboard)/sim-trading/operations/page.tsx` — 嵌入批量平仓
4. `services/dashboard/dashboard_web/app/(dashboard)/sim-trading/page.tsx` — 嵌入执行质量
5. `services/dashboard/dashboard_web/lib/api/sim-trading.ts` — 新增 getEquityHistory
6. `services/dashboard/dashboard_web/hooks/use-dashboard-data.ts` — 新增权益曲线数据
7. `services/dashboard/dashboard_web/package.json` — 添加 lightweight-charts 依赖

**新建文件（6 个）**：
8. `services/dashboard/dashboard_web/components/dashboard/equity-chart.tsx`
9. `services/dashboard/dashboard_web/components/dashboard/daily-report-card.tsx`
10. `services/dashboard/dashboard_web/components/dashboard/emergency-stop-button.tsx`
11. `services/dashboard/dashboard_web/components/sim-trading/kline-chart.tsx`
12. `services/dashboard/dashboard_web/components/sim-trading/batch-close-dialog.tsx`
13. `services/dashboard/dashboard_web/components/sim-trading/execution-quality-card.tsx`

## 验收标准

1. 权益曲线正确显示最近 30 天数据，30 秒刷新
2. K 线图显示 OHLC 数据，支持 1m/5m/15m/30m/60m 切换
3. 紧急暂停按钮醒目、需二次确认弹窗，暂停后全局显示警告横幅
4. 批量平仓支持多选持仓、二次确认、显示执行进度
5. 执行质量卡片显示滑点/拒单率/延迟/撤单率
6. `pnpm build` 通过

## 前置检查

- [ ] Livis 先 curl 验证 `GET /api/v1/equity/history` 后端是否已实现
- [ ] 若 404，标记为降级处理（使用 mock 数据或跳过）

## 执行记录

- [ ] API 可用性扫描完成
- [ ] 权益曲线组件完成
- [ ] 日报卡片完成
- [ ] K 线图组件完成
- [ ] 紧急暂停按钮完成
- [ ] 批量平仓对话框完成
- [ ] 执行质量统计卡片完成
- [ ] pnpm build 通过
- [ ] Atlas 复核通过

---
**创建人**：Atlas  
**创建时间**：2026-04-18
