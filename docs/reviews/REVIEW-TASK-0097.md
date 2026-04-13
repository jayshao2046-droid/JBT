# REVIEW-TASK-0097 — dashboard P2 四端页面迁移预审

## 元信息

| 字段 | 值 |
|------|-----|
| Review ID | REVIEW-TASK-0097 |
| 关联任务 | TASK-0097 |
| 审核日期 | 2026-04-13 |
| 审核人 | Atlas（项目架构师角色） |
| 审核结论 | APPROVED |

---

## 变更摘要

将四端临时看板（sim-trading_web / backtest_web / decision_web / data_web）的页面与业务组件迁移到 `services/dashboard/dashboard_web/` 统一前端，形成四端统一门户。

---

## 架构合规检查

### 服务边界
- ✅ 所有变更限定在 `services/dashboard/dashboard_web/`，不触碰其他服务目录
- ✅ 四端原始 `*_web/` 目录只读参考，不删除、不修改
- ✅ 路由在 `app/(dashboard)/` 路由组内，与认证、设置路由隔离

### import 约束
- ✅ 迁移后组件 import 路径指向 `dashboard_web/components/` 内部，不跨服务 import
- ✅ API 调用通过 `lib/{service}-api.ts` + next.config.ts rewrites 代理，不直接跨服务调用后端

### 白名单范围合理性
- ✅ 147 个文件均在 `services/dashboard/dashboard_web/` 下，无跨服务文件
- ✅ 包含 3 个配置文件更新（package.json / pnpm-lock.yaml / next.config.ts），用于添加新依赖与 API rewrite 规则
- ✅ 包含 sidebar.tsx 修改权限（新增四端导航条目）
- ✅ UI 组件扩充（23 个）：从四端已有的 shadcn/ui 组件集中补充 dashboard_web 缺少的
- ✅ hooks（2 个）：use-mobile + use-toast，通用工具
- ✅ lib API 文件（9 个）：各端 API client 集中到 dashboard_web/lib/ 管理

### 端口与 API 路由
- ✅ API rewrite 规则：
  - `/api/sim-trading/**` → `http://localhost:8101/api/**`
  - `/api/backtest/**` → `http://localhost:8103/api/**`
  - `/api/decision/**` → `http://localhost:8104/api/**`
  - `/api/data/**` → `http://localhost:8105/api/**`

### P0 保护区
- ✅ 未触碰 `.env.example`、`Dockerfile`、`shared/contracts/**`、`shared/python-common/**`

---

## 验收标准（预审确认）

1. `pnpm build` 成功，四端路由全部出现在构建产物中
2. `pnpm lint` 无错误
3. 白名单文件与磁盘实际文件 diff 为 EXTRA: none / MISSING: none

---

## 预审结论

**APPROVED**：变更范围合理，服务边界清晰，无跨服务侵入，Token 可签发。
