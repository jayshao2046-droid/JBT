# TASK-0099 dashboard v0 模板替换 + 首页 API 对接

## 元信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0099 |
| 任务名称 | dashboard_web v0 模板替换 + 首页 mock→API 对接 |
| 服务归属 | `services/dashboard/` |
| 前端子目录 | `services/dashboard/dashboard_web/` |
| 优先级 | P0 |
| 状态 | ✅ locked |
| 创建人 | Atlas |
| 创建时间 | 2026-04-13 |
| 执行人 | Claude（当前会话） |
| 依赖 | TASK-0096 locked（✅），TASK-0097 revoked（✅）|
| 替代 | TASK-0097（revoked，策略变更）|

---

## 任务背景

Jay.S 于 2026-04-13 变更决策：

- **放弃逐页迁移**（原 TASK-0097）
- **采用 v0 模板全量替换方案**：以 `docs/portal-design/v0-close/` 为蓝本，整体替换 `dashboard_web/` 中的 P0+P1 骨架
- **第一步：清理 mock，接入 API**（本任务范围）
- **第二步：功能二次修改**（后续任务）

参考源：`docs/portal-design/v0-close/`（只读参考，不进入 Git 直接提交）

---

## 任务边界

### 包含（第一阶段：模板移植 + API 对接）

**1. 整体替换 dashboard_web 布局与首页**
- 新布局组件：`MainLayout` + `AppSidebar` + `AppHeader` + `AnimatedGridBg` + `DateTimeDisplay`
- 新首页（`app/(dashboard)/page.tsx`）：v0 设计的 KPI 卡片 + 持仓 + 信号 + 风险 + 新闻
- 登录页更新：对齐 v0 风格（`app/(auth)/login/page.tsx`）

**2. 所有 mock 数据替换为真实 API 调用**
- 见 API 映射表（见下）

**3. 新增依赖（package.json）**
- `recharts`：图表
- `next-themes`：主题切换
- `sonner`：Toast 通知
- `@hookform/resolvers`、`react-hook-form`：表单
- `tailwindcss-animate`：动画

**4. 修改 next.config.ts**
- 确保 API rewrite 规则完整覆盖所有对接端点

### 排除
- 各端业务页面（sim-trading/backtest/decision/data 子页面）——后续任务
- Python 后端代码
- `.env.example`、`Dockerfile`（P0 保护路径）

---

## API 映射表

### sim-trading（rewrite: `/api/sim-trading/**` → `http://localhost:8101/api/**`）

| 数据需求 | 端点 | 说明 |
|---------|------|------|
| 账户权益、保证金占用、浮动盈亏 | `GET /api/sim-trading/account` | AccountInfo |
| 今日盈亏、胜率、盈亏比 | `GET /api/sim-trading/stats/performance` | PerformanceStats |
| 仓位使用率、VaR 风险值 | `GET /api/sim-trading/risk/l1` | L1Risk |
| 今日交易笔数 | `GET /api/sim-trading/report/daily` | DailyReport |
| 持仓列表 | `GET /api/sim-trading/positions` | Position[] |
| 下单（手动开仓） | `POST /api/sim-trading/orders` | PlaceOrder |
| 平仓 | `POST /api/sim-trading/positions/batch_close` | BatchClose |
| 服务状态 | `GET /api/sim-trading/status` | ServiceStatus |

### decision（rewrite: `/api/decision/**` → `http://localhost:8104/api/**`）

| 数据需求 | 端点 | 说明 |
|---------|------|------|
| 策略信号列表 | `GET /api/decision/dashboard/signals` | Signal[] |
| 服务状态 | `GET /api/decision/api/health` | HealthResponse |

### data（rewrite: `/api/data/**` → `http://localhost:8105/api/**`）

| 数据需求 | 端点 | 说明 |
|---------|------|------|
| 数据源状态监控 | `GET /api/data/api/v1/dashboard/collectors` | CollectorStatus[] |
| 新闻列表 | `GET /api/data/api/v1/dashboard/news` | NewsItem[] |
| 服务状态 | `GET /api/data/api/v1/health` | HealthResponse |

### backtest（rewrite: `/api/backtest/**` → `http://localhost:8103/api/**`）

| 数据需求 | 端点 | 说明 |
|---------|------|------|
| 服务状态 | `GET /api/backtest/health` | HealthResponse |

---

## 验收标准

1. `pnpm build` 成功，无 TypeScript 错误
2. `pnpm lint` 无 ESLint 错误
3. **首页不再有任何 `mock-data` import**（`lib/mock-data.ts` 或内联 mock 数组）
4. 所有组件的数据来自 `fetch/async` 函数，带 loading/error 状态处理
5. 白名单文件与磁盘实际文件 diff 为 `EXTRA: none / MISSING: none`

---

## 文件白名单（共 62 个文件）

### 配置文件更新（3 个）
```
services/dashboard/dashboard_web/package.json
services/dashboard/dashboard_web/pnpm-lock.yaml
services/dashboard/dashboard_web/next.config.ts
```

### 全局样式（1 个）
```
services/dashboard/dashboard_web/app/globals.css
```

