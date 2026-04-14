# TASK-0109 Token 签发记录

【签名】模拟交易 Agent（Copilot）  
【时间】2026-04-15  
【设备】MacBook  
【任务文档】docs/tasks/TASK-0109-guardian开盘预检与开盘通知.md  

---

## Token

| 字段 | 值 |
|------|-----|
| token_id | `tok-043ddfca-aac0-48ac-84df-35ebeee28abb` |
| task_id | TASK-0109 |
| agent | 模拟交易Agent |
| action | edit |
| ttl | 60 分钟 |
| issued_at | 2026-04-15 |
| 状态 | 🔒 已锁回（approved） |

**白名单（1 文件）：**

| 文件 | 操作 |
|------|------|
| `services/sim-trading/src/main.py` | 修改 — 新增开盘前5分钟预检 + 开盘飞书通知逻辑 |

**实际变更摘要：**

- 新增常量 `_PREOPEN_CHECKS`（08:55/12:55/20:55）和 `_SESSION_OPENS`（09:00/13:00/21:00）
- 新增防重变量 `_last_preopen_sent` / `_last_open_sent`
- 新增函数 `_check_preopen()` / `_check_open()`（±2min 匹配，周末 None）
- 新增 `_send_preopen_check()`：td+md 未连接 → P0 告警；账户未回传 → P1；全就绪 → P2 确认
- 新增 `_send_open_notification()`：开盘时 P2 "🔔 XX盘开盘 — CTP状态"
- 代码已 scp 推送到 Alienware：`C:\Users\17621\jbt\services\sim-trading\src\main.py`
- 语法验证：`ast.parse` SYNTAX_OK
