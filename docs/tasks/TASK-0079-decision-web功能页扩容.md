# TASK-0079 decision_web 功能页扩容

【签名】Atlas  
【时间】2026-04-13  
【设备】MacBook  

## 基本信息

| 项 | 值 |
|----|-----|
| 任务编号 | TASK-0079 |
| 对应计划项 | CA3/CA4/C0-3 前端配套 |
| 执行 Agent | Claude-Code |
| 服务 | decision |
| 优先级 | P1 |
| Token ID | tok-0ca581e2 |
| 状态 | Token 已签发 |

## 需求描述

decision 后端已完成策略导入（C0-3 TASK-0051）、参数调优（CA4 TASK-0061）、回测报告导出（CA3 TASK-0060）。当前 decision_web 已有 /research 页面（含股票池、盘中信号、期货研究面板），需要新增 import、optimizer、reports 三个功能页。

## 白名单

| 文件 | 操作 |
|------|------|
| `services/decision/decision_web/app/import/page.tsx` | 新建 |
| `services/decision/decision_web/app/optimizer/page.tsx` | 新建 |
| `services/decision/decision_web/app/reports/page.tsx` | 新建 |
| `services/decision/decision_web/components/StrategyImport.tsx` | 新建 |
| `services/decision/decision_web/components/OptimizerPanel.tsx` | 新建 |
| `services/decision/decision_web/components/ReportViewer.tsx` | 新建 |

## 验收标准

1. `/import` 页面：支持 YAML 文件上传（drag-drop 或文件选择），调用 `POST /api/v1/strategy/import/yaml`，显示导入成功/失败反馈
2. `/optimizer` 页面：选择已有策略，调用 `POST /api/v1/research/optimize`，展示网格搜索进度和最优参数结果
3. `/reports` 页面：列表展示回测报告（`GET /api/v1/research/report/{strategy_id}`），支持查看详情和导出 JSON
4. 使用 decision_web 已有的 shadcn/ui + Tailwind + Navbar 风格
5. API 调用使用环境变量 `NEXT_PUBLIC_API_URL`，默认 `http://localhost:8104`
6. 在 Navbar.tsx 中添加 Import / Optimizer / Reports 导航入口
