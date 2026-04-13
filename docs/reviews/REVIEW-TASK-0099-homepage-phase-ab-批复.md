# REVIEW-TASK-0099 首页强化 A+B 批次 预审批复

**编号**: REVIEW-TASK-0099-PhaseAB  
**日期**: 2026-04-14  
**审核人**: Atlas（总项目经理）  
**执行人**: Claude（Copilot）  
**对应任务**: TASK-0099  
**状态**: ✅ 执行完成 — 待项目架构师终审 + lockback

---

## 一、当前状态快照

| 文件 | 状态 | 说明 |
|------|------|------|
| `app/(dashboard)/page.tsx` | ❌ Build Fail | import 方式错误 + 类型不匹配 |
| `hooks/use-dashboard-data.ts` | ⚠️ 缺字段 | 缺 `orders` / `lastUpdate` |
| `hooks/use-service-status.ts` | ✅ 逻辑正确 | 返回 Record，page.tsx 调用方式有误 |
| `lib/api/sim-trading.ts` | ❌ 路径全错 | BASE 缺 `/api/v1`，closePosition 端点不存在 |
| `lib/api/decision.ts` | ⚠️ health 路径错 | `/api/health` 多了一截 `/api` |
| `lib/api/data.ts` | ✅ 路径正确 | 已含 `/api/v1` |
| `lib/api/backtest.ts` | ⚠️ 待核 | 仅有 `/health`，需确认后端前缀 |
| `app/(dashboard)/layout.tsx` | ✅ 已是 passthrough | 无需再改 |
| `app/(dashboard)/settings/page.tsx` | ✅ 无需改 | layout 已处理 |

---

## 二、问题清单（按优先级）

### P0：构建崩溃

**BUG-01**：`page.tsx` L10  
```typescript
// 错误（named import - MainLayout 是 default export）
import { MainLayout } from "@/components/layout/main-layout"
// 正确
import MainLayout from "@/components/layout/main-layout"
```

---

### P1：类型错误（build 会在 P0 修完后继续报错）

**BUG-02**：`page.tsx` 使用了 `lastUpdate`，但 `useDashboardData()` 不返回该字段  
**BUG-03**：`page.tsx` 使用了 `orders`，但 `useDashboardData()` 不返回该字段  
**BUG-04**：`page.tsx` 调用 `serviceStatuses.map(...)`，但 `useServiceStatus()` 返回的是 `Record<ServiceName, ServiceStatus>`，对象不能 `.map()`  
正确写法：`Object.entries(serviceStatuses).map(([name, status]) => ...)`

---

### P1：API 路径错误（运行时全部 404）

**BUG-05**：`lib/api/sim-trading.ts` BASE 错误  
```typescript
// 当前（错）
const BASE = "/api/sim-trading"
// → 代理到 http://localhost:8101/account
// → 后端实际路径 http://localhost:8101/api/v1/account → 404

// 正确
const BASE = "/api/sim-trading/api/v1"
```
影响范围：`getAccount / getPositions / getPerformance / getRiskL1 / getDailyReport / getOrders / getStatus / placeOrder / closePosition` 全部 404

**BUG-06**：`lib/api/sim-trading.ts` closePosition 端点不存在  
```typescript
// 当前（错）— 后端无此路由
closePosition: (positionId: string, volume?: number) =>
  apiFetch(`${BASE}/positions/${positionId}/close`, { method: "POST", ... })

// 正确 — 平仓 = 反向下单到 /orders
closePosition: (position: Position) =>
  apiFetch<Order>(`${BASE}/orders`, {
    method: "POST",
    body: JSON.stringify({
      instrument_id: position.instrument_id,
      direction: position.direction === "long" ? "short" : "long",
      volume: position.volume,
      order_type: "market",
      offset: "close",
    })
  })
```
⚠️ 同时：`page.tsx` 中调用处 `simTradingApi.closePosition(position.position_id, volume)` 需改为 `simTradingApi.closePosition(position)`

**BUG-07**：`lib/api/decision.ts` health 路径多了 `/api`  
```typescript
// 当前（错）: /api/decision/api/health → 代理 → localhost:8104/api/health → 404
getHealth: () => apiFetch<{ status: string }>(`${BASE}/api/health`)

// 正确: /api/decision/health → 代理 → localhost:8104/health ✅
getHealth: () => apiFetch<{ status: string }>(`${BASE}/health`)
```

---

### P2：功能缺口（影响两个新组件的数据）

**GAP-01**：`use-dashboard-data.ts` 缺 `orders` 数据  
`TodayTradingSummary` 需要 `orders` 数组，hook 未调用 `simTradingApi.getOrders()`

**GAP-02**：`use-dashboard-data.ts` 缺 `lastUpdate` 时间戳  
`MainLayout` 的 Header 刷新时间显示依赖此字段

---

## 三、确认事项（需 Claude 回复）

1. **`closePosition` 签名变更**：改为接受完整 `Position` 对象，`page.tsx` 调用处同步改。确认？
2. **`use-service-status` 返回是 Record**，页面改为 `Object.entries` 遍历，确认？
3. **`lastUpdate` 格式**：建议在 hook 内用 `new Date().toLocaleTimeString('zh-CN')` 更新，确认？
4. **backtest API**: `backtestApi.getHealth()` 当前调 `/health`，需确认后端路由前缀后再定。目前先不动 backtest.ts，等下一 TASK 再处理。确认？

---

## 四、最终执行方案（待 Jay.S 拍板后执行）

### 修改文件清单（均在现有 tok-3e1c1970 白名单内）

| 编号 | 文件 | 修改内容 |
|------|------|---------|
| F1 | `lib/api/sim-trading.ts` | BASE 加 `/api/v1`；closePosition 改为反向下单 |
| F2 | `lib/api/decision.ts` | health 路径去掉多余 `/api` |
| F3 | `hooks/use-dashboard-data.ts` | 加 orders 状态 + lastUpdate 时间戳 |
| F4 | `app/(dashboard)/page.tsx` | 改 import 方式；改 serviceStatuses 遍历；改 closePosition 调用 |

### 执行顺序：F1 → F2 → F3 → F4 → `pnpm build` → `pnpm lint`

---

## 五、验收标准

- [ ] `pnpm build` 零错误
- [ ] `pnpm lint` 零 warning/error
- [ ] 页面 `localhost:3005` HTTP 200，无 console 报 404
- [ ] `TodayTradingSummary` 正常显示（含 orders 数据）
- [ ] Header 显示最后刷新时间
- [ ] 服务状态点正常遍历渲染（4 个服务彩点）
- [ ] 平仓弹窗弹出后可提交（closePosition 调用到正确端点）

---

*Atlas 预审完成 — 等待 Claude 确认上方 4 个事项后，由 Jay.S 最终拍板，再进入执行。*
