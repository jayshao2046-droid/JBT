# TASK-0007 backtest 8004 并回预审交接单

【签名】项目架构师
【时间】2026-04-04
【设备】MacBook

## 任务结论

- 当前事项已独立建档为 `TASK-0007`，不复用旧 `TASK-0006`。
- 本轮目标冻结为：把当前运行态 `8004` 的仓外 backtest 后端能力并回 JBT 正式后端，并完成 JBT 内本地联调链第一轮收口。
- 当前公共状态建议为：**`TASK-0007` 已预审，必须先契约后实现；待 Jay.S 按批次签发 A / B / C 三枚 Token。**

## 只读复核摘要

1. `services/backtest/src/api/app.py` 当前只包含 `health` 与 `jobs` skeleton，无法直接承接当前前端依赖的 `/api/backtest/*`、`/api/strategy/*`、`/api/system/*`、`/api/market/*`。
2. `shared/contracts/backtest/api.md` 当前 formal contract 只登记 `/api/v1/*` 主路径，未登记上述当前前端实际调用接口族。
3. `services/backtest/backtest_web/src/utils/api.ts` 与 `services/backtest/backtest_web/next.config.mjs` 当前仍默认指向 `http://localhost:8004`；`friendlyError` 也仍提示检查 `8004`。
4. 仓内不存在 `services/backtest/docker-compose.yml`；仓内实际 compose 只有根级 `docker-compose.dev.yml`。
5. `docker-compose.dev.yml` 虽声明 `JBT-BACKTEST-8103`，但 `services/backtest/` 当前不存在服务根 Dockerfile，因此本任务第一轮不把工作区级 Docker 修复并入白名单。
6. 当前 `TASK-0004` 的 2 文件 Token 不能覆盖本任务后端/API/其他前端文件。

## 建议批次拆分

### 批次 A：P0 契约先行

1. `shared/contracts/backtest/api.md`

### 批次 B：P1 正式后端 API 并回

1. `services/backtest/src/api/app.py`
2. `services/backtest/src/api/routes/backtest.py`
3. `services/backtest/src/api/routes/strategy.py`
4. `services/backtest/src/api/routes/support.py`
5. `services/backtest/tests/test_api_surface.py`

### 批次 C：P1 本地链路与 8004 口径收口

1. `services/backtest/backtest_web/src/utils/api.ts`
2. `services/backtest/backtest_web/next.config.mjs`

### 运行态后置动作（非 Git）

1. `JBT-BACKTEST-8004` 运行态容器 stop / rm / 清理
2. 该动作不纳入代码 Token，不得作为扩白名单理由

## P0 / P1 结论

1. `shared/contracts/backtest/api.md` 属于 P0，且必须先做。
2. `services/backtest/src/api/**`、`services/backtest/tests/**`、`services/backtest/backtest_web/src/**` 属于本任务 P1 实施区。
3. `docker-compose.dev.yml` 属于 P0，但当前不纳入第一轮白名单。
4. 本任务涉及 `shared/contracts`，但当前最小触点只有 `shared/contracts/backtest/api.md` 单文件。

## 当前继续锁定的重点文件

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

## Atlas 向 Jay.S 汇报摘要

1. 已完成 `TASK-0007` 预审建档，且确认旧 `TASK-0006` 已被历史任务占用，本事项不能复用旧编号。
2. 当前仓内正式后端只有 `/api/v1` skeleton，而前端实际仍指向 `localhost:8004` 并依赖一整组未登记的 `/api/*` 接口。
3. 当前任务必须先契约后实现；最小实施已拆为 A / B / C 三个代码批次。
4. 第一轮不碰 `docker-compose.dev.yml` 与 `services/backtest/Dockerfile`，不把工作区级 Docker 修复顺手并入。
5. `JBT-BACKTEST-8004` 的运行态清理保留为代码闭环后的后置动作，不进入本次代码 Token。

## Atlas 下一步应向 Jay.S 请求的精确 Token 申请口径

### 批次 A（P0）

请为项目架构师签发 `TASK-0007` 批次 A 的单 Agent、单任务、单文件 P0 Token，允许修改文件仅 `shared/contracts/backtest/api.md`，动作类型 `edit`，目的为先补登记 JBT backtest 正式 API 契约，并冻结 `/api/backtest/*`、`/api/strategy/*`、`/api/system/*`、`/api/market/*` 与既有 `/api/v1/*` 的对齐关系；有效期 30 分钟；白名单外文件继续锁定。

### 批次 B（P1）

请为回测 Agent 签发 `TASK-0007` 批次 B 的单 Agent、单任务、5 文件 P1 Token，允许修改文件仅 `services/backtest/src/api/app.py`、`services/backtest/src/api/routes/backtest.py`、`services/backtest/src/api/routes/strategy.py`、`services/backtest/src/api/routes/support.py`、`services/backtest/tests/test_api_surface.py`，动作类型 `edit/create`，目的为把当前前端依赖的 `8004` API 路由面正式并回 JBT 后端；有效期 30 分钟；如需 `runner.py`、`result_builder.py` 或任何第 6 个文件，当前 Token 立即失效并返回补充预审。

### 批次 C（P1）

请为回测 Agent 签发 `TASK-0007` 批次 C 的单 Agent、单任务、2 文件 P1 Token，允许修改文件仅 `services/backtest/backtest_web/src/utils/api.ts` 与 `services/backtest/backtest_web/next.config.mjs`，动作类型 `edit`，目的为把仓内默认后端代理与错误提示从 `localhost:8004` 收口到 JBT 正式后端口径；有效期 30 分钟；白名单外文件继续锁定。

## 下一步建议

1. Atlas 先为批次 A 向 Jay.S 申请单文件 P0 Token。
2. 批次 A 终审锁回后，再申请批次 B 的 5 文件 P1 Token。
3. 批次 B 终审锁回后，再申请批次 C 的 2 文件 P1 Token。
4. 批次 C 终审锁回后，再单独确认 `JBT-BACKTEST-8004` 的运行态清理窗口。