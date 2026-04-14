# TASK-0109：sim-trading 开盘前5分钟检查 + 开盘飞书通知

## 任务信息

- 任务 ID：TASK-0109
- 任务名称：guardian 开盘前预检 + 开盘飞书通知
- 所属服务：sim-trading
- 执行 Agent：模拟交易 Agent（Copilot）
- 前置依赖：TASK-0107（sim-trading 已在 Alienware 运行）
- 当前状态：待 Token 签发

## 任务目标

在 `_ctp_connection_guardian()` 中新增：

1. **开盘前 5 分钟检查**（08:55 / 12:55 / 20:55 ±2 分钟匹配）
   - 检查 CTP 已登录（md + td 均 connected）
   - 检查账户数据已回传（ledger.get_account_summary() 有 balance）
   - 未就绪 → P0 告警 "开盘前5分钟 CTP 未就绪"
   - 已就绪 → P2 "✅ XX盘开盘前5分钟检查通过"

2. **开盘通知**（09:00 / 13:00 / 21:00 ±2 分钟匹配）
   - 发飞书 P2 通知 "🔔 XX盘开盘 — CTP状态"

## 允许修改文件白名单

| 文件 | 操作 |
|------|------|
| `services/sim-trading/src/main.py` | 修改 — 守护协程新增预检逻辑 |

## 验证方式

1. 代码：新增 `_PREOPEN_CHECKS` / `_SESSION_OPENS` 常量
2. 代码：新增 `_check_preopen()` / `_check_open()` 函数
3. 代码：新增 `_send_preopen_check()` / `_send_open_notification()` 函数
4. 守护循环中调用以上函数，tracking var 防重触发
