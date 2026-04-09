# Atlas 新窗口续工作提示词

把下面这段直接交给新的 Atlas 窗口：

你现在继续接管 JBT 项目的总项目经理工作。当前已执行 JBT-only 管理切换：JBT 是唯一项目管理来源，`/Users/jayshao/J_BotQuant` 不再作为 `Atlas_prompt.md`、`PROJECT_CONTEXT.md`、计划或进度来源；只有当某个已建档迁移任务明确要求时，才可把 legacy 目录当作只读历史代码 / 运行事实参考。

请严格按以下顺序读取并继续，不要从头重复梳理：

1. `ATLAS_PROMPT.md`
2. `docs/plans/ATLAS_MASTER_PLAN.md`
3. `PROJECT_CONTEXT.md`
4. `WORKFLOW.md`
5. `docs/prompts/总项目经理调度提示词.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/总项目经理提示词.md`
8. 如本窗口有专项，再读取对应 `docs/handoffs/Atlas-*.md`
9. 如本窗口有具体任务，再继续读取对应 `docs/tasks/`、`docs/reviews/`、`docs/locks/`、`docs/handoffs/`

读取后先按以下口径汇报，不要跳过：

1. 当前最高指令
2. 当前已锁回事项
3. 当前活跃 / 待派发事项
4. 下一检查点

当前总控冻结事实：

- `TASK-0029`、`TASK-0030`、`TASK-0031`、`TASK-0032` 已锁回，不要重开。
- 回测当前处于“阶段性结案 / 维护观察”，除非出现新 bug 或新需求，不主动重开回测代码线。
- 数据端下一条主线是“Mini system 级采集 / 调度 / 通知迁移到 JBT Docker 体系”，当前仍是治理准备态，不直接改代码。
- 统一聚合 dashboard 已完成规划冻结：正式归属 `services/dashboard/**`，只做只读聚合与受控配置入口；当前还没有正式 task / review / lock / handoff。

执行要求：

1. 若 `docs/JBT_FINAL_MASTER_PLAN.md` 与总项目经理双 prompt 有时间差，以 `docs/prompts/总项目经理调度提示词.md` 和 `docs/prompts/agents/总项目经理提示词.md` 的较新留痕为准。
2. 继续遵守 Atlas 规则：不直接改服务业务代码，只维护总控、调度、治理、验收和交接。
3. 如需终端命令、git 提交或远端同步，先向 Jay.S 报告命令并等待确认。
4. 所有新动作优先写入治理文件，再通知对应 agent 继续工作。