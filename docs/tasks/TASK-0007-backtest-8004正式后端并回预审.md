# TASK-0007 backtest 8004 正式后端并回预审

## 文档信息

- 任务 ID：TASK-0007
- 文档类型：新任务预审与范围冻结
- 签名：项目架构师
- 建档时间：2026-04-04
- 设备：MacBook

---

## 一、任务目标

在严格限制于 JBT 工作区内的前提下，把当前运行态 `8004` 的仓外 backtest 后端能力并回到 JBT 正式后端实现，并完成 JBT 内本地工作链第一轮收口。

本轮冻结目标如下：

1. 以 `services/backtest/src/api/` 为唯一正式后端实现基线，不再把当前运行中的 `JBT-BACKTEST-8004` 视为仓内正式能力。
2. 先补登记 JBT 正式 API 边界，再把当前前端实际依赖的 `/api/backtest/*`、`/api/strategy/*`、`/api/system/*`、`/api/market/*` 能力并回 JBT。
3. 把仓内仍写死 `localhost:8004` 的前端代理与错误提示收口到 JBT 正式后端口径。
4. 运行态 `JBT-BACKTEST-8004` 的 stop / rm / 清理动作只作为执行后置动作，不进入本次 Git 白名单，不得据此扩白名单。

---

## 二、任务编号与归属结论

### 任务编号结论

- **本事项应新建为 `TASK-0007`。**

### 编号判定理由

1. 仓内已存在旧 `TASK-0006` 预审产物，其主题为 Docker 部署与契约更新，不应与当前“8004 正式后端并回”事项复用同一任务号。
2. 当前事项的目标、白名单、风险与执行顺序均与旧 `TASK-0006` 不同，必须独立建档。

### 服务归属结论

- **任务归属：`services/backtest/` 单服务范围；仅在必须登记正式 API 边界时触及 `shared/contracts/backtest/api.md`。**

### 判定理由

1. 当前前端目录 `services/backtest/backtest_web/` 与正式后端目录 `services/backtest/src/api/` 同属 backtest 服务。
2. 本轮目标是把仓外 `8004` 运行能力并回 JBT 正式后端，而不是接入其他服务或读取 legacy 仓。
3. 前后端联通属于同服务内能力并回，不构成跨服务实现；只有正式 API 边界登记会触发 `shared/contracts/**`。

### 强制边界

1. 严禁读取、引用或修改 `/Users/jayshao/JBT/` 之外的任何目录，包括 `/Users/jayshao/J_BotQuant/`。
2. 不得扩展到 `services/decision/**`、`services/data/**`、`services/dashboard/**`、`integrations/**` 或其他服务目录。
3. 不得把工作区级 Docker / Compose 缺口顺手并入本任务；`docker-compose.dev.yml` 与任何服务根 Dockerfile 补齐都默认继续锁定。
4. 运行态容器清理不属于代码 Token 范围，必须在代码批次终审后由 Jay.S 单独确认执行窗口。

---

## 三、只读现状结论

基于当前 JBT 仓内只读复核，得到以下结论：

