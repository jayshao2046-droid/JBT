# JBT Atlas Master Plan

【签名】Atlas
【时间】2026-04-09
【设备】MacBook
【状态】JBT 本地 Atlas 计划入口

## 1. 本文件定位

1. 本文件是 Atlas 模式在 JBT 工作区内的 master plan 入口文件。
2. 详细总计划以 `docs/JBT_FINAL_MASTER_PLAN.md` 为主。
3. 若 `docs/JBT_FINAL_MASTER_PLAN.md` 与 `docs/prompts/总项目经理调度提示词.md`、`docs/prompts/agents/总项目经理提示词.md` 存在时间差，以后两者的较新留痕为准；Atlas 后续负责回补总计划。

## 2. 当前总优先级

1. 数据端：准备“Mini system 级采集 / 调度 / 通知迁移到 JBT Docker 体系”的治理与切换方案。
2. 看板端：统一聚合 dashboard 已完成规划冻结，下一步先建治理账本，不直接写 `services/dashboard/**`。
3. 模拟交易：维持 `TASK-0017` 待开盘验证，不擅自扩范围。
4. 回测：维持阶段性结案 / 维护观察。
5. 决策：如继续做 legacy 清洗迁移，先走专项 handoff 与架构判边。

## 3. 已锁回基线

1. `TASK-0029` 已锁回：`极速维修 V2` 正式治理规则已落地。
2. `TASK-0030` 已锁回：`终极维护模式 U0` 正式治理规则已落地。
3. `TASK-0031` 已锁回：data 单服务热修完成。
4. `TASK-0032` 已锁回：`data_web` 临时原型导入完成。

## 4. 开工后的继续读取链

1. `docs/prompts/总项目经理调度提示词.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/总项目经理提示词.md`
4. 如有专项，继续读取对应 `docs/handoffs/Atlas-*.md`