# TASK-0047 预审记录

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0047 |
| 任务标题 | 仓库级 agent model 统一升级预审 |
| 审核人 | 项目架构师 |
| 审核日期 | 2026-04-11 |
| 审核结果 | ✅ 预审通过（A1/A2 待 Token；实施前需先处置目标文件现有未纳管差异） |

---

## 预审检查清单

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | 问题归属明确 | ✅ | 仓库级治理变更，不归属任何单服务 |
| 2 | P0 路径识别明确 | ✅ | 目标全部位于 `.github/agents/**`，属于 `.github/**` P0 保护区 |
| 3 | 变更目标最小化 | ✅ | 目标冻结为 7 个 agent 定义文件，且仅允许第 5 行 `model` 值替换 |
| 4 | 单任务文件数约束满足 | ✅ | 7 文件按 `WORKFLOW.md` 上限拆为 A1=5 文件、A2=2 文件 |
| 5 | 白名单精确可执行 | ✅ | A1 / A2 白名单均已冻结为精确文件列表，无目录级通配放大 |
| 6 | 自身影响已识别 | ✅ | `.github/agents/architect.agent.md` 本身在变更范围内 |
| 7 | 验收标准可量化 | ✅ | 旧值 0 命中、新值 7 命中、frontmatter 合法、无白名单外改动、最小可用性确认 |
| 8 | 当前工作树状态可直接进入实施 | ⚠️ | 只读复核显示目标 7 文件已为 opus 值且存在未纳管差异；不阻塞建档，但阻塞后续直接按“未写入”口径推进 |

---

## 当前只读事实

1. 目标 7 文件当前都已显示为 `model: "claude-opus-4-6-high"`。
2. JBT `.github/agents/**` 下 `claude-sonnet-4-6-high` 为 0 命中，`claude-opus-4-6-high` 为 7 命中。
3. 当前工作树已存在 7 个目标文件的未纳管差异；该事实不等同于 `TASK-0047` 已执行完成，也不能替代 Token、终审与锁回。

---

## 预审意见

1. 本次变更必须严格限定为 7 个目标文件 frontmatter 第 5 行 `model` 值替换；不得改 `name`、`description`、`tools` 或正文。
2. A1 与 A2 必须作为两个独立 P0 批次分别签发、分别实施、分别终审与分别锁回，不得合批穿透 `WORKFLOW.md` 的 5 文件上限。
3. `.github/agents/architect.agent.md` 因为直接影响当前架构师 Agent 定义，实施时必须额外关注前后装载可用性。
4. 若 `claude-opus-4-6-high` 标识在运行器侧未被识别，实施应立即停止，不得继续把其余文件批量推进到未知状态。
5. 在 A1 / A2 正式实施前，Jay.S / Atlas 必须先裁定当前目标文件现有未纳管差异的处置方式，否则后续验证、lockback 与独立提交证据链会被污染。

---

## 风险与阻塞

1. P0 风险：`.github/**` 为保护区，任何未签发写入都违反治理流程。
2. 拆批风险：7 文件若不拆批，会直接违反单任务默认 5 文件上限。
3. 自身影响风险：`architect.agent.md` 处于本轮变更范围内，若 model 标识或 frontmatter 被破坏，可能影响当前 Agent 装载。
4. 兼容性风险：`claude-opus-4-6-high` 若不被运行器识别，可能触发装载失败或静默回退。
5. 当前阻塞：目标 7 文件已存在未纳管工作树差异，需先由 Jay.S / Atlas 明确“清理 / 吸收 / 重建于受控批次内”的处置口径。

---

## 白名单冻结

### A0 批次（治理账本，无需 Token）

```
docs/tasks/TASK-0047-仓库级agent-model统一升级预审.md
docs/reviews/TASK-0047-review.md
docs/locks/TASK-0047-lock.md
docs/handoffs/TASK-0047-架构预审交接单.md
```

### A1 批次（待签发）

```
.github/agents/architect.agent.md
.github/agents/backtest.agent.md
.github/agents/dashboard.agent.md
.github/agents/data.agent.md
.github/agents/decision.agent.md
```

### A2 批次（待签发）

```
.github/agents/live-trading.agent.md
.github/agents/sim-trading.agent.md
```

---

【签名】项目架构师
【时间】2026-04-11
【设备】MacBook