# REVIEW-TASK-0099 — dashboard v0 模板替换 + API 对接预审

## 元信息

| 字段 | 值 |
|------|-----|
| Review ID | REVIEW-TASK-0099 |
| 关联任务 | TASK-0099 |
| 审核日期 | 2026-04-13 |
| 审核人 | Atlas（项目架构师角色） |
| 审核结论 | APPROVED |

---

## 变更背景

Jay.S 决策调整：放弃逐页迁移方案（TASK-0097 revoked），改为用 `docs/portal-design/v0-close/` 中由 v0 工具生成的全新统一看板一次性替换 `services/dashboard/dashboard_web/` 的 P0+P1 骨架，并在替换基础上移除所有 mock 数据，接入真实 API。

---

## 架构合规检查

### 服务边界
- ✅ 所有变更限定在 `services/dashboard/dashboard_web/`
- ✅ 源代码参考目录 `docs/portal-design/v0-close/`（只读参考）不进入 Git 变更范围
- ✅ 四端后端服务（sim-trading/backtest/decision/data）仅通过 API 调用，不侵入其源码

### 替换范围
- ✅ 整体替换 P0+P1 骨架：新布局体系（MainLayout + AppSidebar + AppHeader + AnimatedGridBg）完全自包含
- ✅ 端口配置不变：前端 3005，API rewrite 8101/8103/8104/8105
- ✅ 认证机制延续：localStorage `jbt_user` + `/login` 路由保留

### API 对接（mock 到真实端点）

| Mock 数据 | 对应真实 API | 服务 |
|---------|------------|------|
| `mockPositions` | `GET /api/sim-trading/positions` | sim-trading:8101 |
| `mockKPIData`（账户权益、保证金、浮动盈亏） | `GET /api/sim-trading/account` | sim-trading:8101 |
| `mockKPIData`（今日盈亏、胜率、盈亏比） | `GET /api/sim-trading/stats/performance` | sim-trading:8101 |
| `mockKPIData`（仓位使用率、VaR） | `GET /api/sim-trading/risk/l1` | sim-trading:8101 |
| `mockKPIData`（今日交易笔数） | `GET /api/sim-trading/report/daily` | sim-trading:8101 |
| `mockSignals` | `GET /api/decision/dashboard/signals` | decision:8104 |
| `mockDataSources` | `GET /api/data/api/v1/dashboard/collectors` | data:8105 |
| `mockNews` | `GET /api/data/api/v1/dashboard/news` | data:8105 |
| 四端模块状态卡片（status） | `GET /api/sim-trading/status` + `GET /api/backtest/health` + `GET /api/decision/api/health` + `GET /api/data/api/v1/health` | 各端 |

### P0 保护区
- ✅ 未触碰 `.env.example`、`Dockerfile`、`shared/contracts/**`
- ✅ `services/dashboard/dashboard_web/` 为 TASK-0096 已批准目录

---

## 预审结论

**APPROVED**：变更范围清晰，服务边界合规，API 对接路径已确认，Token 可签发。
