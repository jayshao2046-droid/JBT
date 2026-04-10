# TASK-0042 预审记录

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0042 |
| 任务标题 | CTP 自动重连与 system/state 状态同步 |
| 审核人 | 项目架构师（Atlas 代记录） |
| 审核日期 | 2026-04-11 |
| 审核结果 | ✅ 预审通过 |

---

## 预审检查清单

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | 服务归属明确 | ✅ | 仅 sim-trading 单服务 |
| 2 | 不涉及跨服务 | ✅ | 无跨服务 import 或共享契约改动 |
| 3 | 不涉及 P0 保护区 | ✅ | 仅服务内业务文件与测试 |
| 4 | 问题来源明确 | ✅ | 直接来自 `TASK-0039` 的 `ISSUE-DR1-001` |
| 5 | 白名单最小必要 | ✅ | 2 个业务文件 + 1 个测试文件 |
| 6 | 验收标准明确 | ✅ | 自动重连、主动断开、状态同步三类验证 |

---

## 预审意见

1. 本任务必须同时修复两处相关缺陷：应用层自动重连缺失、`system/state` 状态缓存滞后。
2. 不扩大到 Docker restart policy 或 data_scheduler 守护，这两项保留给后续独立子任务。
3. 自动重连必须避免重复线程与重连风暴，至少具备单通道去重与基础退避。

---

## 白名单冻结

```
services/sim-trading/src/gateway/simnow.py
services/sim-trading/src/api/router.py
services/sim-trading/tests/test_console_runtime_api.py
```

---

【签名】Atlas（代项目架构师记录）
【时间】2026-04-11 00:10
【设备】MacBook