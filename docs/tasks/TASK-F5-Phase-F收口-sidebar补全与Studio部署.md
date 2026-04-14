# TASK-F5: Phase F 收口 — Sidebar 补全 + Studio 部署

**状态**：✅ 已完成并锁回（commit `463bb0c`，token `tok-16dffac3-8da5-4866-bc54-e6a1abff522d`，2026-04-15）  
**服务**：services/dashboard/dashboard_web  
**前置**：TASK-0099 + TASK-0100 + TASK-0101 + TASK-0102 + TASK-0103 全部 locked  
**执行端**：Atlas  
**目标**：补齐 sidebar 缺失路由入口，并在 Studio 完成 Next.js 构建部署

---

## 任务范围

### 1. Sidebar 入口补全

**缺失项：**

| 路由 | 功能 | 当前状态 |
|------|------|----------|
| /backtest/results | 回测结果 | ✅ 已补齐 |
| /backtest/review | 策略审查 | ✅ 已补齐 |
| /backtest/optimizer | 参数优化 | ✅ 已补齐 |
| /decision/reports | 通知与日报 | ✅ 已补齐 |

### 2. Studio 部署

- `git pull` 已同步 TASK-0099~0103 + TASK-F5
- `pnpm install` 已完成
- `pnpm build` 已通过（28/28）
- Studio 已完成部署验证

---

## 文件白名单（1 file）

- `services/dashboard/dashboard_web/components/layout/app-sidebar.tsx`

---

## 验收标准

- [x] sidebar 4 个缺失入口全部补齐
- [x] pnpm build 28/28 通过
- [x] Studio 上 Next.js 可以访问
