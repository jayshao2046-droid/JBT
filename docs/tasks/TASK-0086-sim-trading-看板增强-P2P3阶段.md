# TASK-0086 — Sim-Trading 看板增强 P2/P3 阶段

**任务编号**：TASK-0086  
**父任务**：TASK-0085（SIMWEB-01 P0+P1，已完成）  
**创建时间**：2026-04-13  
**创建人**：Atlas  
**执行人**：Claude Code  
**状态**：🔒 已完成并锁回（2026-04-13）

---

## 一、任务背景

SIMWEB-01（TASK-0085）完成后，Claude 在同一工作窗口超出范围实现了 P2（中优先级，6项）和 P3（高级功能，3项）。代码已在本地，测试通过，但未提交（正确遵守禁提交规则）。本任务为 P2/P3 部分补建审批流程，签发后允许提交。

---

## 二、功能范围

### P2（中优先级，6项）

| 编号 | 功能 | 说明 |
|------|------|------|
| P2-1 | 持仓分析增强 | 饼图/排行榜/集中度/时长分布 |
| P2-2 | 订单流增强 | 筛选/搜索/CSV导出/统计 |
| P2-3 | 风控规则可视化编辑 | L1开关 + L2阈值滑块 |
| P2-4 | 连接质量监控 | 延迟/丢包率/重连次数/历史图表 |
| P2-5 | 风控模板功能 | 预设模板/自定义/导入导出 |
| P2-6 | 多周期切换 | 1m/5m/15m/30m/1h/1d |

### P3（高级功能，3项）

| 编号 | 功能 | 说明 |
|------|------|------|
| P3-1 | 键盘快捷键系统 | 8个全局快捷键 |
| P3-2 | 主题切换 | 暗色/亮色模式 + localStorage 持久化 |
| P3-3 | 交易热力图 | 时段热力图 + 品种频率 Top 10 |

---

## 三、文件白名单（15个文件）

### 后端（Python）—— 新建目录

| 操作 | 文件路径 |
|------|---------|
| 新建目录 | `services/sim-trading/src/kpi/` |
| 新建 | `services/sim-trading/src/kpi/__init__.py` |
| 新建 | `services/sim-trading/src/kpi/calculator.py` |
| 新建目录 | `services/sim-trading/src/persistence/` |
| 新建 | `services/sim-trading/src/persistence/__init__.py` |
| 新建 | `services/sim-trading/src/persistence/storage.py` |

### 前端（TypeScript/React）—— 新建文件

| 操作 | 文件路径 |
|------|---------|
| 新建 | `services/sim-trading/sim-trading_web/components/ConnectionQuality.tsx` |
| 新建 | `services/sim-trading/sim-trading_web/components/KeyboardShortcutsHelp.tsx` |
| 新建 | `services/sim-trading/sim-trading_web/components/OrderFlowEnhanced.tsx` |
| 新建 | `services/sim-trading/sim-trading_web/components/PositionAnalysis.tsx` |
| 新建 | `services/sim-trading/sim-trading_web/components/RiskConfigEditor.tsx` |
| 新建 | `services/sim-trading/sim-trading_web/components/RiskTemplates.tsx` |
| 新建 | `services/sim-trading/sim-trading_web/components/ThemeToggle.tsx` |
| 新建 | `services/sim-trading/sim-trading_web/components/TradeHeatmap.tsx` |
| 新建 | `services/sim-trading/sim-trading_web/lib/keyboard.ts` |

### 前端 —— 修改文件

| 操作 | 文件路径 |
|------|---------|
| 修改 | `services/sim-trading/sim-trading_web/components/TechnicalChart.tsx` |

### 公共文档

| 操作 | 文件路径 |
|------|---------|
| 新建 | `services/sim-trading/sim-trading_web/public/alert-audio-note.md` |

**总计：15 文件（6 后端 + 9 前端）**

---

## 四、边界约束

1. 严格限于 `services/sim-trading/**`，禁止跨服务
2. 不引入新的 Python 或 npm 依赖包
3. `src/kpi/` 和 `src/persistence/` 仅作 sim-trading 内部使用，禁止被其他服务 import
4. 风控配置修改只写入内存或 localStorage，不引入外部数据库
5. 不修改 `docker-compose.dev.yml`、`.env.example`、`shared/**`

---

## 五、验收标准

- [x] `pytest tests/ -q` → 109 passed, 1 skipped ✅
- [x] `pnpm build` → Compiled successfully（9 routes）✅
- [x] P2 功能：持仓分析/订单流/风控编辑/连接质量/模板/周期切换全部可用 ✅
- [x] P3 功能：快捷键/主题切换/热力图全部可用 ✅
- [x] 无跨服务 import ✅

**验收完成时间**：2026-04-13  
**验收人**：Claude Code  
**提交记录**：
- de1947e: feat(sim-trading): SIMWEB-02/03 看板全面增强第二、三阶段（Claude 实现）
- 32e76c7: fix(sim-trading): 修复测试文件 import 路径错误（验收修复）

---

## 六、关联文档

- 父任务：[TASK-0085-sim-trading-看板全面增强-第一阶段.md](./TASK-0085-sim-trading-看板全面增强-第一阶段.md)
- 复审：[TASK-0086-review.md](../reviews/TASK-0086-review.md)
- 完成报告：[SIMWEB-02-03-完成报告-Claude.md](../handoffs/SIMWEB-02-03-完成报告-Claude.md)
