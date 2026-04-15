# JBT Atlas Master Plan

【签名】Atlas
【时间】2026-04-14
【设备】MacBook
【状态】JBT 本地 Atlas 计划入口

## 1. 本文件定位

1. 本文件是 Atlas 模式在 JBT 工作区内的 master plan 入口文件。
2. 详细总计划以 `docs/JBT_FINAL_MASTER_PLAN.md` 为主。
3. 若 `docs/JBT_FINAL_MASTER_PLAN.md` 与 `docs/prompts/总项目经理调度提示词.md`、`docs/prompts/agents/总项目经理提示词.md` 存在时间差，以后两者的较新留痕为准；Atlas 后续负责回补总计划。

## 2. 当前总优先级

1. 四设备运行架构已冻结为 Mini / Studio / Alienware / Air；MacBook 仅保留开发/控制，不计入运行态四设备。
2. Mini 更新为“纯数据采集节点”；Studio 更新为“决策/开发主控节点”，本地常驻模型只记 `deepcoder:14b` + `phi4-reasoning:14b`；Alienware（192.168.31.224）固定为“交易执行 + 情报研究员节点”，正式承载 `sim-trading:8101`，当前只保留 `qwen3:14b`；Air 继续作为回测生产节点。
3. 研究范围冻结：期货优先且只跟踪已有策略覆盖品种；股票只分析策略筛出的 30 只股票池；搜索/外部信息只作为排除项增强。
4. `TASK-0107` 已完成：sim-trading 已正式迁移至 Alienware 裸 Python 部署；若后续要改为 Docker 化部署，仍需另建任务、预审、白名单与 Token。
5. 数据端：准备“Mini system 级采集 / 调度 / 通知迁移到 JBT Docker 体系”的治理与切换方案。
6. 看板端：统一聚合 dashboard 已完成 Phase F 全闭环，当前进入维护态，不扩范围。
7. 模拟交易：维持 `TASK-0017` 待正式交易日开盘验证，不擅自扩范围。
8. 回测：维持阶段性结案 / 维护观察。
9. 决策：`TASK-0104-D2` 已部署待 Studio 重启生效，其余维持维护态；后续若继续 legacy 清洗迁移，先走专项 handoff 与架构判边。

## 3. 已锁回基线

1. `TASK-0029` 已锁回：`极速维修 V2` 正式治理规则已落地。
2. `TASK-0030` 已锁回：`终极维护模式 U0` 正式治理规则已落地。
3. `TASK-0031` 已锁回：data 单服务热修完成。
4. `TASK-0032` 已锁回：`data_web` 临时原型导入完成。
5. `TASK-0104` 已锁回：data 预读投喂决策端（夜间摘要生成 + 开盘前上下文注入）完成，D1 data 侧 + D2 decision 侧全部部署。
6. `TASK-0119` 已锁回：全服务安全漏洞修复完成，修复 4 个 P0 高危漏洞 + 7 个 P1 中危漏洞 + 6 个 P2 低危问题。

## 3.1 进行中任务

1. `TASK-0121` 建档完成，待预审：data 研究员 24/7 重构（Alienware qwen3:14b + 多进程 + 内外盘联动）
   - 问题：当前报告完全为空（0 品种，711 bytes，置信度 0.0）
   - 根因：Mini `/api/v1/bars` 端点未实现 + 架构设计不合理
   - 方案：24/7 多进程（5 进程）+ 内外盘联动 + 增量去重 + 连贯写作
   - 批次：M1 (Mini API) → A1-A6 (Alienware 研究员) → D1 (Studio 决策对接)
   - 状态：A0 建档完成，等待架构师预审 + Token 签发

## 4. 开工后的继续读取链

1. `docs/prompts/总项目经理调度提示词.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/总项目经理提示词.md`
4. 如有专项，继续读取对应 `docs/handoffs/Atlas-*.md`