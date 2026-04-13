# 模拟交易端（sim-trading）功能比对：临时看板 vs v0 看板

**比对日期**：2026-04-13  
**临时看板路径**：`services/sim-trading/sim-trading_web/`  
**v0 看板路径**：`docs/portal-design/v0-close/app/sim-trading/` + `v0-close/sim-trading/`  
**后端 API**：`services/sim-trading/src/api/router.py` (port 8101)

---

## 页面级对比

| 页面 | 临时看板 | v0 看板（统一门户路由） | v0 独立子应用 | 差异 |
|------|---------|----------------------|------------|------|
| 首页/总览 | `app/page.tsx` (SPA 侧边栏切页) | `app/sim-trading/page.tsx` (风控仪表盘) | 无独立首页 | v0 首页只有风控，临时有完整 SPA 导航 |
| 交易终端 | `app/operations/page.tsx` ✅ **已对接API** | `app/sim-trading/operations/page.tsx` 🔴 全 mock | `sim-trading/app/operations/page.tsx` | v0 operations 全硬编码 mock 数据 |
| 行情报价 | `app/market/page.tsx` ✅ **已对接 CTP ticks** | `app/sim-trading/market/page.tsx` 🔴 全 mock | `sim-trading/app/market/page.tsx` | v0 market 是静态 mock 报价表 |
| 风控监控 | `app/intelligence/page.tsx` ✅ **已对接API** | `app/sim-trading/page.tsx`（风控面板） 🔴 部分 mock | `sim-trading/app/intelligence/page.tsx` | v0 风控 L1/L2/L3 数据全硬编码 |
| 品种风控 | `app/risk-presets/page.tsx` ✅ **已对接API** | `app/sim-trading/risk-presets/page.tsx` 🔴 全 mock | `sim-trading/app/risk-presets/page.tsx` | v0 品种风控 mock preset 表 |
| CTP 配置 | `app/ctp-config/page.tsx` ✅ **已对接API** | `app/sim-trading/ctp-config/page.tsx` 🔴 全 mock | `sim-trading/app/ctp-config/page.tsx` | v0 CTP 页面无法真正连接 |

---

## 组件级功能对比

### 交易终端 (operations)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 账户权益/可用/保证金 | ✅ `simApi.account()` 实时 | 🔴 硬编码 `¥1,245,680` | v0 需对接 `/account` |
| 持仓列表 | ✅ `simApi.positions()` 实时 | 🔴 mock positions 数组 (5条) | v0 需对接 `/positions` |
| 下单面板 | ✅ 完整下单 `simApi.placeOrder()` | 🟡 有 UI 无真实提交 | v0 需对接 `/orders` POST |
| 订单列表 | ✅ `simApi.orders()` | 🔴 mock orders (4条) | v0 需对接 `/orders` GET |
| 撤单 | ✅ `simApi.cancelOrder()` | ❌ 无撤单功能 | v0 需增加撤单 |
| 合约自动补全 | ✅ `ALL_CONTRACTS` + `instruments` | ❌ 无 | v0 缺失 |
| 执行质量 KPI | ✅ `ExecutionQualityKPI` + `/stats/execution` | ❌ 无 | v0 缺失 |
| 绩效 KPI | ✅ `PerformanceKPI` + `/stats/performance` | ❌ 无 | v0 缺失 |
| 快速预设下单 | ✅ `QuickOrderPresets` | ❌ 无 | v0 缺失 |
| 今日盈亏合计 | ✅ 实时计算 | 🔴 mock `+¥17,640` | v0 需从 API 聚合 |
| 批量平仓 | ✅ `/positions/batch_close` | ❌ 无 | v0 缺失（临时看板有） |

### 行情报价 (market)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 实时 Tick 数据 | ✅ `/ticks` 1s轮询 | 🔴 mock 10 条静态报价 | v0 需对接 `/ticks` |
| CTP 连接状态 | ✅ `/ctp/status` 实时 | 🔴 mock `已连接` | v0 需对接 `/ctp/status` |
| 自选列表管理 | ✅ localStorage 持久化 | ❌ 无 | v0 缺失 |
| 技术图表 | ✅ `TechnicalChart` + K线 | ❌ 无 K线组件 | v0 缺失 |
| 涨跌排行 | ✅ `MarketMovers` 排序 | ❌ 无 | v0 缺失 |
| 交易量/持仓量 | ✅ 实时 volume/OI | 🔴 mock 数据 | v0 需对接 |
| 分组看板 (按交易所) | ✅ WATCHLISTS 分组 | ❌ 无分组 | v0 缺失 |

### 风控监控 (intelligence)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| L1 预检查 (10项) | ✅ `/risk/l1` 实时 | 🔴 mock l1Checks (全 pass) | v0 需对接 `/risk/l1` |
| L2 日线级风控 | ✅ `/risk/l2` 连续亏损/保证金 | 🔴 mock `consecutiveLosses=2, marginLevel=45` | v0 需对接 `/risk/l2` |
| L3 熔断状态 | ✅ API 获取 | 🔴 mock `pass` | v0 需对接 |
| 告警历史 | ✅ localStorage + `/risk/alerts` | ❌ 无 | v0 缺失 |
| 日志查看面板 | ✅ `/logs/tail` 200条 + level filter | ❌ 无 | v0 缺失 |
| L2 盈亏曲线 | ✅ recharts `ComposedChart` | 🔴 mock 数组 10 点 | v0 需对接权益曲线 |
| 浏览器通知 | ✅ `requestNotificationPermission()` | ❌ 无 | v0 缺失 |
| 警报声音 | ✅ `playAlertSound()` | ❌ 无 | v0 缺失 |
| 交易日历 | ✅ `isTradingDay()` | ❌ 无 | v0 缺失 |
| 全局交易暂停/恢复 | ✅ `/system/pause` `/system/resume` | ❌ 无 | v0 缺失 |

