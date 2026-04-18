# 阶段 0 只读诊断报告

**生成时间**: 2026-04-18  
**执行人**: Livis (Claude/Kiro)  
**状态**: 已完成

---

## 一、后端 API 可用性扫描结果

### 扫描概况

**扫描时间**: 2026-04-18 16:42:00  
**扫描方法**: curl HTTP 状态码检测  
**扫描范围**: 4 个服务，共 40 个 API 端点

### 服务运行状态

| 服务 | 端口 | 状态 | 可用端点 | 说明 |
|------|------|------|----------|------|
| **Data** | 8105 | ✅ 运行中 | 6/8 (75%) | 主要 API 可用 |
| **Sim-Trading** | 8102 | ❌ 停止 | 0/16 (0%) | 服务未启动 |
| **Backtest** | 8103 | ❌ 停止 | 0/6 (0%) | 服务未启动 |
| **Decision** | 8104 | ❌ 停止 | 0/11 (0%) | 服务未启动 |

### 详细扫描结果

#### 1. Data Service (8105) - ✅ 运行中

| API Endpoint | Method | Status | 说明 |
|--------------|--------|--------|------|
| /api/v1/health | GET | ✅ 200 | 健康检查 |
| /api/v1/dashboard/collectors | GET | ✅ 200 | 采集器状态 |
| /api/v1/dashboard/system | GET | ✅ 200 | 系统状态 |
| /api/v1/dashboard/news | GET | ✅ 200 | 新闻列表 |
| /api/v1/symbols | GET | ✅ 200 | 合约列表 |
| /api/v1/researcher/reports | GET | ✅ 200 | 研究员报告 |
| /api/v1/researcher/status | GET | ❌ 404 | **端点不存在** |
| /api/v1/context/preread | POST | ❌ 404 | **端点不存在** |

**结论**: Data 服务运行正常，6/8 端点可用。2 个 404 端点需要后端实现。

---

#### 2. Sim-Trading Service (8102) - ❌ 停止

所有 16 个端点均返回连接错误 (ERR)。

**关键端点清单**:
- `/api/v1/account` - 账户信息
- `/api/v1/positions` - 持仓列表
- `/api/v1/orders` - 订单列表
- `/api/v1/stats/performance` - 绩效统计
- `/api/v1/stats/execution` - 执行质量
- `/api/v1/risk/l1` - L1 风控
- `/api/v1/risk/l2` - L2 风控
- `/api/v1/equity/history` - 权益曲线历史 ⭐
- `/api/v1/report/daily` - 日报
- `/api/v1/market/kline/{symbol}` - K线数据 ⭐
- `/api/v1/market/movers` - 市场异动
- `/api/v1/system/pause` - 暂停交易 ⚠️
- `/api/v1/system/resume` - 恢复交易 ⚠️
- `/api/v1/positions/batch_close` - 批量平仓 ⚠️

**结论**: 服务未启动，无法验证端点是否实现。需要启动服务后重新扫描。

---

#### 3. Backtest Service (8103) - ❌ 停止

所有 6 个端点均返回连接错误 (ERR)。

**关键端点清单**:
- `/api/health` - 健康检查
- `/api/strategies` - 策略列表
- `/api/system/status` - 系统状态
- `/api/v1/jobs` - 任务列表
- `/api/v1/strategy-queue/status` - 队列状态
- `/api/backtest/results` - 回测结果

**结论**: 服务未启动，无法验证端点是否实现。

---

#### 4. Decision Service (8104) - ❌ 停止

所有 11 个端点均返回连接错误 (ERR)。

**关键端点清单**:
- `/health` - 健康检查
- `/strategies` - 策略列表
- `/strategies/overview` - 策略总览 ⭐
- `/signals` - 信号列表
- `/signals/overview` - 信号总览 ⭐
- `/models/status` - 模型状态
- `/models/runtime` - 运行时总览 ⭐
- `/api/v1/factors` - 因子列表
- `/api/v1/stock/pool` - 股票池
- `/api/v1/stock/evening-rotation` - 轮动计划
- `/api/v1/stock/post-market` - 盘后报告