1. `services/backtest/src/api/app.py` 当前只注册 `health_router` 与 `jobs_router`。
2. `services/backtest/src/api/routes/jobs.py` 当前只覆盖 `/api/v1/jobs` 创建 / 列表 / 详情骨架，不包含当前前端实际使用的 `/api/backtest/*` 等路由。
3. `shared/contracts/backtest/api.md` 当前正式契约仅覆盖 `/api/v1/health`、`/api/v1/jobs*`、`/api/v1/results/{job_id}`、`/api/v1/metrics/{job_id}`、`/api/v1/equity_curve/{job_id}`，且明确排除了批量操作与更多扩展接口。
4. `services/backtest/backtest_web/src/utils/api.ts` 当前默认后端仍为 `http://localhost:8004`，且 `friendlyError` 仍提示检查 `http://localhost:8004`。
5. `services/backtest/backtest_web/next.config.mjs` 当前 rewrites 默认后端仍为 `http://localhost:8004`。
6. `services/backtest/backtest_web/src/utils/api.ts` 当前已实际依赖以下接口族：`/api/backtest/*`、`/api/strategy/*`、`/api/system/*`、`/api/market/*`。
7. 仓内实际存在的 compose 文件只有根级 `docker-compose.dev.yml`；仓内不存在 `services/backtest/docker-compose.yml`。
8. 根级 `docker-compose.dev.yml` 虽已声明 `backtest` 服务与 `JBT-BACKTEST-8103` 容器名，但当前 `services/backtest/` 目录内不存在服务根 Dockerfile；因此“全 Docker 本地链修复”不应在本任务第一轮最小白名单中顺手展开。
9. 当前有效 `TASK-0004` Token 只覆盖 `services/backtest/backtest_web/app/agent-network/page.tsx` 与 `services/backtest/backtest_web/app/operations/page.tsx`，对本任务后端/API/其他前端文件全部无效。
10. `services/backtest/backtest_web/next.config.mjs` 在构建期读取 `BACKEND_BASE_URL` 生成 `/api/*` rewrite destination，因此镜像构建时的默认值会直接影响远端代理目标。
11. `services/backtest/backtest_web/Dockerfile` 当前默认 `ARG BACKEND_BASE_URL` 与对应 `ENV BACKEND_BASE_URL` 仍为 `http://backtest-api:8103`。
12. 根级 `docker-compose.dev.yml` 中 backtest API 服务名为 `backtest`，不是 `backtest-api`；若远端构建未显式覆盖 `BACKEND_BASE_URL`，则构建产物会把 `/api/*` rewrite 到不存在的主机名。
13. 因此 2026-04-06 的最小补充修复应收敛为 `services/backtest/backtest_web/Dockerfile` 单文件，把构建期 / 运行期默认目标与 compose 服务名 `backtest:8103` 对齐；不得借机扩大到 compose、page、后端或其他前端文件。

---

## 四、批次拆分结论

### 是否必须拆批

- **必须拆批，当前冻结为 4 个代码批次 + 1 个运行态后置动作。**

### 拆批理由

1. `shared/contracts/backtest/api.md` 属于 P0 保护区，必须先契约后实现，不能与服务代码混做。
2. 当前最小后端并回范围已达到 5 文件边界，不能再混入前端代理口径修复。
3. 仓内 `8004` 残留既包含正式 API 漂移，也包含前端默认代理与错误文案残留，必须分层收口。
4. 远端 `/api/*` 代理 500 的根因已收敛到 backtest-web 镜像构建期默认目标主机名，与本地 dev / 页面代理口径不是同一文件族，必须额外拆出单文件补充批次，避免 reopen 既有批次 C。

### 批次 A：正式契约先行（P0）

目标：先把 JBT 正式 API 边界补登记，禁止在未更新 formal contract 的前提下直接把仓外 `8004` 路由面并回 JBT。

冻结白名单：

1. `shared/contracts/backtest/api.md`

说明：

1. 本批只改 formal API 契约，不改任何服务代码。
2. `backtest_job.md`、`backtest_result.md`、`performance_metrics.md` 当前继续锁定；只有在批次 A 证明现有模型字段不足时，才允许重新提交补充 P0 预审。

### 批次 B：正式后端 API 并回（P1）

目标：在 JBT 正式后端中建立当前前端所需的 API 路由面，同时保持现有 `/api/v1` 健康与 jobs 骨架不回退。

冻结白名单：

1. `services/backtest/src/api/app.py`
2. `services/backtest/src/api/routes/backtest.py`
3. `services/backtest/src/api/routes/strategy.py`
4. `services/backtest/src/api/routes/support.py`
5. `services/backtest/tests/test_api_surface.py`

说明：

