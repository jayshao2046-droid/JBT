# TASK-0046 RooCode 接入 JBT 业务流程与 Token 锁控预审

## 文档信息

- 任务 ID：TASK-0046
- 文档类型：治理建档与补充预审
- 签名：项目架构师
- 建档时间：2026-04-11
- 设备：MacBook

---

## 一、编号修正说明

1. `TASK-0044` 不再使用（历史误占）。
2. `TASK-0045` 已被 DR3 事项"Mini macOS 容器自愈守护基线"正式占用，拥有完整 review/lock/handoff。
3. 自本文件起，RooCode 接入事项的全部 `task/review/lock/handoff` 留痕统一为 `TASK-0046`，不再复用 `TASK-0044` 或 `TASK-0045`。

---

## 二、任务目标

1. Jay.S 与 Atlas 继续保持单线沟通；除非 Jay.S 明确要求 Atlas / Copilot 直接介入，否则默认所有代码开发、修复、查漏、漏洞排查与增量功能实施均交由 RooCode 承接。
2. RooCode 在 JBT 仓库内必须复用现有 JBT 标准流程与同一套 `task/review/lock/handoff/prompt` 留痕口径，不得形成第二套协作流程。
3. 不新增 Roo 专用业务 prompt；业务语义只认现有 `ATLAS_PROMPT.md` 与 `docs/prompts/**`。
4. Roo 接入层只允许落在最小治理接入面：`ATLAS_PROMPT.md`、`.roomodes`、`.roo/mcp.json`、`.roo/rules/**` 与 `governance/roo_jbt_mcp_server.py`；当前轮次只做 P-LOG 建档与白名单冻结，不实施任何仓内接入写入。
5. Roo 若需遵守 Token 锁控，必须复用现有 `governance/jbt_lockctl.py` 流程；本任务不得改写该既有治理文件。
6. 每批次终审通过后，必须由 Atlas 按既有职责完成 lockback、独立 git commit 与两地同步收口。

---

## 三、Roo 正式协作口径（冻结）

1. Roo 正式协作只冻结为两条流程：实施类与只读巡检类；两条流程共用同一套 `task/review/lock/handoff/prompt` 与 Token 口径，不构成第二套制度。
2. 实施类流程固定为：`Jay.S 提需求 -> Atlas 确认边界 -> 项目架构师预审并冻结白名单 -> Jay.S 签发 Token -> Roo 按白名单实施 -> Roo 每批次结束后回写 ATLAS_PROMPT.md 并署名 Roo -> Atlas 复核 -> 项目架构师终审 -> Atlas lockback + 独立 git commit + 两地同步`。
3. 只读巡检类流程固定为：`Jay.S / Atlas 派发只读巡检 -> Roo 只读查漏 / 查 bug / 查漏洞 -> Roo 每批次结束后回写 ATLAS_PROMPT.md 并署名 Roo -> 若无需改动则以巡检结论收口；若确认需要正式改代码，则必须回到"预审 -> 白名单 -> Token -> 实施"标准流程后再允许落写`。
4. 只读巡检本体不构成任何业务文件写授权；A1 白名单内的 `ATLAS_PROMPT.md` 批次回写只用于 Roo 留痕，不得扩写为 Roo 专用业务 prompt。

---

## 四、只读确认结果

1. 仓内当前已存在 `.roo/mcp.json`，内容仅包含 `sequentialthinking` MCP 配置，尚未接入 JBT 工作流与锁控口径。
2. 仓内当前不存在 `.roomodes`。
3. 仓内当前不存在 `.roo/rules/` 目录与任何 Roo 规则文件。
4. `governance/` 目录当前仅有 `governance/README.md` 与 `governance/jbt_lockctl.py`。
5. `ATLAS_PROMPT.md` 已作为 JBT 本地 Atlas 入口 prompt；`docs/prompts/**` 已是现行业务 prompt 体系。
6. 当前未发现任何 Roo 专用业务 prompt 文件；本任务不新增、不复制、不分叉业务 prompt。

---

## 五、任务归属与边界结论

1. `TASK-0046` 归属为仓库级治理接入任务，不归属任何 `services/**` 单服务业务目录。
2. 业务 prompt 只认 `ATLAS_PROMPT.md` 与现有 `docs/prompts/**`；Roo 侧只允许复用该现有体系，其中 `ATLAS_PROMPT.md` 作为 A1 白名单内的批次回写入口，`docs/prompts/**` 继续只读引用，不得复制或派生第二套业务 prompt 来源。
3. Roo 接入实施当前只允许触及以下最小非 P-LOG 白名单：`ATLAS_PROMPT.md`、`.roomodes`、`.roo/mcp.json`、`.roo/rules/**`、`governance/roo_jbt_mcp_server.py`。
4. `governance/jbt_lockctl.py` 当前仅作为既有锁控入口复用，不在本轮白名单内，不得改写。
5. Roo 接入不得写入 `services/**`、`shared/contracts/**`、`.github/**`、`WORKFLOW.md`、`docker-compose.dev.yml`、任一 `.env.example`、`runtime/**`、`logs/**`、任一真实 `.env`。
6. 若后续实施证明必须新增第 6 个非 P-LOG 白名单项、触及 `.roo/**` 下白名单外文件、把 `ATLAS_PROMPT.md` 的写入扩大到批次回写之外、或改写 `docs/prompts/**` / `governance/jbt_lockctl.py`，当前预审立即失效，必须补充预审。

