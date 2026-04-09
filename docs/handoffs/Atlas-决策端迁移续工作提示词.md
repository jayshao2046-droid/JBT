# Atlas 决策端迁移续工作提示词

把下面这段直接交给新的 Atlas 窗口：

你现在继续接管 JBT 项目的总项目经理工作，这一轮只处理“Studio 旧 J_BotQuant 决策端清洗升级后迁移到 JBT 决策端”的治理与派发准备。JBT 当前是唯一项目管理来源；`J_BotQuant` 在本任务中只承担旧决策域代码的只读参考，不再承担 prompt / plan / context 来源。请严格按以下顺序读取并继续，不要跳过：

1. `ATLAS_PROMPT.md`
2. `docs/plans/ATLAS_MASTER_PLAN.md`
3. `PROJECT_CONTEXT.md`
4. `WORKFLOW.md`
5. `docs/prompts/总项目经理调度提示词.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/项目架构师提示词.md`
8. `docs/prompts/agents/总项目经理提示词.md`
9. `docs/prompts/agents/决策提示词.md`
10. `docs/tasks/TASK-0016-J_BotQuant-Studio-决策端API接入预审.md`
11. `docs/reviews/TASK-0016-review.md`
12. `docs/locks/TASK-0016-lock.md`
13. `docs/handoffs/TASK-0016-Studio-正式接入预审交接单.md`
14. `docs/handoffs/Atlas-全员协同执行提示词.md`
15. `services/decision/README.md`
16. 以下 legacy 决策端文件，明确只读：
   - `J_BotQuant/src/api/decision_api.py`
   - `J_BotQuant/src/strategy/ai_engine/base.py`
   - `J_BotQuant/src/strategy/ai_engine/decision_layer.py`
   - `J_BotQuant/src/strategy/ai_engine/local_model.py`
   - `J_BotQuant/src/strategy/ai_engine/cloud_api.py`
   - `J_BotQuant/configs/ai_decision.yaml`
   - `J_BotQuant/Dockerfile.decision`
   - `J_BotQuant/configs/launchagents/com.botquant.decision_api.plist`

读取后先汇报以下事实，不要跳过：

1. JBT 已是唯一项目管理来源；`J_BotQuant` 在本任务里只承担旧决策端代码的只读参考，不再作为开工 prompt / plan / progress 来源。
2. Jay.S 已明确授权：本轮可以只读读取 `J_BotQuant` 旧决策端代码，用于清洗升级和迁移拆解；仍然禁止在 legacy 目录写入。
3. JBT 当前 `services/decision/` 仍只有骨架（README + `.env.example`），正式业务代码尚未启动。
4. legacy 决策端不是单一 API 文件，而是一整套决策系统：`decision_api`、AI 分层决策引擎、Mini 数据上下文拉取、向 trading_api 推送 approve、SQLite 缓存 / 审计、AI 配置、Docker 与 LaunchAgent。
5. `TASK-0016` 当前冻结的是“Studio 正式 API 接入”边界，不自动等于“旧决策端整体清洗迁移”；新窗口中的 Atlas 不能直接把整个决策端迁移混并进 `TASK-0016`。
6. 这件事是跨边界、跨服务、带 legacy 清洗的架构迁移任务，默认需要项目架构师 / Livis 先做边界判定，再决定是否新建正式任务。
7. 当前没有任何针对 `services/decision/**`、`shared/contracts/**`、`integrations/legacy-botquant/**` 的新代码 Token；未建档、未白名单、未解锁前，不得启动代码写入。

你在新窗口中的第一轮工作重点：

1. 先要求项目架构师判断：这次“旧决策端清洗升级后迁移到 JBT decision”是沿 `TASK-0016` 拆批继续，还是必须新建独立的 decision 迁移任务；在这个判断出来前，不给任何 Agent 发代码执行。
2. 先把 legacy 决策端按职责拆干净，至少区分：
   - `services/decision/` 应承接的决策 API / 信号审批 / 编排逻辑
   - 应下沉到 `services/data/` 的数据上下文拉取
   - 应留在 `sim-trading` 或 `live-trading` 的交易执行 / 账本逻辑
   - 需要放进 `integrations/legacy-botquant/` 的兼容适配逻辑
   - 需要升级到 `shared/contracts/` 的跨服务契约
3. 先输出一份“legacy 决策端迁移清单”，把旧代码分成 `保留迁移 / 清洗重写 / 删除淘汰 / 暂留兼容` 四类，避免把旧杂质整包搬进 JBT。
4. 先冻结 JBT 决策端的目标边界：固定服务端口 `8104`，只负责因子、信号、审批和策略编排；不得维护交易主账本，不得直接写交易服务内部目录，不得跨服务直读运行态目录。
5. 若需要终端命令、git 提交、远端同步、容器验证或 legacy 运行态探测，先把命令逐条汇报给 Jay.S，等待确认后再执行。

新窗口中的交付物顺序必须是：

1. 边界判定结论
2. 正式任务归属建议（沿用 `TASK-0016` 还是新建任务）
3. legacy 决策端迁移清单
4. 需要项目架构师建档的 task/review/lock/handoff 列表
5. 只有在上述治理动作完成后，才允许进入具体代码派发

输出要求：

- 始终先汇报当前阻塞、当前派发、下一检查点。
- 必须明确提醒：这是架构迁移任务，默认先走项目架构师 / Livis，不允许 Atlas 直接下场改决策业务代码。
- 所有新动作优先落治理文件，不得先写 `services/decision/**` 后补账本。
- 不要把“只读读取 J_BotQuant 旧代码”误解成“允许在 J_BotQuant 继续修补”。