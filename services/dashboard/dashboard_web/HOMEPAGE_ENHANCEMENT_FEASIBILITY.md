# Dashboard 首页强化可行性分析

## 一、后端 API 现状核查

### 1.1 sim-trading 服务（端口 8101）

#### ✅ 已存在的端点
```python
GET  /api/v1/account              # 账户信息（包含 local_virtual + ctp_snapshot）
GET  /api/v1/positions            # 持仓列表
GET  /api/v1/stats/performance    # 绩效统计（P1-1）
GET  /api/v1/risk/l1              # L1 风控状态（P0-2）
POST /api/v1/orders               # 下单接口（已实现完整风控校验）
POST /api/v1/orders/cancel        # 撤单接口
```

#### ❌ 缺失的端点
```python
# 前端期望的端点格式与后端实际不匹配：
GET /account                      # 前端期望，后端实际是 /api/v1/account
GET /positions                    # 前端期望，后端实际是 /api/v1/positions
GET /stats/performance            # 前端期望，后端实际是 /api/v1/stats/performance
GET /risk/l1                      # 前端期望，后端实际是 /api/v1/risk/l1
```

**问题：** 前端 API 路径缺少 `/api/v1` 前缀！

---

### 1.2 decision 服务（端口 8104）

#### ✅ 已存在的端点
```python
GET /signals/dashboard/signals    # Dashboard 信号摘要（line 265-276）
GET /signals                      # 完整信号列表
POST /signals/review              # 信号审核
```

#### ❌ 缺失的端点
```python
POST /signals/{id}/disable        # 禁止信号
POST /signals/{id}/enable         # 恢复信号
```

**问题：** 信号管理端点不存在，需要后端新增。

---

### 1.3 data 服务（端口 8105）

#### ❓ 未检查的端点
```python
GET /collectors                   # 数据采集器状态
GET /news                         # 新闻列表
```

**问题：** 需要检查 data 服务是否实现了这两个端点。

---

## 二、前端 API 层问题

### 2.1 路径前缀错误

**当前前端代码：**
```typescript
// lib/api/sim-trading.ts
const BASE = "/api/sim-trading"

export const simTradingApi = {
  getAccount: () => apiFetch<AccountInfo>(`${BASE}/account`),
  getPositions: () => apiFetch<Position[]>(`${BASE}/positions`),
  getPerformance: () => apiFetch<PerformanceStats>(`${BASE}/stats/performance`),
  getRiskL1: () => apiFetch<RiskL1>(`${BASE}/risk/l1`),
}
```

**实际后端路径：**
```python
# services/sim-trading/src/api/router.py
router = APIRouter(prefix="/api/v1", tags=["sim-trading"])

@router.get("/account")           # 实际路径: /api/v1/account
@router.get("/positions")         # 实际路径: /api/v1/positions
@router.get("/stats/performance") # 实际路径: /api/v1/stats/performance
@router.get("/risk/l1")           # 实际路径: /api/v1/risk/l1
```

**Next.js rewrite 配置：**
```typescript
// next.config.ts
async rewrites() {
  return [
    {
      source: '/api/sim-trading/:path*',
      destination: 'http://localhost:8101/api/v1/:path*',  // ✅ 正确
    },
  ]
}
```

**结论：** Next.js rewrite 配置正确，前端 API 路径也正确！问题不在这里。

---

### 2.2 数据结构不匹配

**前端期望的 AccountInfo：**
```typescript
export interface AccountInfo {
  equity: number       // 总权益
  available: number    // 可用资金
  margin: number       // 保证金
  float_pnl: number    // 浮动盈亏
}
```

**后端实际返回的结构：**
```python
{
  "connected": True,
  "local_virtual": {
    "label": "本地虚拟盘总本金",
    "principal": 500000.0,
    "currency": "CNY",
    "active_preset": "sim_50w"
  },
  "ctp_snapshot": {
    "connected": True,
    "balance": 500000.0,        # 对应 equity
    "available": 450000.0,      # 对应 available
    "margin": 50000.0,          # 对应 margin
    "floating_pnl": 1200.0,     # 对应 float_pnl
    "close_pnl": 800.0,
    "commission": 50.0,
    "initial_balance": 500000.0,
    "margin_rate": 10.0,
    "net_pnl": 2000.0,
    "note": "CTP 账户快照"
  }
}
```

**问题：** 前端期望扁平结构，后端返回嵌套结构！需要适配层。

---

## 三、可行性评估

### 3.1 我能做到的部分（✅ 可立即实现）

#### 阶段 1：Dialog 连接与状态管理
- ✅ 在首页引入 4 个 Dialog 组件
- ✅ 添加状态管理（useState）
- ✅ 连接回调函数到子组件
- ✅ 渲染 Dialog

**工作量：** 2 小时  
**依赖：** 无

---

#### 阶段 2：API 层修复与扩展

**2.1 修复数据结构适配（✅ 可立即实现）**
```typescript
// lib/api/sim-trading.ts
export const simTradingApi = {
  getAccount: async () => {
    const data = await apiFetch<any>(`${BASE}/account`)
    // 适配层：从嵌套结构提取扁平数据
    return {
      equity: data.ctp_snapshot?.balance || data.local_virtual?.principal || 0,
      available: data.ctp_snapshot?.available || 0,
      margin: data.ctp_snapshot?.margin || 0,
      float_pnl: data.ctp_snapshot?.floating_pnl || 0,
    } as AccountInfo
  },
}
```

