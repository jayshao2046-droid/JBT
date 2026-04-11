# JBT Atlas Prompt

【签名】Atlas
【时间】2026-04-11
【设备】MacBook
【状态】JBT-only 管理已切换 / TASK-0046(RooCode) 全闭环 / TASK-0047(agent-model升级) 全闭环 / TASK-0048(Phase C扩展总计划) 全闭环 / TASK-0049(安全治理横线) A0/A1完成+A2 Atlas侧同步完成

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
- 已完成 DR3 只读边界研判并完成 A0 建档：该问题属于 Mini 宿主机部署治理，不适合按单服务热修处理；当前已独立建档为 `TASK-0045 Mini macOS 容器自愈守护基线`。
- RooCode 接入 JBT 业务流程已独立建档为 `TASK-0046`，A1+A2 均已终审通过并锁回。A1 白名单 5 项：`.roomodes`、`.roo/mcp.json`、`.roo/rules/01-jbt-governance.md`、`governance/roo_jbt_mcp_server.py`、`ATLAS_PROMPT.md`；A2 白名单 1 项：`.gitignore`（移除 `.roo/` 排除规则）。`.roo/` 已纳入版本控制。TASK-0046 全任务闭环。
- `TASK-0047` 仓库级 agent model 统一升级已完成：7 个 `.github/agents/*.agent.md` 的 `model` 已从 `claude-sonnet-4-6-high` 统一升级为 `claude-opus-4-6-high`。A1（5 文件）Token tok-740d9433 + A2（2 文件）Token tok-d41da82b 均已终审通过并锁回。TASK-0047 全任务闭环。
- `TASK-0039` 锁控记录中 `ISSUE-DR3-001` 的过期引用（TASK-0044→TASK-0045）已修正。
- 回测维持“阶段性结案 / 维护观察”。
- `TASK-0048` 已完成 A0 建档、A1 总计划修订与 A2 prompt 同步。Phase C 现已冻结为：decision 双沙箱（期货/股票）自动研究主路径、backtest 人工二次回测关卡、股票荐股循环、飞书口头策略、邮件/看板 YAML 导入、decision 本地 Sim 容灾、共享因子双地同步。后续必须按服务拆批，不得把总计划修订误当成已获准代码实施。
- `TASK-0049` 已完成 A0 建档与 A1 最小 Token 签发 / validate。当前总计划已正式纳入 `SG1`~`SG5` 安全治理横线，顺序固定为“策略端只读安全检查 → 策略端复核 → 全域只读安全检查 → 全域安全复核 → 统一修复预审与实施”；当前阶段不做即时修复。
- 当前第一优先级已切换为策略端只读安全检查与复核冻结。策略端边界固定为 `decision + backtest`，首批主落点先以 `backtest` 已确认的 `F-001` 为主，`decision` 作为补充复核范围；data 侧 `F-002/F-003` 留待 SG3 再统一进入只读可达性复核。
- live-trading 当前明确后置，待 sim-trading 在 Mini 上连续稳定运行 2~3 个月后再评估是否启动。
- 决策若继续推进 legacy 迁移，必须先走专项 handoff 和治理判边。

## 最近动作

