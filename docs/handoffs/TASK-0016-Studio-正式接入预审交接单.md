# TASK-0016 Studio 正式接入预审交接单

【签名】项目架构师
【时间】2026-04-06
【设备】MacBook

## 任务结论

1. `TASK-0016` 已完成预审建档与第二轮治理账本补齐。
2. 正式 Studio API 接入已与 `TASK-0012` 的兼容桥接边界彻底分开。
3. 当前轮次只完成治理冻结，不进入代码执行。

## 该任务交给谁执行

1. `services/sim-trading/**` 批次：模拟交易 Agent。
2. `integrations/legacy-botquant/**` 批次：由 Jay.S 另行指定 P0 执行主体。
3. `shared/contracts/**` 批次：按 P0 路径独立执行，不与服务实现混批。

## 执行前置依赖

1. `TASK-0009` 必须闭环。
2. `TASK-0013`、`TASK-0010`、`TASK-0014` 必须先形成可验证基线。
3. `TASK-0015` 必须完成临时看板审阅结论，或由 Jay.S 书面豁免。
4. `TASK-0012` 的兼容桥接状态必须先明确。
5. Jay.S 必须确认进入正式 Studio API 接入测试窗口。

## 不得跨越的边界

1. 不得把本任务并回 `TASK-0012`。
2. 不得把 `shared/contracts/**`、`services/sim-trading/**`、`integrations/legacy-botquant/**` 混在同一批次执行。
3. 不得绕过 `TASK-0009` 的风控门槛与 `TASK-0013` 的 stage preset 治理。
4. 不得把上游 API URL、鉴权 key、签名密钥与回调凭证写入仓库。

## 进入执行前 Atlas / Jay.S / 对应 Agent 还需完成什么

### Atlas

1. 先把 contracts P0、服务侧 P1、integrations P0 三类批次拆成独立 Token 申请项。
2. 未完成拆批前，不得向模拟交易 Agent 或其他执行主体发放模糊白名单。

### Jay.S

1. 确认 `TASK-0012` 当前是否仍为正式接入前置路径。
2. 指定 `integrations/**` 的执行主体与测试窗口。
3. 提供上游 Secret 注入方案与轮换口径。

### 对应 Agent

1. 模拟交易 Agent：提交 `services/sim-trading/**` 的文件级白名单与自校验方案。
2. P0 集成执行主体：提交 `integrations/legacy-botquant/**` 的文件级白名单与失败收口方案。
3. 各主体都必须同步私有 prompt 与 handoff。

## 当前授权状态

1. 当前只完成治理账本闭环，不含任何代码 Token。
2. 当前不允许进入 `shared/contracts/**`、`services/sim-trading/**` 或 `integrations/**` 写入。

## 向 Atlas 汇报摘要

1. `TASK-0016` 的 review / lock / rollback / handoff 已补齐。
2. 正式接入与兼容桥接边界已冻结，未来必须拆为 contracts / 服务侧 / integrations 三类批次执行。
3. 当前仍是“预审未执行”状态，需等待前置依赖、执行主体与 P0 / P1 Token。

## 下一步建议

1. 先由 Jay.S 明确 `TASK-0012` 状态与正式接入测试窗口。
2. 再由 Atlas 准备三类独立 Token 申请清单。
3. 未获确认前，各执行主体继续待命。