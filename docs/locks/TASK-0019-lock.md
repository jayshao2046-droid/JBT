# TASK-0019 Lock 记录

## Lock 信息

- 任务 ID：TASK-0019
- 阶段：sim-trading 收盘统计邮件 / 定时报表预审
- 当前任务是否仍处于“预审未执行”状态：整体是；B0 / B1 / B2 已冻结待签发
- 执行 Agent：
  - 项目架构师（当前 P-LOG 治理文件）
  - 模拟交易 Agent（后续服务实现主体）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `TASK-0019-B0`：`services/sim-trading/.env.example`，后续单文件 P0 Token
  - `TASK-0019-B1`：`services/sim-trading/src/main.py`、`src/notifier/email.py`、`src/ledger/service.py` + 最多 2 个测试文件，后续 P1 Token
  - `TASK-0019-B2`：`services/sim-trading/src/gateway/simnow.py`、`src/ledger/service.py`、`src/api/router.py` + 最多 2 个测试文件，后续 P1 Token

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0019-sim-trading-收盘统计邮件预审.md`
2. `docs/reviews/TASK-0019-review.md`
3. `docs/locks/TASK-0019-lock.md`
4. `docs/rollback/TASK-0019-rollback.md`
5. `docs/handoffs/TASK-0019-收盘统计邮件预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 当前锁定范围

1. `services/sim-trading/**`
2. `services/sim-trading/.env.example`
3. `shared/contracts/**`
4. 其他全部非白名单文件

## 批次冻结信息

### B0

1. 批次名称：补充批次 B0 — 报表收件人 / 时间窗配置占位（如需要）
2. 执行 Agent：模拟交易
3. 保护级别：P0
4. 建议白名单：`services/sim-trading/.env.example`
5. 当前 Token 状态：待 Jay.S 确认是否需要该批次；如需要则为 pending_token

### B1

1. 批次名称：补充批次 B1 — scheduler 与最小邮件报表骨架
2. 执行 Agent：模拟交易
3. 保护级别：P1
4. 建议白名单：
   - `services/sim-trading/src/main.py`
   - `services/sim-trading/src/notifier/email.py`
   - `services/sim-trading/src/ledger/service.py`
   - 最多 2 个 `services/sim-trading/tests/**` 测试文件
5. 当前 Token 状态：pending_token

### B2

1. 批次名称：补充批次 B2 — 账户 / 持仓 / 成交报表充实
2. 执行 Agent：模拟交易
3. 保护级别：P1
4. 建议白名单：
   - `services/sim-trading/src/gateway/simnow.py`
   - `services/sim-trading/src/ledger/service.py`
   - `services/sim-trading/src/api/router.py`
   - 最多 2 个 `services/sim-trading/tests/**` 测试文件
5. 执行顺序：B2 仅能在 B1 完成自校验并锁回后启动。
6. 当前 Token 状态：pending_token

## 当前继续禁止修改的路径说明

1. 当前整个 `services/sim-trading/**` 仍未对本任务解锁，禁止写入。
2. 禁止把 `TASK-0019` 与 `TASK-0014` 混批执行。
3. 禁止把真实收件人、邮箱密码、SMTP Secret 或 webhook 写入仓库。
4. 禁止在服务代码中耦合 `/Users/jayshao/J_BotQuant/.env` 路径。

## 进入执行前需要的 Token / 授权

1. `TASK-0014-A1` 与 `TASK-0014-A2` 应先于本任务执行。
2. Jay.S 需最终确认晚间时间窗采用 `23:10` 还是 `23:40`。
3. B0 若需要，必须先以单文件 P0 方式签发 `services/sim-trading/.env.example`。
4. B1 / B2 需要先冻结精确到文件的最多 2 个测试文件名单，再分别签发 P1 Token。

## 当前状态

- 预审状态：已通过
- Token 状态：B0 待确认是否需要；B1 / B2 均为 `pending_token`
- 解锁时间：N/A
- 失效时间：N/A
- 锁回时间：N/A
- lockback 结果：尚未进入代码执行阶段

## 结论

**TASK-0019 当前仍处于“预审未执行”状态；收盘统计邮件 / 定时报表继续锁定，后续仅能按 B0（如需要）→ B1 → B2 顺序进入执行。**