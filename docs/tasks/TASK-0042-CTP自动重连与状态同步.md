# TASK-0042 CTP 自动重连与状态同步

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0042 |
| 任务标题 | CTP 自动重连与 system/state 状态同步 |
| 服务归属 | sim-trading |
| 执行 Agent | 模拟交易 / Atlas |
| 优先级 | P1 |
| 来源 | TASK-0039 / ISSUE-DR1-001 |
| 状态 | 建档完成，待实施 |

---

## 背景

1. `TASK-0039` 灾备演练确认 `ISSUE-DR1-001`：CTP gateway 在 `OnFrontDisconnected` 中仅记录断线与发送告警，没有应用层自动重连策略。
2. Mini 运行态复核发现另一处相关问题：日志已出现 `md_logged_in`，但 `/api/v1/system/state` 仍可能返回 `ctp_md_connected=false`，说明该接口依赖 `_system_state` 缓存，缺少实时同步。
3. 若只修自动重连、不修状态同步，会继续出现“实际已恢复但状态页仍显示断开”的假阴性。

---

## 白名单冻结

| 文件 | 操作 | 说明 |
|------|------|------|
| services/sim-trading/src/gateway/simnow.py | 修改 | 增加断线后单通道重连调度、去重与退避逻辑 |
| services/sim-trading/src/api/router.py | 修改 | `get_system_state()` / `ctp_status()` 返回前实时同步 gateway 状态 |
| services/sim-trading/tests/test_console_runtime_api.py | 修改 | 补充自动重连与状态同步测试 |

---

## 验收标准

1. MD 或 TD 任一通道触发 `OnFrontDisconnected` 后，网关会在后台调度该通道重连，不重复创建并发重连线程。
2. 自动重连不影响手动 `disconnect()` 的主动断开语义，不会在主动断开后立即拉起重连。
3. `/api/v1/system/state` 在请求时会先同步 gateway 实时状态，再做密码脱敏返回。
4. `tests/test_console_runtime_api.py` 覆盖至少以下场景：
   - 断线后只调度一次重连
   - 主动断开不调度重连
   - `system/state` 返回前同步连接状态且保持凭证脱敏

---

【签名】Atlas
【时间】2026-04-11 00:10
【设备】MacBook