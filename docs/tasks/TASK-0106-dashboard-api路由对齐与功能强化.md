# TASK-0106 — 看板全端 API 路由对齐与功能强化

**状态**：in_progress  
**服务**：services/dashboard/dashboard_web  
**执行端**：Atlas  
**日期**：2026-04-14  
**优先级**：P1（当前 decision 端全部 404）

---

## 问题分析

### 1. decision 端 API BASE 路径错误（P0 级）

**现状**：`lib/api/decision.ts` BASE = `/api/decision/api/v1`  
**代理后访问**：`http://localhost:8104/api/v1/strategies` 等  
**后端实际路由**：`/strategies`, `/signals`, `/approvals` 等（无 `/api/v1/` 前缀）  
**影响**：decision 所有页面 100% 404，完全不可用

**修复**：将 `API_BASE = "/api/decision/api/v1"` 改为 `API_BASE = "/api/decision"`

### 2. backtest 端路由错位（P1 级）

**错位路由**：

| 客户端调用 | 实际后端 | 修复方案 |
|-----------|---------|---------|
| `GET /api/backtest/health` | `/api/health` | `const HEALTH = "/api/backtest"` 单独处理，或改为 `/api/backtest/api/health` |
| `GET /api/backtest/jobs` | `/api/backtest/api/v1/jobs` | 补充 V1 BASE |
| `GET /api/backtest/jobs/{id}` | `/api/backtest/api/v1/jobs/{job_id}` | 同上 |
| `POST /api/backtest/enqueue` | `/api/backtest/api/v1/strategy-queue/enqueue` | 同上 |
| `GET /api/backtest/queue/status` | `/api/backtest/api/v1/strategy-queue/status` | 同上 |
| `GET /api/backtest/history` | 不存在（无历史列表路由）| 移除或 fallback |
| `GET /api/backtest/history/{id}` | `/api/backtest/backtest/history/{strategy_id}` | 修正路径 |
| `POST /api/backtest/validate` | 不存在 | 移除 |

**修复**：在 `backtest.ts` 增加 `BASE_V1 = "/api/backtest/api/v1"` 用于 jobs/queue；health 用独立路径 `/api/backtest/api/health`

### 2.1 backtest 返回结构与前端假设不一致（P1 级）

**实测返回**：

- `/api/strategies` 直接返回数组，不是 `{ strategies: [] }`
- `/api/v1/jobs` 返回分页对象 `{ total, page, limit, items }`，不是 `{ jobs: [] }`
- `/api/system/status` 返回 `cpu/memory/disk/latency/services`，不是 `cpu_usage/memory_usage/uptime`
- `/api/backtest/results` 直接返回数组，不是 `{ results: [] }`

**影响**：backtest 首页、结果页虽然能编译，但运行时显示为空或字段错位。

**修复**：在 API/hook 层做兼容映射，统一输出给页面当前已消费的结构。

### 2.2 decision 局部组件仍直连旧路径（P1 级）

**现状**：`evening-rotation-plan.tsx`、`optimizer-panel.tsx`、`strategy-import.tsx` 仍绕过 `lib/api/decision.ts`，直接请求旧路径。

**影响**：研究页、报告页、仓库页的局部功能仍会 404 或请求体不匹配。

**修复**：按 Studio decision openapi 实测路径修正 URL，并按真实 schema 对齐请求体与空状态展示。

### 3. 空状态处理与加载状态（P2 级）

各页面在 API 返回空数组/null 时的友好提示缺失，需统一加上空状态 UI。

---

## 文件白名单

| 文件 | 操作 | 优先级 |
|------|------|-------|
| `lib/api/decision.ts` | 修改 API_BASE | P0 |
| `lib/api/backtest.ts` | 修复多条路由 | P1 |
| `hooks/use-decision.ts` | 检查直接 fetch 调用 | P1 |
| `hooks/use-backtest.ts` | 检查直接 fetch 调用 | P1 |
| `hooks/use-backtest-results.ts` | 检查 | P2 |
| `components/decision/evening-rotation-plan.tsx` | 修正 rotation plan 路由与空状态 | P1 |
| `components/decision/optimizer-panel.tsx` | 修正 optimizer 路由与请求体 | P1 |
| `components/decision/strategy-import.tsx` | 修正 strategy import 路由与请求体 | P1 |
| `components/decision/overview.tsx` | 空状态/错误展示 | P2 |
| `components/decision/signal-review.tsx` | 空状态 | P2 |
| `components/backtest/backtest-queue.tsx` | 空状态 | P2 |

## 验收标准

1. `pnpm build` 通过（无新增类型错误）
2. Studio 上 `/api/decision/strategies` 返回 200
3. Studio 上 `/api/decision/signals` 返回 200
4. Studio 上 backtest jobs/queue 路由返回正确响应
5. backtest 首页 / 结果页与实际返回结构对齐，不再出现空白列表
6. decision 研究页 / 仓库页 / 报告页的直连接口可用
7. 各页面无白屏，有数据时正常显示，无数据时有空状态提示
