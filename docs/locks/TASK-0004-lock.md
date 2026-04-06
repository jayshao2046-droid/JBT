# TASK-0004 Lock 记录

## Lock 信息

- 任务 ID：TASK-0004
- 阶段：看板阶段预审 / 2026-04-04 Token 签发同步 / 2026-04-06 单文件补充预审授权留痕 / 2026-04-06 单文件补充终审与锁回 / 2026-04-06 金额型日亏损字段语义保持修复补充预审授权留痕 / 2026-04-06 金额型日亏损字段语义保持修复终审与锁回
- 执行 Agent：
  - 项目架构师（P-LOG 治理文件）
  - 回测 Agent（当前有效 P1 Token 绑定执行主体）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `services/backtest/backtest_web/`：Jay.S 已于 2026-04-04 为回测 Agent 签发当前有效 2 文件 P1 Token；具体 Token 不入 Git，仅记录范围摘要
  - `services/backtest/backtest_web/app/agent-network/page.tsx`：2026-04-06 单文件补充范围按“Jay.S 当前会话授权 + 范围摘要”留痕，不记录 `token_id`；当前已完成实施、自校验、项目架构师终审与锁回
  - `services/backtest/backtest_web/app/agent-network/page.tsx`：2026-04-06 最新单文件补充范围（二：金额型日亏损字段语义保持修复）继续按“Jay.S 当前会话授权 + 单文件范围摘要”留痕，不记录 `token_id`；当前已完成实施、自校验、air 远端验证、项目架构师终审与锁回

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0004-backtest-dashboard-Phase1-两页收敛.md`
2. `docs/reviews/TASK-0004-review.md`
3. `docs/locks/TASK-0004-lock.md`
4. `docs/rollback/TASK-0004-rollback.md`
5. `docs/handoffs/TASK-0004-看板预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 业务文件白名单（历史 2 文件 Token）

1. `services/backtest/backtest_web/app/agent-network/page.tsx`
2. `services/backtest/backtest_web/app/operations/page.tsx`

## 最新单文件补充预审冻结白名单（2026-04-06）

1. `services/backtest/backtest_web/app/agent-network/page.tsx`

## 当前继续锁定的相关文件（以最新补充预审口径为准）

1. `services/backtest/backtest_web/app/page.tsx`
2. `services/backtest/backtest_web/app/operations/page.tsx`
3. `services/backtest/backtest_web/app/layout.tsx`
4. `services/backtest/backtest_web/package.json`
5. `services/backtest/backtest_web/app/command-center/page.tsx`
6. `services/backtest/backtest_web/app/intelligence/page.tsx`
7. `services/backtest/backtest_web/app/systems/page.tsx`
8. `services/backtest/backtest_web/src/**`
9. `services/backtest/src/**`
10. `shared/contracts/**`
11. `docker-compose.dev.yml`
12. 其他全部非白名单文件

## 2026-04-05 补充解锁范围（经补充预审）

1. `services/backtest/src/api/routes/support.py`
2. `services/backtest/backtest_web/src/utils/api.ts`
3. `services/backtest/backtest_web/src/utils/strategyPresentation.ts`
4. `services/backtest/tests/test_api_surface.py`

说明：本次补充范围仅用于解决“主力合约需从 TqSdk 实时导入”和“对象型错误详情不能显示为 `[object Object]`”两类问题；不得据此扩展到其他后端路由、首页壳层、Docker、contracts 或其他服务目录。

## 2026-04-05 紧急补充解锁范围（正式回测收口 + YAML symbols 解析 + hydration 修复）

1. `services/backtest/src/backtest/generic_strategy.py`
2. `services/backtest/backtest_web/app/agent-network/page.tsx`
3. `services/backtest/tests/test_generic_strategy_pipeline.py`

