# TASK-0099 锁控记录

## 基本信息

| 字段 | 值 |
|------|----|
| 任务 ID | TASK-0099 |
| 任务名称 | dashboard 首页强化 Phase A+B 全收口 |
| Token ID | tok-3e1c1970-707b-412b-8bbe-189eac0fa287 |
| 执行 Agent | Claude + Atlas（补丁） |
| 预审记录 | docs/reviews/REVIEW-TASK-0099-homepage-phase-ab-批复.md |
| 签发时间 | 2026-04-11 |
| 锁回时间 | 2026-04-14 |
| 锁回人 | Atlas |

## 验收结果

### 构建 ✅

- `pnpm build` 通过，4 个路由全部静态化
- `pnpm lint` 通过，零 warning / error

### Commits（共 1 个独立提交）

| Commit | 描述 |
|--------|------|
| bee35c9 | feat(dashboard): TASK-0099 首页强化 Phase A+B 全收口 |

## 修复项汇总（7 bug + 2 功能缺口）

### BUG 修复

| 编号 | 文件 | 修复内容 | 修复方 |
|------|------|---------|------|
| BUG-01 | `page.tsx` | MainLayout named import → default import | Claude |
| BUG-04 | `page.tsx` | `serviceStatuses.map()` → `Object.entries(...).map()` | Claude |
| BUG-05 | `lib/api/sim-trading.ts` | BASE `/api/sim-trading` → `/api/sim-trading/api/v1` | Atlas |
| BUG-06 | `lib/api/sim-trading.ts` | closePosition 不存在端点 → POST /orders 反向下单 | Claude |
| BUG-07 | `lib/api/decision.ts` | health 路径多余 `/api` → `/health` | Atlas |

### 功能缺口补充

| 编号 | 文件 | 补充内容 | 修复方 |
|------|------|---------|------|
| GAP-01 | `hooks/use-dashboard-data.ts` | 新增 `orders` 状态供 TodayTradingSummary 使用 | Claude |
| GAP-02 | `hooks/use-dashboard-data.ts` | 新增 `lastUpdate` 时间戳供 AppHeader 显示 | Claude |

### 新增能力

- `lib/api/decision.ts`：新增 `disableSignal(signalId, reason)` 方法
- `page.tsx`：接入 `useServiceStatus`，服务状态指示灯渲染
- `page.tsx`：全 4 个 Dialog（ManualOpen / SignalConfirm / ClosePosition / DisableSignal）
- `page.tsx`：Header 接入 `onRefresh={refetch}` + `lastUpdate`

## 白名单核验（4 文件）

- [x] `services/dashboard/dashboard_web/app/(dashboard)/page.tsx`
- [x] `services/dashboard/dashboard_web/hooks/use-dashboard-data.ts`
- [x] `services/dashboard/dashboard_web/lib/api/decision.ts`
- [x] `services/dashboard/dashboard_web/lib/api/sim-trading.ts`

## lockctl 状态说明

lockback 命令需要 Jay.S 发行时的完整 JWT（`header.payload.signature` 三段式）。该 JWT 设计上不存储于 state 文件，由 Jay.S 在 `jbt_lockctl.py issue` 时自行保存。

**Jay.S 请执行以下命令完成 lockctl 正式锁回：**

```bash
cd /Users/jayshao/JBT
python3 governance/jbt_lockctl.py lockback \
  --token <TASK-0099 发行时输出的完整 JWT> \
  --result approved \
  --review-id REVIEW-TASK-0099-homepage-phase-ab \
  --summary "TASK-0099 Phase A+B 全收口，build/lint通过，commit bee35c9"
```

## 锁控状态

**TASK-0099 → LOCKED ✅**（Atlas 治理层面，lockctl 待 Jay.S 提供 JWT 后正式置 locked）
