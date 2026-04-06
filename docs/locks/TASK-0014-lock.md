# TASK-0014 Lock 记录

## Lock 信息

- 任务 ID：TASK-0014
- 阶段：sim-trading 风控通知链路预审
- 当前任务是否仍处于“预审未执行”状态：整体是；补充批次 A1 / A2 已冻结待签发
- 执行 Agent：
  - 项目架构师（当前 P-LOG 治理文件）
  - 模拟交易 Agent（后续服务实现主体）
- Token 摘要：
  - P-LOG 协同账本区文件：不需要文件级 Token
  - `TASK-0014-A1`：`services/sim-trading/src/main.py`、`src/risk/guards.py`、`src/notifier/dispatcher.py`、`tests/test_risk_hooks.py`、`tests/test_notifier.py`，后续 P1 Token
  - `TASK-0014-A2`：`services/sim-trading/src/api/router.py`、`src/gateway/simnow.py` + 最多 2 个测试文件，后续 P1 Token
  - `services/sim-trading/.env.example`：后续单文件 P0 Token
  - `shared/contracts/**` 若补通知事件契约：后续 P0 Token

## 治理文件白名单（本轮已使用）

1. `docs/tasks/TASK-0014-sim-trading-风控通知链路预审.md`
2. `docs/reviews/TASK-0014-review.md`
3. `docs/locks/TASK-0014-lock.md`
4. `docs/rollback/TASK-0014-rollback.md`
5. `docs/handoffs/TASK-0014-风控通知链路预审交接单.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`

## 当前锁定范围

1. `services/sim-trading/**`
2. `services/live-trading/**`
3. `shared/contracts/**`
4. `services/sim-trading/.env.example`
5. 其他全部非白名单文件

## 即时通知补充批次冻结信息

### 补充批次 A1

1. 批次名称：补充批次 A1 — 通知 bootstrap 与风险钩子闭环
2. 执行 Agent：模拟交易
3. 保护级别：P1
4. 建议白名单：
  - `services/sim-trading/src/main.py`
  - `services/sim-trading/src/risk/guards.py`
  - `services/sim-trading/src/notifier/dispatcher.py`
  - `services/sim-trading/tests/test_risk_hooks.py`
  - `services/sim-trading/tests/test_notifier.py`
5. 当前 Token 状态：pending_token

### 补充批次 A2

1. 批次名称：补充批次 A2 — 系统事件来源接线
2. 执行 Agent：模拟交易
3. 保护级别：P1
4. 建议白名单：
  - `services/sim-trading/src/api/router.py`
  - `services/sim-trading/src/gateway/simnow.py`
  - 最多 2 个 `services/sim-trading/tests/**` 测试文件
5. 执行顺序：A2 仅能在 A1 完成自校验并锁回后启动。
6. 当前 Token 状态：pending_token

### 凭证来源治理

1. Jay.S 已明确允许 legacy `J_BotQuant/.env` 作为“凭证来源”。
2. 推荐采用部署侧 env mapping / fallback，不得在服务代码中硬编码或读取 `/Users/jayshao/J_BotQuant/.env` 路径。
3. 真实 Secret 继续禁止写入 Git、`.env.example` 或治理账本。

## 当前继续禁止修改的路径说明

1. 当前整个 `services/sim-trading/**` 仍未对本任务冻结文件级白名单，禁止写入。
2. 禁止复用 `services/live-trading/**` 或其他服务的默认 webhook、邮箱配置与通知模板。
3. 禁止在 `shared/contracts/**` 中先写通知事件契约后补审。
4. 禁止把真实 webhook、邮箱账号、邮箱密码或 SMTP Secret 写入仓库。
5. 禁止在服务代码中耦合 `/Users/jayshao/J_BotQuant/.env` 路径。

## 进入执行前需要的 Token / 授权

1. `TASK-0009`、`TASK-0013` 必须先闭环。
2. `TASK-0010` 必须先完成最小风险事件输出与风控钩子占位。
3. 需要由 Jay.S 先按 `TASK-0014-A1` → `TASK-0014-A2` 顺序签发对应 P1 Token。
4. 若后续需要补 `services/sim-trading/.env.example` 通知占位，必须另拆单文件 P0 批次。
5. A2 若涉及测试文件，必须先冻结精确到文件的最多 2 个测试文件名单，再签发 Token。

## 当前状态

- 预审状态：已通过
- Token 状态：未申请主任务代码 Token；补充批次 A1 / A2 均为 `pending_token`
- 解锁时间：N/A
- 失效时间：N/A
- 锁回时间：N/A
- lockback 结果：尚未进入代码执行阶段

## 结论

**TASK-0014 当前仍处于“预审未执行”状态；即时通知继续归入补充批次 A1 / A2，且两批均待签发；通知链路相关服务文件、契约文件与 `.env.example` 继续锁定。**