# JBT Atlas Prompt

【签名】Atlas
【时间】2026-04-11
【设备】MacBook
【状态】JBT-only 管理已切换 / TASK-0043 已收口 / TASK-0045 A0完成

## 本文件定位

1. 本文件是 JBT 本地的 Atlas 入口 prompt。
2. 对 JBT 任务，`/Users/jayshao/J_BotQuant/Atlas_prompt.md` 已降级为历史档案，不再作为开工来源。
3. 只有当某个已建档迁移任务明确要求时，才可把 `J_BotQuant` 当作只读历史代码或运行事实参考。

## 开工顺序

1. 读取 `WORKFLOW.md`
2. 读取 `docs/plans/ATLAS_MASTER_PLAN.md`
3. 读取 `PROJECT_CONTEXT.md`
4. 读取 `docs/prompts/总项目经理调度提示词.md`
5. 读取 `docs/prompts/公共项目提示词.md`
6. 读取 `docs/prompts/agents/总项目经理提示词.md`

## 当前状态

- `TASK-0029`、`TASK-0030`、`TASK-0031`、`TASK-0032` 已完成并锁回；其中 `TASK-0034` 已补建为 `TASK-0031` 后续 data 单服务 U0 直修的事后审计锚点。
- 数据端下一条主线是“Mini system 级采集 / 调度 / 通知迁移到 JBT Docker 体系”，原因是当前真实 24h 运行链路仍大量依赖 legacy system；当前先做治理准备，不直接写代码。
- `TASK-0034` 当前只负责 U0 审计账本、prompt 同步与独立远端备份，不反写 `TASK-0031` 的 6 文件标准热修边界，也不继续扩展 data 代码范围。
- 统一聚合 dashboard 已完成规划冻结：正式归属 `services/dashboard/**`，但在 sim-trading / decision / data 三端临时看板未基本收口前，不进入正式实施。
- 模拟交易维持 `TASK-0017` 待开盘验证状态；当前尚未接通期货公式 / 策略公式执行链路，不主动扩新范围。
- `TASK-0041`、`TASK-0042`、`TASK-0043` 已连续收口并锁回；`TASK-0039` 当前仅剩 `ISSUE-DR3-001`（Docker restart policy）一个 P1 遗留问题。
- 已完成 DR3 只读边界研判并完成 A0 建档：该问题属于 Mini 宿主机部署治理，不适合按单服务热修处理；当前已改号为 `TASK-0045`，避免与既有 RooCode `TASK-0044` 冲突。
- 回测维持“阶段性结案 / 维护观察”。
- live-trading 当前明确后置，待 sim-trading 在 Mini 上连续稳定运行 2~3 个月后再评估是否启动。
- 决策若继续推进 legacy 迁移，必须先走专项 handoff 和治理判边。

## 最近动作

- 2026-04-11 01:30：已完成 `TASK-0043` lockback 与治理回写。Mini `data_scheduler` 已切换为 `LaunchAgent` 守护，`kill -9` 后可自动恢复，运行态收敛为单实例；当前灾备尾项仅剩 DR3 容器 restart policy。
- 2026-04-11：已完成 `ISSUE-DR3-001` 只读边界研判并完成 A0 建档。结论：DR3 不是单服务问题，至少涉及 `docker-compose.mac.override.yml`，并可能条件性触及 `docker-compose.dev.yml`；当前已改号为 `TASK-0045 Mini macOS 容器自愈守护基线`，以避开现有 RooCode `TASK-0044`。

## 接管要求

1. 若 `docs/JBT_FINAL_MASTER_PLAN.md` 与总项目经理双 prompt 有时间差，以双 prompt 的较新留痕为准。
2. 如需终端命令、git 提交、远端同步或运行态探测，先向 Jay.S 汇报命令并等待确认。
3. 所有推进优先落治理文件；Atlas 不直接修改服务业务代码。