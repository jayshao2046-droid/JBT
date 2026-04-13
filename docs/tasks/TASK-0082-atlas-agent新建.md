# TASK-0082 — Atlas Agent 新建

【签名】Atlas
【时间】2026-04-13
【服务】治理
【保护级别】P0

## 背景

`.github/agents/` 下现有 7 个 agent 文件（architect/backtest/dashboard/data/decision/live-trading/sim-trading），缺少总项目经理 Atlas 对应的 agent.md。Jay.S 要求新建 Atlas agent 继承原 Atlas 位置。

## 白名单

| 文件 | 操作 | 说明 |
|------|------|------|
| `.github/agents/atlas.agent.md` | 新建 | Atlas 总项目经理 agent 定义 |

## 验收标准

1. 文件格式对齐现有 7 个 `.agent.md`（YAML frontmatter + markdown body）
2. `model` 字段使用 `claude-opus-4-6-high`（与 TASK-0047 统一升级后的口径一致）
3. 开工必读、核心职责、禁止行为、可写范围对齐 `docs/prompts/agents/总项目经理提示词.md` 的角色定义
4. 不涉及任何业务代码

## 状态

✅ 已完成（`.github/agents/atlas.agent.md` 已存在，格式与内容符合验收标准）
