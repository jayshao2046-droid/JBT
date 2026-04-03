# JBT Workspace Instructions

## Core Rules

1. JBT 是多服务工作区，不是单仓大项目。
2. 所有服务必须保持目录独立、配置独立、账本独立、通知独立。
3. 除 `shared/contracts` 与 `shared/python-common` 外，不得跨服务 import 代码。
4. 除 API 调用外，不得跨服务读取对方数据目录。
5. 任何新功能先判断它属于哪个服务边界，再写代码。
6. 所有新开发只允许发生在 `~/jbt/`；`J_BotQuant` 视为 legacy，不再承接新开发。
7. Atlas 默认只读，只能在 Jay.S 明确授权时修改治理文件。
8. 项目架构师默认只负责审核、公共进度更新与锁控记录，不直接代写服务业务代码。
9. 任一写操作都必须遵守 `WORKFLOW.md` 中的一件事一审核一上锁流程。
10. 没有 Jay.S Token，不得修改锁定文件。
11. 每个 agent 每完成一个动作，必须更新自己的私有 prompt。
12. 只有项目架构师可以写公共项目 prompt。
13. 只有 Atlas 可以写总项目经理调度 prompt。
14. 每个任务完成后，必须先向 Jay.S 汇报并等待确认，才能进入下一任务。
15. 每个任务必须独立提交、独立上传、独立回滚。

## Service Ownership

- `services/sim-trading/`: 模拟交易、账本、执行风控
- `services/live-trading/`: 实盘交易、账本、执行风控
- `services/backtest/`: 历史回测与参数优化
- `services/decision/`: 因子、信号、审批编排
- `services/data/`: 数据采集、标准化、供数
- `services/dashboard/`: 看板与只读聚合

## Contract Governance

1. 跨服务字段与请求响应模型统一登记到 `shared/contracts`。
2. 若某个服务需要另一个服务的新字段，先改契约，再改双方实现。
3. 旧 BotQuant 的兼容逻辑只允许放在 `integrations/legacy-botquant`。
4. 修改 `shared/contracts` 必须先经过项目架构师预审，并取得 Jay.S 对指定文件的 Token。

## Runtime Governance

1. 每个服务未来必须拥有自己的 `.env.example`。
2. 运行日志与数据必须写入各自的挂载卷，不进入 Git。
3. 通知 webhook 不能跨服务复用为默认值。
4. `runtime/`、`logs/`、真实 `.env`、账本、数据库快照属于永久禁改区。

## Collaboration Ledgers

以下路径属于自动协同账本区：

- `docs/tasks/**`
- `docs/reviews/**`
- `docs/locks/**`
- `docs/handoffs/**`
- `docs/prompts/总项目经理调度提示词.md`
- `docs/prompts/公共项目提示词.md`
- `docs/prompts/agents/**`

规则：

1. 该区域不使用代码 Token 锁控。
2. 总项目经理调度 prompt 仅 Atlas 可写。
3. 公共项目 prompt 仅项目架构师可写。
4. 私有 prompt 仅对应 agent 自己可写。
5. 每次开始工作前，必须先读取总项目经理调度 prompt、公共项目 prompt 和自己的私有 prompt。

## Protected Paths

以下路径默认视为 P0 保护区：

- `WORKFLOW.md`
- `.github/**`
- `shared/contracts/**`
- `shared/python-common/**`
- `integrations/**`
- `docker-compose.dev.yml`
- `services/*/.env.example`

对这些路径的任何修改，都必须先预审，再解锁，再终审，再锁回。
