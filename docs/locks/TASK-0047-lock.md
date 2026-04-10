# TASK-0047 锁控记录

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0047 |
| 任务标题 | 仓库级 agent model 统一升级预审 |
| 锁控管理人 | 项目架构师 |
| 创建日期 | 2026-04-11 |

---

## 锁控文件清单

### A0 批次（治理建档）— 协同账本区，无需 Token

| 文件 | 操作 | 状态 | 写入者 |
|------|------|------|--------|
| docs/tasks/TASK-0047-仓库级agent-model统一升级预审.md | 新建 | ✅ 已完成 | 项目架构师 |
| docs/reviews/TASK-0047-review.md | 新建 | ✅ 已完成 | 项目架构师 |
| docs/locks/TASK-0047-lock.md | 新建 | ✅ 已完成 | 项目架构师 |
| docs/handoffs/TASK-0047-架构预审交接单.md | 新建 | ✅ 已完成 | 项目架构师 |

### A1 批次（待签发）

| 文件 | 操作 | Token | 状态 |
|------|------|-------|------|
| .github/agents/architect.agent.md | 更新（仅第 5 行 `model`） | 待 Jay.S 为 Atlas 签发 | 🔲 待签发 |
| .github/agents/backtest.agent.md | 更新（仅第 5 行 `model`） | 待 Jay.S 为 Atlas 签发 | 🔲 待签发 |
| .github/agents/dashboard.agent.md | 更新（仅第 5 行 `model`） | 待 Jay.S 为 Atlas 签发 | 🔲 待签发 |
| .github/agents/data.agent.md | 更新（仅第 5 行 `model`） | 待 Jay.S 为 Atlas 签发 | 🔲 待签发 |
| .github/agents/decision.agent.md | 更新（仅第 5 行 `model`） | 待 Jay.S 为 Atlas 签发 | 🔲 待签发 |

### A2 批次（待签发）

| 文件 | 操作 | Token | 状态 |
|------|------|-------|------|
| .github/agents/live-trading.agent.md | 更新（仅第 5 行 `model`） | 待 Jay.S 为 Atlas 签发 | 🔲 待签发 |
| .github/agents/sim-trading.agent.md | 更新（仅第 5 行 `model`） | 待 Jay.S 为 Atlas 签发 | 🔲 待签发 |

---

## 锁控日志

| 时间 | 操作 | 批次 | 说明 |
|------|------|------|------|
| 2026-04-11 | 建档 | A0 | 创建 TASK-0047 的 task/review/lock/handoff 四份治理账本 |
| 2026-04-11 | 冻结 | A1 | 冻结 5 文件白名单，目标仅限 frontmatter 第 5 行 `model` 值替换 |
| 2026-04-11 | 冻结 | A2 | 冻结 2 文件白名单，目标仅限 frontmatter 第 5 行 `model` 值替换 |
| 2026-04-11 | 只读核验 | A0 | 目标 7 文件当前旧值 0 命中、新值 7 命中，且已存在未纳管工作树差异，待 Jay.S / Atlas 裁定处置 |

---

【签名】项目架构师
【时间】2026-04-11
【设备】MacBook