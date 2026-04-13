# Dashboard 首页强化计划

## 一、现状分析

### 1.1 组件结构
首页 (`app/(dashboard)/page.tsx`) 已完成基础布局，包含：
- 4 个 KPI 卡片（总权益、可用资金、今日盈亏、持仓数）
- 当前持仓列表（CurrentPositions）
- 策略信号推荐（StrategySignals）
- 实时风控指标（RealTimeRisk）
- 数据源状态（DataSourceStatus）
- 新闻列表（NewsList）
- 今日交易汇总（TodayTradingSummary）

### 1.2 API 对接情况
**已对接的 API（7个）：**
- `simTradingApi.getAccount()` - 账户信息
- `simTradingApi.getPositions()` - 持仓列表
- `simTradingApi.getPerformance()` - 绩效统计
- `simTradingApi.getRiskL1()` - L1 风控指标
- `decisionApi.getSignals()` - 策略信号
- `dataApi.getCollectors()` - 数据采集器状态
- `dataApi.getNews()` - 新闻列表

**数据流：**
- 使用 `useDashboardData` hook 统一管理数据获取
- 支持 loading/error 状态
- 无 mock 数据残留 ✅

### 1.3 交互缺陷识别

#### 问题 1：Dialog 组件未连接
已创建 4 个 Dialog 组件，但未在首页中引入和使用：
- `SignalConfirmDialog` - 信号确认下单
- `ClosePositionDialog` - 平仓确认
- `ManualOpenDialog` - 手动开仓
- `DisableSignalDialog` - 禁止信号（未找到此文件，可能需要创建）

**影响：**
- 用户点击"手动开仓"按钮无响应
- 用户点击信号列表的"开仓"按钮无响应
- 用户点击持仓列表的"平仓"按钮无响应
- 用户点击信号列表的"禁止"按钮无响应

#### 问题 2：缺少操作 API
Dialog 提交后需要调用后端 API，但当前 API 层缺少：
- 开仓 API（信号确认开仓、手动开仓）
- 平仓 API（全部平仓、部分平仓）
- 信号管理 API（禁止信号、恢复信号）

#### 问题 3：缺少数据刷新机制
- 操作成功后，首页数据不会自动刷新
- 无定时轮询机制（持仓、信号等实时数据）
- 无手动刷新按钮（虽然 AppHeader 有刷新按钮，但未连接到首页数据刷新逻辑）

#### 问题 4：缺少用户反馈
- 操作成功/失败后无 Toast 提示
- 无 loading 状态（按钮点击后无反馈）
- 错误信息未展示给用户

---

## 二、强化方案

### 阶段 1：Dialog 连接与状态管理

#### 1.1 在首页引入 Dialog 组件
**文件：** `app/(dashboard)/page.tsx`

**改动：**
```typescript
// 1. 引入 Dialog 组件
import { SignalConfirmDialog } from "@/components/dashboard/signal-confirm-dialog"
import { ClosePositionDialog } from "@/components/dashboard/close-position-dialog"
import { ManualOpenDialog } from "@/components/dashboard/manual-open-dialog"

// 2. 添加状态管理
const [signalDialogOpen, setSignalDialogOpen] = useState(false)
const [selectedSignal, setSelectedSignal] = useState<StrategySignal | null>(null)

const [closeDialogOpen, setCloseDialogOpen] = useState(false)
const [selectedPosition, setSelectedPosition] = useState<Position | null>(null)

const [manualOpenDialogOpen, setManualOpenDialogOpen] = useState(false)

// 3. 添加回调函数
const handleConfirmSignal = (signal: StrategySignal) => {
  setSelectedSignal(signal)
  setSignalDialogOpen(true)
}

const handleClosePosition = (position: Position) => {
  setSelectedPosition(position)
  setCloseDialogOpen(true)
}

const handleManualOpen = () => {
  setManualOpenDialogOpen(true)
}

// 4. 传递回调到子组件
<StrategySignals
  signals={data.signals}
  onManualOpen={handleManualOpen}
  onConfirmSignal={handleConfirmSignal}
  onDisableSignal={handleDisableSignal}
/>

<CurrentPositions
  positions={data.positions}
  onClose={handleClosePosition}
/>

// 5. 渲染 Dialog
<SignalConfirmDialog
  open={signalDialogOpen}
  onOpenChange={setSignalDialogOpen}
  signal={selectedSignal}
  onConfirm={handleSignalOrderSubmit}
/>

<ClosePositionDialog
  open={closeDialogOpen}
  onOpenChange={setCloseDialogOpen}
  position={selectedPosition}
  onConfirm={handleClosePositionSubmit}
/>

<ManualOpenDialog
  open={manualOpenDialogOpen}
  onOpenChange={setManualOpenDialogOpen}
  onConfirm={handleManualOrderSubmit}
/>
```