**结论**: 服务未启动，无法验证端点是否实现。

---

## 二、批次 1 详细技术方案

### 任务 1.1: 主看板权益曲线

#### 技术选型
- **图表库**: Recharts (已在项目中使用)
- **数据格式**: `{ timestamp: string, equity: number }[]`
- **刷新策略**: 30 秒轮询

#### 组件设计

**文件**: `components/dashboard/equity-chart.tsx`

```typescript
interface EquityChartProps {
  data: Array<{ timestamp: string; equity: number }>
  loading?: boolean
  height?: number
}

export function EquityChart({ data, loading, height = 300 }: EquityChartProps) {
  // 使用 Recharts LineChart
  // 支持时间范围切换: 1天/7天/30天/全部
  // 显示最高/最低/当前权益
  // 显示收益率百分比
}
```

#### API 对接

**新增方法**: `lib/api/sim-trading.ts`

```typescript
getEquityHistory: (start?: string, end?: string) =>
  apiFetch<{ history: Array<{ timestamp: string; equity: number }>; count: number }>(
    `${BASE}/equity/history${start ? `?start=${start}` : ''}${end ? `&end=${end}` : ''}`
  )
```

#### 集成位置

在主看板 `app/(dashboard)/page.tsx` 的 KPI 卡片下方，占据 2/3 宽度。

---

### 任务 1.2: 市场行情 K 线图 ⭐

#### 技术选型
- **图表库**: `lightweight-charts` v4.x
- **理由**: 专业金融图表库，性能优秀，支持实时更新
- **安装**: `pnpm add lightweight-charts`

#### 组件设计

**文件**: `components/market/kline-chart.tsx`

```typescript
interface KlineChartProps {
  symbol: string
  interval: '1m' | '5m' | '15m' | '30m' | '60m'
  onIntervalChange: (interval: string) => void
}

export function KlineChart({ symbol, interval, onIntervalChange }: KlineChartProps) {
  // 使用 lightweight-charts 的 CandlestickSeries
  // 支持缩放、平移、十字光标
  // 显示成交量柱状图
  // 实时更新最新 K 线
}
```

**文件**: `components/market/symbol-selector.tsx`

```typescript
interface SymbolSelectorProps {
  value: string
  onChange: (symbol: string) => void
  symbols: string[]
}

export function SymbolSelector({ value, onChange, symbols }: SymbolSelectorProps) {
  // 使用 Combobox 组件
  // 支持搜索过滤
  // 显示合约中文名称
}
```

#### 数据流设计

1. **初始加载**: 获取最近 500 根 K 线
2. **实时更新**: 每 5 秒轮询最新数据
3. **时间周期切换**: 重新请求对应周期数据
4. **合约切换**: 清空图表，加载新合约数据

#### 性能优化

- 使用 `useMemo` 缓存图表配置
- 使用 `useCallback` 缓存事件处理函数
- 限制最大 K 线数量为 1000 根
- 使用虚拟滚动优化大数据量

---

### 任务 1.3: 系统控制 UI 组件

#### 组件设计

**文件**: `components/dashboard/emergency-stop-button.tsx`

```typescript
export function EmergencyStopButton() {
  // 醒目的红色按钮
  // 点击弹出确认对话框
  // 需要输入暂停原因
  // 调用 pauseTrading API
}
```

**文件**: `components/dashboard/trading-status-banner.tsx`

```typescript
interface TradingStatusBannerProps {
  isPaused: boolean
  pauseReason?: string
  onResume: () => void
}

export function TradingStatusBanner({ isPaused, pauseReason, onResume }: TradingStatusBannerProps) {
  // 全局顶部横幅
  // 暂停时显示警告样式
  // 显示暂停原因
  // 提供恢复按钮
}
```

#### 交互流程

1. **暂停交易**:
   - 点击紧急暂停按钮
   - 弹出确认对话框
   - 输入暂停原因（必填）
   - 二次确认
   - 调用 API
   - 显示全局横幅

