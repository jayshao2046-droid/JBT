# TASK-0023 sim-trading 发布接口预审交接单

【签名】项目架构师
【时间】2026-04-08
【设备】MacBook

## 一、交接目标

为模拟交易 Agent 提供 `TASK-0023` 的正式预审结论、批次白名单与 Token 申请清单；当前仅允许据此准备执行，不得越权写代码。

## 二、当前结论

1. `TASK-0023` 已独立成立，不并入 `TASK-0021`、`TASK-0017` 或 `TASK-0022`。
2. 本轮归属明确冻结为 `services/sim-trading/**` 单服务范围。
3. 当前 shared contract 已足够承接本轮实现，本轮不进入 `shared/contracts/**`。
4. 下游接收端正式路径冻结为：`POST /api/v1/strategy/publish`。

## 三、批次清单

### `TASK-0023-A` 最小发布接收接口

- 执行 Agent：模拟交易 Agent
- 保护级别：P1
- 是否需要 Token：需要 P1
- 是否可并行：可与 `TASK-0021-H4` 并行

白名单：

1. `services/sim-trading/src/api/router.py`
2. `services/sim-trading/tests/test_strategy_publish_api.py`

目标：

1. 在现有 `/api/v1` 命名空间下提供最小策略发布接收接口。
2. 校验 `publish_target=sim-trading` 与策略包关键字段。
3. 返回最小确认回执，供 decision 判定“已接收 / 已拒绝”。

验收标准：

1. `POST /api/v1/strategy/publish` 不再返回 404。
2. 非 `sim-trading` 目标或关键字段缺失时返回显式 4xx。
3. 合法载荷返回 2xx，并带 `strategy_id`、接收结果与时间戳等最小确认信息。
4. 不触碰 `.env.example`、compose、shared contract 或前端页面。

## 四、执行约束

1. 本轮只允许“接收 + 校验 + 回执”，不允许顺手接入真实下单或 CTP 执行链。
2. 本轮不复用 `TASK-0021`、`TASK-0017`、`TASK-0022` 的任何白名单或 Token。
3. 若执行中发现必须新增第 3 个业务文件、修改 `.env.example` 或 shared contract，当前批次立即失效，必须回交补充预审。

## 五、向 Jay.S 汇报摘要

1. `TASK-0023` 已完成独立预审建档；sim-trading 发布接收接口不再混入 `TASK-0021`。
2. 当前只冻结 1 个 P1 批次：`router.py` + `test_strategy_publish_api.py`。
3. 正式命名空间已冻结为 `/api/v1/strategy/publish`，可与 `TASK-0021-H4` 并行推进，但端到端验收需两边同时完成。
4. 本轮不改 `.env.example`、compose、shared contract；若后续证明仍需这些文件，必须另起 **P0** 补审。

## 六、下一步建议

1. 先由 Jay.S 决定是否为模拟交易 Agent 签发 `TASK-0023-A` 的 P1 Token。
2. 一旦签发，可与 decision 侧 `TASK-0021-H4` 并行推进。
3. 在 Jay.S 未确认前，不派发模拟交易 Agent 进入 `TASK-0023` 代码写入。