#### 1.2 创建 DisableSignalDialog（如果不存在）
**文件：** `components/dashboard/disable-signal-dialog.tsx`

**功能：**
- 显示信号详情
- 确认禁止/恢复信号
- 可选：添加禁止原因输入框

---

### 阶段 2：API 层扩展

#### 2.1 扩展 sim-trading API
**文件：** `lib/api/sim-trading.ts`

**新增接口：**
```typescript
export const simTradingApi = {
  // ... 现有接口
  
  // 开仓（信号确认）
  openPositionFromSignal: (data: {
    signal_id: string
    quantity: number
    stop_loss: number
    take_profit: number
  }) => apiFetch(`${BASE}/orders/open-from-signal`, {
    method: "POST",
    body: JSON.stringify(data),
  }),
  
  // 手动开仓
  openPositionManual: (data: {
    instrument_id: string
    direction: "long" | "short"
    quantity: number
    price: number
    stop_loss: number
    take_profit: number
  }) => apiFetch(`${BASE}/orders/open-manual`, {
    method: "POST",
    body: JSON.stringify(data),
  }),
  
  // 平仓
  closePosition: (data: {
    instrument_id: string
    direction: "long" | "short"
    quantity: number
    close_type: "full" | "partial"
  }) => apiFetch(`${BASE}/orders/close`, {
    method: "POST",
    body: JSON.stringify(data),
  }),
}
```

#### 2.2 扩展 decision API
**文件：** `lib/api/decision.ts`

**新增接口：**
```typescript
export const decisionApi = {
  // ... 现有接口
  
  // 禁止信号
  disableSignal: (signalId: string) => apiFetch(`${BASE}/signals/${signalId}/disable`, {
    method: "POST",
  }),
  
  // 恢复信号
  enableSignal: (signalId: string) => apiFetch(`${BASE}/signals/${signalId}/enable`, {
    method: "POST",
  }),
}
```

---

### 阶段 3：操作逻辑实现

#### 3.1 实现 Dialog 提交处理
**文件：** `app/(dashboard)/page.tsx`

