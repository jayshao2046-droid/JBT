# sim-trading 全量审计报告（2026-04-24）

| 模块 | 审计结论 | 问题 | 状态 |
|------|----------|------|------|
| src/api/router.py | 风控主路径已全量接入，接口逻辑清晰，风控点齐全 | B6/B7 已修复，B8/B9 本次修复 | ✅
| src/main.py | guardian/心跳/重连逻辑完善，冷却门控已加，重连限速已加，远端匿名访问已锁死 | B1/B2/B9 已修复，B8/B10 本次修复 | ✅
| src/gateway/simnow.py | 断线冷却 300s，gateway 实例管理合理 | B1 已修复，架构隐患已识别 | ✅
| src/api/router.py（connect 路径） | front 不可达时不再盲目 destroy+recreate gateway | B11 本次修复 | ✅
| src/notifier/feishu.py | 路由分流准确，category 优先 | B3 已修复 | ✅
| src/health/heartbeat.py | account 字段来源正确 | B4 已修复 | ✅
| src/risk/guards.py | 风控守卫逻辑健全，告警分级合理 | B6/B7 已修复 | ✅
| src/ledger/service.py | 持仓/账户快照逻辑正常 | 无 | ✅
| src/persistence/storage.py | JSON 存储线程安全 | 无 | ✅
| src/execution/service.py | 委托执行逻辑正常 | 无 | ✅
| src/failover/handler.py | 容灾接收逻辑正常 | 无 | ✅
| src/notifier/dispatcher.py | 去重/升级/冷却逻辑健全 | 无 | ✅
| src/notifier/quiet_window.py | 静默窗口穿透逻辑正确 | 无 | ✅
| src/notifier/trade_push.py | 成交回报推送及时 | 无 | ✅
| src/stats/performance.py | 绩效计算逻辑正常 | 无 | ✅
| src/stats/execution.py | 执行质量计算正常 | 无 | ✅
| src/stats/market.py | 市场异动计算正常 | 无 | ✅
| src/kpi/calculator.py | KPI 计算逻辑正常 | 无 | ✅

## 已修复问题（B1-B9）
- B1: 断线噪音（simnow.py/main.py 冷却门控）
- B2: guardian 断联报警冷却
- B3: 飞书路由 category 优先
- B4: 心跳 account 字段修正
- B5: 死代码清理
- B6: 灾难止损风控接入
- B7: 只减仓/持仓上限风控接入
- B8: 初始连接失败告警冷却（本次修复）
- B9: gw is None 路径静默（本次修复）
- B10: 非 production 且未配置 `SIM_API_KEY` 时，远端非 public API 默认锁死；仅保留本机与可信代理主机（Studio/本机）访问
- B11: `ctp_connect()` 建连前新增 md/td front TCP 探测，双 front 不可达时直接拒绝重建 gateway
- B12: 删除 `router.py` 中残留的 `CTP_AUTH_CODE` 硬编码默认值，避免凭证默认回退
- B13: guardian 记录最近一次建连尝试时间；闲时启动后 10 秒内不再立刻二次 reconnect，而是进入 throttle

## 本轮远端验证
- 已将 main.py 与 router.py 部署到 Alienware `192.168.31.187:8101`
- 远端健康检查通过：`/health -> {"status":"ok","service":"sim-trading"}`
- 新实例已确认启动：23:04 / 23:05 watchdog 重启后，23:07 watchdog 记录恢复为 `[OK] sim-trading alive on :8101`
- 新实例启动日志中未再检出 `CTP_CONNECT_FAILED` / `CTP_RECONNECT_FAIL` 关键字，说明“服务重启即立刻发 P1/P0”的已知噪声路径已压住
- 当前仍可见 CTP/SimNow 外部不可达导致的断联重试，但这是外部链路问题，不再等价于本地告警风暴
- 2026-04-24 23:48 远端实测：MacBook 无 key 直连 `GET /api/v1/status` 与 `GET /api/v1/ctp/config` 已从 `200` 收口为 `503 SIM_API_KEY not configured; remote access is locked`
- 2026-04-24 23:54 远端实测：新实例启动后只保留 initial connect；10 秒后 guardian 进入 `idle: disconnected ... reconnect throttled`，未再立即二次 destroy/recreate gateway

## 新增根因结论（2026-04-24 夜）
- 安全根因已坐实：Alienware 运行态在 `JBT_ENV!=production` 且缺失 `SIM_API_KEY` 时，会把所有非 public 读接口暴露给局域网；已用远端实测确认 `/api/v1/status`、`/api/v1/ctp/config`、`/api/v1/logs` 均可无 key 返回 `200`
- 断联主因已坐实：Alienware 到 SimNow `124.74.248.10:41213/41205` 的 TCP 连通性均为 `False`，说明当前主要断联源头在外部 front 不可达，而不是本地业务代码
- 重连抖动主因已坐实：guardian 在外部 front 双挂时仍会周期性调用 `ctp_connect()` 重建 gateway；本次已在 connect 入口加 reachability gate，避免双 front 不可达时继续 destroy+recreate
- 额外安全结论：本地服务初始化仍残留 `CTP_AUTH_CODE` 硬编码默认值；已确认 Alienware 运行态有显式 `.env` 提供该值，因此本次已删除硬编码回退，不影响现网凭证来源

## 遗留风险
- 架构隐患：ctp_connect() 每次 destroy+recreate gateway，长时间运行可能导致 CTP SDK 崩溃（已加限速，建议后续彻底复用实例）
- SimNow/CTP 网络不稳定，偶发断联属外部不可控
- Alienware watchdog 仅做本地 TCP 8101 探活，不看 HTTP 健康，也没有启动宽限期；手工重启窗口内可能出现一次额外补拉，但当前已恢复稳定
- Windows `JBT_SimTrading_Watchdog` 计划任务本体与远端 `watchdog_sim_trading.ps1` 不在当前仓内白名单资产中；其 TCP-only + 无 startup grace 的误判风险已被确认，后续若要彻底消除 23:04/23:05 这一类二次补拉，仍需单独任务改远端守护脚本

## 最终定性
- 外部根因：Alienware 到 SimNow `124.74.248.10:41213/41205` 的连通性不稳定或不可达，是当前 `md/td` 无法真正就绪的主因
- 本地安全根因：`SIM_API_KEY` 缺失时，旧逻辑把整个非 public 读接口面对局域网放开；现已收口为“仅本机 + 可信代理主机可无 key 访问”
- 本地运行根因：guardian 原逻辑会在启动后很快进入第二次 idle reconnect；现已改为按最近尝试时间节流，避免启动期自抖
- 守护遗留根因：Windows watchdog 仍然只有 TCP 探活，没有 `/health` 和 startup grace；这部分风险已定位，但仍需单独任务改远端守护脚本

---

**本报告由 Atlas 自动生成，所有主路径已全量审计，风控与通知链路已闭环。**
