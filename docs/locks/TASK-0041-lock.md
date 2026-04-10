# TASK-0041 锁控记录

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0041 |
| 任务标题 | CTP前端下单/撤单UI + system/state密码脱敏 |
| 锁控管理人 | 项目架构师 |
| 创建日期 | 2026-04-10 |

---

## 锁控文件清单

### A0 批次（治理建档）— 协同账本区，无需 Token

| 文件 | 操作 | 状态 | 写入者 |
|------|------|------|--------|
| docs/tasks/TASK-0041-CTP前端下单与密码脱敏.md | 新建 | ✅ 已完成 | Atlas |
| docs/reviews/TASK-0041-review.md | 新建 | ✅ 已完成 | Atlas |
| docs/locks/TASK-0041-lock.md | 新建 | ✅ 已完成 | Atlas |

### A 批次（CTP前端，P1，2 文件）

| 文件 | 操作 | Token | 状态 |
|------|------|-------|------|
| services/sim-trading/sim-trading_web/app/operations/page.tsx | 修改 | tok-2ce2cd05 | ✅ locked |
| services/sim-trading/sim-trading_web/lib/sim-api.ts | 修改 | tok-2ce2cd05 | ✅ locked |

### B 批次（密码脱敏，P0 安全，1 文件）

| 文件 | 操作 | Token | 状态 |
|------|------|-------|------|
| services/sim-trading/src/api/router.py | 修改 | tok-e83586d9 | ✅ locked |

### C 批次（CTP网关改进，P1，2 文件）

| 文件 | 操作 | Token | 状态 |
|------|------|-------|------|
| services/sim-trading/src/gateway/simnow.py | 修改 | 待签发 | 🔲 待签发 |
| services/sim-trading/tests/test_console_runtime_api.py | 修改 | 待签发 | 🔲 待签发 |

**C 批改进内容：**
1. `_select_tradeable_contract()` — 优先跳过当月/交割合约，选下一个可交易合约
2. `OnRtnOrder` 交易所拒绝追踪 — 状态码5+拒绝关键字时记录到 `_order_errors`
3. `query_account()` 公开方法暴露
4. 对应单元测试 3 个新用例

---

## 锁控日志

| 时间 | 操作 | 批次 | 说明 |
|------|------|------|------|
| 2026-04-10 | 建档 | A0 | 创建 task/review/lock |
| 2026-04-10 | 签发+lockback | A | tok-2ce2cd05 → locked; commit 16ac25b |
| 2026-04-10 | 签发+lockback | B | tok-e83586d9 → locked; commit 2e1d147; P0安全修复 |
| 2026-04-10 | 建档 | C | 追加 C 批网关改进白名单 |

---

【签名】Atlas
【时间】2026-04-10 20:30
【设备】MacBook
