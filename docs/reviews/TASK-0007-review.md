# TASK-0007 Review

## Review 信息

- 任务 ID：TASK-0007
- 审核角色：项目架构师
- 审核阶段：8004 正式后端并回预审；2026-04-06 补充批次 D 终审；2026-04-10 批次 B/C 终审
- 审核时间：2026-04-04（预审）；2026-04-06（补充批次 D 终审）；2026-04-10（批次 B/C 终审）
- 审核结论：通过（全部 4 个批次 A/B/C/D 均已完成终审与锁回）

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

### 补充批次 D：P1 白名单

1. `services/backtest/backtest_web/Dockerfile`

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

## 七、2026-04-06 补充预审：backtest-web 构建期代理目标热修

1. `services/backtest/backtest_web/next.config.mjs` 会在构建期读取 `BACKEND_BASE_URL` 生成 `/api/*` rewrite destination。✅
2. `services/backtest/backtest_web/Dockerfile` 当前默认 `ARG/ENV BACKEND_BASE_URL` 仍为 `http://backtest-api:8103`。✅
3. 根级 `docker-compose.dev.yml` 的 backtest API 服务名为 `backtest`；若远端构建未显式覆盖该默认值，镜像会把 `/api/*` rewrite 到不存在的主机名，从而在远端表现为代理 500。✅
4. 该问题应继续归属 `TASK-0007`，不新开 `TASK-0017`：因为它属于 backtest 单服务内 `8004/8103` 口径收口下的构建期代理目标热修，不是 SimNow Docker / Mini 部署治理事项。✅
5. 补充批次 D 白名单必须冻结为单文件 `services/backtest/backtest_web/Dockerfile`，执行主体建议为回测 Agent。✅
6. 变更语义必须冻结为：仅把 Dockerfile 中构建期 / 运行期 `BACKEND_BASE_URL` 默认值与 compose 服务名 `backtest:8103` 对齐；不得顺手修改 `docker-compose.dev.yml`、`next.config.mjs`、`src/utils/api.ts`、任何 page、任何后端文件。✅
7. 若执行中证明需要第 2 个业务文件，当前补充范围立即失效，必须重新补充预审。✅
8. 本补充批次验收冻结为：Docker build 默认目标不再是 `backtest-api:8103`，且远端重建 backtest-web 后，`/api/system/status` 或等价代理请求不再因主机名错误而返回 500。✅

## 八、2026-04-06 当前会话即时执行确认补录

1. Jay.S 已在当前会话以“远端 api 报错 500”明确确认：补充批次 D 立即进入执行态。✅
2. 本次即时执行确认仅绑定回测 Agent，且白名单仍严格限于 `services/backtest/backtest_web/Dockerfile` 单文件。✅
3. 本次补录按要求不记录 token_id，也不把当前会话即时执行确认表述为终审或锁回完成。✅
4. 若补充批次 D 执行中证明需要第 2 个业务文件，当前授权立即失效，必须重新补充预审。✅
5. 本次即时执行确认只解决“是否可立即实施”问题，不替代后续自校验、项目架构师终审与锁回。✅

## 九、2026-04-06 补充批次 D 终审

1. 只读核验确认：本轮业务写入仍严格限于 `services/backtest/backtest_web/Dockerfile` 单文件；`docs/prompts/agents/回测提示词.md` 的更新属于 P-LOG 流程同步，不构成业务白名单越界。✅
2. 当前 Dockerfile 实际收口仍仅为两处默认值：构建期 `ARG BACKEND_BASE_URL` 与运行期 `ENV BACKEND_BASE_URL` 已统一从 `http://backtest-api:8103` 收口到 `http://backtest:8103`；未发现第 2 个业务文件被 reopen。✅
3. 最小自校验已补核：`services/backtest/backtest_web/Dockerfile` 与 `docs/prompts/agents/回测提示词.md` 的诊断结果均为 `No errors found`。✅
4. 远端验证已补核：air 端完成 backtest-web 单服务重建后，`http://127.0.0.1:3001/agent-network` 返回 200，`http://127.0.0.1:3001/api/system/status` 返回 200，且 API body 正常返回 JSON；此前由错误主机名引起的代理 500 已消失。✅
5. 终审结论：补充批次 D 通过；当前可判定白名单未越界，且本轮问题已在单文件范围内闭环。✅
6. 锁回结论：`services/backtest/backtest_web/Dockerfile` 当前已按补充批次 D 终审结论重新锁回；后续如需再次修改该文件，仍须重新补充预审，不得沿用本轮授权。✅

## 十、2026-04-10 批次 B 终审补录

1. 批次名称：批次 B — 正式后端 API 并回
2. 执行 Agent：回测 Agent
3. token_id：`tok-47940111-1c84-48fc-a005-86847096c740`
4. review-id：`REVIEW-TASK-0007-B`
5. 实际白名单严格限于：`services/backtest/src/api/app.py`、`services/backtest/src/api/routes/backtest.py`、`services/backtest/src/api/routes/strategy.py`、`services/backtest/src/api/routes/support.py`、`services/backtest/tests/test_api_surface.py`
6. 最小自校验结果：71 passed / 2 pre-existing
7. lockback 时间：2026-04-10
8. lockback 结果：`approved`
9. 当前 Token 状态：`locked`

## 十一、2026-04-10 批次 C 终审补录

1. 批次名称：批次 C — 前端 8004 收口
2. 执行 Agent：回测 Agent
3. token_id：`tok-c19ceb4a-82f6-44f1-a240-b9254b2ea5d1`
4. review-id：`REVIEW-TASK-0007-C`
5. 实际白名单严格限于：`services/backtest/backtest_web/src/utils/api.ts`、`services/backtest/backtest_web/next.config.mjs`
6. 最小自校验结果：已在先前批次完成收口，0 errors
7. lockback 时间：2026-04-10
8. lockback 结果：`approved`
9. 当前 Token 状态：`locked`

## 十二、当前结论

1. **TASK-0007 预审通过。**
2. **本轮必须按“批次 A 契约先行 → 批次 B 正式后端并回 → 批次 C 前端 8004 口径收口”的顺序推进。**
3. **批次 A 已完成契约补登并锁回。**
4. **批次 B 已完成正式后端 API 并回并锁回（71 passed / 2 pre-existing）。**
5. **批次 C 已完成前端 8004 收口并锁回（0 errors）。**
6. **2026-04-06 补充批次 D 已完成终审与锁回；业务白名单未越界。**
7. **TASK-0007 全部 4 个批次均已闭环。**
8. **运行态 `JBT-BACKTEST-8004` 清理不属于代码 Token 范围，需在代码批次终审锁回后单独确认。**