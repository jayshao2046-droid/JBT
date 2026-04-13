# TASK-0099 Claude 实施派单交接单

**任务**：dashboard v0 模板替换 + API 对接  
**Token**：`tok-3e1c1970-707b-412b-8bbe-189eac0fa287` | TASK-0099 | Claude | active | TTL 4320min  
**时间**：2026-04-13  
**授权文件**：`docs/tasks/TASK-0099-dashboard-v0模板替换-API对接.md`  
**预审**：`docs/reviews/REVIEW-TASK-0099.md` | APPROVED  

---

## 任务背景

Jay.S 已弃用原有分步迁移方案（TASK-0097），改用 v0 一体化模板重做 dashboard_web 的主页框架。  
模板来源：`docs/portal-design/v0-close/`（只读参考，不得直接改这个目录）  
实施目标：`services/dashboard/dashboard_web/`（写操作目标）

---

## 当前 dashboard_web 文件状态（TASK-0096 骨架，commit 4b3bfe9）

```
app/
  (auth)/layout.tsx
  (auth)/login/layout.tsx
  (auth)/login/page.tsx      ← 需替换（用 v0 login 样式）
  (dashboard)/layout.tsx     ← 需替换（用 MainLayout 包裹）
  (dashboard)/page.tsx       ← 需重写（v0 dashboard 首页，无 mock）
  (dashboard)/settings/layout.tsx
  (dashboard)/settings/page.tsx
  globals.css                ← 需替换（v0 橙色主题变量）
  layout.tsx                 ← 需更新（加 ThemeProvider + Toaster）

components/
  layout/
    sidebar.tsx              ← 删除（被 app-sidebar.tsx 替代）
    topbar.tsx               ← 删除（被 app-header.tsx 替代）
    nav-item.tsx             ← 删除（合入 app-sidebar）
  dashboard/
    quick-links.tsx          ← 删除
    service-status-card.tsx  ← 删除
    status-overview.tsx      ← 删除
  ui/（现有）: avatar, badge, button, card, dropdown-menu, 
               input, label, scroll-area, separator, switch, tabs

lib/
  api-client.ts              ← 保留（可能弃用，但在白名单外，不删）
  auth.ts                    ← 保留
  constants.ts               ← 保留
  utils.ts                   ← 保留
```

---

## 需要新增的依赖（与 v0-close 对比差异）

**需要新增到 dashboard_web/package.json**：
```json
{
  "recharts": "2.15.4",
  "next-themes": "^0.4.6",
  "sonner": "^1.7.4",
  "@hookform/resolvers": "^3.10.0",
  "@radix-ui/react-checkbox": "^1.1.3",
  "@radix-ui/react-collapsible": "^1.1.2",
  "@radix-ui/react-dialog": "^1.1.4",
  "@radix-ui/react-progress": "^1.1.1",
  "@radix-ui/react-toast": "^1.2.4",
  "@radix-ui/react-tooltip": "^1.1.6"
}
```

**next 版本**：从 15.1.6 升到 15.2.6（对齐 v0）  
**lucide-react**：保留现有 ^0.468.0（比 v0 的 ^0.454.0 更新，直接用）

---

## v0-close 模板文件映射（只读参考路径 → 目标路径）

### Step 1：删除旧 layout 和 dashboard 组件
直接删除以下文件：
- `services/dashboard/dashboard_web/components/layout/sidebar.tsx`
- `services/dashboard/dashboard_web/components/layout/topbar.tsx`
- `services/dashboard/dashboard_web/components/layout/nav-item.tsx`
- `services/dashboard/dashboard_web/components/dashboard/quick-links.tsx`
- `services/dashboard/dashboard_web/components/dashboard/service-status-card.tsx`
- `services/dashboard/dashboard_web/components/dashboard/status-overview.tsx`

### Step 2：新增 layout 组件（从 v0-close 复制并适配）

| 参考文件 | 目标路径 |
|---------|---------|
| `docs/portal-design/v0-close/components/layout/main-layout.tsx` | `services/dashboard/dashboard_web/components/layout/main-layout.tsx` |
| `docs/portal-design/v0-close/components/layout/app-sidebar.tsx` | `services/dashboard/dashboard_web/components/layout/app-sidebar.tsx` |
| `docs/portal-design/v0-close/components/layout/app-header.tsx` | `services/dashboard/dashboard_web/components/layout/app-header.tsx` |
| `docs/portal-design/v0-close/components/layout/animated-grid-bg.tsx` | `services/dashboard/dashboard_web/components/layout/animated-grid-bg.tsx` |
| `docs/portal-design/v0-close/components/layout/date-time-display.tsx` | `services/dashboard/dashboard_web/components/layout/date-time-display.tsx` |
| `docs/portal-design/v0-close/components/theme-provider.tsx` | `services/dashboard/dashboard_web/components/theme-provider.tsx` |