**2.2 新增开仓/平仓 API（✅ 可立即实现）**
```typescript
// lib/api/sim-trading.ts
export const simTradingApi = {
  // 开仓（信号确认）
  openPositionFromSignal: (data: {
    signal_id: string
    quantity: number
    stop_loss: number
    take_profit: number
  }) => {
    // 调用后端 POST /api/v1/orders
    return apiFetch(`${BASE}/orders`, {
      method: "POST",
      body: JSON.stringify({
        instrument_id: data.signal_id,  // 需要从 signal 获取
        direction: "buy",  // 需要从 signal 获取
        offset: "open",
        price: 0,  // 市价单
        volume: data.quantity,
      }),
    })
  },
  
  // 平仓
  closePosition: (data: {
    instrument_id: string
    direction: "long" | "short"
    quantity: number
  }) => {
    return apiFetch(`${BASE}/orders`, {
      method: "POST",
      body: JSON.stringify({
        instrument_id: data.instrument_id,
        direction: data.direction === "long" ? "sell" : "buy",
        offset: "close",
        price: 0,  // 市价单
        volume: data.quantity,
      }),
    })
  },
}
```

**工作量：** 2 小时  
**依赖：** 无

---

#### 阶段 3：操作逻辑实现（✅ 可立即实现）
- ✅ 实现 Dialog 提交处理函数
- ✅ 添加 Toast 提示
- ✅ 添加 loading 状态
- ✅ 错误处理

**工作量：** 3 小时  
**依赖：** 阶段 1 + 阶段 2

---

#### 阶段 4：数据刷新机制（✅ 可立即实现）
- ✅ 扩展 useDashboardData hook，添加 refetch 函数
- ✅ 添加定时轮询（30 秒）
- ✅ 连接 AppHeader 刷新按钮

**工作量：** 2 小时  
**依赖：** 无

---

#### 阶段 5：用户体验优化（✅ 可立即实现）
- ✅ 添加 Toaster 组件到 layout
- ✅ 添加 Loading 状态到 Dialog
- ✅ 优化错误边界处理

**工作量：** 1 小时  
**依赖：** 无

---

### 3.2 我不能做到的部分（❌ 需要后端支持）

#### 信号管理 API（decision 服务）
```python
# 需要后端新增：
POST /signals/{id}/disable        # 禁止信号
POST /signals/{id}/enable         # 恢复信号
```

**影响：** 用户点击"禁止信号"按钮后，前端无法调用 API，只能本地状态管理（刷新后失效）

**替代方案：** 
- 前端本地维护禁止列表（localStorage）
- 刷新后从 localStorage 恢复状态
- 等待后端实现后再切换到 API

---

#### 数据服务端点验证（data 服务）
```python
# 需要验证是否存在：
GET /collectors                   # 数据采集器状态
GET /news                         # 新闻列表
```

**影响：** 如果不存在，首页的"数据源状态"和"新闻列表"模块会显示空数据

**替代方案：**
- 前端先用空数组兜底
- 等待后端实现后再对接

---

## 四、最终答案

### 我能做到的（90%）：

✅ **完整实现 Dialog 交互逻辑**
- 手动开仓 Dialog ✅
- 信号确认开仓 Dialog ✅
- 平仓 Dialog ✅
- 禁止信号 Dialog ✅（本地状态管理）

✅ **完整实现 API 对接**
- 账户信息 ✅（需要适配层）
- 持仓列表 ✅
- 绩效统计 ✅
- 风控指标 ✅
- 开仓操作 ✅（调用 POST /orders）
- 平仓操作 ✅（调用 POST /orders）

✅ **完整实现数据刷新**
- 定时轮询 ✅
- 手动刷新 ✅
- 操作后刷新 ✅

✅ **完整实现用户反馈**
- Toast 提示 ✅
- Loading 状态 ✅
- 错误处理 ✅

---

### 我不能做到的（10%）：

❌ **信号管理 API**
- 禁止/恢复信号需要后端新增端点
- 前端可用 localStorage 临时替代

❌ **数据服务端点验证**
- 需要检查 data 服务是否实现了 collectors 和 news 端点
- 前端可用空数组兜底

---

## 五、实施建议

### 方案 A：立即实施（推荐）
1. 我先实现 90% 的功能（Dialog + API + 刷新 + 反馈）
2. 信号管理用 localStorage 临时替代
3. 数据服务端点用空数组兜底
4. 等待后端补齐后再切换

**优点：** 用户可以立即使用核心功能（开仓/平仓）  
**缺点：** 信号禁止功能刷新后失效

---

### 方案 B：等待后端（不推荐）
1. 等待后端实现信号管理 API
2. 等待后端确认数据服务端点
3. 再开始前端实施

**优点：** 一次性完成 100% 功能  
**缺点：** 用户需要等待更长时间

---

## 六、我的建议

**立即开始实施方案 A**，理由：
1. 核心功能（开仓/平仓）可以立即使用
2. 信号禁止功能的临时方案（localStorage）足够应对短期需求
3. 数据服务端点即使缺失，也不影响核心交易流程
4. 后端补齐后，前端只需修改 2-3 行代码即可切换

**预计完成时间：** 8-10 小时（约 1.5 个工作日）

---

**你的决定？**
- [ ] 方案 A：立即实施（我推荐）
- [ ] 方案 B：等待后端
- [ ] 方案 C：其他建议
