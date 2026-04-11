# sim-trading

## 角色

JBT 模拟交易服务，唯一目标是对接 SimNow 并完成模拟交易执行。

## 固定边界

1. 只负责 SimNow 模拟交易。
2. 不使用内存模拟交易。
3. 不使用 TqSim 作为模拟盘。
4. 自己维护订单、成交、持仓、资金和风控执行链。
5. 只通过 API 接收决策端或人工操作指令。

## 端口

- 后端 API：8101
- 前端看板（sim-trading_web）：3002

## 目录职责

- `src/api/` — API 路由（28 个端点）
- `src/gateway/` — CTP/SimNow 网关（MdSpi + TdSpi + 自动重连）
- `src/execution/` — 交易执行服务（委托到 gateway）
- `src/ledger/` — 内存账本（trade/account/position/daily_report）
- `src/risk/` — 风控守卫（reduce_only/disaster_stop/emit_alert）
- `src/notifier/` — 通知系统（飞书卡片 + HTML 邮件，去重/抑制/升级/恢复）
- `tests/` — 72 个测试函数（1,480 行）
- `configs/` — SimNow、风控、通知配置
- `sim-trading_web/` — Next.js 15 前端看板（5 页面，10,571 行 TSX/TS）

## 外部依赖

- 上游：decision（信号接收 `/api/v1/signals/receive`）
- 下游：dashboard（只读查询）
- 兼容层：legacy-botquant

## 快速启动

```bash
# 复制环境模板
cp .env.example .env
# 编辑 .env，填入 SimNow 账号密码

# 安装依赖
pip install -r requirements.txt

# 启动后端
uvicorn src.main:app --host 0.0.0.0 --port 8101

# 启动前端看板
cd sim-trading_web && pnpm install && pnpm dev
```

## API 端点

| # | 方法 | 路径 | 说明 |
|---|---|---|---|
| 1 | GET | `/health` | 健康检查 |
| 2 | GET | `/api/v1/status` | 服务状态 |
| 3 | GET | `/api/v1/positions` | 持仓查询 |
| 4 | GET | `/api/v1/orders` | 订单列表 |
| 5 | POST | `/api/v1/orders` | 下单（6层前置校验） |
| 6 | POST | `/api/v1/orders/cancel` | 撤单 |
| 7 | GET | `/api/v1/orders/errors` | 订单错误日志 |
| 8 | GET | `/api/v1/instruments` | 合约规格查询 |
| 9 | GET | `/api/v1/system/state` | 系统全量状态（脱敏） |
| 10 | POST | `/api/v1/system/pause` | 暂停交易 |
| 11 | POST | `/api/v1/system/resume` | 恢复交易 |
| 12 | POST | `/api/v1/system/preset` | 切换预设 |
| 13 | GET | `/api/v1/ctp/config` | CTP 配置（脱敏） |
| 14 | POST | `/api/v1/ctp/config` | 保存 CTP 配置 |
| 15 | POST | `/api/v1/ctp/connect` | 连接 CTP |
| 16 | POST | `/api/v1/ctp/disconnect` | 断开 CTP |
| 17 | GET | `/api/v1/ctp/status` | CTP 双通道状态 |
| 18 | GET | `/api/v1/ticks` | 实时 Tick 行情 |
| 19 | GET | `/api/v1/risk-presets` | 58品种风控预设 |
| 20 | POST | `/api/v1/risk-presets` | 更新风控预设 |
| 21 | GET | `/api/v1/account` | 账户信息 |
| 22 | POST | `/api/v1/signals/receive` | 信号接收（幂等） |
| 23 | POST | `/api/v1/strategy/publish` | 策略发布接收 |
| 24 | GET | `/api/v1/report/daily` | 日报数据 |
| 25 | GET | `/api/v1/report/trades` | 成交列表 |
| 26 | GET | `/api/v1/report/positions` | 持仓列表 |
| 27 | GET | `/api/v1/logs` | 日志查询 |
| 28 | GET | `/api/v1/logs/tail` | 日志轮询 |

## 前端看板页面（sim-trading_web）

| 页面 | 路由 | 功能 |
|---|---|---|
| 风控监控 | `/intelligence` | L1/L2/L3 三层风控、告警历史、日志实时查看 |
| 交易终端 | `/operations` | 下单/撤单、5档盘口、权益曲线、持仓/订单流 |
| 行情报价 | `/market` | 自选列表、实时 Tick、涨跌统计 |
| 品种风控 | `/risk-presets` | 58品种风控参数可视化编辑 |
| CTP 配置 | `/ctp-config` | SimNow 前置地址管理、自动时段切换 |

## 技术栈

- **后端**：Python 3.11 / FastAPI / openctp-ctp 6.7.7
- **前端**：Next.js 15 / React 19 / Tailwind CSS / Recharts / shadcn/ui
- **CTP 网关**：openctp-ctp (MdApi + TraderApi)，支持 SimNow 7×24 + 交易时段自动切换
| GET | /api/v1/positions | 持仓查询（占位） |
| GET | /api/v1/orders | 订单查询（占位） |
| POST | /api/v1/orders | 下单（占位） |

## 批次进度

- ✅ A0：`.env.example` 占位符字段冻结（commit e713640）
- ✅ A1：入口 + API 骨架（本批次）
- ⏳ B：execution / ledger 骨架
- ⏳ C：risk / gateway 骨架 + 风控钩子占位
