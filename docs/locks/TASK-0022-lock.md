# TASK-0022 Lock 记录

## Lock 信息

- 任务 ID：TASK-0022
- 阶段：sim-trading 运行态交互收口与只读日志预审
- 当前任务是否仍处于“预审未执行”状态：否；批次 A 已完成第二次正式终审与 lockback，批次 B 尚未进入代码执行
- 执行 Agent：
  - 项目架构师（当前 P-LOG 治理文件）
  - 模拟交易 Agent（后续批次 A / B 代码实施）

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0022-sim-trading-运行态交互收口与只读日志预审.md`
2. `docs/reviews/TASK-0022-review.md`
3. `docs/locks/TASK-0022-lock.md`
4. `docs/handoffs/TASK-0022-sim-trading-运行态交互预审交接单.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

## 当前锁定范围

1. `services/**`
2. `shared/contracts/**`
3. `services/sim-trading/.env.example`
4. `docker-compose.dev.yml`
5. 其他全部非白名单文件

## Token 摘要

### 当前轮次

1. P-LOG 协同账本区：不需要文件级 Token。
2. 当前状态：仅建档，未申请代码 Token。

### 批次 A（首轮 token，终审未通过，历史留痕）

1. 任务：`TASK-0022-A`
2. 执行 Agent：模拟交易 Agent
3. 保护级别：**P1**
4. token_id：`tok-780c5ba1-8873-41a9-a395-668fb39f0b7f`
5. review-id：`REVIEW-TASK-0022-A`
6. 实际白名单：
   - `services/sim-trading/src/api/router.py`
   - `services/sim-trading/src/gateway/simnow.py`
   - `services/sim-trading/sim-trading_web/app/operations/page.tsx`
   - `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`
   - `services/sim-trading/tests/test_console_runtime_api.py`
7. 目标：自动补齐 futures-only、主卡片 50 万口径、L2 说明收口。
8. 当前终审结果：`blocked`
9. 未执行 lockback 原因：
   - `app/operations/page.tsx` 存在 stale closure 回归，自动补齐 / 盘口联动未形成稳定通过态。
   - `app/intelligence/page.tsx` 混入 `dailyPnlMap` / 历史清空 / 日历着色等超 A 批范围 hunk，且 `acct?.net_pnl` 与当前 `/api/v1/account` 结构不一致。
   - `src/api/router.py` 夹带默认 CTP front / `ctp_app_id` / `ctp_auth_code` / 连接成功去重等非 A 批冻结目标 runtime hunk。
10. 当前状态：不得 lockback；如修复完成时原 token 已失效，需由 Jay.S 重新签发。

### 批次 A（二次收口重签 token，已 lockback）

1. 任务：`TASK-0022-A`
2. 执行 Agent：模拟交易 Agent
3. 保护级别：**P1**
4. token_id：`tok-6610ebec-c5ab-4271-8e62-b5cb12f85666`
5. review-id：`REVIEW-TASK-0022-A`
6. 实际白名单：
   - `services/sim-trading/src/api/router.py`
   - `services/sim-trading/src/gateway/simnow.py`
   - `services/sim-trading/sim-trading_web/app/operations/page.tsx`
   - `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`
   - `services/sim-trading/tests/test_console_runtime_api.py`
7. 重签目的：终审阻断二次收口；仅修首轮 review 的 3 个 blockers。
8. validate 结果：通过；任务、agent、action 与 5 个白名单文件完全匹配。
9. lockback 时间：`2026-04-08 02:57:17 +0800`
10. lockback 结果：`approved`
11. lockback 摘要：`TASK-0022-A 第二次正式终审通过，执行锁回`
12. 当前状态：`locked`

### 批次 B（pending_token）

1. 任务：`TASK-0022-B`
2. 执行 Agent：模拟交易 Agent
3. 保护级别：**P1**
4. 建议白名单：
   - `services/sim-trading/src/main.py`
   - `services/sim-trading/src/api/router.py`
   - `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`
   - `services/sim-trading/tests/test_log_view_api.py`（允许新增）
5. 目标：最小只读日志查看。
6. 前置关系：必须等待 `TASK-0014-A4` 与 `TASK-0017-A4` 锁回后再启动。

## 当前继续禁止修改的路径说明

1. `TASK-0022` 当前不解锁 `shared/contracts/**`，禁止以“字段边界”名义顺手修改正式契约。
2. `TASK-0022` 当前不解锁 `.env.example`，禁止把 50 万本金改成配置项并写入仓库文件。
3. `TASK-0022` 当前不解锁 `docker-compose.dev.yml` 或任何部署文件，禁止把 UI / API 收口混成部署批次。
4. `TASK-0022` 当前不复用 `TASK-0015`、`TASK-0017`、`TASK-0020` 的任何白名单或 Token。

## 并行性结论

1. 批次 A 与批次 B **不可并行**。
2. 原因：两批共享 `services/sim-trading/src/api/router.py` 与 `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`。
3. 若强行并行，白名单与回滚单元都会发生交叉污染。

## 进入执行前需要的 Token / 授权

1. `TASK-0022-A` 已完成第二次正式终审并锁回，无需再签发 A 批 Token。
2. Jay.S 需在 `TASK-0014-A4` 与 `TASK-0017-A4` 锁回后，再决定是否签发 `TASK-0022-B` 的 P1 Token。
3. 若 Jay.S 要求批次 B 扩展为“文件级历史日志 / 下载 / 路径选择”，当前批次 B 立即失效，必须回交补充预审。

## 当前状态

- 预审状态：已通过
- Token 状态：批次 A 首轮 token = `historical_blocked`；批次 A 当前重签 token = `locked`；批次 B = `pending_token`
- 解锁时间：批次 A 当前重签 token 已签发并 validate 通过；批次 B = N/A
- 失效时间：批次 A 首轮 token 已失效；当前重签 token 已在失效前完成 lockback
- 锁回时间：批次 A = `2026-04-08 02:57:17 +0800`；批次 B = N/A
- lockback 结果：批次 A 当前重签 token 已执行 `approved` 锁回；批次 B 尚未进入代码执行

## 结论

**`TASK-0022` 当前状态更新为：批次 A 已完成第二次正式终审并已 lockback；当前有效锁回 token_id 为 `tok-6610ebec-c5ab-4271-8e62-b5cb12f85666`，review-id 为 `REVIEW-TASK-0022-A`，结果 `approved`，状态 `locked`。批次 B 继续 `pending_token`，且必须等待 `TASK-0014-A4` 与 `TASK-0017-A4` 收口后再启动。除 A 批五个白名单文件外，继续锁定 `services/**`、`shared/contracts/**`、`.env.example`、`docker-compose.dev.yml` 及其他非白名单文件。**