- 2026-04-11 01:30：已完成 `TASK-0043` lockback 与治理回写。Mini `data_scheduler` 已切换为 `LaunchAgent` 守护，`kill -9` 后可自动恢复，运行态收敛为单实例；当前灾备尾项仅剩 DR3 容器 restart policy。
- 2026-04-11：已完成 `ISSUE-DR3-001` 只读边界研判并完成 A0 建档。结论：DR3 不是单服务问题，至少涉及 `docker-compose.mac.override.yml`，并可能条件性触及 `docker-compose.dev.yml`；已独立建档为 `TASK-0045 Mini macOS 容器自愈守护基线`。
- 2026-04-11：RooCode 接入 JBT 业务流程已独立建档为 `TASK-0046`；A0 治理账本完成，A1 Token `tok-731e8346-50cc-4822-831d-8479fcdfe152` 已签发 validate 通过；Atlas 复核 + 项目架构师终审均通过（review-id `REVIEW-TASK-0046-A1`）；实施内容：`.roomodes`（3 模式：code/ask/debug）、`.roo/mcp.json`（jbt-governance MCP server）、`.roo/rules/01-jbt-governance.md`（治理规则）、`governance/roo_jbt_mcp_server.py`（MCP 桥接）。
- 2026-04-11：`TASK-0046` A2 已闭环：移除 `.gitignore` 中 `.roo/` 排除规则，`.roo/mcp.json` 和 `.roo/rules/**` 已纳入版本控制；Token `tok-1f28c19b-b4dd-461a-8f50-c01de9ecac64`，review-id `REVIEW-TASK-0046-A2`，终审通过并锁回。commit f3ee429。TASK-0046 全任务闭环。
- 2026-04-11：`TASK-0039` 锁控记录过期引用修正（3 处 TASK-0044→TASK-0045），含在 commit f3ee429。
- 2026-04-11：`TASK-0047` A1 签发 tok-740d9433（5 文件），实施认定 + 终审 REVIEW-TASK-0047-A1 通过，lockback 完成，commit 8ea1f4a。
- 2026-04-11：`TASK-0047` A2 签发 tok-d41da82b（2 文件），实施认定 + 终审 REVIEW-TASK-0047-A2 通过，lockback 完成，commit 039e720。TASK-0047 全任务闭环。
- 2026-04-11：已完成 `TASK-0048` A0 建档、A1 总计划修订与 A2 prompt 同步。`docs/JBT_FINAL_MASTER_PLAN.md` 已正式纳入 Phase C 双沙箱、人工二次回测、股票荐股循环、口头策略、邮件 YAML、Sim 容灾与共享因子双地同步口径；下一步需按服务拆成决策 / 数据 / 回测 / 模拟交易独立任务，并为共享因子库单独建 P0 任务。
- 2026-04-11：已完成 `TASK-0049` A0 建档与 A1 最小 Token `tok-da51ff91-10d9-47f1-95ef-1d369f39fb1f` 签发 / validate，并完成 `docs/JBT_FINAL_MASTER_PLAN.md` 与本文件同步。当前正式口径为：先完成 `SG1` 策略端只读安全检查，再完成 `SG2` 策略端复核，随后进入 `SG3/SG4` 全域安全检查与复核，最后才允许 `SG5` 统一修复预审与实施。
- 2026-04-11：已完成 `TASK-0049` 的 Atlas 侧 A2 prompt 同步。`docs/prompts/总项目经理调度提示词.md` 与 `docs/prompts/agents/总项目经理提示词.md` 已对齐 SG 口径；`docs/prompts/公共项目提示词.md` 与 `docs/prompts/agents/项目架构师提示词.md` 继续待项目架构师补齐。
- 决策开发前置清理完成：TASK-0046 / TASK-0047 / TASK-0039引用修复 全部闭环，工作区干净，可进入决策端迁移。
- Phase C Qwen 协作流水线已建立（docs/handoffs/qwen-audit-collab/）：Batch-1/2/3 完成并通过审核；Batch-4（CA2'/CB2'/CG3/CA6）Qwen 重做后 Atlas 补漏 8 处（§2 anchor 修正），最终评定 91/100，2026-04-11 全批通过。Batch-5（CA3/CA4/CB3/CF2）已预建派发单，激活条件：TASK-0056(CA2') + TASK-0057(CB2') + TASK-0051(C0-3) 完成。TASK-0056~0059 预建任务单已建档。
- 2026-04-11：TASK-0056~0059 联合架构预审完成（review-id: REVIEW-TASK-0056-0059-PRE）。所有 4 项均预审通过。关键裁定：CA2' 用 FactorLoader 取数 / SandboxResult 不入 contracts / CG3 补入 stock_runner.py / CA6 需额外 contracts Token（signal_dispatch.py）/ 信号幂等用内存缓存 / 重试用 tenacity。白名单冻结完毕，待 Jay.S 确认后签发 Token。
- 2026-04-11：TASK-0056~0059 全部 Token 签发完毕（6 枚）：tok-b73294b3(0056/决策/4文件)、tok-00da5e7e(0057/决策/2文件)、tok-b09df21e(0058/回测/4文件)、tok-3185c6c9(0059-D/决策/3文件)、tok-c5b83bfe(0059-S/模拟交易/2文件)、tok-9e1369d9(0059-C/决策/1文件·P0)。锁控记录已写入 docs/locks/。4 个任务单状态已更新为"Token 已签发"。

- 2026-04-12：TASK-0050~0055 联合架构预审完成（review-id: REVIEW-TASK-0050-0055-PRE）。所有 6 项均预审通过。关键裁定：TASK-0050 白名单调整为 2 项（不新建 api/ 目录，直接改 main.py）/ TASK-0051 StrategyModel 在 publish/ / TASK-0052 内存队列 / TASK-0053 股票代码需 .SZ/.SH 后缀 / TASK-0054 方案A watchlist 同批 / TASK-0055 修改 app.py 非 main.py。Lane-A（0050/0051/0052）无依赖可并行；Lane-B（0053/0054/0055）待 Lane-A 完成后签发。
- 2026-04-12：TASK-0050 Token tok-b7358d64 已签发（数据 Agent，2 文件）。TASK-0051/0052 待 Jay.S 终端密码签发。Batch-5 已激活派发。

## 接管要求

1. 若 `docs/JBT_FINAL_MASTER_PLAN.md` 与总项目经理双 prompt 有时间差，以双 prompt 的较新留痕为准。
2. 如需终端命令、git 提交、远端同步或运行态探测，先向 Jay.S 汇报命令并等待确认。
3. 所有推进优先落治理文件；Atlas 不直接修改服务业务代码。