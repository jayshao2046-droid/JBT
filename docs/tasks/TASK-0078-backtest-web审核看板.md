# TASK-0078 backtest_web 审核看板

【签名】Atlas  
【时间】2026-04-13  
【设备】MacBook  

## 基本信息

| 项 | 值 |
|----|-----|
| 任务编号 | TASK-0078 |
| 对应计划项 | CG1/CG2/CG3 前端配套 |
| 执行 Agent | Claude-Code |
| 服务 | backtest |
| 优先级 | P1 |
| Token ID | tok-87bcbffc |
| 状态 | Token 已签发 |

## 需求描述

backtest 端已完成策略导入队列（CG1 TASK-0052）、手动回测审核（CG2 TASK-0055）、股票手动回测（CG3 TASK-0058）的后端实现。当前 backtest_web 只有 agent-network 和 operations 两个页面，需要新增 review 页面作为人工审核入口。

## 白名单

| 文件 | 操作 |
|------|------|
| `services/backtest/backtest_web/app/review/page.tsx` | 新建 |
| `services/backtest/backtest_web/components/ReviewPanel.tsx` | 新建 |
| `services/backtest/backtest_web/components/StockReviewTable.tsx` | 新建 |

## 验收标准

1. `/review` 路由可访问，显示两个 Tab：期货审核 / 股票审核
2. ReviewPanel 组件：展示策略导入队列（来自 `/api/v1/strategy/queue`），每条可点击"执行回测"和"审核通过/拒绝"
3. StockReviewTable 组件：展示股票待审策略（来自 `/api/v1/stock/approval/pending`），显示回测绩效指标，支持批量审核
4. 使用 backtest_web 已有的 shadcn/ui + Tailwind 风格
5. API 调用使用环境变量 `NEXT_PUBLIC_API_URL`，默认 `http://localhost:8103`
6. 在 layout.tsx 或导航中添加 Review 入口链接
