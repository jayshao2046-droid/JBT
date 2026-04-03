# Legacy BotQuant Integration

本目录只负责 JBT 与当前仍在运行的 J_BotQuant 之间的兼容对接。

原则：

1. 只通过 API 对接旧系统。
2. 不直接复制旧交易模块到新服务目录继续开发。
3. 旧系统过渡期可以作为上游或下游，但不能成为 JBT 的内部依赖。

典型用途：

- 将 JBT 的 `sim-trading` 暴露给旧决策端调用
- 将旧数据端 API 适配为 JBT `decision` 可消费的格式
- 为旧看板提供到新交易端的桥接查询
