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
- 2026-04-12：Lane-A 三枚 Token 全部签发完毕：tok-b7358d64(TASK-0050/数据/2文件)、tok-2e393387(TASK-0051/决策/5文件)、tok-5d4f2cca(TASK-0052/回测/4文件)。Batch-5 已激活派发。Lane-B（0053/0054/0055）待 Lane-A 实施完成后签发。
- 2026-04-12：TASK-0064 建档并签发 Token tok-5b40deb2（Claude-Code / data 服务 / 6文件 / 4320min）。白名单：collectors/base.py、scheduler/data_scheduler.py、health/health_check.py、notify/dispatcher.py、main.py、tests/test_collectors.py。Claude-Code Round 1 可开始实施。
- 2026-04-12：TASK-0065 建档并签发 Token（Claude-Code / backtest 服务 / 3文件 / 4320min）。白名单：generic_strategy.py、api/app.py、tests/test_api_surface.py。Claude-Code Round 2 可开始实施。
- 2026-04-12：TASK-0066 建档并签发 Token tok-b7688e4e（Claude-Code / decision 服务 / 8文件 / 4320min）。白名单：api/app.py、main.py、signal_dispatcher.py、sandbox_engine.py、stock_screener.py、research_gate.py、settings.py、tests/test_api_auth.py。Claude-Code Round 3 可开始实施。
- 2026-04-12：【Atlas Round 2 复审 — TASK-0065 backtest 服务】Round 2 完成，2 commits，3 文件改动，项目架构师终审结论：有条件通过。(1)Commit 6477af2 F-001 eval 加固主体正确（长度/节点数/Pow+`__builtins__`清空+白名单），但存在一个中级安全漏洞：`visit_BinOp` 只检查常量右操作数，动态指数（如 `2**(50+51)`）可绕过 Pow 限制；必须修复后方可合并。(2)Commit 6e4539d API 认证中间件使用 hmac.compare_digest、全局依赖注入、公开路径豁免，终审通过。**当前状态：Claude Code 需补一个 Pow 动态指数修复 commit（仍在 TASK-0065 Token 白名单 generic_strategy.py 范围内），修复完成后再推送 Round 2。**
- 2026-04-12：【Atlas 总计划更新】JBT_FINAL_MASTER_PLAN.md 已同步 Round 1~3 进展：data 93%→**100%**（健康检查+通知+API认证已修复）、backtest 88%→95%（F-001 eval加固+API认证，Pow待补修）、SG1~SG4 全标为完成、SG5 标为进行中、总进度仪表盘 ~62%→~72%、sim-trading 68%→85%。Round 3 decision (TASK-0066) Token 已签发，Claude Code 开始实施。
- 2026-04-12：【Round 2 补丁终审】Commit 97f4888 — Pow 非常量指数修复，项目架构师终审：有条件通过（P3 补测试建议，不阻塞合入）。`visit_BinOp` 现在要求 Pow 右操作数必须是 `ast.Constant` 且 `int/float`，否则拒绝。上一轮架构师审出的动态指数绕过已完全封堵。
- 2026-04-12：【Round 3 终审 — TASK-0066 decision 服务】Commit 32e4d99 — decision API 认证中间件，项目架构师终审：**通过**。`DECISION_API_KEY` 全局依赖注入，`/health`+`/ready` 免认证，`hmac.compare_digest` 防时序攻击，5 项测试全通过。与 data/backtest 认证模式完全一致。decision 仅完成 SG API 认证加固（75%→80%），功能收口待后续 Phase C 继续。
- 2026-04-12：**当前本地 HEAD** `97f4888`（Round 2 补丁），origin/main 仍在 `6e27866`（Round 1 尾端）。共 5 个待推送 commit：Round 1 已审通过、Round 2 有条件通过（P3 不阻塞）、Round 3 通过。待 Jay.S 确认后一次性 push。Round 1 完成，7 commits，6 文件全部改动，77 个测试全通过。改动内容：(1)main.py 添加 DATA_API_KEY 全局认证中间件（hmac.compare_digest，/health 免认证）；(2)base.py 清除 A2 STUB 转延迟注入设计；(3)data_scheduler.py 因子通知器和 SLA 追踪器 STUB 替换为实际实现；(4)health_check.py 修复 FeishuNotifier 死代码引用；(5)dispatcher.py 新增 FACTOR/WATCHLIST 通知类型；(6)test_collectors.py 扩充 11 个测试用例。SG 备注：F-002/F-003 涉及的 storage.py/health_remediate.py 不在白名单，Claude-Code 正确停止并留待 SG5。append_atlas_log 因 ATLAS_PROMPT.md 不在白名单被拒绝（符合规则）。Atlas 复审通过，data 服务 93%→100% 收口确认。，Jay.S 已二次确认执行协议与冲刺计划。CLAUDE.md + .mcp.json 已入库（commit 416a225）。冲刺目标：data/backtest/sim-trading/decision 四端全部推至 100%，SG2~SG5 安全治理同步完成。执行分 Round 0~5：Round0=SG2~SG4 全域只读安全扫描（无需Token）→ Round1=data 100%+F-002/F-003修复 → Round2=backtest 100%+F-001修复 → Round3=decision 100% → Round4=sim-trading 100%（开盘验证明日） → Round5=SG5统一复核+全域收口报告。协议：改动→私有prompt留痕→独立commit→积累若干commit→append_atlas_log→Atlas一次性审查→Jay.S确认→push→两地同步。每端一个Token白名单，文件级，按服务打包，不跨端。SG修复commit独立于功能commit。当前 Claude Code 正在执行 Round 0（只读扫描，无Token）。
- 2026-04-12：TASK-0067 建档并签发 Token tok-e831aa5d（Claude-Code / sim-trading 服务 / 2文件 / 4320min）。白名单：main.py、tests/test_api_auth.py。Claude-Code Round 4 可开始实施。
- 2026-04-12：TASK-0067 追加 Token 签发（Claude-Code / sim-trading / router.py）。原因：main.py 新认证中间件与 router.py 旧认证代码冲突，需清理 router.py 旧 auth 逻辑。
- 2026-04-12：【Round 4 完成 — TASK-0067 sim-trading 服务】共 3 commits：(1) commit a69df54 添加 SIM_API_KEY 全局 API 认证中间件（hmac.compare_digest，/health+/api/v1/health+/api/v1/version 免认证，5 个测试用例）；(2) commit 0c9accb 清理 router.py 旧认证代码（移除 X-Api-Key 旧中间件，保留纯路由逻辑）；(3) commit 64c491e 修复 router.py 缺失 import os。四端 API 认证模式完全统一：SIM_API_KEY / DATA_API_KEY / BACKTEST_API_KEY / DECISION_API_KEY。
- 2026-04-12：【Round 4 架构师终审 — TASK-0067 sim-trading SG API 认证】项目架构师终审结论：**通过 ✅**。5 项检查全部通过：(1)认证模式统一 hmac.compare_digest；(2)公开路径正确豁免；(3)空 Key 兼容开发环境；(4)旧 auth 完全清理；(5)import os 恢复。改进建议（不阻塞）：CI smoke test 检查 import。
- 2026-04-12：sim-trading 独立全量二次核验完成（commit a30459c，423 行报告）。结论：有条件通过。发现 2 个 bug（1 P0 已修复、1 P2 测试适配）+ 1 个安全漏洞（已修复）。报告见 `docs/reviews/sim-trading-二次核验報告-2026-04-12.md`。
- 2026-04-12：Git 状态：HEAD 64c491e，origin/main 64c491e（已同步），Mini 64c491e（已同步），Studio SSH 连接被拒（待 Jay.S 手动处理）。
- 2026-04-12：**sim-trading 进度 85% → 90%**。SG API 认证完成 + 二次核验通过。剩余：开盘验证 CTP、CS1-S 容灾交接接口、Phase C 执行协同。总进度 ~75% → ~80%。
- 2026-04-12：**全服务看板上线 ✅**。所有 JBT 容器全部启动并配置 restart=unless-stopped：Mini（JBT-SIM-TRADING-8101/WEB-3002、JBT-DATA-8105/WEB-3004）；Studio（JBT-BACKTEST-8103/WEB-3001、JBT-DECISION-8104/WEB-3003）。Docker 基础设施修复：两台机器 PATH+credsStore+镜像源全部修复，Studio Docker VM 崩溃已重启恢复。jbt-data(8105) API 返回 200 正常但容器 healthcheck 标记为 unhealthy（假阳性，待修）。

## 接管要求

1. 若 `docs/JBT_FINAL_MASTER_PLAN.md` 与总项目经理双 prompt 有时间差，以双 prompt 的较新留痕为准。
2. 如需终端命令、git 提交、远端同步或运行态探测，先向 Jay.S 汇报命令并等待确认。
3. 所有推进优先落治理文件；Atlas 不直接修改服务业务代码。