**实现：**
```typescript
const { toast } = useToast()

// 信号确认开仓
const handleSignalOrderSubmit = async (data: SignalOrderData) => {
  try {
    await simTradingApi.openPositionFromSignal({
      signal_id: data.signalId,
      quantity: data.quantity,
      stop_loss: data.stopLoss,
      take_profit: data.takeProfit,
    })
    toast({
      title: "开仓成功",
      description: `已根据信号开仓 ${data.quantity} 手`,
    })
    // 刷新数据
    refetch()
  } catch (error) {
    toast({
      title: "开仓失败",
      description: error.message,
      variant: "destructive",
    })
  }
}

// 手动开仓
const handleManualOrderSubmit = async (data: ManualOrderData) => {
  try {
    await simTradingApi.openPositionManual({
      instrument_id: data.symbol,
      direction: data.direction,
      quantity: data.quantity,
      price: data.price,
      stop_loss: data.stopLoss,
      take_profit: data.takeProfit,
    })
    toast({
      title: "开仓成功",
      description: `${data.symbol} ${data.direction === "long" ? "做多" : "做空"} ${data.quantity} 手`,
    })
    refetch()
  } catch (error) {
    toast({
      title: "开仓失败",
      description: error.message,
      variant: "destructive",
    })
  }
}

// 平仓
const handleClosePositionSubmit = async (data: ClosePositionData) => {
  try {
    const [instrument_id, direction] = data.positionId.split("-")
    await simTradingApi.closePosition({
      instrument_id,
      direction: direction as "long" | "short",
      quantity: data.quantity,
      close_type: data.closeType,
    })
    toast({
      title: "平仓成功",
      description: `已平仓 ${data.quantity} 手`,
    })
    refetch()
  } catch (error) {
    toast({
      title: "平仓失败",
      description: error.message,
      variant: "destructive",
    })
  }
}

// 禁止/恢复信号
const handleDisableSignal = async (signal: StrategySignal) => {
  try {
    const isDisabled = signal.status === "disabled"
    if (isDisabled) {
      await decisionApi.enableSignal(signal.id)
      toast({ title: "已恢复信号" })
    } else {
      await decisionApi.disableSignal(signal.id)
      toast({ title: "已禁止信号" })
    }
    refetch()
  } catch (error) {
    toast({
      title: "操作失败",
      description: error.message,
      variant: "destructive",
    })
  }
}
```

---

### 阶段 4：数据刷新机制

#### 4.1 扩展 useDashboardData hook
**文件：** `hooks/use-dashboard-data.ts`

**改动：**
```typescript
export function useDashboardData() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      const [account, positions, performance, risk, signals, collectors, news] = await Promise.all([
        simTradingApi.getAccount(),
        simTradingApi.getPositions(),
        simTradingApi.getPerformance(),
        simTradingApi.getRiskL1(),
        decisionApi.getSignals(),
        dataApi.getCollectors(),
        dataApi.getNews(),
      ])
      setData({ account, positions, performance, risk, signals, collectors, news })
      setError(null)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    // 每 30 秒自动刷新
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [fetchData])

  return { data, loading, error, refetch: fetchData }
}
```

#### 4.2 连接 AppHeader 刷新按钮
**文件：** `app/(dashboard)/page.tsx`

**改动：**
```typescript
// 1. 从 useDashboardData 获取 refetch
const { data, loading, error, refetch } = useDashboardData()

// 2. 通过 Context 或 props 传递 refetch 到 AppHeader
// 方案 A：使用 Context
// 方案 B：在 MainLayout 中接收 onRefresh prop
```

**文件：** `components/layout/app-header.tsx`

**改动：**
```typescript
interface AppHeaderProps {
  onRefresh?: () => void
}

export function AppHeader({ onRefresh }: AppHeaderProps) {
  // ...
  <Button
    variant="ghost"
    size="icon"
    onClick={onRefresh}
    disabled={isRefreshing}
  >
    <RefreshCw className={cn("w-5 h-5", isRefreshing && "animate-spin")} />
  </Button>
}
```

---

### 阶段 5：用户体验优化

#### 5.1 添加 Toaster 组件
**文件：** `app/layout.tsx`

**改动：**
```typescript
import { Toaster } from "@/components/ui/toaster"

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <ThemeProvider>
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  )
}
```

#### 5.2 添加 Loading 状态
**文件：** `app/(dashboard)/page.tsx`

**改动：**
```typescript
// Dialog 提交时显示 loading
const [isSubmitting, setIsSubmitting] = useState(false)

const handleSignalOrderSubmit = async (data: SignalOrderData) => {
  setIsSubmitting(true)
  try {
    // ... API 调用
  } finally {
    setIsSubmitting(false)
  }
}

// 传递 loading 状态到 Dialog
<SignalConfirmDialog
  open={signalDialogOpen}
  onOpenChange={setSignalDialogOpen}
  signal={selectedSignal}
  onConfirm={handleSignalOrderSubmit}
  isSubmitting={isSubmitting}
/>
```

#### 5.3 错误边界处理
**文件：** `app/(dashboard)/page.tsx`

