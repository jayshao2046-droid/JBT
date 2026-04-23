# JBT Project Context

【签名】Atlas
【时间】2026-04-14
【设备】MacBook
【状态】JBT 为唯一项目管理来源

## 1. 项目定位

1. JBT 是下一代多服务工作区，也是当前唯一的任务、prompt、进度、计划来源。
2. `J_BotQuant` 继续保留为 legacy 运行工程，但不再承担 JBT 的项目管理上下文来源。
3. 只有当某个已建档迁移任务明确授权时，才可只读读取 `J_BotQuant` 的旧代码或旧运行事实；仍然禁止在 legacy 目录写入。

## 2. 服务边界

| 服务 | 目录 | 职责 |
|---|---|---|
| sim-trading | `services/sim-trading/` | 模拟交易、执行风控、账本 |
| live-trading | `services/live-trading/` | 实盘交易、执行风控、账本 |
| backtest | `services/backtest/` | 在线 / 本地回测、报告、绩效评估 |
| decision | `services/decision/` | 因子、信号、审批、策略编排 |
| data | `services/data/` | 数据采集、标准化、供数 API |
| dashboard | `services/dashboard/` | 聚合看板、只读查询、受控配置入口 |

## 3. 设备与端口冻结

1. 运行态四设备架构冻结为 Mini / Studio / Alienware / Air；MacBook 仅保留开发/控制，不计入运行态四设备。
2. Mini：`192.168.31.74`，`data:8105`、`sim-trading:8101`、`sim-trading-web:3002`；角色为“数据源 + 情报落库存储 + 快速投喂节点”，且这是当前 JBT sim-trading 的现网部署面。
3. Studio：`192.168.31.142`，`decision:8104`、`decision-web:3003`、`dashboard:8106/3005`；角色为“决策/开发主控节点”，本地常驻模型冻结为 `deepcoder:14b` + `phi4-reasoning:14b`，不再把 `qwen3:14b` 记在 Studio 常驻里。
4. Alienware：`192.168.31.187`；角色固定为“Windows 交易端 + 情报研究员节点”，当前只保留 `qwen3:14b`；负责读取 Mini 同源数据、生成 Studio / Jay.S 双报告，并承载期货公司官方 Windows 交易软件 24h 在线主机。
5. Air：`192.168.31.156`，`backtest:8103`、`backtest-web:3001`；继续作为回测生产节点。
6. 端口语义固定：Web `3001~3006`，API `8101~8106`；只允许主机名 / IP 变化，不允许改端口语义。

## 4. 当前冻结事实

1. JBT 当前只允许文件级 Token，不存在目录级或整仓级“全局 Token”。
2. `极速维修 V2` 与 `终极维护模式 U0` 已正式落地并锁回；二者都不是目录级解锁。
3. `TASK-0029`、`TASK-0030`、`TASK-0031`、`TASK-0032` 已锁回，不重开。
4. 四设备运行架构已冻结：Mini 负责纯数据采集与 `data:8105`；Studio 负责决策/开发主控；Alienware 负责 `sim-trading:8101` 交易执行与研究员报告；Air 负责回测生产。
5. 研究范围已冻结：期货优先且仅跟踪已有策略覆盖品种；股票只分析策略筛出的 30 只股票池；搜索/外部信息主要作为“排除项增强”，负面或不确定信息权重更高，不作为无条件加分项。
6. `TASK-0107` 已完成：sim-trading 已正式迁移至 Alienware 裸 Python 部署；Mini 不再承载 sim-trading。
7. 后续若要把 Alienware 裸 Python 进一步切到 Docker 化部署，仍必须单独建任务、预审、白名单、Token。
8. 数据端当前优先级最高的是 system 级迁移治理，不是继续临时热修；原因是 Mini 现网真实 24h 采集 / 调度 / 通知仍大量依赖 legacy system。
9. 统一聚合 dashboard 已完成 Phase F 全闭环并进入维护态；后续只按新增问题或扩展需求单独建任务。
10. 回测本轮处于阶段性结案 / 维护观察；模拟交易维持 `TASK-0017` 待开盘验证，且当前尚未接通期货公式 / 策略公式执行链路。
11. live-trading 当前明确后置，待 sim-trading 在 Alienware 上连续稳定运行 2~3 个月后再评估是否启动。

## 5. 接管规则

1. 开工先读 `ATLAS_PROMPT.md`、`docs/plans/ATLAS_MASTER_PLAN.md`、本文件，再进入总项目经理双 prompt。
2. 若 `docs/JBT_FINAL_MASTER_PLAN.md` 与总项目经理双 prompt 存在时间差，以双 prompt 的较新留痕为准。
3. 所有专项续接统一走 `docs/handoffs/Atlas-*.md`。