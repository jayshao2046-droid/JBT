# TASK-0077 CS1-S 容灾交接API

【签名】Atlas  
【时间】2026-04-13  
【设备】MacBook  

## 基本信息

| 项 | 值 |
|----|-----|
| 任务编号 | TASK-0077 |
| 对应计划项 | CS1-S |
| 执行 Agent | Claude-Code |
| 服务 | sim-trading |
| 优先级 | P1 |
| Token ID | tok-629df929 |
| 状态 | Token 已签发 |

## 需求描述

decision 端的 LocalSimEngine（TASK-0076 CS1 已完成）在 sim-trading 不可用时可本地接管模拟交易。当 sim-trading 恢复后，需要提供交接 API 接收 decision 端积累的临时订单、持仓和账本差异，并完成任务回切。

## 白名单

| 文件 | 操作 |
|------|------|
| `services/sim-trading/src/api/router.py` | 修改（新增交接路由） |
| `services/sim-trading/src/failover/__init__.py` | 新建 |
| `services/sim-trading/src/failover/handler.py` | 新建 |
| `services/sim-trading/tests/test_failover.py` | 新建 |

## 验收标准

1. `POST /api/v1/failover/handover` 接收 decision LocalSimEngine 的订单/持仓/账本 JSON，写入本地账本
2. `GET /api/v1/failover/status` 返回交接状态（idle/receiving/completed/error）
3. `POST /api/v1/failover/confirm` 确认交接完成，清除临时状态
4. handler.py 实现交接逻辑：校验数据完整性 → 合并账本 → 更新持仓 → 返回差异摘要
5. 测试覆盖至少 8 个用例（正常交接、重复交接、数据校验失败、空数据等）
6. 所有 Pydantic model 使用 `Optional[str]` 而非 `str | None`（Python 3.9 兼容）