### 路由页面（修改/新建，5 个）
```
services/dashboard/dashboard_web/app/layout.tsx
services/dashboard/dashboard_web/app/(auth)/login/page.tsx
services/dashboard/dashboard_web/app/(auth)/login/layout.tsx
services/dashboard/dashboard_web/app/(dashboard)/layout.tsx
services/dashboard/dashboard_web/app/(dashboard)/page.tsx
```

### 布局组件（5 个，全新）
```
services/dashboard/dashboard_web/components/layout/main-layout.tsx
services/dashboard/dashboard_web/components/layout/app-sidebar.tsx
services/dashboard/dashboard_web/components/layout/app-header.tsx
services/dashboard/dashboard_web/components/layout/animated-grid-bg.tsx
services/dashboard/dashboard_web/components/layout/date-time-display.tsx
```

### 首页业务组件（11 个，全新）
```
services/dashboard/dashboard_web/components/dashboard/kpi-card.tsx
services/dashboard/dashboard_web/components/dashboard/churn-chart.tsx
services/dashboard/dashboard_web/components/dashboard/current-positions.tsx
services/dashboard/dashboard_web/components/dashboard/close-position-dialog.tsx
services/dashboard/dashboard_web/components/dashboard/today-trading-summary.tsx
services/dashboard/dashboard_web/components/dashboard/strategy-signals.tsx
services/dashboard/dashboard_web/components/dashboard/signal-confirm-dialog.tsx
services/dashboard/dashboard_web/components/dashboard/disable-signal-dialog.tsx
services/dashboard/dashboard_web/components/dashboard/manual-open-dialog.tsx
services/dashboard/dashboard_web/components/dashboard/real-time-risk.tsx
services/dashboard/dashboard_web/components/dashboard/data-source-status.tsx
services/dashboard/dashboard_web/components/dashboard/news-list.tsx
```

> 注：首页业务组件共 12 个，但 churn-chart 和 kpi-card 各算 1 个，合计 12 个。

### UI 组件（13 个，补充 v0 新增）
```
services/dashboard/dashboard_web/components/ui/checkbox.tsx
services/dashboard/dashboard_web/components/ui/collapsible.tsx
services/dashboard/dashboard_web/components/ui/dialog.tsx
services/dashboard/dashboard_web/components/ui/progress.tsx
services/dashboard/dashboard_web/components/ui/select.tsx
services/dashboard/dashboard_web/components/ui/skeleton.tsx
services/dashboard/dashboard_web/components/ui/table.tsx
services/dashboard/dashboard_web/components/ui/tooltip.tsx
services/dashboard/dashboard_web/components/ui/sonner.tsx
services/dashboard/dashboard_web/components/ui/toast.tsx
services/dashboard/dashboard_web/components/ui/toaster.tsx
services/dashboard/dashboard_web/components/ui/switch.tsx
services/dashboard/dashboard_web/components/theme-provider.tsx
```

### API 客户端层（新建，8 个）
```
services/dashboard/dashboard_web/lib/api/sim-trading.ts
services/dashboard/dashboard_web/lib/api/decision.ts
services/dashboard/dashboard_web/lib/api/data.ts
services/dashboard/dashboard_web/lib/api/backtest.ts
services/dashboard/dashboard_web/lib/api/types.ts
services/dashboard/dashboard_web/lib/api/fetcher.ts
services/dashboard/dashboard_web/hooks/use-dashboard-data.ts
services/dashboard/dashboard_web/hooks/use-service-status.ts
```

---

## Claude 执行要点

### 1. 布局替换策略
- 删除旧 `components/layout/sidebar.tsx` + `topbar.tsx` + `nav-item.tsx`
- 用 v0-close 的 `app-sidebar.tsx` + `app-header.tsx` + `main-layout.tsx` 替代
- `app/(dashboard)/layout.tsx` 改为使用 `MainLayout`

### 2. mock 清理规则
- **不允许**创建 `lib/mock-data.ts`
- `page.tsx` 中所有 `const [xxx] = useState(mockXxx)` 替换为 `const [xxx] = useState<T[]>([])`，数据来自 API fetch

### 3. API fetch 模式（统一规范）
```typescript
// 所有 API 调用统一用 useEffect + fetch，带 loading/error 状态
const [data, setData] = useState<T[]>([])
const [loading, setLoading] = useState(true)
const [error, setError] = useState<string | null>(null)

useEffect(() => {
  fetch('/api/sim-trading/positions')
    .then(r => r.json())
    .then(setData)
    .catch(e => setError(e.message))
    .finally(() => setLoading(false))
}, [])
```

### 4. 端点 rewrite 规则（next.config.ts）
```typescript
rewrites: [
  { source: '/api/sim-trading/:path*', destination: 'http://localhost:8101/api/:path*' },
  { source: '/api/backtest/:path*',    destination: 'http://localhost:8103/api/:path*' },
  { source: '/api/decision/:path*',    destination: 'http://localhost:8104/api/:path*' },
  { source: '/api/data/:path*',        destination: 'http://localhost:8105/api/:path*' },
]
```

---

## 相关文档

- 参考源：`docs/portal-design/v0-close/`
- 设计方案：`docs/portal-design/v0-prompt-complete.md`
- 后续任务：TASK-0100（功能二次修改，待定）
