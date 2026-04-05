# TASK-0007 Review

## Review 信息

- 任务 ID：TASK-0007
- 审核角色：项目架构师
- 审核阶段：8004 正式后端并回预审
- 审核时间：2026-04-04
- 审核结论：通过（`TASK-0006` 已被历史任务占用，当前事项顺延为 `TASK-0007`；本轮必须先走 `shared/contracts/backtest/api.md` 的 P0 契约补登，再进入 backtest 正式后端并回与前端 `8004` 口径收口；当前最小实施拆为 3 个代码批次；`docker-compose.dev.yml`、`services/backtest/Dockerfile`、`src/backtest/**` 与 `TASK-0004` 两个 page 文件继续锁定）

---

## 一、任务边界核验

1. 任务目标明确：把当前运行态 `8004` 的仓外 backtest 后端能力并回 JBT 正式后端，并完成 JBT 内本地联调链第一轮收口。
2. 任务目录明确：实施区仅限 `services/backtest/`；契约登记最小触点仅 `shared/contracts/backtest/api.md`。
3. 本轮明确禁止扩展到：
   - `/Users/jayshao/J_BotQuant/**`
   - `services/decision/**`
   - `services/data/**`
   - `services/dashboard/**`
   - `integrations/**`
   - `docker-compose.dev.yml`
   - `services/backtest/Dockerfile`
   - `services/backtest/src/backtest/**`
4. 运行态 `JBT-BACKTEST-8004` 清理属于执行后置动作，不进入 Git 白名单，也不作为扩白名单理由。

## 二、只读技术结论

1. `services/backtest/src/api/app.py` 当前只注册 `health_router` 与 `jobs_router`。✅
2. `services/backtest/src/api/routes/jobs.py` 当前只覆盖 `/api/v1/jobs` 创建 / 列表 / 详情骨架，无法直接承接当前前端调用的 `/api/backtest/*`、`/api/strategy/*`、`/api/system/*`、`/api/market/*`。✅
3. `shared/contracts/backtest/api.md` 当前正式契约仅覆盖 `/api/v1/health`、`/api/v1/jobs*`、`/api/v1/results/{job_id}`、`/api/v1/metrics/{job_id}`、`/api/v1/equity_curve/{job_id}`，且明确排除了批量操作与更多扩展接口。✅
4. `services/backtest/backtest_web/src/utils/api.ts` 与 `services/backtest/backtest_web/next.config.mjs` 当前默认后端仍为 `http://localhost:8004`，`friendlyError` 也仍提示检查 `http://localhost:8004`。✅
5. 仓内不存在 `services/backtest/docker-compose.yml`；仓内实际 compose 文件只有根级 `docker-compose.dev.yml`。✅
6. 根级 `docker-compose.dev.yml` 虽已声明 `backtest` 服务，但 `services/backtest/` 当前不存在服务根 Dockerfile，因此不应把工作区级 Docker 修复混入本任务第一轮最小实施。✅

## 三、任务编号核验

1. 仓内已存在旧 `TASK-0006` 预审产物，主题为 Docker 部署与契约更新。✅
2. 当前事项与旧 `TASK-0006` 的目标、白名单与风险完全不同，若继续复用 `TASK-0006` 会造成治理账本冲号。✅
3. 因此当前事项应顺延建档为 `TASK-0007`。✅

## 四、白名单冻结

### 批次 A：P0 白名单

1. `shared/contracts/backtest/api.md`

### 批次 B：P1 白名单

1. `services/backtest/src/api/app.py`
2. `services/backtest/src/api/routes/backtest.py`
3. `services/backtest/src/api/routes/strategy.py`
4. `services/backtest/src/api/routes/support.py`
5. `services/backtest/tests/test_api_surface.py`

### 批次 C：P1 白名单

1. `services/backtest/backtest_web/src/utils/api.ts`
2. `services/backtest/backtest_web/next.config.mjs`

### 当前不建议纳入的文件

1. `shared/contracts/backtest/backtest_job.md`
2. `shared/contracts/backtest/backtest_result.md`
3. `shared/contracts/backtest/performance_metrics.md`
4. `docker-compose.dev.yml`
5. `services/backtest/Dockerfile`
6. `services/backtest/src/api/routes/jobs.py`
7. `services/backtest/src/api/routes/health.py`
8. `services/backtest/src/backtest/**`
9. `services/backtest/backtest_web/app/page.tsx`
10. `services/backtest/backtest_web/app/agent-network/page.tsx`
11. `services/backtest/backtest_web/app/operations/page.tsx`
12. `services/backtest/backtest_web/Dockerfile`

## 五、必须先契约后实现的判断依据

1. 当前正式契约没有登记 `/api/backtest/*`、`/api/strategy/*`、`/api/system/*`、`/api/market/*` 这组前端实际调用接口。 
2. 若跳过契约补登直接把仓外 `8004` 路由面并回 JBT，会形成正式实现与 formal contract 漂移。 
3. 因此本任务必须先完成 `shared/contracts/backtest/api.md` 的 P0 批次，再进入 P1 实施。 

## 六、风险与缓解

| 风险 | 等级 | 缓解措施 |
|---|---|---|
| 直接复用旧 `TASK-0006` 编号导致账本冲号 | P-LOG | 当前任务顺延建档为 `TASK-0007` |
| 在未更新契约前直接并回 `/api/backtest/*` 等路由 | P0 | 先申请批次 A 单文件 P0 Token，先契约后实现 |
| 顺手把 `docker-compose.dev.yml` 或 `services/backtest/Dockerfile` 纳入 | P0 | 预审明确排除工作区级 Docker 修复；若 Jay.S 强制推进，必须补充预审 |
| 批次 B 实施时发现需要改 `runner.py` / `result_builder.py` | P1 | 当前 Token 立即失效，返回架构师补充预审 |
| 继续沿用 `localhost:8004` 前端默认口径，导致仍误连仓外容器 | P1 | 单独拆出批次 C，仅修 `src/utils/api.ts` 与 `next.config.mjs` |

## 七、预审结论

1. **TASK-0007 预审通过。**
2. **本轮必须按“批次 A 契约先行 → 批次 B 正式后端并回 → 批次 C 前端 8004 口径收口”的顺序推进。**
3. **当前可进入 Jay.S 分批签发 Token 的准备态。**
4. **运行态 `JBT-BACKTEST-8004` 清理不属于代码 Token 范围，需在代码批次终审锁回后单独确认。**