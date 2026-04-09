# JBT 新 Copilot 账号无缝接管交接单

【签名】Atlas
【时间】2026-04-09
【设备】MacBook
【用途】给新的 Copilot 账号使用；登录后把下面“用户输入”整段发到新窗口，即可无缝接管 JBT 全项目继续开发。

---

## 用户输入（复制粘贴到新窗口即可）

```
JBT 继续工作。

你现在接管的是已经切断 J_BotQuant 管理来源后的 JBT 主工作区。先严格按以下顺序读取：

1. `ATLAS_PROMPT.md`
2. `docs/plans/ATLAS_MASTER_PLAN.md`
3. `PROJECT_CONTEXT.md`
4. `WORKFLOW.md`
5. `docs/prompts/总项目经理调度提示词.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/总项目经理提示词.md`
8. `docs/handoffs/Atlas-全员协同执行提示词.md`

必须执行的总控口径：

- JBT 是唯一任务、prompt、进度、计划来源。
- `/Users/jayshao/J_BotQuant` 不再作为 `Atlas_prompt.md`、`PROJECT_CONTEXT.md`、计划或进度来源。
- 只有当某个已建档迁移任务明确要求时，才可只读读取 `J_BotQuant` 旧代码或旧运行事实；仍然禁止在 legacy 目录写入。
- 若 `docs/JBT_FINAL_MASTER_PLAN.md` 与总项目经理双 prompt 有时间差，以 `docs/prompts/总项目经理调度提示词.md` 和 `docs/prompts/agents/总项目经理提示词.md` 的较新留痕为准。
- 不要重开 `TASK-0029`、`TASK-0030`、`TASK-0031`、`TASK-0032`，这四条都已锁回。

接管后先输出：

1. 当前最高指令
2. 当前活跃主线
3. 当前阻塞
4. 下一检查点

当前活跃主线至少包含：

- 数据端：Mini system 级采集 / 调度 / 通知迁移到 JBT Docker 体系，仍处治理准备态，先做 inventory / shadow run / 切换方案，不直接改代码。
- 看板端：统一聚合 dashboard 方案已冻结为 `services/dashboard/**`，只做只读聚合与受控配置入口；参考 `0329` 原型的导航和视觉骨架，但还没正式建 task / review / lock / handoff。
- 模拟交易：`TASK-0017` 保持待开盘验证，不扩新范围。
- 回测：阶段性结案 / 维护观察，除非出现新 bug 或新需求，不主动重开。
- 决策：主线已完成主要闭环；若继续做 legacy 决策迁移，先读 `docs/handoffs/Atlas-决策端迁移续工作提示词.md` 并先走治理判边。

执行纪律继续生效：

1. 所有已具备执行条件的改造任务进入 3 天 / 4320 分钟执行窗口。
2. JBT 不允许目录级或整仓级“全局 Token”；只能按任务 / 批次 / 文件白名单分别签发 4320 分钟 Token。
3. 每完成一项都必须先完成最小验证并保留证据，再回写 review / handoff 摘要并执行 lockback；未留证据、未锁回，不得进入下一项。
```

---

## 当前冻结事实（供新账号内部参考）

### 1. 管理源切换

1. 当前已正式执行 JBT-only 管理切换。
2. JBT 的唯一 Atlas 管理链固定为：`ATLAS_PROMPT.md` → `docs/plans/ATLAS_MASTER_PLAN.md` → `PROJECT_CONTEXT.md` → `WORKFLOW.md` → `docs/prompts/总项目经理调度提示词.md` → `docs/prompts/公共项目提示词.md` → `docs/prompts/agents/总项目经理提示词.md`。
3. `J_BotQuant` 只在两种场景下保留价值：
	- 某个迁移任务明确要求只读读取旧代码
	- 需要核实现网 legacy 运行事实
4. `J_BotQuant` 不再承担 prompt、计划、进度、开工上下文来源。

### 2. 当前项目状态快照

| 主线 | 当前状态 | 说明 |
|------|---------|------|
| 治理 | 稳定 | `TASK-0029` 与 `TASK-0030` 均已 locked |
| 数据热修 | 已收口 | `TASK-0031` 已 locked |
| data_web 原型 | 已收口 | `TASK-0032` 已 locked，当前仍是临时原型 |
| 回测 | 维护观察 | 本轮问题已收口，不主动扩写 |
| 模拟交易 | 待开盘验证 | `TASK-0017` 保持待验证状态 |
| 决策 | 主线闭环后待下一治理 | 若做旧决策迁移，需重新判边 |
| 聚合 dashboard | 规划已冻结 | 尚未建正式任务 |

### 3. 统一聚合 dashboard 已冻结的规划口径

1. 正式归属固定为 `services/dashboard/**`，不再把四个服务里的临时看板混作正式聚合端。
2. 定位固定为“只读聚合 + 受控配置入口”，不直接承担交易写操作。
3. 当前冻结的信息架构：登录页、总览首页、总配置页、backtest、decision、sim-trading、data、监控。
4. 总配置页必须覆盖：子账户与权限管理、交易时段 / 日期开关、飞书通知启停、邮箱通知启停。
5. 视觉与交互基线沿用 `0329` 原型的导航与设计语言，但不继承 mock 数据模型、SessionStorage 或缺失权限体系。
6. 下一步不是直接写代码，而是先由项目架构师新建正式治理任务并冻结白名单。

### 4. 专项续窗入口

1. 若继续推进数据端 system 级迁移，读取 `docs/handoffs/Atlas-数据端迁移续工作提示词.md`。
2. 若继续推进 legacy 决策端迁移，读取 `docs/handoffs/Atlas-决策端迁移续工作提示词.md`。
3. 若只做总控续接，按本文件的“用户输入”直接开工即可。

### 5. 执行纪律

1. 一个窗口同时只有一个 Agent 在写代码，其他 Agent 可做只读分析。
2. 跨服务变更必须经项目架构师预审。
3. 看板端正式实现后置，在治理建档完成前不进入 `services/dashboard/**` 写入。
4. 任何实际变更与终局计划有差异，必须按 `[PLAN-DELTA]` 规则留痕。

---

【签名】Atlas
【时间】2026-04-09
【设备】MacBook
