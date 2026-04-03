---
applyTo: "docs/prompts/**"
description: "Use when: 读取或更新 JBT 的公共 prompt 与私有 agent prompt，强制执行 prompt 同步和中文协同规则"
---

# Prompt Sync

当你处理 `docs/prompts/**` 下的文件时，必须遵守：

1. 总项目经理调度提示词只允许 Atlas 写入。
2. 公共项目提示词只允许项目架构师写入。
3. 私有 agent 提示词只允许对应 agent 自己写入。
4. 每个 agent 每完成一个动作，必须同步更新自己的私有 prompt。
5. 项目架构师每完成一次审核，必须同步更新公共项目提示词。
6. 所有 prompt 内容必须使用中文，避免英文工作口径。
