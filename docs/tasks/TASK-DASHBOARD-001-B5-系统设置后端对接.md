# TASK-DASHBOARD-001-B5：系统设置后端对接

## 任务信息

- 任务 ID：TASK-DASHBOARD-001-B5
- 上级任务：TASK-DASHBOARD-001（Dashboard 页面完成计划）
- 所属服务：dashboard
- 执行 Agent：Livis（Claude-Code）
- 复核人：Atlas
- 优先级：P2
- 预计工期：0.5-1 天
- 前置依赖：TASK-DASHBOARD-001-B4 完成并锁回
- 当前状态：待执行

## 任务目标

将 Settings 页面的静态 UI 连接到后端 API：
1. 创建 settings API 客户端
2. 对接交易时段控制
3. 对接通知配置（飞书/邮件）
4. 对接服务管理（重启/状态查询）

## 现状评估

- `settings/page.tsx` — UI 结构已完整（账户/交易时段/通知/服务管理四个 Tab），但全部是静态展示，未连接任何后端 API
- 无 `lib/api/settings.ts` — 需要新建

## 文件白名单（3 个）

**修改文件（2 个）**：
1. `services/dashboard/dashboard_web/app/(dashboard)/settings/page.tsx`
2. `services/dashboard/dashboard_web/app/(dashboard)/settings/layout.tsx`

**新建文件（1 个）**：
3. `services/dashboard/dashboard_web/lib/api/settings.ts`

## 验收标准

1. 设置页面显示真实后端数据（而非静态占位）
2. 支持修改通知配置并保存
3. 支持查看服务状态
4. `pnpm build` 通过

## 执行要求

- 先确认各后端服务是否提供 settings 类 API
- 若后端无对应 API，使用 sim-trading 的 `system/state` 和 `ctp/config` 等已有端点作为数据源
- 不创建独立的设置后端服务

## 执行记录

- [ ] 后端 API 可用性确认
- [ ] settings API 客户端创建
- [ ] 设置页面后端对接完成
- [ ] pnpm build 通过
- [ ] Atlas 复核通过

---
**创建人**：Atlas  
**创建时间**：2026-04-18
