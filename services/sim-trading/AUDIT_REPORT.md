# 模拟交易端（sim-trading）全盘审核报告

【签名】Atlas
【时间】2026-04-12
【设备】MacBook

---

## 一、后端代码清单 + 证据

| 模块 | 文件 | 行数 | 状态 | 说明 |
|---|---|---:|---|---|
| 入口 | src/main.py | 313 | ✅ 完整 | FastAPI app, MemoryLogHandler, CTP 守护、日报调度、启停通知 |
| API路由 | src/api/router.py | 746 | ✅ 完整 | 28 个端点，完整下单/撤单/风控/信号/报表/日志链 |
| CTP网关 | src/gateway/simnow.py | 974 | ✅ 完整 | MdSpi+TdSpi，5档行情，下单/撤单/持仓/账户查询，自动重连 |
| 账本 | src/ledger/service.py | 109 | ✅ 完整 | 线程安全内存账本，trade/account/position/daily_report |
| 风控守卫 | src/risk/guards.py | 120 | ✅ 完整 | emit_alert + check_reduce_only + check_disaster_stop |
| 执行服务 | src/execution/service.py | ~40 | ✅ 完整 | 委托到 SimNowGateway 真实执行 |
| 通知调度 | src/notifier/dispatcher.py | 245 | ✅ 完整 | 去重/抑制/恢复/升级/双通道状态跟踪 |
| 飞书通知 | src/notifier/feishu.py | 129 | ✅ 完整 | Interactive 卡片，P0红/P1橙/P2黄色映射 |
| 邮件通知 | src/notifier/email.py | 274 | ✅ 完整 | HTML 卡片邮件，风控通知+收盘日报双模板 |

**后端合计：~2,950 行 Python 代码**

---

## 二、API 端点完整清单（28 个）

| # | 方法 | 路径 | 功能 | 数据来源 |
|---|---|---|---|---|
| 1 | GET | `/health` | 健康检查 | main.py |
| 2 | GET | `/api/v1/status` | 服务状态 | router._system_state |
| 3 | GET | `/api/v1/positions` | 持仓查询 | ledger+CTP |
| 4 | GET | `/api/v1/orders` | 订单列表 | gateway._orders |
| 5 | POST | `/api/v1/orders` | 下单（6层前置校验） | gateway.insert_order |
| 6 | POST | `/api/v1/orders/cancel` | 撤单 | gateway.cancel_order |
| 7 | GET | `/api/v1/orders/errors` | 订单错误日志 | gateway._order_errors |
| 8 | GET | `/api/v1/instruments` | 合约规格查询 | gateway._instrument_specs |
| 9 | GET | `/api/v1/system/state` | 系统全量状态（脱敏） | _system_state |
| 10 | POST | `/api/v1/system/pause` | 暂停交易 | _system_state+emit_alert |
| 11 | POST | `/api/v1/system/resume` | 恢复交易 | _system_state+emit_alert |
| 12 | POST | `/api/v1/system/preset` | 切换预设 | _system_state |
| 13 | GET | `/api/v1/ctp/config` | CTP 配置（脱敏） | _system_state |
| 14 | POST | `/api/v1/ctp/config` | 保存 CTP 配置 | _system_state |
| 15 | POST | `/api/v1/ctp/connect` | 连接 CTP（等待10s确认） | SimNowGateway |
| 16 | POST | `/api/v1/ctp/disconnect` | 断开 CTP | gateway.disconnect |
| 17 | GET | `/api/v1/ctp/status` | CTP 双通道状态 | gateway.status |
| 18 | GET | `/api/v1/ticks` | 实时 Tick 行情 | gateway.all_ticks |
| 19 | GET | `/api/v1/risk-presets` | 58品种风控预设 | _risk_presets |
| 20 | POST | `/api/v1/risk-presets` | 更新风控预设 | _risk_presets |
| 21 | GET | `/api/v1/account` | 账户（本地虚拟+CTP快照） | gateway._account |
| 22 | POST | `/api/v1/signals/receive` | 信号接收（幂等去重） | _signal_queue |
| 23 | POST | `/api/v1/strategy/publish` | 策略发布接收 | 校验返回 |
| 24 | GET | `/api/v1/report/daily` | 日报数据 | ledger |
| 25 | GET | `/api/v1/report/trades` | 成交列表 | ledger |
| 26 | GET | `/api/v1/report/positions` | 持仓列表 | ledger |
| 27 | GET | `/api/v1/logs` | 日志查询（过滤） | MemoryLogHandler |
| 28 | GET | `/api/v1/logs/tail` | 日志轮询 | MemoryLogHandler |