### Step 3：新增 dashboard 业务组件（从 v0-close 复制，**移除所有 mock 导入**）

| 参考文件 | 目标路径 | mock 清理要点 |
|---------|---------|-------------|
| `components/dashboard/kpi-card.tsx` | 同名 → dashboard_web | 接受 props，不内部导入 mock |
| `components/dashboard/churn-chart.tsx` | 同名 | 接受 `data` prop，不默认 mockChurnData |
| `components/dashboard/current-positions.tsx` | 同名 | 接受 `positions` prop，不 import mock |
| `components/dashboard/close-position-dialog.tsx` | 同名 | 纯 UI Dialog，props-driven |
| `components/dashboard/today-trading-summary.tsx` | 同名 | 接受统计 props |
| `components/dashboard/strategy-signals.tsx` | 同名 | 接受 `signals` prop |
| `components/dashboard/signal-confirm-dialog.tsx` | 同名 | 纯 UI Dialog |
| `components/dashboard/disable-signal-dialog.tsx` | 同名 | 纯 UI Dialog |
| `components/dashboard/manual-open-dialog.tsx` | 同名 | 纯 UI Dialog |
| `components/dashboard/real-time-risk.tsx` | 同名 | 接受 risk metrics props |
| `components/dashboard/data-source-status.tsx` | 同名 | 接受 `sources` prop |
| `components/dashboard/news-list.tsx` | 同名 | 接受 `news` prop |

### Step 4：新增 UI 组件（从 v0-close 直接复制，无 mock 问题）

| 参考文件 | 目标路径 |
|---------|---------|
| `components/ui/checkbox.tsx` | `dashboard_web/components/ui/checkbox.tsx` |
| `components/ui/collapsible.tsx` | `dashboard_web/components/ui/collapsible.tsx` |
| `components/ui/dialog.tsx` | `dashboard_web/components/ui/dialog.tsx` |
| `components/ui/progress.tsx` | `dashboard_web/components/ui/progress.tsx` |
| `components/ui/select.tsx` | `dashboard_web/components/ui/select.tsx`（替换现有） |
| `components/ui/skeleton.tsx` | `dashboard_web/components/ui/skeleton.tsx` |
| `components/ui/table.tsx` | `dashboard_web/components/ui/table.tsx` |
| `components/ui/tooltip.tsx` (从 v0-close 获取模板) | `dashboard_web/components/ui/tooltip.tsx` |
| `components/ui/sonner.tsx` (需新建) | `dashboard_web/components/ui/sonner.tsx` |
| `components/ui/toast.tsx` | `dashboard_web/components/ui/toast.tsx` |
| `components/ui/toaster.tsx` | `dashboard_web/components/ui/toaster.tsx` |

> **注意**：v0-close 没有 sonner.tsx，但有 `@radix-ui/react-toast`。sonner.tsx 按 shadcn/ui 标准写法生成即可。

### Step 5：新建 API 层（全部新建，无参考文件）

#### `lib/api/types.ts` — TypeScript 接口（对应真实 API 响应）
```typescript
// sim-trading 接口
export interface AccountInfo {
  equity: number;        // 总权益
  available: number;     // 可用资金
  margin: number;        // 占用保证金
  float_pnl: number;     // 浮动盈亏
}
export interface PerformanceStats {
  daily_pnl: number;
  win_rate: number;
  pnl_ratio: number;
  total_trades: number;
}
export interface RiskL1 {
  position_usage: number;  // 仓位使用率 0~1
  var_1d: number;          // 单日 VaR
  drawdown: number;        // 最大回撤
}
export interface DailyReport {
  trade_count: number;
  pnl: number;
  date: string;
}
export interface Position {
  instrument_id: string;
  direction: 'long' | 'short';
  volume: number;
  open_price: number;
  current_price: number;
  float_pnl: number;
}
export interface Order {
  order_id: string;
  instrument_id: string;
  direction: 'buy' | 'sell';
  volume: number;
  price: number;
  status: string;
  timestamp: string;
}

// decision 接口
export interface StrategySignal {
  id: string;
  strategy_name: string;
  instrument_id: string;
  direction: 'long' | 'short';
  confidence: number;
  status: 'pending' | 'approved' | 'rejected' | 'disabled';
  timestamp: string;
}

// data 接口
export interface CollectorStatus {
  name: string;
  status: 'running' | 'stopped' | 'error';
  last_update: string;
  data_count?: number;
}
export interface NewsItem {
  id: string;
  title: string;
  source: string;
  timestamp: string;
  url?: string;
  summary?: string;
}

// 服务健康
export interface ServiceHealth {
  status: 'ok' | 'error' | 'unknown';
  service: string;
  timestamp?: string;
}
```

