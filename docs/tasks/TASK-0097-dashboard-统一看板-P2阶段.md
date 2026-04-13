# TASK-0097 dashboard 统一看板 P2 — 四端页面迁移整合

## 元信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0097 |
| 任务名称 | dashboard 统一看板 P2 — 四端页面迁移整合 |
| 服务归属 | `services/dashboard/` |
| 前端子目录 | `services/dashboard/dashboard_web/` |
| 优先级 | P2 |
| 状态 | pending_review |
| 创建人 | Atlas |
| 创建时间 | 2026-04-13 |
| 执行人 | Claude（当前会话） |
| 依赖 | TASK-0096 locked |

---

## 任务边界（P2）

将现有四端临时看板页面及组件迁移/整合到 `dashboard_web` 统一前端。

### 目标路由结构
```
/sim-trading/operations      ← 来自 sim-trading_web/app/operations/
/sim-trading/intelligence    ← 来自 sim-trading_web/app/intelligence/
/sim-trading/market          ← 来自 sim-trading_web/app/market/
/sim-trading/ctp-config      ← 来自 sim-trading_web/app/ctp-config/
/sim-trading/risk-presets    ← 来自 sim-trading_web/app/risk-presets/

/backtest/operations         ← 来自 backtest_web
/backtest/review             ← 来自 backtest_web
/backtest/agent-network      ← 来自 backtest_web
/backtest/history            ← 来自 backtest_web
/backtest/optimizer          ← 来自 backtest_web

/decision/operations         ← 来自 decision_web
/decision/research           ← 来自 decision_web
/decision/history            ← 来自 decision_web
/decision/optimizer          ← 来自 decision_web

/data/operations             ← 来自 data_web
/data/quality                ← 来自 data_web
/data/collectors             ← 来自 data_web
/data/history                ← 来自 data_web
/data/optimizer              ← 来自 data_web
```

### 包含
- 四端页面文件迁移（page.tsx + 页面级组件）
- 各端共享 UI 组件（chart、table 等）迁移到 dashboard_web/components/ 对应子目录
- API fetch hooks / SWR hooks 迁移

### 排除
- 各端 Python 后端代码（不触碰）
- 各端原有 `*_web/` 目录（只读参考，不删除）

---

## 验收标准

1. `pnpm build` 成功，所有四端路由均在产出中
2. 编辑器静态诊断无红色错误
3. 四端页面在 dashboard_web 内可独立导航（通过统一 sidebar nav）

---

## 文件白名单（P2，约 70-100 个文件）

由于 P2 文件数量较多（约 420 个原始文件中提取核心页面约 70-100 个），**白名单将在 TASK-0096 完成后、本批 Token 签发前由架构师二次确认具体文件清单**。

暂定范围（目录级说明，签发时落成文件）：
```
services/dashboard/dashboard_web/app/(dashboard)/sim-trading/**
services/dashboard/dashboard_web/app/(dashboard)/backtest/**
services/dashboard/dashboard_web/app/(dashboard)/decision/**
services/dashboard/dashboard_web/app/(dashboard)/data/**
services/dashboard/dashboard_web/components/sim-trading/**
services/dashboard/dashboard_web/components/backtest/**
services/dashboard/dashboard_web/components/decision/**
services/dashboard/dashboard_web/components/data/**
services/dashboard/dashboard_web/hooks/**
services/dashboard/dashboard_web/lib/api/
```
