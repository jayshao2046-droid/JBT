# TASK-0041 CTP前端下单UI与密码脱敏

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0041 |
| 任务标题 | CTP前端下单/撤单UI + system/state密码脱敏 |
| 服务归属 | sim-trading |
| 执行 Agent | 模拟交易 / Atlas |
| 优先级 | P1（A批前端）+ P0（B批安全脱敏） |
| 状态 | 建档完成，待预审 |

---

## 背景

1. CTP 已对接光大期货(broker 6000)，MD+TD 均在线运行。
2. 另一个 Copilot session 已完成前端下单/撤单/错误追踪 UI 的代码编写（commit `0c02441` 的后续工作），代码在工作树中未提交。
3. 同时发现 `/api/v1/system/state` 端点直接返回 `_system_state` 字典，含 `ctp_password` 和 `ctp_auth_code` 明文，属于 P0 安全漏洞。

---

## 批次划分

### A 批 — CTP 前端下单/撤单 UI（P1）

| 文件 | 操作 | 说明 |
|------|------|------|
| services/sim-trading/sim-trading_web/app/operations/page.tsx | 修改 | 新增真实下单/撤单/错误追踪 UI |
| services/sim-trading/sim-trading_web/lib/sim-api.ts | 修改 | 新增 OrderRequest/OrderResult/OrderError 类型 + createOrder/cancelOrder/orderErrors/instruments API |

### B 批 — system/state 密码脱敏（P0 安全）

| 文件 | 操作 | 说明 |
|------|------|------|
| services/sim-trading/src/api/router.py | 修改 | `get_system_state()` 返回值中 `ctp_password` 和 `ctp_auth_code` 用 `***` 替代 |

---

## 验收标准

### A 批
1. operations 页面可调用 `createOrder`/`cancelOrder` API
2. 订单错误列表可实时展示 `orderErrors` 返回值
3. 合约规格查询 `instruments` 可正常返回
4. `pnpm build` 无编译错误

### B 批
1. `GET /api/v1/system/state` 返回中 `ctp_password` 和 `ctp_auth_code` 字段值为 `***`
2. 内部逻辑（`ctp/connect`、`save_ctp_config` 等）仍可读取真实密码
3. `GET /api/v1/ctp/config` 保持现有脱敏逻辑不变

---

【签名】Atlas
【时间】2026-04-10 20:30
【设备】MacBook
