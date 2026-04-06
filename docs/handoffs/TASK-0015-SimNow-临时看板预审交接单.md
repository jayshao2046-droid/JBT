# TASK-0015 SimNow 临时看板预审交接单

【签名】项目架构师
【时间】2026-04-06
【设备】MacBook

## 任务结论

1. `TASK-0015` 已完成预审建档与第二轮治理账本补齐。
2. SimNow 临时看板正式归属 `services/dashboard/**`，且明确不等于 backtest 看板任务。
3. 当前轮次只完成治理冻结，不进入代码执行。

## 该任务交给谁执行

1. 后续执行主体：看板 Agent。

## 执行前置依赖

1. `TASK-0009` 必须闭环。
2. `TASK-0013` 必须完成统一风控核心与阶段预设治理冻结。
3. `TASK-0010` 必须提供最小可读 API 面。
4. `TASK-0014` 必须冻结风险事件级别与通知口径。
5. Jay.S 必须提供前端材料或给出书面豁免。

## 不得跨越的边界

1. 不得修改 `services/backtest/backtest_web/**`。
2. 不得在前端页面中直接发起交易、清退、强平等写操作。
3. 不得绕过 `services/sim-trading/**` 直接读取账本、运行态目录、真实 `.env` 或数据库快照。
4. 若需要新增 API 字段，必须先回交预审，不得先写页面再补契约。

## 进入执行前 Atlas / Jay.S / 对应 Agent 还需完成什么

### Atlas

1. 先向 Jay.S 收集前端材料，再冻结 `services/dashboard/**` 的文件级白名单。
2. 不得在前端材料缺失时提前派发看板 Agent 进入实现。

### Jay.S

1. 提供前端材料、页面目标与必要环境变量需求。
2. 确认是否需要补 `services/dashboard/.env.example` 或只读契约字段。

### 看板 Agent

1. 在材料到位后提交 `services/dashboard/**` 的文件级白名单申请。
2. 严格按只读聚合边界设计页面，不复用 backtest 看板白名单。
3. 每完成一动作同步私有 prompt 与 handoff。

## 当前授权状态

1. 当前只完成治理账本闭环，不含任何代码 Token。
2. 当前不允许进入 `services/dashboard/**`、`.env.example` 或 `shared/contracts/**` 写入。

## 向 Atlas 汇报摘要

1. `TASK-0015` 的 review / lock / rollback / handoff 已补齐。
2. 看板归属、只读边界与前端材料前置依赖已冻结。
3. 当前仍是“预审未执行”状态，需等待 Jay.S 提供材料与签发 Token。

## 下一步建议

1. 先由 Jay.S 提供前端材料。
2. 再冻结 `services/dashboard/**` 文件级白名单并准备 P1 / P0 Token。
3. 未获材料前，看板 Agent 继续待命。