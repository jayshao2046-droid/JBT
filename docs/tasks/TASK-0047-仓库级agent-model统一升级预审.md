# TASK-0047 仓库级 agent model 统一升级预审

## 文档信息

- 任务 ID：TASK-0047
- 文档类型：治理建档与补充预审
- 签名：项目架构师
- 建档时间：2026-04-11
- 设备：MacBook

---

## 一、任务目标

1. 用户要求把 JBT 仓内 7 个 `.github/agents/*.agent.md` 定义文件的 frontmatter 第 5 行 `model` 统一从 `claude-sonnet-4-6-high` 切换为 `claude-opus-4-6-high`。
2. 该事项归属仓库级治理变更，目标路径位于 `.github/**`，属于 P0 保护区，必须走标准预审、白名单冻结、Jay.S Token 签发、实施、终审与锁回流程。
3. 依据 `WORKFLOW.md` 第 6 条“单任务默认最多修改 5 个文件”，本次 7 文件目标必须拆分为两个执行批次，不得单批推进。
4. 当前轮次仅允许完成 A0 治理建档与白名单冻结，不对 `.github/agents/**` 实施任何受控写入。
5. 本任务的目标改动必须冻结为：仅替换各目标文件 frontmatter 第 5 行 `model` 值；`name`、`description`、`tools` 与正文一律不得顺手修改。

---

## 二、只读确认结果

1. 本次目标文件精确为：
   1. `.github/agents/architect.agent.md`
   2. `.github/agents/backtest.agent.md`
   3. `.github/agents/dashboard.agent.md`
   4. `.github/agents/data.agent.md`
   5. `.github/agents/decision.agent.md`
   6. `.github/agents/live-trading.agent.md`
   7. `.github/agents/sim-trading.agent.md`
2. 当前工作树只读复核结果为：JBT `.github/agents/**` 下 `claude-sonnet-4-6-high` 为 0 命中，`claude-opus-4-6-high` 为 7 命中；上述 7 个目标文件当前都已显示为 `model: "claude-opus-4-6-high"`。
3. 上述只读事实不等同于 `TASK-0047` 已实施完成；当前仓内已存在目标 7 文件的未纳管工作树差异，必须在正式签发与实施前由 Jay.S / Atlas 裁定其处置方式。
4. `.github/agents/architect.agent.md` 本身属于变更范围，说明本次 P0 改动会直接影响当前项目架构师 Agent 定义。
5. 除上述 7 个目标文件外，本轮未冻结任何 `.github/agents/**` 其他文件。

---

## 三、任务归属与边界结论

1. `TASK-0047` 归属为仓库级治理任务，不归属任何 `services/**` 单服务业务目录。
2. 当前实施边界严格限定在 7 个目标 agent 定义文件，不得顺手扩展到 `.github/agents/**` 其他文件、`.github/instructions/**`、`WORKFLOW.md`、`docs/prompts/**` 以外的任意目录。
3. 7 个目标文件的每个批次都只允许做同一件事：frontmatter 第 5 行 `model` 值替换；不得引入格式化、字段排序、注释、换行风格或正文内容调整。
4. 若实施中发现需要新增第 8 个非 P-LOG 文件、需要修改第 5 行之外的 frontmatter 字段、需要改正文、或需要补改 `.github/agents/**` 其他文件，当前预审立即失效，必须重新补充预审。

---

## 四、冻结实施批次

### A0：治理建档（本批）

- 状态：`completed`
- 范围：仅 `docs/tasks/**`、`docs/reviews/**`、`docs/locks/**`、`docs/handoffs/**`
- 说明：本批只负责完成独立编号留痕，不进入 `.github/agents/**` 实施。

### A1：agent model 统一升级第一批（待 Token）

- 状态：`pending_token`
- 保护口径：P0
- 冻结白名单：
  1. `.github/agents/architect.agent.md`
  2. `.github/agents/backtest.agent.md`
  3. `.github/agents/dashboard.agent.md`
  4. `.github/agents/data.agent.md`
  5. `.github/agents/decision.agent.md`

### A2：agent model 统一升级第二批（待 Token）

- 状态：`pending_token`
- 保护口径：P0
- 冻结白名单：
  1. `.github/agents/live-trading.agent.md`
  2. `.github/agents/sim-trading.agent.md`

---

## 五、目标改动冻结

1. 仅允许把 7 个目标文件 frontmatter 第 5 行 `model` 从 `claude-sonnet-4-6-high` 替换为 `claude-opus-4-6-high`。
2. `name`、`description`、`tools`、frontmatter 其他字段与正文全部保持原样，不得顺手调整。
3. 本任务不得制造“统一风格”“顺手整理注释”“修正描述文案”“补充工具组”等额外改动。
4. A1 与 A2 均需分别完成最小自校验、终审与锁回，不得跨批次混提、混验、混锁。

---

## 六、主要风险

1. 目标路径位于 `.github/**`，属于 P0 保护区；任何未签发、越白名单或提前写入都会直接违反治理流程。
2. 7 文件超过 `WORKFLOW.md` 单任务默认 5 文件上限，若不拆分 A1 / A2 即构成流程违规。
3. `.github/agents/architect.agent.md` 本身在变更范围内；若写入不当，可能直接影响当前项目架构师 Agent 的装载与后续协作。
4. 若 `claude-opus-4-6-high` 标识不被运行器识别，可能导致 agent 装载失败、静默回退或运行期行为与预期不符。
5. 当前工作树已出现目标 7 文件的未纳管差异；在未先裁定其来源与处置方式前，A1 / A2 即使获签发，也无法把现有工作树直接视为“尚未实施”的干净起点。

---

## 七、验收标准

1. `.github/agents/**` 下最终 `claude-sonnet-4-6-high` 为 0 命中。
2. `.github/agents/**` 下最终 `claude-opus-4-6-high` 为 7 命中，且仅限本任务冻结的 7 个目标文件。
3. 7 个目标文件的 frontmatter 语法合法，且改动限定为第 5 行 `model` 替换。
4. 不得出现任何白名单外改动，尤其不得波及 `.github/agents/**` 其他文件、`.github/instructions/**`、`WORKFLOW.md`、`services/**`。
5. 至少完成一次最小可用性确认：能够对 7 个目标文件完成 frontmatter 读取 / 发现检查或等价的运行器配置加载确认，且无新增语法错误。
6. A1 与 A2 必须分别保留可独立复核、独立锁回、独立提交的留痕。

---

## 八、当前轮次治理白名单（P-LOG）

1. `docs/tasks/TASK-0047-仓库级agent-model统一升级预审.md`
2. `docs/reviews/TASK-0047-review.md`
3. `docs/locks/TASK-0047-lock.md`
4. `docs/handoffs/TASK-0047-架构预审交接单.md`

---

## 九、预审结论

1. `TASK-0047` 正式成立。
2. 当前仅完成 A0 治理建档；A1 与 A2 状态均冻结为 `pending_token`。
3. 按 `TASK-0047` 标准流程，当前尚未对 `.github/agents/**` 实施受控写入；但目标 7 文件已存在未纳管工作树差异，实施前必须先由 Jay.S / Atlas 裁定其处置方式。