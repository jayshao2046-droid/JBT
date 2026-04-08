# TASK-0021 总包执行与 Token 清单

【签名】项目架构师
【时间】2026-04-07
【设备】MacBook

## 目的

把 `TASK-0021` 从“仅批次 A 可执行”升级为“总包执行治理已就绪”，供 Jay.S 直接据此签发后续批次 Token。

## 当前冻结事实

1. 当前执行组织固定为：**项目架构师 + 决策 agent**。
2. 当前不使用 Livis。
3. A 批 contracts 10 文件 Token 已 active，可直接开工。
4. B、C0、C、D、E0、E、F0、F、G 当前均未 active。
5. 其余批次应按本 Manifest 由 Jay.S 一次性签发；在实际签发完成前，不得提前越权执行。

## Jay.S 可直接签发的 Manifest

| 批次 | 执行 agent | 建议白名单类别 | 保护级别 | 目的 | 签发建议 |
|---|---|---|---|---|---|
| A | 决策 agent | `shared/contracts/README.md` + `shared/contracts/decision/*.md` 正式契约 | P0 | 冻结 decision 正式契约、通知事件、看板只读聚合字段 | 已 active，可直接开工 |
| B | 决策 agent | `integrations/legacy-botquant/**` 中“旧决策域只读适配 / 输入映射 / 迁移兼容”类别文件 | P0 | 建立迁移期只读兼容层，隔离 legacy 输入，不带入 legacy 交易/回测逻辑 | 建议纳入一次性签发 |
| C0 | 决策 agent | `services/decision/.env.example` 与决策服务受保护模板配置 | P0 | 决策服务环境模板、模型路由占位、研究窗口与门禁占位 | **必须单独 P0** |
| C | 决策 agent | `services/decision/src/**`、`services/decision/tests/**`、必要 `configs/**` 的核心服务实现类别 | P1 | 决策 API、审批编排、策略仓库、模型路由、执行资格门禁 | 建议纳入一次性签发 |
| D | 决策 agent | `services/decision/src/research/**`、`services/decision/src/gating/**`、对应测试 | P1 | 研究中心主线、XGBoost 研究编排、回测/因子/研究资格门禁联动 | 建议纳入一次性签发 |
| E0 | 决策 agent | `services/dashboard/.env.example` 与决策看板受保护模板配置 | P0 | 决策看板 API 入口、只读聚合开关、运行模板占位 | **必须单独 P0** |
| E | 决策 agent | `services/dashboard/**` 的决策看板页面、只读聚合展示、前台交互类别文件 | P1 | 落地 7 页决策看板与策略仓库前台 | 建议纳入一次性签发 |
| F0 | 决策 agent | `docker-compose.dev.yml`、`services/decision/Dockerfile`、`services/dashboard/Dockerfile`、`deploy/**`、反代/发布配置 | P0 | 决策与看板容器化、compose、deploy、反代与发布骨架 | **必须单独 P0** |
| F | 决策 agent | `services/decision/src/notifier/**`、`services/decision/src/reporting/**`、对应测试 | P1 | 飞书/邮件通知、研究完成摘要、日报周报月报链路 | 建议纳入一次性签发 |
| G | 决策 agent | `services/decision/src/publish/**`、相关 API / tests、迁移收口治理留痕 | P1 | 仅推送到 `sim-trading` 的发布链路、`live-trading` 锁定可见入口、迁移收口与验收交接 | 建议纳入一次性签发 |

## 单独 P0 批次说明

1. `C0`：凡涉及 `services/decision/.env.example` 或同级受保护模板配置，必须独立 P0。
2. `E0`：凡涉及 `services/dashboard/.env.example` 或同级受保护模板配置，必须独立 P0。
3. `F0`：凡涉及 compose、Dockerfile、deploy、反代、发布配置，必须独立 P0。

## 不得混签的规则

1. 不得把 `C0` 混入 `C`。
2. 不得把 `E0` 混入 `E`。
3. 不得把 `F0` 混入 `F` 或 `G`。
4. 不得把 `TASK-0021` 与 `TASK-0016`、`TASK-0012` 混签。
5. 不得把 `services/sim-trading/**`、`services/live-trading/**`、`services/data/**`、`services/backtest/**` 直接并入本主任务 Manifest。

