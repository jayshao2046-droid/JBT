# TASK-0129 Lock Record

- task_id: TASK-0129
- service: decision
- agent: 决策
- review_id: REVIEW-TASK-0129
- token_id: tok-79b0d20d-0eca-44a8-a551-8eb75aed13ee
- status: locked
- issued_at: 2026-04-26
- expires_at: 2026-04-26
- locked_at: 2026-04-26
- ttl: 60min
- reason: 为 decision 启动新一轮模板种子批量生成前，清理双端历史生成目录，确保 MacBook 与 Studio 处于一致干净状态

## Allowed Files
- services/decision/strategies/llm_generated
- services/decision/strategies/llm_ranked
- services/decision/strategies/_tqsdk_runtime/llm_generated
- services/decision/strategies/_tqsdk_runtime/llm_ranked

## Notes
- 本批仅批准清理历史生成目录，不得改写 strategy_library、scripts、shared/contracts 或其他 decision 文件。
- 执行 Agent 固定为“决策”；Atlas 只负责建档、签发推进、验收与锁回，不代写 decision 业务代码。
- Studio 端操作仅限与上述相同相对路径的同步清理，不得扩展到其他目录。
- 2026-04-26 已完成 lockback；MacBook 与 Studio 四个历史目录 YAML 已清零，Atlas_Import_Check.yaml 保留，Studio 缺少 strategy_library 属既有环境差异而非本次误删。