---

## 六、冻结实施批次

### A0：治理建档（本批）

- 状态：`completed`
- 范围：仅 `docs/tasks/**`、`docs/reviews/**`、`docs/locks/**`、`docs/handoffs/**`
- 说明：当前批次只负责完成独立编号留痕，不进入 Roo 接入实施。

### A1：Roo 仓库级接入配置（已完成）

- 状态：`completed`
- 保护口径：仓库级治理配置，按 P0 同等审慎执行
- 冻结白名单：
  1. `ATLAS_PROMPT.md`
  2. `.roomodes`
  3. `.roo/mcp.json`
  4. `.roo/rules/**`
  5. `governance/roo_jbt_mcp_server.py`

执行硬约束：

1. `ATLAS_PROMPT.md` 仅允许 Roo 在每批次结束后回写本批完成动作、只读巡检结论或实施结果、验证摘要、待审问题与下一步建议，且署名必须为 `Roo`；不得改写 Atlas 既有调度主体，不得复制 `docs/prompts/**` 正文。
2. `.roomodes` 只允许写入 Roo 模式入口与 JBT 流程约束，不得复制业务 prompt 正文。
3. `.roo/mcp.json` 只允许补足 Roo 对现有治理工具与 `roo_jbt_mcp_server.py` 的调用配置，不得扩展到服务运行态、真实密钥或跨仓路径。
4. `.roo/rules/**` 只允许承载 Roo 的 JBT 治理规则文件，不得复制业务 prompt 正文，也不得扩展到 `.roo/**` 其他白名单外配置。
5. `governance/roo_jbt_mcp_server.py` 只允许作为 Roo 到既有治理工具的桥接入口；允许封装对现有 `governance/jbt_lockctl.py` 的调用，但不得改写、替换或分叉 `governance/jbt_lockctl.py`。
6. 只读巡检类若确认需要正式改代码，必须先回到"预审 -> 白名单 -> Token -> 实施"标准流程；不得借 `ATLAS_PROMPT.md` 回写或 `.roo/**` 接入口径直接落写业务文件。
7. 每批次终审通过后，必须由 Atlas 按既有职责执行 lockback、独立 git commit 与两地同步；未完成前不得视为闭环。
8. 若 A1 实施中发现需要第 6 个非 P-LOG 白名单项，或需要触及 `.roo/**` 下白名单外文件，必须先回交补充预审。

### A2：.roo 目录版本控制持久化（已完成）

- 状态：`completed`
- 保护口径：仓库级配置
- 冻结白名单：
  1. `.gitignore`

执行硬约束：

1. 仅允许移除 `.gitignore` 中的 `.roo/` 排除规则，使 `.roo/mcp.json` 和 `.roo/rules/**` 纳入版本控制。
2. 不得改动 `.gitignore` 中的其他规则。
3. 变更后必须验证 `git status` 能正确追踪 `.roo/mcp.json` 和 `.roo/rules/01-jbt-governance.md`。

---

## 七、当前轮次治理白名单（P-LOG）

1. `docs/tasks/TASK-0046-RooCode接入JBT业务流程与Token锁控预审.md`
2. `docs/reviews/TASK-0046-review.md`
3. `docs/locks/TASK-0046-lock.md`
4. `docs/handoffs/TASK-0046-架构预审交接单.md`

---

## 八、交付标准

1. `TASK-0046` 的 `task/review/lock/handoff` 四份账本已独立建档，且不再与 `TASK-0044` 或 `TASK-0045` 混写。
2. 后续 Roo 接入实施范围已冻结为 5 项白名单：`ATLAS_PROMPT.md`、`.roomodes`、`.roo/mcp.json`、`.roo/rules/**`、`governance/roo_jbt_mcp_server.py`。
3. 已明确冻结 Roo 正式协作口径仅有"实施类"与"只读巡检类"两条流程，且两条流程共用同一套 JBT 标准流程，不得引入第二套制度。
4. 已明确冻结"Roo 每批次结束后必须回写 `ATLAS_PROMPT.md`，署名 `Roo`"。
5. 已明确冻结"不新增 Roo 专用业务 prompt；业务 prompt 只认 `ATLAS_PROMPT.md` 与现有 `docs/prompts/**`"。
6. 已明确冻结"`governance/jbt_lockctl.py` 仅复用不改写"。
7. 已明确冻结"每批次终审通过后，由 Atlas 执行 lockback、独立 git commit 与两地同步"。
8. 当前轮次未触碰任何 `services/**`、`shared/contracts/**`、`.github/**`、`WORKFLOW.md`、`docker-compose.dev.yml`、任一 `.env.example`、`runtime/**`、`logs/**`、任一真实 `.env`。

---

## 九、预审结论

1. `TASK-0046` 正式成立。
2. A0 治理建档已完成；A1 Roo 接入配置批次已终审通过并锁回（token_id: tok-731e8346-50cc-4822-831d-8479fcdfe152，review-id: REVIEW-TASK-0046-A1，commit: 76d59d5）。
3. A2 `.roo/` 版本控制持久化已终审通过并锁回（token_id: tok-1f28c19b-b4dd-461a-8f50-c01de9ecac64，review-id: REVIEW-TASK-0046-A2）。
