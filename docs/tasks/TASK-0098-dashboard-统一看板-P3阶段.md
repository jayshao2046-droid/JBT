# TASK-0098 dashboard 统一看板 P3 — API 代理 + 测试 + 部署配置

## 元信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0098 |
| 任务名称 | dashboard 统一看板 P3 — API 代理配置、基础测试、部署就绪 |
| 服务归属 | `services/dashboard/` |
| 前端子目录 | `services/dashboard/dashboard_web/` |
| 优先级 | P3 |
| 状态 | pending_review |
| 创建人 | Atlas |
| 创建时间 | 2026-04-13 |
| 执行人 | Claude（当前会话） |
| 依赖 | TASK-0097 locked |

---

## 任务边界（P3）

### 包含
- `next.config.ts` 更新：添加四端 API rewrites 代理规则（/api/sim-trading → 8101, /api/backtest → 8103, /api/decision → 8104, /api/data → 8105）
- `services/dashboard/tests/test_dashboard_web.py`：最小冒烟测试
- `services/dashboard/dashboard_web/.env.example`：前端环境变量模板（注：此文件属 P0 保护区，需独立预审确认）
- `docker-compose.mac.override.yml` 可能补充 dashboard_web 容器（视 Jay.S 是否授权）

### 排除
- `services/dashboard/.env.example`（Python 后端侧，P0 保护路径，本轮不触碰）
- `docker-compose.dev.yml`（P0 保护路径，不触碰）

---

## 验收标准

1. `pnpm build` 产出完整（全部路由）
2. API rewrites 配置正确（端口与 JBT 端口注册表一致）
3. `pytest services/dashboard/tests/ -q` 通过

---

## 文件白名单（P3，待 TASK-0097 完成后补全）

```
services/dashboard/dashboard_web/next.config.ts
services/dashboard/tests/test_dashboard_web.py
```

> `.env.example` 需 Jay.S 单独确认是否纳入，涉及 P0 保护路径。