**改动：**
```typescript
if (error) {
  return (
    <div className="flex items-center justify-center h-screen">
      <Card className="max-w-md">
        <CardHeader>
          <CardTitle className="text-red-400">数据加载失败</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-neutral-400 mb-4">{error.message}</p>
          <Button onClick={refetch}>重试</Button>
        </CardContent>
      </Card>
    </div>
  )
}
```

---

## 三、实施优先级

### P0（必须完成）
1. ✅ Dialog 连接与状态管理（阶段 1）
2. ✅ API 层扩展（阶段 2）
3. ✅ 操作逻辑实现（阶段 3）
4. ✅ Toaster 组件添加（阶段 5.1）

### P1（高优先级）
5. ✅ 数据刷新机制（阶段 4）
6. ✅ Loading 状态（阶段 5.2）
7. ✅ 错误边界处理（阶段 5.3）

### P2（可选优化）
8. ⏳ 添加操作确认二次提示（高风险操作）
9. ⏳ 添加操作历史记录
10. ⏳ 添加快捷键支持（如 Cmd+R 刷新）

---

## 四、后端 API 依赖

### 需要后端新增的端点：

#### sim-trading 服务
- `POST /orders/open-from-signal` - 信号确认开仓
- `POST /orders/open-manual` - 手动开仓
- `POST /orders/close` - 平仓

#### decision 服务
- `POST /signals/{id}/disable` - 禁止信号
- `POST /signals/{id}/enable` - 恢复信号

**注意：** 这些端点需要后端团队实现后才能完成前端对接。

---

## 五、验收标准

### 功能验收
- [ ] 点击"手动开仓"按钮，弹出 ManualOpenDialog
- [ ] 填写表单并提交，调用 API 成功后显示 Toast 提示
- [ ] 点击信号列表的"开仓"按钮，弹出 SignalConfirmDialog
- [ ] 点击持仓列表的"平仓"按钮，弹出 ClosePositionDialog
- [ ] 点击信号列表的"禁止"按钮，调用 API 并刷新数据
- [ ] 点击 AppHeader 的刷新按钮，重新加载首页数据
- [ ] 操作成功后，首页数据自动刷新
- [ ] 操作失败时，显示错误 Toast

### 性能验收
- [ ] 首页加载时间 < 2s
- [ ] Dialog 打开/关闭动画流畅（60fps）
- [ ] 数据刷新时无明显卡顿

### 代码质量
- [ ] pnpm lint 通过（0 warnings）
- [ ] pnpm build 成功
- [ ] 无 console.error 或 console.warn
- [ ] 无 TypeScript 类型错误

---

## 六、风险与依赖

### 风险
1. **后端 API 未就绪**：前端无法完成完整测试
   - 缓解措施：先完成前端逻辑，使用 mock API 测试
2. **API 响应格式不一致**：可能需要调整类型定义
   - 缓解措施：与后端团队对齐 API 文档

### 依赖
1. 后端团队提供 5 个新增 API 端点
2. 后端团队提供 API 文档（请求/响应格式）
3. 测试环境可用（sim-trading, decision 服务运行中）

---

## 七、时间估算

| 阶段 | 工作量 | 说明 |
|------|--------|------|
| 阶段 1 | 2h | Dialog 连接与状态管理 |
| 阶段 2 | 1h | API 层扩展 |
| 阶段 3 | 3h | 操作逻辑实现 + 错误处理 |
| 阶段 4 | 2h | 数据刷新机制 |
| 阶段 5 | 1h | 用户体验优化 |
| **总计** | **9h** | 约 1.5 个工作日 |

---

## 八、后续优化方向

1. **实时数据推送**：使用 WebSocket 替代轮询
2. **操作撤销**：支持撤销最近一次操作
3. **批量操作**：支持批量平仓、批量禁止信号
4. **高级筛选**：持仓/信号列表支持筛选和排序
5. **图表增强**：添加持仓分布饼图、盈亏趋势图
6. **移动端适配**：优化小屏幕下的 Dialog 布局

---

**文档版本：** v1.0  
**创建时间：** 2026-04-13  
**作者：** Claude (TASK-0099 后续强化)