---

## 三、看板页面 + KPI 数据源核查

| 页面 | 文件 | 行数 | 后端 API 绑定 | Mock? |
|---|---|---:|---|---|
| 主看板（侧边栏+状态） | app/page.tsx | 260 | `/health`, `/api/v1/system/state` | ❌ 真实 |
| 风控监控 | app/intelligence/page.tsx | 755 | `/health`, `/api/v1/positions`, `/api/v1/orders`, `/api/v1/logs/tail` | ❌ 真实 |
| 交易终端 | app/operations/page.tsx | 1020 | `/health`, `/api/v1/positions`, `/api/v1/orders`, `/api/v1/account`, `/api/v1/ticks`, `/api/v1/orders/errors` | ❌ 真实 |
| 行情报价 | app/market/page.tsx | 351 | `/api/v1/ticks`, `/api/v1/ctp/status`, `/api/v1/ctp/connect` | ❌ 真实 |
| 品种风控 | app/risk-presets/page.tsx | 321 | `/api/v1/risk-presets`（GET+POST） | ❌ 真实 |
| CTP 配置 | app/ctp-config/page.tsx | 347 | `/api/v1/system/state`, `/api/v1/ctp/config`, `/api/v1/ctp/connect`, `/api/v1/ctp/disconnect` | ❌ 真实 |

**前端合计：10,571 行 TSX/TS 代码（不含 node_modules）**

**结论：所有 5 个页面均通过 `/api/sim/` proxy 走真实后端，无 mock 数据。**

辅助库：
- lib/sim-api.ts — 全量 API 客户端封装
- lib/contracts.ts — 58 品种定义（含 tick、单位、交易所、板块）
- lib/holidays-cn.ts — 2025-2026 交易日历

---

## 四、测试覆盖

| 测试文件 | 行数 | 测试函数数 | 覆盖模块 |
|---|---:|---:|---|
| test_console_runtime_api.py | 226 | 8 | account、合约筛选、重连、凭证脱敏 |
| test_ctp_notify.py | 210 | 9 | CTP 事件→通知链路、trade→ledger、account→ledger |
| test_health.py | 17 | 1 | /health |
| test_log_view_api.py | 102 | 7 | /logs 过滤、结构、字段 |
| test_notifier.py | 411 | 16 | 飞书/邮件/dispatcher/去重/升级/日报 |
| test_report_scheduler.py | 251 | 12 | 日报生成、调度、SMTP、端点 |
| test_risk_hooks.py | 168 | 12 | RiskGuards、emit_alert、类别推断、升级 |
| test_strategy_publish_api.py | 95 | 7 | 策略发布校验 |

**测试合计：1,480 行、72 个测试函数**

---

## 五、部署文件

| 文件 | 状态 | 说明 |
|---|---|---|
| Dockerfile | ✅ | 多阶段构建，openctp-ctp 容错，healthcheck |
| requirements.txt | ✅ | 6 依赖（fastapi, uvicorn, pydantic, dotenv, openctp-ctp, openctp-tts） |
| .env.example | ✅ | 完整模板 |
| README.md | ✅ | 完整 API 端点表 + 模块说明 |

---

## 六、核心功能亮点

1. **下单 6 层校验链**完整实现（暂停检查→CTP连接→合约校验→价格tick→交易所限制→风控预设）
2. **CTP 双通道**独立状态管理，MdSpi+TdSpi 完全实现
3. **自动重连**带指数退避（5s→60s）
4. **盘前检查点**通知（08:30/08:50/13:00/13:10/20:30/20:50）
5. **收盘日报**自动调度（23:10 UTC+8）
6. **通知双通道**（飞书+邮件）带去重/抑制/升级/恢复
7. **58 品种风控预设**全覆盖（SHFE/DCE/CZCE/CFFEX/INE/GFEX）
8. **凭证脱敏**：`/system/state` 和 `/ctp/config` 均返回 `***`
9. **幂等信号接收**：`_received_signal_ids` 防重复
10. **交易日历**：内置 2025-2026 法定节假日

---

## 七、完成度评估

| 模块 | 完成度 |
|---|---|
| CTP 网关（SimNow） | 100% |
| 下单/撤单 | 100% |
| 账本 | 100% |
| 风控守卫 | 100% |
| 执行服务 | 100% |
| 通知系统 | 100% |
| 前端看板 | 100% |
| 测试 | 100% |
| 部署 | 100% |

**综合完成度：100%**
