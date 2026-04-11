# TASK-0059 — CA6 信号真闭环 → sim-trading

【签名】Atlas  
【时间】2026-04-11  
【设备】MacBook  
【状态】� Token 已签发（tok-3185c6c9/D + tok-c5b83bfe/S + tok-9e1369d9/C，等待 TASK-0055 完成后激活实施）

## 任务基本信息

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0059 |
| 任务名称 | CA6 信号真闭环 → sim-trading |
| 所属阶段 | Phase C / Lane-B |
| 主责服务 | `services/decision/`（信号发出侧）|
| 协同服务 | `services/sim-trading/`（信号接收侧）|
| 优先级 | P1 |
| 前置依赖 | **TASK-0055（CG2）完成**（人工审核通过才允许信号进入 sim-trading）|
| **⚠️ 跨服务** | 需独立 Token × 2（decision 侧 + sim-trading 侧各一个文件白名单）|
| 状态 | 📋 预建，未激活 |

## 激活条件

TASK-0055（CG2）经架构师终审并由 Jay.S 确认后自动激活。  
**激活时需同时申请 decision 侧 + sim-trading 侧两份 Token。**

## 任务背景

信号链路：CG2 人工审核通过 → CA6 触发信号派发 → decision `POST /signals/{id}/dispatch` → sim-trading `POST /api/v1/signals/receive` → sim-trading 执行订单。

**sim-trading 接收端代码实情（Atlas 预查）**：  
- `services/sim-trading/src/api/router.py` ✅ 已存在，路由前缀 `/api/v1`  
- router.py 当前端点：`/status`, `/positions`, `/orders`, `/orders/cancel`, `/orders/errors`, `/instruments`  
- **无 `/signals` 相关端点** → sim-trading 侧需新建 `POST /api/v1/signals/receive`

## 实现范围（最小白名单草案，待架构师确认）

### Decision 侧（services/decision/）

| 文件路径 | 操作 | 说明 |
|----------|------|------|
| `services/decision/src/api/routes/signal.py` | 修改 | 新增 `POST /api/v1/signals/{signal_id}/dispatch` 端点（已存在路由文件，追加端点）|
| `services/decision/src/core/signal_dispatcher.py` | 新建 | 信号派发核心逻辑（httpx 调用 sim-trading `/signals/receive`，含重试与超时）|
| `tests/decision/api/test_signal_dispatch.py` | 新建 | dispatch 端点测试（含 sim-trading mock）|

### Sim-trading 侧（services/sim-trading/）

| 文件路径 | 操作 | 说明 |
|----------|------|------|
| `services/sim-trading/src/api/router.py` | 修改 | 新增 `POST /api/v1/signals/receive` 端点，解析信号并调用内部 order gateway |
| `tests/sim_trading/api/test_signal_receive.py` | 新建 | 接收端测试 |

### 统一信号体格式（两侧必须一致）

```json
{
  "signal_id": "sg-uuid-xxx",
  "strategy_id": "st-uuid-yyy",
  "symbol": "rb2501",
  "direction": "buy",
  "quantity": 1,
  "price": null,
  "signal_type": "market",
  "source": "decision",
  "timestamp": "2026-04-11T09:30:00+08:00"
}
```

## 安全要求

1. `signal_dispatcher.py` 中 sim-trading URL 从 `JBT_SIM_TRADING_API_URL` 读取，**不得硬编码**。
2. sim-trading `/signals/receive` 必须校验 `signal_id` 格式（UUID v4），拒绝格式错误请求。
3. 重复 `signal_id` 必须幂等（same signal_id → return original result, no duplicate order）。

## 验收标准

1. `POST /api/v1/signals/{signal_id}/dispatch`（CG2 审核通过后调用）→ sim-trading 收到信号并返回 200 ✅
2. sim-trading `/signals/receive` 收到合法信号 → 内部触发 order gateway ✅
3. 重复发送同一 `signal_id` → 返回 200（幂等），不创建重复订单 ✅
4. sim-trading URL 从环境变量读取，单元测试用 mock 替代真实连接 ✅
5. 两侧 Token 独立，任一侧 Token 失效不影响对方 ✅