1. 本批严格卡在 5 文件上限内。
2. `support.py` 用于承接 `/api/system/*` 与 `/api/market/*`，避免把路由拆散后超出 5 文件边界。
3. 预审假设本批通过 route-layer adapter 即可承接现有 `runner.py`、`result_builder.py`、`session.py` 能力；若执行中证明必须修改 `runner.py` 或 `result_builder.py`，当前 Token 立即失效，必须回到项目架构师补充预审。
4. `jobs.py`、`health.py`、`src/backtest/**` 其余文件在本批默认继续锁定。

### 批次 C：本地链路与 8004 错误口径收口（P1）

目标：把仓内前端默认代理与用户可见错误提示从 `8004` 收口到 JBT 正式后端口径，形成 JBT 内可自洽的本地联调链。

冻结白名单：

1. `services/backtest/backtest_web/src/utils/api.ts`
2. `services/backtest/backtest_web/next.config.mjs`

说明：

1. 本批不 reopen 当前 `TASK-0004` 两个 page 文件，也不纳入 `app/page.tsx`。
2. 本批策略是“后端兼容现有页面”，而不是以 page 改造收口本任务。
3. `services/backtest/backtest_web/Dockerfile` 当前仍是 `backtest-api:8103` 口径，但不并入本批；该单文件仅在补充批次 D 中单独处理。
4. 本批验收口径定义为“本地 dev / proxy 链收口”，不扩展成 root compose / Docker 全链修复。

### 补充批次 D：backtest-web 构建期代理目标热修（P1）

目标：仅修正 `services/backtest/backtest_web/Dockerfile` 中构建期 / 运行期 `BACKEND_BASE_URL` 默认值，使远端构建产物默认把 `/api/*` rewrite 到 `http://backtest:8103`，不再指向不存在的 `http://backtest-api:8103`。

冻结白名单：

1. `services/backtest/backtest_web/Dockerfile`

说明：

1. 本批只允许调整 `ARG BACKEND_BASE_URL` 与对应 `ENV BACKEND_BASE_URL` 默认值。
2. 不得修改 `docker-compose.dev.yml`、`services/backtest/backtest_web/next.config.mjs`、`services/backtest/backtest_web/src/utils/api.ts`、任何 `app/**` page、任何后端文件或其他 Docker 文件。
3. 若执行中证明必须新增第 2 个业务文件，当前补充范围立即失效，必须回到项目架构师重新补充预审。
4. 本批验收以“Docker build 默认目标不再是 `backtest-api:8103` 而是 `backtest:8103`，且远端重建 backtest-web 后，`/api/system/status` 或等价代理请求不再因主机名错误而返回 500”为准。

### 运行态后置动作：8004 容器清理（非 Git 批次）

目标：在代码批次全部终审通过后，确认并清理当前残留 `JBT-BACKTEST-8004` 运行态容器。

说明：

1. 该动作不进入 Git 白名单，不申请代码 Token。
2. 需由 Jay.S 单独确认运行窗口后执行。
3. 不得借“清理容器”为由把 `docker-compose.dev.yml`、`services/backtest/Dockerfile`、脚本或其他运维文件并入当前任务。

---

## 五、最小白名单冻结

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

### 当前明确继续锁定的相关文件

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
12. 其他全部非白名单文件

---

## 六、P0 / P1 分级与 shared/contracts 结论

1. `shared/contracts/backtest/api.md` 属于 **P0**，且 **本任务必须先处理它**。
2. `services/backtest/src/api/**`、`services/backtest/tests/**`、`services/backtest/backtest_web/src/**` 属于本任务的 **P1** 实施区。
3. `docker-compose.dev.yml` 属于 **P0** 保护区，但 **当前不纳入 TASK-0007 第一轮白名单**。
4. `services/backtest/Dockerfile` 不属于当前冻结白名单；若 Jay.S 后续要求把 Docker 本地链一并修复，必须另开补充预审。
5. `services/backtest/backtest_web/Dockerfile` 在补充批次 D 中按 **P1** 处理，但语义严格冻结为“仅修正默认 `BACKEND_BASE_URL` 到 `http://backtest:8103`”；若需改动第 2 个业务文件，必须重做补充预审。
6. **本任务涉及 `shared/contracts`，但当前最小触点仅 `shared/contracts/backtest/api.md` 单文件。**