2. **恢复交易**:
   - 点击横幅中的恢复按钮
   - 弹出确认对话框
   - 二次确认
   - 调用 API
   - 隐藏横幅

---

### 任务 1.4: 批量操作 UI 组件

#### 组件设计

**文件**: `components/trading/batch-close-dialog.tsx`

```typescript
interface BatchCloseDialogProps {
  open: boolean
  positions: Position[]
  onClose: () => void
  onConfirm: (positionIds: string[]) => Promise<void>
}

export function BatchCloseDialog({ open, positions, onClose, onConfirm }: BatchCloseDialogProps) {
  // 显示选中的持仓列表
  // 计算总浮动盈亏
  // 显示预计手续费
  // 进度条显示平仓进度
  // 显示成功/失败结果
}
```

**文件**: `components/trading/stop-loss-dialog.tsx`

```typescript
interface StopLossDialogProps {
  open: boolean
  position: Position
  onClose: () => void
  onConfirm: (stopLoss: number) => Promise<void>
}

export function StopLossDialog({ open, position, onClose, onConfirm }: StopLossDialogProps) {
  // 显示当前持仓信息
  // 显示当前止损价
  // 输入新止损价
  // 计算止损距离百分比
  // 风险提示
}
```

#### 持仓列表增强

在 `app/(dashboard)/sim-trading/operations/page.tsx` 中：

- 添加全选/反选 Checkbox
- 添加批量平仓按钮（选中时启用）
- 每行添加修改止损按钮

---

### 任务 1.5: 执行质量统计卡片

#### 组件设计

**文件**: `components/trading/execution-quality-card.tsx`

```typescript
interface ExecutionQualityCardProps {
  stats: ExecutionStats
  loading?: boolean
}

export function ExecutionQualityCard({ stats, loading }: ExecutionQualityCardProps) {
  // 显示 4 个关键指标:
  // 1. 平均滑点 (avg_slippage)
  // 2. 拒单率 (rejection_rate)
  // 3. 平均延迟 (avg_latency_ms)
  // 4. 撤单率 (cancel_rate)
  
  // 使用进度条显示百分比指标
  // 使用颜色区分好坏 (绿/黄/红)
}
```

#### 集成位置

在模拟交易总览页面 `app/(dashboard)/sim-trading/page.tsx` 的风控状态卡片下方。

---

## 三、关键技术决策

### 1. K 线图库选择

**候选方案**:
- ✅ **lightweight-charts** (推荐)
  - 优点: 专业金融图表，性能优秀，API 简洁
  - 缺点: 需要额外安装依赖
  
- ❌ Recharts
  - 优点: 项目已使用，无需额外依赖
  - 缺点: 不是专业金融图表，K 线显示效果一般

- ❌ TradingView Lightweight Charts (商业版)
  - 优点: 功能最强大
  - 缺点: 需要付费授权

**决策**: 使用 `lightweight-charts`，性价比最高。

---

### 2. 数据刷新策略

| 数据类型 | 刷新间隔 | 策略 | 理由 |
|---------|---------|------|------|
| 账户信息 | 30 秒 | 轮询 | 变化频率低 |
| 持仓列表 | 30 秒 | 轮询 | 变化频率低 |
| 订单列表 | 10 秒 | 轮询 | 变化频率中等 |
| K 线数据 | 5 秒 | 轮询 | 需要实时性 |
| 风控状态 | 30 秒 | 轮询 | 变化频率低 |
| 执行质量 | 60 秒 | 轮询 | 统计数据，变化慢 |

**未来优化**: 考虑使用 WebSocket 实现真正的实时推送。

---

### 3. 状态管理

**当前方案**: 使用 React Hooks + Context

**组件级状态**:
- `useState` - 组件内部状态
- `useEffect` - 数据获取和轮询

**跨组件状态**:
- 暂停状态 - 使用 Context 全局共享
- 用户偏好 - 使用 localStorage 持久化

**未来优化**: 如果状态复杂度增加，考虑引入 Zustand 或 Jotai。

---

## 四、依赖库清单

### 需要新增的依赖