说明：本次紧急补充范围仅用于解决“匹配 YAML 的正式回测以 `回测结束` 误失败收口”“根级 `symbols:` 列表解析失败”“首屏 hydration mismatch”三类阻断问题；不得据此扩展到 `runner.py`、`strategy_base.py`、`test_api_surface.py`、contracts、Docker 或其他服务目录。

## 2026-04-06 单文件补充解锁范围（已实施并锁回）

1. `services/backtest/backtest_web/app/agent-network/page.tsx`

说明：

1. 授权来源原样记录为：Jay.S 当前会话明确要求继续沿用 `TASK-0004`，且本轮仅允许修改 `services/backtest/backtest_web/app/agent-network/page.tsx`，把“日亏损限制”统一为与“最大回撤”一致的百分比输入 / 显示方式；YAML 内部保存值仍保持 `0..1` 原始比例小数，不改变执行语义。
2. 本轮执行主体固定为：回测 Agent。
3. 本轮验收标准冻结为：输入 `0.7` 保存 `0.007`；读取 `0.007` 显示 `0.7`；`maxDrawdown` 百分比交互不回归；`positionFraction` 现有行为不回归。
4. 本轮明确继续锁定：`services/backtest/backtest_web/app/operations/page.tsx`、`services/backtest/backtest_web/app/page.tsx`、`services/backtest/backtest_web/src/**`、`services/backtest/src/**`、`shared/contracts/**` 与其他全部非白名单文件。
5. 本轮不得顺手调整摘要文案、后端解析、其他风控字段、operations 页面联动、helper 或 contract。
6. 若执行中证明必须新增第 2 个业务文件，当前补充范围立即失效，必须回交补充预审。
7. 本轮按要求不记录 `token_id`；当前执行口径以“当前会话授权 + 单文件范围摘要”为准。

## 2026-04-06 最新单文件补充解锁范围（二：金额型日亏损字段语义保持修复，已实施并锁回）

1. `services/backtest/backtest_web/app/agent-network/page.tsx`

说明：

1. 授权来源原样记录为：Jay.S 当前会话明确确认立即执行；执行闭环固定为“先修本地，再推送 git，再同步到 air 远端 docker，并验证远端可用且不能回退到之前的 API 500”。
2. 根因冻结为：`app/agent-network/page.tsx` 读取时把 `risk.daily_loss_limit` 与 `risk.daily_loss_limit_yuan` 混到同一状态，但写回 YAML 时只会序列化 `daily_loss_limit`，会把金额型日亏损字段误写为比例字段，并触发正式引擎 `risk.daily_loss_limit must be a ratio between 0 and 1`。
3. 本轮执行主体固定为：回测 Agent。
4. 允许的变更语义仅限：保留 `daily_loss_limit_yuan` 与 `daily_loss_limit` 的原始语义；只有比例模式才允许按百分比展示 / 输入；金额模式必须保持金额输入 / 写回；`maxDrawdown` 现有百分比交互不得回归。
5. 本轮验收标准冻结为：
  - 对 `risk.daily_loss_limit_yuan` 策略，修改 `maxDrawdown` 后再保存 / 回测，不得把金额字段误写成 `daily_loss_limit`；
  - 对比例型策略，`daily_loss_limit` 仍按百分比交互，输入 `0.7` 保存 `0.007`；
  - `maxDrawdown` 百分比交互不回归；
  - 不扩展第 2 个业务文件。
6. 本轮明确继续锁定：`services/backtest/backtest_web/app/operations/page.tsx`、`services/backtest/backtest_web/app/page.tsx`、`services/backtest/backtest_web/src/**`、`services/backtest/src/**`、`shared/contracts/**`、Dockerfile、tests 与其他全部非白名单文件。
7. 若执行中证明必须新增第 2 个业务文件，或需要改后端 / helper / tests / contracts / Dockerfile，当前补充范围立即失效，必须回交补充预审。
8. 本轮按要求不记录 `token_id`；当前执行口径以“当前会话授权 + 单文件范围摘要”为准。