#### `lib/api/fetcher.ts` — 基础 fetch 封装
```typescript
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    throw new ApiError(res.status, `API error: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}
```

#### `lib/api/sim-trading.ts`
```typescript
import { apiFetch } from './fetcher';
import type { AccountInfo, PerformanceStats, RiskL1, DailyReport, Position, Order } from './types';

const BASE = '/api/sim-trading';

export const simTradingApi = {
  getAccount: () => apiFetch<AccountInfo>(`${BASE}/account`),
  getPositions: () => apiFetch<Position[]>(`${BASE}/positions`),
  getPerformance: () => apiFetch<PerformanceStats>(`${BASE}/stats/performance`),
  getRiskL1: () => apiFetch<RiskL1>(`${BASE}/risk/l1`),
  getDailyReport: () => apiFetch<DailyReport>(`${BASE}/report/daily`),
  getOrders: () => apiFetch<Order[]>(`${BASE}/orders`),
  getStatus: () => apiFetch<{ status: string }>(`${BASE}/status`),
};
```

#### `lib/api/decision.ts`
```typescript
import { apiFetch } from './fetcher';
import type { StrategySignal } from './types';

const BASE = '/api/decision';

export const decisionApi = {
  getSignals: () => apiFetch<StrategySignal[]>(`${BASE}/dashboard/signals`),
  getHealth: () => apiFetch<{ status: string }>(`${BASE}/api/health`),
};
```

#### `lib/api/data.ts`
```typescript
import { apiFetch } from './fetcher';
import type { CollectorStatus, NewsItem } from './types';

const BASE = '/api/data';

export const dataApi = {
  getCollectors: () => apiFetch<CollectorStatus[]>(`${BASE}/api/v1/dashboard/collectors`),
  getNews: () => apiFetch<NewsItem[]>(`${BASE}/api/v1/dashboard/news`),
  getHealth: () => apiFetch<{ status: string }>(`${BASE}/api/v1/health`),
};
```

#### `lib/api/backtest.ts`
```typescript
import { apiFetch } from './fetcher';

const BASE = '/api/backtest';

export const backtestApi = {
  getHealth: () => apiFetch<{ status: string }>(`${BASE}/health`),
};
```

#### `hooks/use-dashboard-data.ts` — 首页聚合 Hook
```typescript
'use client';
import { useState, useEffect } from 'react';
import { simTradingApi } from '@/lib/api/sim-trading';
import { decisionApi } from '@/lib/api/decision';
import { dataApi } from '@/lib/api/data';
import type { AccountInfo, PerformanceStats, RiskL1, Position, StrategySignal, CollectorStatus, NewsItem } from '@/lib/api/types';

