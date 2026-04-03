---
applyTo: "**"
description: "Use when: 在 JBT 工作区内准备进行任意写操作时，强制执行审核、Token 解锁、锁回流程"
---

# Change Control

在 JBT 工作区中准备修改任意文件前，必须先检查：

1. 当前任务是否已经登记。
2. Architect 是否已完成预审。
3. 本次修改文件是否已经列入白名单。
4. Jay.S 是否已为这些指定文件生成有效 Token。

例外：

1. `docs/tasks/**`
2. `docs/reviews/**`
3. `docs/locks/**`
4. `docs/handoffs/**`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/**`

上述协同账本文件不走代码 Token，但仍必须遵守角色独占写权限。

没有满足上述条件时：

1. 不得修改任何锁定文件。
2. 不得扩展任务范围。
3. 不得顺手修复无关问题。

修改完成后，必须要求：

1. 先做本地自校验。
2. 再交给 Architect 终审。
3. 终审通过后立即锁回文件。
4. 同步更新自己的私有 prompt。