---

## 七、Token 建议

### 建议执行 Agent

1. 批次 A：项目架构师
2. 批次 B：回测 Agent
3. 批次 C：回测 Agent
4. 补充批次 D：回测 Agent

### Atlas 下一步应向 Jay.S 请求的精确 Token 申请口径

#### 批次 A（P0）

请为项目架构师签发 `TASK-0007` 批次 A 的单 Agent、单任务、单文件 P0 Token，允许修改文件仅 `shared/contracts/backtest/api.md`，动作类型 `edit`，目的为先补登记 JBT backtest 正式 API 契约，并冻结 `/api/backtest/*`、`/api/strategy/*`、`/api/system/*`、`/api/market/*` 与既有 `/api/v1/*` 的对齐关系；有效期 30 分钟；白名单外文件继续锁定。

#### 批次 B（P1）

请为回测 Agent 签发 `TASK-0007` 批次 B 的单 Agent、单任务、5 文件 P1 Token，允许修改文件仅 `services/backtest/src/api/app.py`、`services/backtest/src/api/routes/backtest.py`、`services/backtest/src/api/routes/strategy.py`、`services/backtest/src/api/routes/support.py`、`services/backtest/tests/test_api_surface.py`，动作类型 `edit/create`，目的为把当前前端依赖的 `8004` API 路由面正式并回 JBT 后端；有效期 30 分钟；如需 `runner.py`、`result_builder.py` 或任何第 6 个文件，当前 Token 立即失效并返回补充预审。

#### 批次 C（P1）

请为回测 Agent 签发 `TASK-0007` 批次 C 的单 Agent、单任务、2 文件 P1 Token，允许修改文件仅 `services/backtest/backtest_web/src/utils/api.ts` 与 `services/backtest/backtest_web/next.config.mjs`，动作类型 `edit`，目的为把仓内默认后端代理与错误提示从 `localhost:8004` 收口到 JBT 正式后端口径；有效期 30 分钟；白名单外文件继续锁定。

#### 补充批次 D（P1）

请为回测 Agent 签发 `TASK-0007` 补充批次 D 的单 Agent、单任务、单文件 P1 Token，允许修改文件仅 `services/backtest/backtest_web/Dockerfile`，动作类型 `edit`，目的为把 backtest-web 镜像构建期 / 运行期 `BACKEND_BASE_URL` 默认值从 `http://backtest-api:8103` 收口到 `http://backtest:8103`，修复远端 `/api/*` rewrite 指向不存在主机名导致的代理 500；有效期 30 分钟；不得顺手修改 `docker-compose.dev.yml`、`next.config.mjs`、`src/utils/api.ts`、任何 page、任何后端文件；如需第 2 个业务文件，当前 Token 立即失效并返回补充预审。

### 运行态后置动作说明

1. `JBT-BACKTEST-8004` 清理不进入代码 Token 申请，不得混入上述三批任何一枚 Token。
2. 该动作需在批次 C 终审锁回后，由 Jay.S 单独确认运行窗口再执行。

---

## 八、预审结论

1. **TASK-0007 正式成立。**
2. **当前事项不得复用 TASK-0004 的 2 文件 Token，也不得按旧 `TASK-0006` 的 Docker 口径推进。**
3. **本任务必须先契约后实现。**
4. **第一轮最小实施不碰 `docker-compose.dev.yml`，不碰 `services/backtest/Dockerfile`，不修工作区级 Docker 缺口。**
5. **补充批次 D 正式成立：仅允许回测 Agent 在 `services/backtest/backtest_web/Dockerfile` 单文件内把默认 `BACKEND_BASE_URL` 从 `http://backtest-api:8103` 收口到 `http://backtest:8103`。**
6. **若补充批次 D 执行中需要第 2 个业务文件，当前补充预审立即失效，必须重新补白名单。**
7. **代码批次完成并终审锁回后，运行态 `JBT-BACKTEST-8004` 再进入单独清理动作。**