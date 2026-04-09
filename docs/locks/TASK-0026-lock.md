# TASK-0026 Lock 记录

## Lock 信息

- 任务 ID：TASK-0026
- 阶段：回测新增因子与下划线兼容 — 全部完成
- 当前任务是否仍处于"预审未执行"状态：否
- 当前总状态：`completed`
- 执行 Agent：
  - 项目架构师（预审建档 + C 批次锁回）
  - 回测 Agent（A/B 代码实施）

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0026-backtest-新增因子与下划线兼容实现.md`
2. `docs/reviews/TASK-0026-review.md`
3. `docs/locks/TASK-0026-lock.md`
4. `docs/handoffs/TASK-0026-架构预审交接单.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

## 批次 Token 摘要

### 批次 A（TASK-0026-A）

1. 保护级别：P1
2. 状态：`locked_back`
3. 白名单：
   - `services/backtest/src/backtest/factor_registry.py`
   - `services/backtest/tests/test_factor_registry_aliases.py`
4. 目标：新增 `Spread`、`Spread_RSI`。
5. token_id：`tok-81a76988-7317-42a5-b0e0-5c10b3587a14`
6. review-id：`REVIEW-TASK-0026-A`
7. validate：passed（2026-04-08）
8. lockback_time：2026-04-10
9. lockback_summary：批次A新增因子Spread/Spread_RSI已闭环，6 tests passed，执行锁回

### 批次 B（TASK-0026-B）

1. 保护级别：P1
2. 状态：`locked_back`
3. 白名单：
   - `services/backtest/src/backtest/factor_registry.py`
   - `services/backtest/src/backtest/generic_strategy.py`
   - `services/backtest/src/api/routes/support.py`
   - `services/backtest/tests/test_factor_registry_aliases.py`
4. 目标：全量下划线别名兼容。
5. token_id：`tok-8ac60661-f8bd-47da-b2fc-02c677e94898`
6. review-id：`REVIEW-TASK-0026-B`
7. validate：passed（2026-04-08）
8. lockback_time：2026-04-10
9. lockback_summary：批次B全量下划线别名兼容已闭环，10 tests passed（含4新增），全量回测60 passed/2 failed（既有），执行锁回

### 批次 C（TASK-0026-C）

1. 保护级别：P1
2. 状态：`locked_back`
3. 白名单：
   - `docs/reviews/TASK-0026-review.md`
   - `docs/locks/TASK-0026-lock.md`
   - `docs/handoffs/TASK-0026-实施交接与回归结果.md`
4. 目标：回归收口、终审留痕与锁回。
5. token_id：`tok-96414cea`
6. review-id：`REVIEW-TASK-0026-C`
7. validate：passed（2026-04-10）
8. lockback_time：2026-04-10
9. lockback_summary：批次C回归留痕与锁回已闭环，三批全部locked_back，TASK-0026完成

## 强制锁定声明

1. **未签发不得写 `services/backtest/**` 白名单文件。**
2. A/B/C 任一批次在 Token 未签发前，均不得进入服务代码修改。
3. 批次执行中若需新增文件，当前 Token 视为失效，必须回交补充预审。

## 当前继续锁定范围

1. `services/backtest/**` 中除未来获签批次白名单外的全部文件。
2. `shared/contracts/**`、`services/data/**`、`services/decision/**`、`services/dashboard/**`。
3. 其他全部非白名单文件。

## 当前状态

- `TASK-0026-A`：`locked_back`（2026-04-10）
- `TASK-0026-B`：`locked_back`（2026-04-10）
- `TASK-0026-C`：`locked_back`（2026-04-10）

## 结论

`TASK-0026` A/B/C 三批次全部通过终审并完成锁回，当前总状态 `completed`。全部白名单文件已重新锁定，后续如需修改须另起任务。