## 执行语义冻结

1. 点击策略后，默认显示基本信息、策略参数、信号参数、风控参数。
2. 合约选择保留并上移。
3. 并发上限 KPI 下移到回测按钮下。
4. 取消 KPI 收起。
5. 扩充当前策略摘要。
6. 去掉行情类型与品种专属预设。

## 锁控说明

1. Token 已由 Jay.S 于 2026-04-04 签发，执行主体固定为回测 Agent。
2. 本轮有效白名单只有 2 个文件：`app/agent-network/page.tsx`、`app/operations/page.tsx`。
3. `app/page.tsx` 不在本轮有效 Token 范围内，当前继续锁定。
4. 若执行中发现必须修改第 3 个业务文件 `app/page.tsx` 或任一后端文件，当前 Token 立即暂停，必须补充预审。
5. 当前不需要 delete Token、rename Token 或目录级解锁。
6. 若执行主体发生变化，必须重新绑定 Token 并补充留痕。

## 当前状态

- 预审状态：已通过；2026-04-06 最新单文件补充终审已通过并锁回
- Token 状态：2026-04-04 历史 2 文件 P1 Token 已留痕；2026-04-06 最新单文件补充按“当前会话授权 + 单文件范围摘要”执行，不记录 `token_id`，当前状态已恢复锁定
- 解锁时间：2026-04-04（历史 2 文件 Token，具体时刻未入 Git）；2026-04-06（最新单文件补充授权留痕，具体时刻未入 Git）
- 失效时间：以 Jay.S 实际签发 / 当前会话执行窗口为准（未入 Git）
- 锁回时间：2026-04-05（补充范围 4 文件已终审通过并锁回）；2026-04-06（前序单文件百分比交互补充已终审通过并锁回）；2026-04-06（金额型日亏损字段语义保持修复单文件补充已终审通过并锁回）
- lockback 结果：`services/backtest/src/api/routes/support.py`、`services/backtest/backtest_web/src/utils/api.ts`、`services/backtest/backtest_web/src/utils/strategyPresentation.ts`、`services/backtest/tests/test_api_surface.py` 已完成本地自校验、项目架构师终审与锁回；运行态服务重启另行执行，不进入本次代码锁控范围
- 2026-04-06 最新单文件补充范围状态：已完成实施、本地自校验、air 远端 docker 验证、项目架构师终审与锁回；`services/backtest/backtest_web/app/agent-network/page.tsx` 当前已恢复锁定

## 2026-04-05 终审与锁回留痕

1. 本地自校验结果：补充范围 4 个目标文件静态诊断为 0。
2. 动态验收结果：代码级回归已确认 `/api/market/main-contracts` 可命中 `tqsdk_realtime_main_contracts`，并在无实时能力时回退到 `service_local_compatibility`；`/api/market/quotes` 同步支持 `tqsdk_realtime_quotes` 与 `service_local` 回退。
3. 项目架构师终审结论：通过，无阻断项，可以锁回本轮补充范围 4 个文件。
4. 白名单边界确认：本轮未越出 2026-04-05 补充预审冻结的 4 文件范围。

## 2026-04-05 紧急补充终审与锁回留痕

1. 本地自校验结果：紧急补充范围 3 个业务文件静态诊断为 0。
2. 回归校验要求：`services/backtest/tests/test_generic_strategy_pipeline.py` 已补充 `BacktestFinished` 落在最终快照 / finish 阶段时的 completed 收口用例。
3. 项目架构师终审结论：通过，无阻断项，可以锁回本轮紧急补充范围 3 个业务文件。
4. 白名单边界确认：本轮未越出 2026-04-05 紧急补充预审冻结的 3 个业务文件范围。

## 2026-04-06 单文件补充终审与锁回留痕