```json
{
  "dependencies": {
    "lightweight-charts": "^4.2.0"
  }
}
```

### 已有依赖（确认）

```json
{
  "dependencies": {
    "recharts": "^2.x",
    "lucide-react": "^0.x",
    "@radix-ui/react-dialog": "^1.x",
    "@radix-ui/react-checkbox": "^1.x"
  }
}
```

---

## 五、风险评估

### 高风险项

1. **服务未启动** ⚠️
   - **风险**: 无法验证 API 是否实现
   - **缓解**: 需要先启动服务再继续开发
   - **影响**: 批次 1/2/3 全部受影响

2. **K 线图组件复杂度** ⚠️
   - **风险**: lightweight-charts 学习曲线
   - **缓解**: 参考官方示例，先实现基础功能
   - **影响**: 批次 1 工期可能延长 0.5 天

3. **写操作授权未明确** ⚠️
   - **风险**: 开发完成后可能被禁用
   - **缓解**: 等待 Jay.S 确认后再开发
   - **影响**: 批次 1.3/1.4 可能取消

### 中风险项

1. **API 端点未实现**
   - **风险**: 部分 API 可能返回 404
   - **缓解**: 前端做好错误处理和降级
   - **影响**: 功能不完整但不阻塞

2. **数据格式不匹配**
   - **风险**: 后端返回格式与前端预期不一致
   - **缓解**: 添加数据适配层
   - **影响**: 需要额外调试时间

---

## 六、执行建议

### 立即可做（无需服务启动）

1. ✅ **K 线图组件开发** - 使用模拟数据先实现 UI
2. ✅ **权益曲线组件开发** - 使用模拟数据先实现 UI
3. ✅ **批量操作 UI 组件** - 先实现交互逻辑
4. ✅ **执行质量卡片** - 先实现 UI 布局

### 需要服务启动后

1. ⏸️ **API 对接验证** - 验证数据格式
2. ⏸️ **实时数据测试** - 测试轮询逻辑
3. ⏸️ **错误处理完善** - 处理各种异常情况

### 建议执行顺序

**阶段 1: UI 组件开发（使用模拟数据）**
- 开发 K 线图组件
- 开发权益曲线组件
- 开发批量操作对话框
- 开发执行质量卡片

**阶段 2: 服务启动与 API 验证**
- 启动 Sim-Trading 服务
- 验证 API 端点
- 调整数据适配层

**阶段 3: 集成与测试**
- 集成到页面
- 端到端测试
- 错误处理完善

---

## 七、下一步行动

### 等待确认的事项

1. **Jay.S 确认写操作授权** - 决定批次 1.3/1.4 是否执行
2. **服务启动计划** - 何时启动 Sim-Trading/Backtest/Decision 服务
3. **Atlas 建档** - 为批次 1 创建独立任务文件
4. **Token 签发** - 批次 1 文件级白名单 Token

### 可以立即开始的工作

1. ✅ **安装 lightweight-charts** - `pnpm add lightweight-charts`
2. ✅ **创建组件骨架** - 使用模拟数据先实现 UI
3. ✅ **编写单元测试** - 测试组件逻辑
4. ✅ **准备模拟数据** - 用于开发和测试

---

## 八、总结

### 关键发现

1. **只有 Data 服务在运行** - 其他 3 个服务都停止了
2. **Data 服务 75% 端点可用** - 2 个端点需要后端实现
3. **无法验证其他服务的 API** - 需要先启动服务
4. **K 线图是批次 1 最复杂的任务** - 需要 1.5 天

### 执行建议

**推荐方案**: 先用模拟数据开发 UI 组件，等服务启动后再对接真实 API。

**优势**:
- 不阻塞前端开发
- 可以先完成 UI 交互
- 降低服务依赖风险

**劣势**:
- 可能需要调整数据格式
- 需要额外的模拟数据准备

---

**报告生成人**: Livis (Claude/Kiro)  
**报告时间**: 2026-04-18  
**下一步**: 等待 Atlas 和 Jay.S 确认后开始批次 1 执行
