# REVIEW-TASK-0082-PRE — Atlas Agent 新建预审

【签名】项目架构师
【时间】2026-04-13
【任务】TASK-0082
【类型】预审

## 审核结论：通过

## 审核要点

1. **范围合规**：仅新建 `.github/agents/atlas.agent.md` 单一文件，属于 `.github/**` P0 保护区，需要 Jay.S Token 签发。
2. **格式对齐**：必须与现有 7 个 `.agent.md` 保持相同 YAML frontmatter 结构（name/description/tools/model）。
3. **角色对齐**：Atlas 定义应对齐 `docs/prompts/agents/总项目经理提示词.md` 的职责边界。
4. **无业务代码**：本任务不涉及任何 `services/**` 目录变更。

## 白名单冻结

| 文件 | 操作 |
|------|------|
| `.github/agents/atlas.agent.md` | 新建 |