export function useDashboardData() {
  const [account, setAccount] = useState<AccountInfo | null>(null);
  const [performance, setPerformance] = useState<PerformanceStats | null>(null);
  const [risk, setRisk] = useState<RiskL1 | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [signals, setSignals] = useState<StrategySignal[]>([]);
  const [collectors, setCollectors] = useState<CollectorStatus[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([
      simTradingApi.getAccount().then(setAccount),
      simTradingApi.getPerformance().then(setPerformance),
      simTradingApi.getRiskL1().then(setRisk),
      simTradingApi.getPositions().then(setPositions),
      decisionApi.getSignals().then(setSignals),
      dataApi.getCollectors().then(setCollectors),
      dataApi.getNews().then(setNews),
    ])
      .then((results) => {
        const failed = results.filter((r) => r.status === 'rejected');
        if (failed.length > 0) {
          setError(`${failed.length} 个数据接口加载失败`);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  return { account, performance, risk, positions, signals, collectors, news, loading, error };
}
```

#### `hooks/use-service-status.ts` — 四服务状态 Hook
```typescript
'use client';
import { useState, useEffect } from 'react';
import { simTradingApi } from '@/lib/api/sim-trading';
import { decisionApi } from '@/lib/api/decision';
import { dataApi } from '@/lib/api/data';
import { backtestApi } from '@/lib/api/backtest';

export type ServiceName = 'sim-trading' | 'decision' | 'data' | 'backtest';
export type ServiceStatus = 'ok' | 'error' | 'loading';

export function useServiceStatus(intervalMs = 30000) {
  const [statuses, setStatuses] = useState<Record<ServiceName, ServiceStatus>>({
    'sim-trading': 'loading',
    decision: 'loading',
    data: 'loading',
    backtest: 'loading',
  });

  const checkAll = () => {
    const check = (name: ServiceName, promise: Promise<unknown>) => {
      promise
        .then(() => setStatuses((prev) => ({ ...prev, [name]: 'ok' })))
        .catch(() => setStatuses((prev) => ({ ...prev, [name]: 'error' })));
    };
    check('sim-trading', simTradingApi.getStatus());
    check('decision', decisionApi.getHealth());
    check('data', dataApi.getHealth());
    check('backtest', backtestApi.getHealth());
  };

  useEffect(() => {
    checkAll();
    const timer = setInterval(checkAll, intervalMs);
    return () => clearInterval(timer);
  }, [intervalMs]);

  return statuses;
}
```

### Step 6：更新路由文件

#### `app/layout.tsx` — 加入 ThemeProvider + Toaster
参考 v0-close/app/layout.tsx，添加：
```tsx
import { ThemeProvider } from '@/components/theme-provider';
import { Toaster } from '@/components/ui/toaster';
// 或 Sonner: import { Toaster } from '@/components/ui/sonner';
```

#### `app/(dashboard)/layout.tsx` — 替换为 MainLayout 包裹
```tsx
import MainLayout from '@/components/layout/main-layout';
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <MainLayout>{children}</MainLayout>;
}
```

#### `app/(dashboard)/page.tsx` — 首页重写
- 移除所有旧组件（StatusOverview, ServiceStatusCard, QuickLinks）
- 使用 `useDashboardData()` hook 获取数据
- 渲染 v0 的 12 个 dashboard 组件（KpiCard × N, CurrentPositions, StrategySignals, RealTimeRisk, DataSourceStatus, NewsList, ChurnChart）
- **严禁**任何 `import * from '@/lib/mock-data'` 或内联 mock 数组

#### `app/(auth)/login/page.tsx` — 替换为 v0 login 样式
参考 `docs/portal-design/v0-close/app/login/page.tsx`，保持路由组结构 `(auth)/login/page.tsx`  
认证逻辑：`localStorage.setItem('jbt_user', JSON.stringify(user))` → redirect to `/`

#### `app/globals.css` — 替换为 v0 橙色主题
参考 `docs/portal-design/v0-close/app/globals.css`（orange-500 + neutral-900）

---

## next.config.ts — API 代理（确认已有，补充缺失）

当前已有代理，确认包含以下 4 个：
```typescript
async rewrites() {
  return [
    { source: '/api/sim-trading/:path*', destination: 'http://localhost:8101/:path*' },
    { source: '/api/backtest/:path*', destination: 'http://localhost:8103/:path*' },
    { source: '/api/decision/:path*', destination: 'http://localhost:8104/:path*' },
    { source: '/api/data/:path*', destination: 'http://localhost:8105/:path*' },
  ];
}
```

---

## 硬性约束（违反即 lint/review 不通过）

1. **禁止 `lib/mock-data.ts` 文件**（不得创建）
2. **禁止内联 mock 数组**在 useState 初始值
3. **必须有 loading 状态**：每个 fetch 数据的组件必须展示 loading skeleton
4. **必须有 error 状态**：fetch 失败时展示 error UI，不能无声崩溃
5. **路由组结构不变**：`(auth)/login`, `(dashboard)/`，与 v0-close 的 flat 结构不同，必须映射
6. **端口不变**：`package.json` 中 `dev` 和 `start` 保持 `--port 3005`
7. **不得新建** `app/sim-trading/page.tsx`, `app/backtest/page.tsx` 等子应用路由（不在白名单）
8. **不修改白名单外的文件**（`lib/constants.ts`, `lib/auth.ts`, settings/*, 等均不在白名单）

---

## 验收标准

```bash
cd services/dashboard/dashboard_web
pnpm install            # 无报错
pnpm build             # 构建通过，无 TypeScript 错误
pnpm lint              # lint 通过
grep -r "mock-data" src components lib app  # 0 结果
```

- 首页显示真实 loading skeleton（不是硬编码数据）
- API 挂掉时不白屏，显示 error 提示
- 侧边栏链接正确（AppSidebar 匹配 v0-close 导航结构）
- ThemeProvider 已挂载（dark mode toggle 可用）

---

## 完成后执行

1. `cd /Users/jayshao/JBT && python3 governance/jbt_lockctl.py status | grep TASK-0099` 确认 token 仍 active
2. `pnpm build` + `pnpm lint` 通过截图/输出抄送 Atlas
3. Atlas 复审 → 架构师终审 → lockback → commit

---

**派单人**：Atlas  
**执行端**：Claude (Sonnet 4.6)  
**任务文档**：docs/tasks/TASK-0099-dashboard-v0模板替换-API对接.md  
