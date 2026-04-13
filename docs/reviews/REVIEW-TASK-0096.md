# REVIEW-TASK-0096 dashboard 统一看板 P0+P1 预审

## 审核元信息

| 字段 | 值 |
|------|-----|
| 审核编号 | REVIEW-TASK-0096 |
| 关联任务 | TASK-0096 |
| 审核类型 | 预审（Pre-Review） |
| 审核人 | 项目架构师（Atlas 代行） |
| 审核时间 | 2026-04-13 |
| 结论 | ✅ 通过，可签发 Token |

---

## 技术可行性审核

### 1. 服务边界 ✅
- `services/dashboard/dashboard_web/` 为全新目录，不影响任何现有服务
- 不触碰 `services/dashboard/src/`（Python 后端）
- 不触碰 `services/dashboard/.env.example`（P0 保护路径）
- 不触碰 `Dockerfile`
- 四端服务（sim-trading/backtest/decision/data）本轮只读参考，不写入

### 2. 架构合理性 ✅
- Next.js 15 + shadcn/ui + Tailwind 与四端现有技术栈完全一致
- Route Groups `(auth)` / `(dashboard)` 是 Next.js 标准分层模式
- lib/auth.ts、lib/api-client.ts、lib/constants.ts 是标准的前端分层

### 3. 端口注册 ✅
- dashboard_web 端口注册为 3005（见 `docs/PORT_REGISTRY.md`）
- 本批次不需要配置 API 代理（P3 再做），不存在端口冲突风险

### 4. 白名单合理性 ✅
- 38 个文件均为全新创建，不修改任何已存在文件（`services/dashboard/` 旧有 4 个文件均不在白名单内）
- 文件粒度清单符合 lockctl 文件级要求

### 5. 风险点
- `pnpm-lock.yaml` 需要通过 `pnpm install` 自动生成，不手写；可接受
- 如需要额外的 shadcn/ui 组件（如 popover、toast 等），需补签

---

## 预审结论

**结论**：通过。可向 Jay.S 申请签发 TASK-0096 P0+P1 Token，白名单按任务文件附表执行。

**保留项**：
1. `pnpm-lock.yaml` 由 `pnpm install` 自动生成，不计入 lockctl 文件级校验（仅作记录）
2. `public/` 目录下静态资源（favicon.ico 等）如需添加，可在白名单外按需创建（不含业务逻辑）

---

## REVIEW-TASK-0097 REVIEW-TASK-0098 预审说明

- TASK-0097（P2）白名单将在 TASK-0096 完成后二次确认，当前预审通过"迁移四端页面到 dashboard_web 对应子目录"的整体方向
- TASK-0098（P3）白名单较小（2 个核心文件），方向无风险，预审通过
- `.env.example`（TASK-0098 中的 dashboard_web 前端 env）需 Jay.S 单独确认是否解锁
