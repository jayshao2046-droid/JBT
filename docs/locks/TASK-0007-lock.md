# TASK-0007 Lock 记录

## Lock 信息

- 任务 ID：TASK-0007
- 阶段：批次 A 契约补登已执行并锁回；补充批次 D 已完成终审并锁回
- 执行 Agent：
  - 项目架构师（批次 A，P0 契约补登）
  - 回测 Agent（批次 B、批次 C、补充批次 D，P1 实施）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `shared/contracts/backtest/api.md`：批次 A 已在当前会话即时确认后执行；授权来源：Jay.S 当前会话明确确认：立即签发批次A；按要求不记录 token_id，当前状态已锁回
  - `services/backtest/src/api/**` 与指定 tests：待 Jay.S 为回测 Agent 签发 5 文件 P1 Token
  - `services/backtest/backtest_web/src/utils/api.ts`、`services/backtest/backtest_web/next.config.mjs`：待 Jay.S 为回测 Agent 签发 2 文件 P1 Token
  - `services/backtest/backtest_web/Dockerfile`：补充批次 D 已按 Jay.S 当前会话即时执行确认完成单文件实施、终审与锁回；授权来源原样记录为“远端 api 报错 500”；按要求不记录 token_id；执行主体固定为回测 Agent；终审确认业务白名单未越界，远端 air 重建验证后 API 500 已消失；后续如需再次修改该文件，必须重新补充预审

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0007-backtest-8004正式后端并回预审.md`
2. `docs/reviews/TASK-0007-review.md`
3. `docs/locks/TASK-0007-lock.md`
4. `docs/handoffs/TASK-0007-backtest-8004并回预审交接单.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

说明：

1. `docs/tasks`、`docs/reviews`、`docs/locks`、`docs/handoffs` 为 TASK-0007 预审阶段已使用治理文件。
2. 本次批次 A 按 prompt-sync 额外更新 `docs/prompts/公共项目提示词.md` 与 `docs/prompts/agents/项目架构师提示词.md`。
3. 本轮未扩写 `docs/rollback/**`。

## 批次 A 业务文件白名单（已执行并锁回）

1. `shared/contracts/backtest/api.md`

## 批次 B 业务文件白名单（待 P1 Token）

1. `services/backtest/src/api/app.py`
2. `services/backtest/src/api/routes/backtest.py`
3. `services/backtest/src/api/routes/strategy.py`
4. `services/backtest/src/api/routes/support.py`
5. `services/backtest/tests/test_api_surface.py`

## 批次 C 业务文件白名单（待 P1 Token）

1. `services/backtest/backtest_web/src/utils/api.ts`
2. `services/backtest/backtest_web/next.config.mjs`

## 补充批次 D 业务文件白名单（已执行并锁回）

1. `services/backtest/backtest_web/Dockerfile`

## 当前继续锁定的相关文件

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

## 锁控说明

1. `TASK-0006` 旧任务号已被历史预审产物占用；当前事项已独立建档为 `TASK-0007`，不得跨任务复用旧 Token。
2. 本任务必须先执行批次 A 的 P0 契约补登，再执行批次 B、批次 C 的 P1 实施；不得跳过顺序。
3. 批次 B 白名单已压缩到 5 文件；若执行中发现必须新增 `runner.py`、`result_builder.py` 或任何第 6 个文件，当前 Token 立即失效，必须回交补充预审。
4. 批次 C 只允许修正仓内 `8004` 默认代理与错误文案，不得借此 reopen `TASK-0004` 的 page 文件。
5. 补充批次 D 只允许修正 `services/backtest/backtest_web/Dockerfile` 中默认 `BACKEND_BASE_URL` 到 `http://backtest:8103`，不得借此 reopen `docker-compose.dev.yml`、`next.config.mjs`、`src/utils/api.ts`、任何 page 或后端文件。
6. 若补充批次 D 执行中证明必须新增第 2 个业务文件，当前授权立即失效，必须回交补充预审。
7. `docker-compose.dev.yml` 与 `services/backtest/Dockerfile` 属于当前继续锁定范围；本任务第一轮不处理工作区级 Docker 修复。
8. `JBT-BACKTEST-8004` 运行态容器清理不进入任何代码 Token，不得混入批次 A / B / C / 补充批次 D 白名单。

## 批次 A 执行留痕

1. 批次 A 本次实际业务写入仅限 `shared/contracts/backtest/api.md`。
2. 授权来源原样记录为：Jay.S 当前会话明确确认：立即签发批次A。
3. 执行动作为：补登正式契约中的双层路由口径、冻结当前兼容端点与 `/api/v1/*` 的对齐关系、完成自校验、当前会话即时锁回。
4. 本次按要求不记录 token_id，也不写精确分钟时间戳。

## 补充批次 D 执行留痕

1. 补充批次 D 本次实际业务写入仅限 `services/backtest/backtest_web/Dockerfile`；`docs/prompts/agents/回测提示词.md` 的同步更新属于 P-LOG 留痕，不构成业务白名单越界。
2. 当前实际收口仍仅限两处默认值：构建期 `ARG BACKEND_BASE_URL` 与运行期 `ENV BACKEND_BASE_URL` 均已从 `http://backtest-api:8103` 收口到 `http://backtest:8103`。
3. 最小自校验已补核：`services/backtest/backtest_web/Dockerfile` 与 `docs/prompts/agents/回测提示词.md` 诊断结果均为 `No errors found`。
4. 远端验证已补核：air 端完成 backtest-web 单服务重建后，`/agent-network` 返回 200，`/api/system/status` 返回 200，且 API body 正常返回 JSON；此前由错误主机名导致的代理 500 已消失。
5. 终审结论：补充批次 D 通过，当前业务白名单未越界；本轮单文件范围已闭环并锁回。

## 当前状态

- 预审状态：已通过
- 批次 A 状态：当前会话已执行并锁回
- 批次 B Token 状态：待签发
- 批次 C Token 状态：待签发
- 补充批次 D 状态：已完成自校验、终审与锁回
- 解锁时间：2026-04-04（批次 A 当前会话即时确认）；2026-04-06（补充批次 D 当前会话即时执行确认）
- 失效时间：N/A
- 锁回时间：2026-04-04（批次 A 当前会话即时锁回）；2026-04-06（补充批次 D 终审锁回）
- lockback 结果：批次 A 已锁回；批次 B、批次 C 尚未执行；补充批次 D 已完成单文件实施、终审与锁回

## 结论

**TASK-0007 批次 A 已完成正式契约补登、自校验与锁回；2026-04-06 补充批次 D 已完成单文件实施、终审与锁回，业务白名单未越界，远端 air 重建验证已确认 API 500 消失；后续如需再次修改 `services/backtest/backtest_web/Dockerfile`，必须重新补充预审；`JBT-BACKTEST-8004` 运行态清理继续后置；批次 B 与批次 C 仍待 Jay.S 后续签发对应 P1 Token。**