## 2026-04-08 收口补批裁决

1. 基于对 `services/decision/**`、`services/data/**` 与 `services/sim-trading/**` 的只读复核，decision 收口继续挂在 `TASK-0021` 下新增补充批次 `H0`~`H4`，**不新建第二个 decision 任务**。
2. 但 `sim-trading` 发布接收接口必须拆为独立 `TASK-0023`；不得继续混入本 Manifest。
3. 当前补充批次冻结如下：

| 批次 | 执行 agent | 保护级别 | 白名单 | 目的 | 是否可并行 |
|---|---|---|---|---|---|
| `H0` | 决策 agent | P0 | `services/decision/decision_web/Dockerfile` | 修复 decision_web 镜像构建阻塞 | 可与 `H1` / `H3` 并行 |
| `H1` | 决策 agent | P1 | `src/core/settings.py`、`src/persistence/state_store.py`、`src/strategy/repository.py`、`src/api/routes/approval.py`、`tests/test_state_persistence.py` | 策略仓库与审批状态持久化 | 可与 `H0` / `H3` 并行；不可与 `H2` 并行 |
| `H2` | 决策 agent | P1 | `src/persistence/state_store.py`、`src/gating/backtest_gate.py`、`src/gating/research_gate.py`、`src/model/router.py`、`tests/test_gating.py` | 回测 / 研究资格持久化与模型门禁 | 依赖 `H1` |
| `H3` | 决策 agent | P1 | `pyproject.toml`、`src/research/factor_loader.py`、`tests/test_research.py` | 真实 data API 接入与 research 运行依赖 | 可与 `H0` / `H1` 并行 |
| `H4` | 决策 agent | P1 | `src/api/routes/strategy.py`、`src/api/routes/signal.py`、`src/publish/gate.py`、`src/publish/sim_adapter.py`、`tests/test_publish.py` | signal / strategy publish 真闭环 | 依赖 `H2` / `H3`；可与 `TASK-0023-A` 并行 |

4. `H4` 只修正 decision 侧发布入口与适配器命名空间，当前冻结到 `sim-trading` 既有 `/api/v1/strategy/publish`；不写 `services/sim-trading/**`。
5. 当前不把 `services/decision/.env.example` 或 `docker-compose.dev.yml` 纳入首轮；若实施中证明现有占位不足，再另起 **P0** 补审。

## 建议签发顺序

1. A 已 active，立即开工。
2. B、C0、C、D、E0、E、F0、F、G 按本 Manifest 一次性签发到位。
3. 实际执行时仍按批次顺序推进：A → B → C0 → C → D → E0 → E → F0 → F → G。
4. 对“部署后立即开工”阻塞，最稳妥补签顺序冻结为：`H0` → `H1` → `H2` → `H3` → `H4`；其中 `H0` 可与 `H1` / `H3` 并行，`H2` 必须在 `H1` 之后，`H4` 必须在 `H2` 与 `H3` 之后。
5. `TASK-0023-A` 在本轮命名空间冻结后可与 `H4` 并行推进，但最终端到端验收需两边同时完成。

## 关联交接单

1. `docs/handoffs/TASK-0021-收口补批预审交接单.md`
2. `docs/handoffs/TASK-0023-sim-trading-发布接口预审交接单.md`

## 向 Jay.S 汇报摘要

1. `TASK-0021` 总包执行治理准备已完成。
2. 当前固定执行组织为“项目架构师 + 决策 agent”，不使用 Livis。
3. A 批 contracts 10 文件 Token 已 active，可直接开工。
4. 其余批次已整理为可直接签发的 Manifest，其中 `C0`、`E0`、`F0` 明确为必须单独 P0 的保护批次。

## 下一步建议

1. 允许决策 agent 立刻按 A 批 active 白名单进入 `shared/contracts/**` 实施。
2. 由 Jay.S 依据本文件对 B、C0、C、D、E0、E、F0、F、G 一次性签发。
3. 签发完成后，Atlas 可按已冻结批次顺序连续派发，无需重新补做总包治理准备。