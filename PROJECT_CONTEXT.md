# JBT Project Context

【签名】Atlas
【时间】2026-04-09
【设备】MacBook
【状态】JBT 为唯一项目管理来源

## 1. 项目定位

1. JBT 是下一代多服务工作区，也是当前唯一的任务、prompt、进度、计划来源。
2. `J_BotQuant` 继续保留为 legacy 运行工程，但不再承担 JBT 的项目管理上下文来源。
3. 只有当某个已建档迁移任务明确授权时，才可只读读取 `J_BotQuant` 的旧代码或旧运行事实；仍然禁止在 legacy 目录写入。

## 2. 服务边界

| 服务 | 目录 | 职责 |
|---|---|---|
| sim-trading | `services/sim-trading/` | 模拟交易、执行风控、账本 |
| live-trading | `services/live-trading/` | 实盘交易、执行风控、账本 |
| backtest | `services/backtest/` | 在线 / 本地回测、报告、绩效评估 |
| decision | `services/decision/` | 因子、信号、审批、策略编排 |
| data | `services/data/` | 数据采集、标准化、供数 API |
| dashboard | `services/dashboard/` | 聚合看板、只读查询、受控配置入口 |

## 3. 设备与端口冻结

1. Mini：`data:8105`、`sim-trading:8101`、`sim-trading-web:3002`
2. Air：`backtest:8103`、`backtest-web:3001`
3. Studio：`decision:8104`、`decision-web:3003`、`dashboard:8106/3005`
4. 端口语义固定：Web `3001~3006`，API `8101~8106`；只允许主机名 / IP 变化，不允许改端口语义。

## 4. 当前冻结事实

1. JBT 当前只允许文件级 Token，不存在目录级或整仓级“全局 Token”。
2. `极速维修 V2` 与 `终极维护模式 U0` 已正式落地并锁回；二者都不是目录级解锁。
3. `TASK-0029`、`TASK-0030`、`TASK-0031`、`TASK-0032` 已锁回，不重开。
4. 数据端当前优先级最高的是 system 级迁移治理，不是继续临时热修。
5. 统一聚合 dashboard 当前仅完成 Atlas 级规划冻结，尚未建正式治理任务。
6. 回测本轮处于阶段性结案 / 维护观察；模拟交易维持 `TASK-0017` 待开盘验证。

## 5. 接管规则

1. 开工先读 `ATLAS_PROMPT.md`、`docs/plans/ATLAS_MASTER_PLAN.md`、本文件，再进入总项目经理双 prompt。
2. 若 `docs/JBT_FINAL_MASTER_PLAN.md` 与总项目经理双 prompt 存在时间差，以双 prompt 的较新留痕为准。
3. 所有专项续接统一走 `docs/handoffs/Atlas-*.md`。