1. 本地自校验结果：`services/backtest/backtest_web/app/agent-network/page.tsx` 静态诊断为 0；`docs/prompts/agents/回测提示词.md` 诊断同样为 0。
2. 语义闭环核验结果：
  - `dailyLossLimit` 当前与 `maxDrawdown` 一致，使用 `formatPercentInput()` / `parsePercentInput()` / `formatDecimalAsPercent()`。
  - YAML 读取仍取 `risk.daily_loss_limit` / `risk.daily_loss_limit_yuan` 的原始比例小数。
  - YAML 写出仍由 `buildSystemRiskBlock()` 直接写 `config.dailyLossLimit.trim()`，未改成百分比字符串。
  - 因此输入 `0.7` 会保存 `0.007`，读取 `0.007` 会显示 `0.7`，验收标准成立。
3. 项目架构师范围核验结果：本轮未越出 `services/backtest/backtest_web/app/agent-network/page.tsx` 单文件范围，未扩展到 `app/operations/page.tsx`、`app/page.tsx`、`backtest_web/src/**`、`services/backtest/src/**`、`shared/contracts/**` 或其他非白名单文件。
4. 项目架构师终审结论：通过，无阻断项，可以立即锁回本轮单文件补充范围。
5. 锁回结论：`services/backtest/backtest_web/app/agent-network/page.tsx` 已完成本轮锁回；后续再改该文件仍需重新补充预审与解锁。

## 2026-04-06 最新单文件补充终审与锁回留痕（二：金额型日亏损字段语义保持修复）

1. 业务范围核验结果：本轮实际业务写入仍严格限于 `services/backtest/backtest_web/app/agent-network/page.tsx` 单文件；`docs/prompts/agents/回测提示词.md` 的更新属于 P-LOG 同步，不构成业务白名单越界。
2. 本地自校验结果：`services/backtest/backtest_web/app/agent-network/page.tsx` 诊断为 0 错误；`docs/prompts/agents/回测提示词.md` 诊断为 0 错误；`services/backtest/backtest_web` 下 `pnpm build` 已成功。
3. 语义保持核验结果：
  - `daily_loss_limit_yuan` 与 `daily_loss_limit` 的原始语义已保持分离，不再混写。
  - 对使用 `risk.daily_loss_limit_yuan` 的策略，修改 `maxDrawdown` 后再保存 / 回测，不会再把金额字段误写成 `daily_loss_limit`。
  - 对比例型策略，`daily_loss_limit` 继续保持百分比交互，输入 `0.7` 保存 `0.007`。
  - 金额模式继续保持金额输入 / 写回；`maxDrawdown` 百分比交互未回归。
4. air 远端验证结果：已同步 7 个相关文件到 `~/botquant-backtest-prod/`，并执行 `/usr/local/bin/docker compose -f docker-compose.dev.yml up -d --no-deps --build --force-recreate backtest-web`；`http://127.0.0.1:3001/agent-network` 返回 200，`http://127.0.0.1:3001/api/system/status` 返回 200，API body 正常返回 JSON，未回退到此前 API 500；本地与 air 上 7 个相关文件 `shasum` 完全一致。
5. 项目架构师终审结论：通过，无新的阻断项，可以立即锁回本轮单文件补充范围。
6. 锁回结论：`services/backtest/backtest_web/app/agent-network/page.tsx` 已完成本轮重新锁回；后续再改该文件仍须重新补充预审与解锁。

## 结论

**截至当前，TASK-0004 的两轮 2026-04-05 补充范围、前序 2026-04-06 单文件百分比交互补充，以及本轮 2026-04-06 “金额型日亏损字段语义保持修复”单文件补充，均已完成实施、自校验、项目架构师终审与锁回。当前重新锁回的业务范围为 `services/backtest/backtest_web/app/agent-network/page.tsx`；`app/operations/page.tsx`、`app/page.tsx`、`backtest_web/src/**`、`services/backtest/src/**`、`shared/contracts/**` 与其他非白名单文件继续锁定。**