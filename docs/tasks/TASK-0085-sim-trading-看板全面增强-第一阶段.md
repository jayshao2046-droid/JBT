# TASK-0085 — sim-trading 看板全面增强（第一阶段：P0 + P1）

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0085 |
| 任务名称 | sim-trading 看板全面增强（第一阶段：P0 + P1） |
| 服务归属 | `services/sim-trading/` |
| 优先级 | P1 |
| 状态 | ✅ 已完成预审，Token 已签发 |
| Agent | Claude |
| 建档时间 | 2026-04-13 |
| 建档人 | Atlas |

---

## 一、任务背景

Claude 基于 SIMWEB-01 规划文档与只读诊断，提出对模拟交易临时看板的全面增强方案，覆盖 P0（核心功能补全）和 P1（用户体验提升）共 10 项功能。

参考文档：
- `services/sim-trading/参考文档/SIMWEB-01-模拟交易看板全面增强-第一阶段.md`
- `services/sim-trading/参考文档/SIMWEB-01-只读诊断报告.md`

---

## 二、功能范围

### P0（核心功能）
- P0-1：权益曲线历史数据持久化（后端 `equity/history` 端点）
- P0-2：L1/L2 风控实时数据端点（替换前端模拟数据）
- P0-3：止损修改功能（PATCH `positions/{id}/stop_loss`）

### P1（用户体验）
- P1-1：交易绩效 KPI（胜率/盈亏比/回撤/夏普/今日周月盈亏）
- P1-2：执行质量 KPI（滑点/拒绝率/延迟/撤单率/部分成交）
- P1-3：批量操作（批量平仓/按品种方向盈亏平仓）
- P1-4：快速下单预设（localStorage + F1-F12 快捷键）
- P1-5：实时风控告警推送（SSE + 浏览器通知 + 声音）
- P1-6：技术指标叠加（MA/MACD/RSI/布林带）
- P1-7：异动监控（涨速/振幅/成交量 Top 10）

---

## 三、文件白名单

### 后端（Python）

| 操作 | 文件路径 |
|------|---------|
| 修改 | `services/sim-trading/src/api/router.py` |
| 修改 | `services/sim-trading/src/ledger/service.py` |
| 修改 | `services/sim-trading/src/risk/guards.py` |
| 修改 | `services/sim-trading/src/execution/service.py` |
| 新建 | `services/sim-trading/src/stats/__init__.py` |
| 新建 | `services/sim-trading/src/stats/performance.py` |
| 新建 | `services/sim-trading/src/stats/execution.py` |
| 新建 | `services/sim-trading/src/stats/market.py` |
| 新建 | `services/sim-trading/tests/test_stats.py` |
| 新建 | `services/sim-trading/tests/test_batch_operations.py` |

### 前端（TypeScript/React）

| 操作 | 文件路径 |
|------|---------|
| 修改 | `services/sim-trading/sim-trading_web/app/operations/page.tsx` |
| 修改 | `services/sim-trading/sim-trading_web/app/intelligence/page.tsx` |
| 修改 | `services/sim-trading/sim-trading_web/app/market/page.tsx` |
| 修改 | `services/sim-trading/sim-trading_web/lib/sim-api.ts` |
| 新建 | `services/sim-trading/sim-trading_web/components/PerformanceKPI.tsx` |
| 新建 | `services/sim-trading/sim-trading_web/components/ExecutionQualityKPI.tsx` |
| 新建 | `services/sim-trading/sim-trading_web/components/QuickOrderPresets.tsx` |
| 新建 | `services/sim-trading/sim-trading_web/components/TechnicalChart.tsx` |
| 新建 | `services/sim-trading/sim-trading_web/components/MarketMovers.tsx` |
| 新建 | `services/sim-trading/sim-trading_web/lib/notification.ts` |
| 新建 | `services/sim-trading/sim-trading_web/lib/audio.ts` |
| 新建 | `services/sim-trading/sim-trading_web/public/alert.mp3` |

**总计：22 文件（10 后端 + 12 前端）**

---

## 四、边界约束

1. 严格限于 `services/sim-trading/**` 范围，不得触及其他服务
2. 不得修改 `docker-compose.dev.yml`、`.env.example`、`shared/**`
3. 权益历史数据只在内存中保留最近 30 天（不引入数据库）
4. 告警音频 `alert.mp3` 使用 Creative Commons 免版权素材或自生成
5. 不引入新的 Python 或 npm 依赖包

---

## 五、验收标准

1. 后端新增端点全部有单元测试（≥20 测试用例）
2. `pytest services/sim-trading/tests/ -q` 全部通过
3. `pnpm build` 无错误
4. 权益曲线刷新后数据不丢失
5. 风控页面显示真实 L1/L2 状态（非 mock）

---

## 六、变更日志

| 时间 | 操作 | 内容 |
|------|------|------|
| 2026-04-13 | 建档 | Atlas 基于 SIMWEB-01 方案建档 |
| 2026-04-13 | 预审 | 项目架构师预审通过 |
| 2026-04-13 | Token | Jay.S 签发 Token，Claude 执行 |
