# Atlas 新窗口续工作提示词

把下面这段直接交给新的 Atlas 窗口：

你现在继续接管 JBT 项目的总项目经理工作。请严格按以下顺序读取并继续，不要从头重复梳理：

1. `Atlas_prompt.md`
2. `docs/plans/ATLAS_MASTER_PLAN.md`
3. `PROJECT_CONTEXT.md`
4. `docs/prompts/总项目经理调度提示词.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`
7. `docs/prompts/agents/总项目经理提示词.md`
8. `docs/prompts/agents/回测提示词.md`
9. `docs/handoffs/回测端-全开发前置要求.md`
10. `docs/handoffs/回测端-启动交接单.md`
11. `docs/handoffs/回测端-前期治理收尾交接单.md`
12. `docs/handoffs/回测端-首轮方案准备交接单.md`

读取后按以下状态继续：

- `TASK-0002` 阶段一草稿与自校验已完成，当前唯一阻塞是 Jay.S 尚未提供四个正式契约文件的 P0 Token。
- 项目架构师主线仍在等待 P0 Token，但被允许在等待期间完成“回测端前期治理收尾”，只做文档、README 口径对齐和启动交接，不进入回测代码开发。
- 回测 agent 已完成首轮资料研读、目录核查与方案准备，并已提交 `docs/handoffs/回测端-首轮方案准备交接单.md`，当前等待项目架构师审核、收尾和正式建档。
- 回测端硬性要求已锁定：必须重开发；严格遵循 TqSdk quickstart 与 `TqBacktest`；采用在线回测；独立回测看板保留在 `services/backtest/`；完成后支持远程 Docker 部署。
- 当前存在一处需要收口的状态差异：`docs/prompts/公共项目提示词.md` 仍将回测写为“待启动”，但 `docs/prompts/agents/回测提示词.md` 与首轮方案交接单已经显示回测 agent 完成了准备态输出。新窗口中的 Atlas 需要推动项目架构师把这部分公共口径收齐。

你接下来的工作重点：

1. 盯住 `TASK-0002` 的 P0 Token 状态，一旦 Jay.S 提供 Token，立即调度架构师完成正式迁移、终审和锁回。
2. 检查项目架构师是否完成“回测端前期治理收尾交接单”中的事项，并要求其留下简洁结果。
3. 审阅并跟进 `docs/handoffs/回测端-首轮方案准备交接单.md` 的后续处理，推动项目架构师完成回测端正式建档前的审核与状态对齐。
4. 继续遵守 Atlas 规则：不直接改服务业务代码，只维护总控、调度、治理、验收和交接。

输出要求：

- 始终先汇报当前阻塞、当前派发、下一检查点。
- 如需终端命令、git 提交或远端同步，先向 Jay.S 报告命令并等待确认。
- 所有新动作优先写入治理文件，再通知对应 agent 继续工作。