### 品种风控 (risk-presets)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 风控预设加载 | ✅ `/risk-presets` API | 🔴 mock preset 表 | v0 需对接 |
| 按交易所筛选 | ✅ 5 个交易所 Tab | ❌ 无 | v0 缺失 |
| 单品种编辑保存 | ✅ `simApi.saveRiskPreset()` | ❌ 只读 mock | v0 需对接 POST |
| 品种保证金/手数上限 | ✅ 实时数据 | 🔴 mock | v0 需对接 |

### CTP 配置 (ctp-config)

| 功能/KPI | 临时看板 | v0 看板 | 差距 |
|---------|---------|--------|------|
| 读取 CTP 配置 | ✅ `/ctp/config` | 🔴 mock 表单 | v0 需对接 |
| 保存 CTP 配置 | ✅ POST `/ctp/config` | ❌ 无保存 | v0 需对接 |
| 连接/断开 CTP | ✅ `/ctp/connect` `/ctp/disconnect` | ❌ 无 | v0 缺失 |
| SimNow 预设切换 | ✅ 3 个预设 + 自动切换 | 🔴 mock 预设 | v0 需对接 |
| CTP 双前端状态 | ✅ md/td 分别显示 | 🔴 mock | v0 需对接 `/ctp/status` |
| 交易时段自动切换 | ✅ `isTradingHours()` 联动 | ❌ 无 | v0 缺失 |

---

## 后端 API 清单（sim-trading:8101 已有，v0 需对接）

| API | 方法 | 用途 | v0 当前状态 |
|-----|------|------|-----------|
| `/status` | GET | 服务状态 | ❌ 未用 |
| `/account` | GET | 账户权益 | ❌ 未用 |
| `/positions` | GET | 持仓列表 | ❌ 未用 |
| `/orders` | GET | 订单列表 | ❌ 未用 |
| `/orders` | POST | 下单 | ❌ 未用 |
| `/orders/cancel` | POST | 撤单 | ❌ 未用 |
| `/orders/errors` | GET | 下单错误记录 | ❌ 未用 |
| `/system/state` | GET | 全局状态 | ❌ 未用 |
| `/system/pause` | POST | 暂停交易 | ❌ 未用 |
| `/system/resume` | POST | 恢复交易 | ❌ 未用 |
| `/ctp/config` | GET/POST | CTP 配置 | ❌ 未用 |
| `/ctp/connect` | POST | 连接 CTP | ❌ 未用 |
| `/ctp/disconnect` | POST | 断开 CTP | ❌ 未用 |
| `/ctp/status` | GET | CTP 连接状态 | ❌ 未用 |
| `/ticks` | GET | 实时行情 | ❌ 未用 |
| `/risk-presets` | GET/POST | 品种风控 | ❌ 未用 |
| `/risk/l1` | GET | L1 风控检查 | ❌ 未用 |
| `/risk/l2` | GET | L2 风控 | ❌ 未用 |
| `/risk/alerts` | GET | 告警历史 | ❌ 未用 |
| `/stats/performance` | GET | 绩效统计 | ❌ 未用 |
| `/stats/execution` | GET | 执行质量 | ❌ 未用 |
| `/report/daily` | GET | 日报 | ❌ 未用 |
| `/logs/tail` | GET | 日志 | ❌ 未用 |
| `/equity/history` | GET | 权益曲线 | ❌ 未用 |
| `/market/kline/{symbol}` | GET | K线数据 | ❌ 未用 |
| `/market/movers` | GET | 涨跌排行 | ❌ 未用 |
| `/positions/batch_close` | POST | 批量平仓 | ❌ 未用 |

---

## 升级要求（Claude 实施清单）

### 优先级 P0（核心功能缺失）
1. **operations/page.tsx**：对接 `/account` `/positions` `/orders`，实现真实下单 `/orders` POST，实现撤单 `/orders/cancel`
2. **market/page.tsx**：对接 `/ticks` 实时轮询，对接 `/ctp/status`
3. **intelligence（即 sim-trading/page.tsx 风控面板）**：对接 `/risk/l1` `/risk/l2`，移除所有 mock let/const

### 优先级 P1（完善体验）
4. **risk-presets/page.tsx**：对接 `/risk-presets` GET/POST，实现按交易所筛选
5. **ctp-config/page.tsx**：对接 `/ctp/config` `/ctp/connect` `/ctp/disconnect`
6. 交易日历（holidays-cn）集成
7. 全局交易暂停/恢复按钮

### 优先级 P2（增强功能 - 从临时看板回补）
8. 合约自动补全组件（ALL_CONTRACTS）
9. ExecutionQualityKPI 组件
10. PerformanceKPI 组件
11. QuickOrderPresets 组件
12. TechnicalChart K线图组件
13. MarketMovers 涨跌排行组件
14. 告警历史 + 日志查看面板
15. 浏览器通知 + 警报声音

### 参考代码来源
- 临时看板 `services/sim-trading/sim-trading_web/lib/sim-api.ts`（完整 API client）
- 临时看板 `services/sim-trading/sim-trading_web/lib/contracts.ts`（合约列表）
- 临时看板 `services/sim-trading/sim-trading_web/lib/holidays-cn.ts`（交易日历）
- 临时看板各业务组件（已列在上表）
