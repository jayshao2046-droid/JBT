# TASK-0021 decision 旧决策域清洗升级迁移预审

## 文档信息

- 任务 ID：TASK-0021
- 文档类型：新任务预审与分批冻结
- 签名：项目架构师
- 建档时间：2026-04-07
- 设备：MacBook

---

## 一、任务目标

把 Studio 旧 J_BotQuant 决策域清洗、拆边界、升级后迁入 JBT，形成干净独立的 `services/decision` 服务与独立决策看板。

本任务当前轮次只做预审与治理冻结，不写任何代码。

---

## 二、任务编号与归属结论

### 编号结论

- **本事项必须新建独立任务 `TASK-0021`，不得并入 `TASK-0016` 或 `TASK-0012`。**

### 判定理由

1. `TASK-0016` 的任务边界是“Studio 正式 API 接入、联调、切换与回滚门槛”，不承接旧决策域整体清洗迁移。
2. `TASK-0012` 的任务边界是“legacy 信号兼容桥接”，不承接独立决策服务、研究中心、策略仓库与独立看板重建。
3. 本事项包含决策核心能力、研究能力、执行资格门禁、通知体系重建与独立看板，若并入既有任务，会导致白名单、Token、验收和回滚边界全部失焦。

### 归属结论

- **当前轮次归属：跨治理层任务。**
- **未来实施主归属：`services/decision/**`。**
- **未来联动范围：`services/dashboard/**`、`shared/contracts/**`、`integrations/legacy-botquant/**`，以及按服务边界拆出的 `services/backtest/**`、`services/data/**`、`services/sim-trading/**`、`services/live-trading/**` 子任务。**

### 执行角色

1. 预审：项目架构师
2. 派发与治理协调：Atlas
3. 未来主执行：决策 Agent
4. 外部原型协同：Jay.S / V0（不属于本仓内代码执行主体）

---

## 三、与既有任务的边界冻结

### 1. 与 `TASK-0016` 的边界

1. `TASK-0016` 继续冻结为 Studio 正式 API 接入、正式联调、切换门槛与回滚条件。
2. `TASK-0021` 不承接 Studio 正式接入口切换，不承接 `TASK-0016` 的测试窗口与切换验收。
3. `TASK-0016` 不承接旧决策域整体清洗、独立看板、研究中心与策略仓库重建。

### 2. 与 `TASK-0012` 的边界

1. `TASK-0012` 继续冻结为 legacy 信号兼容桥接。
2. `TASK-0021` 不承接 `TASK-0012` 的兼容桥接实现，不承接其 legacy 信号过渡语义。
3. `TASK-0012` 不承接 decision 主服务、研究能力、执行资格门禁、独立通知体系或独立看板。

### 3. 共通冻结结论

1. `TASK-0021`、`TASK-0016`、`TASK-0012` 三者不得复用白名单、Token、验收口径或回滚单元。
2. 凡涉及 `shared/contracts/**`、`integrations/legacy-botquant/**` 或其他服务目录的修改，都必须在 `TASK-0021` 主任务下拆为独立批次或独立子任务。

---

## 四、当前轮次白名单与保护级别

### 当前 Git 白名单

1. `docs/tasks/TASK-0021-decision-旧决策域清洗升级迁移预审.md`
2. `docs/reviews/TASK-0021-review.md`
3. `docs/locks/TASK-0021-lock.md`
4. `docs/rollback/TASK-0021-rollback.md`
5. `docs/handoffs/TASK-0021-旧决策域清洗升级迁移预审交接单.md`
6. `docs/prompts/总项目经理调度提示词.md`
7. `docs/prompts/agents/总项目经理提示词.md`

### 当前保护级别

- **当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。**

### 当前轮次明确禁止

1. 不得修改 `services/decision/**`。
2. 不得修改 `services/dashboard/**`。
3. 不得修改 `shared/contracts/**`。
4. 不得修改 `integrations/legacy-botquant/**`。
5. 不得修改 `services/backtest/**`、`services/data/**`、`services/sim-trading/**`、`services/live-trading/**`。
6. 不得写入 legacy `J_BotQuant`。
7. 不得提前生成任何代码批次白名单或伪造运行时 Secret。

---

## 五、业务口径冻结

### 1. 清洗原则

1. 旧飞书通知、旧邮件通知、旧日志、旧策略、旧参数、旧设置一概不直接迁移。
2. legacy 混入的交易功能与外露回测功能全部关闭，不进入新决策服务。
3. 新决策服务只保留决策核心能力、研究能力、执行资格门禁、通知体系与只读看板聚合。

### 2. 模型矩阵冻结

1. 本地主模型：`Qwen3 14B`。
2. 本地兼容模型：`DeepSeek-R1 14B`。
3. L1 可切模型：`Qwen2.5` 系列。
4. 在线 L3 默认：`Qwen3.6-Plus`。
5. 在线升级复核：`Qwen3-Max`。
6. 在线备援：`DeepSeek-V3.2`。
7. 在线争议复核位：`DeepSeek-R1`。

### 3. 研究能力冻结

1. `XGBoost` 为研究主线。
2. `LightGBM` 仅预留模型后端抽象位，不进入第一批交付。
3. 研究与调参只允许运行在非交易时段；交易时段禁止自动调参与自动重训练。

### 4. 因子与回测冻结

1. 所有因子必须先完成回测并与策略包同步。
2. 无回测、回测过期、因子版本变化时，策略一律失去执行资格。
3. 策略执行资格必须同时满足：研究完成、回测确认、因子同步对齐。

### 5. 看板冻结

1. 决策端必须新增独立看板。
2. 看板必须沿用回测端与模拟交易端现有风格，不改色、不改设计语言。
3. 页面结构冻结为 7 页：总览、信号审查、模型与因子、策略仓库、研究中心、通知与日报、配置与运行。
4. 因子热力图必须纳入“模型与因子”页首屏第二排左侧主卡。

### 6. 策略仓库冻结

1. 策略仓库必须支持：导入、导出、预约、执行、下架。
2. “执行”只表示进入决策生产发布流程，不等于直接下单。
3. 第一阶段生产发布默认只允许 `sim-trading`，`live-trading` 入口只做锁定可见。

---

## 六、未来实施最小拆批方案

### 批次 A：契约冻结

1. 范围：`shared/contracts/**`
2. 内容：冻结决策请求与审批结果、策略包元数据、研究资格快照、因子版本快照、回测合格证明、通知事件、看板只读聚合字段。
3. 保护级别：**P0**
4. 执行 Agent：决策 Agent

### 批次 B：legacy 适配与只读边界

1. 范围：`integrations/legacy-botquant/**`
2. 内容：legacy decision 输入映射、兼容读取、迁移期只读适配；不得继续沉积 legacy 交易逻辑或 legacy 回测逻辑。
3. 保护级别：**P0**
4. 执行 Agent：决策 Agent

### 批次 C：decision 核心服务

1. 范围：`services/decision/**`
2. 内容：决策 API、审批编排、策略仓库、模型路由、执行资格门禁。
3. 保护级别：**P1**
4. 补充说明：若触及 `services/decision/.env.example`，必须另拆 **P0**。
5. 执行 Agent：决策 Agent

### 批次 D：研究能力与门禁联动

1. 范围：`services/decision/**`
2. 内容：研究中心、XGBoost 主线、LightGBM 后端抽象预留、非交易时段研究编排、回测与因子门禁联动。
3. 保护级别：**P1**
4. 执行 Agent：决策 Agent

### 批次 E：决策独立看板

1. 范围：`services/dashboard/**`
2. 内容：7 页决策看板、只读聚合展示、策略仓库前台、研究与通知前台。
3. 保护级别：**P1**
4. 补充说明：若触及 `.env.example`，必须另拆 **P0**。
5. 执行 Agent：开工前按目录归属改派

### 批次 F：通知体系重建

1. 范围：`services/decision/**` 与对应契约消费层
2. 内容：飞书、邮件、日报链路；完全重建，不复用 legacy 通知实现、旧 webhook 或旧邮箱配置。
3. 保护级别：**P1**
4. 补充说明：若新增 env 占位字段，必须另拆 **P0**。
5. 执行 Agent：决策 Agent

### 2026-04-08 部署后立即开工收口补批裁决

1. 基于对 `services/decision/**`、`services/data/**` 与 `services/sim-trading/**` 的只读复核，decision 收口继续挂在 `TASK-0021` 下新增补充批次，**不新建第二个 decision 任务**。
2. 判定理由：
	- 当前阻塞全部落在 `services/decision/**` 与 `services/decision/decision_web/**` 已建档主线上；
	- 若另起一个 decision 新任务，会把同一服务迁移主线拆成两个回滚单元，导致边界与责任漂移；
	- `TASK-0021` 已经承担旧决策域清洗升级迁移主线，收口补批比“新开第二个 decision 任务”更符合“一件事一审核一上锁”。
3. 但 `sim-trading` 发布接收接口必须拆为独立 `TASK-0023`，不得继续塞回 `TASK-0021`；原因是其实际写入归属 `services/sim-trading/**`，若混入 `TASK-0021` 会破坏跨服务回滚边界。
4. 当前首轮只纳入“部署后立即开工”的真实阻塞，不纳入纯 UI 空态；`research-center`、`notifications-report`、`config-runtime` 等页面空态继续排除。
5. 当前不把 `services/decision/.env.example` 或 `docker-compose.dev.yml` 纳入首轮；现有 `DECISION_DB_URL`、`BACKTEST_SERVICE_URL`、`DATA_SERVICE_URL`、`SIM_TRADING_SERVICE_URL` 占位已足够承接本轮实现。若实施中证明仍缺配置位，再另起 **P0** 补充预审。
6. 最稳妥先签顺序冻结为：`H0` → `H1` → `H2` → `H3` → `H4`；其中 `H0` 可与 `H1` / `H3` 并行，`H2` 依赖 `H1` 的持久化底座，`H4` 依赖 `H2` 与 `H3`，`TASK-0023-A` 在本轮命名空间冻结后可与 `H4` 并行。

#### 补充批次 H0：decision_web Dockerfile 构建收口

- 批次标识：`TASK-0021-H0`
- 执行 Agent：决策 Agent
- 保护级别：**P0**
- 是否可并行：可与 `H1` / `H3` 并行；建议最先签发

业务白名单：

1. `services/decision/decision_web/Dockerfile`

本批次目的：

1. 移除当前 `COPY --from=builder /app/public ./public 2>/dev/null || true` 非法语法。
2. 保证 `decision_web` 生产镜像可构建，不再把“页面本地 build 成功”误判为“容器可部署”。

本批次验收标准：

1. `docker build ./services/decision/decision_web` 不再停在 `COPY --from=builder /app/public ./public`。
2. 不扩展到 `docker-compose.dev.yml`、`.dockerignore` 或页面业务代码。

#### 补充批次 H1：策略仓库与审批状态持久化

- 批次标识：`TASK-0021-H1`
- 执行 Agent：决策 Agent
- 保护级别：**P1**
- 是否可并行：可与 `H0` / `H3` 并行；不可与 `H2` 并行

业务白名单：

1. `services/decision/src/core/settings.py`
2. `services/decision/src/persistence/state_store.py`
3. `services/decision/src/strategy/repository.py`
4. `services/decision/src/api/routes/approval.py`
5. `services/decision/tests/test_state_persistence.py`

本批次目的：

1. 去掉 `StrategyRepository._store` 与 `_approvals` 纯内存状态。
2. 让策略包与审批记录在服务重启后可恢复，部署后可以连续操作而不是每次重启清空。

本批次验收标准：

1. 服务重启后，已导入策略包与审批记录仍可查询。
2. 策略仓库与审批接口不再只依赖进程内 `dict`。
3. 不新增 `.env.example` 变更。

#### 补充批次 H2：研究/回测资格持久化与模型门禁

- 批次标识：`TASK-0021-H2`
- 执行 Agent：决策 Agent
- 保护级别：**P1**
- 是否可并行：依赖 `H1`；不可与 `H1` 并行

业务白名单：

1. `services/decision/src/persistence/state_store.py`
2. `services/decision/src/gating/backtest_gate.py`
3. `services/decision/src/gating/research_gate.py`
4. `services/decision/src/model/router.py`
5. `services/decision/tests/test_gating.py`

本批次目的：

1. 持久化 `backtest_certificate` 与 `research_snapshot`。
2. 让 `model/router.route()` 调用真实 gate 对象，不再只做 ID 非空检查。

本批次验收标准：

1. 回测证书与研究快照在服务重启后仍存在。
2. `model/router.route()` 在证书缺失、快照缺失或状态失效时明确拒绝。
3. 不扩写到 publish 适配或前端页面。

#### 补充批次 H3：research 真实 data API 接入与运行依赖

- 批次标识：`TASK-0021-H3`
- 执行 Agent：决策 Agent
- 保护级别：**P1**
- 是否可并行：可与 `H0` / `H1` 并行；`H4` 依赖其完成

业务白名单：

1. `services/decision/pyproject.toml`
2. `services/decision/src/research/factor_loader.py`
3. `services/decision/tests/test_research.py`

本批次目的：

1. 去掉 `FactorLoader` 随机 `numpy` mock。
2. 对接 `data` 服务现有 `/api/v1/bars` 最小数据接口。
3. 补齐当前 research 模块已实际 import 但尚未声明的运行依赖。

本批次验收标准：

1. `FactorLoader.load()` 使用 `DATA_SERVICE_URL` 的真实 HTTP 数据，不再生成随机矩阵。
2. 上游不可用时返回显式失败，不再静默 mock 成功。
3. `poetry install --only main` 不再遗漏 `numpy`、`xgboost`、`optuna`、`shap`、`onnxruntime`、`onnxmltools` 等现有 research 模块运行依赖。

#### 补充批次 H4：signal/strategy publish 真闭环

- 批次标识：`TASK-0021-H4`
- 执行 Agent：决策 Agent
- 保护级别：**P1**
- 是否可并行：依赖 `H2` 与 `H3`；在本轮命名空间冻结后可与 `TASK-0023-A` 并行

业务白名单：

1. `services/decision/src/api/routes/strategy.py`
2. `services/decision/src/api/routes/signal.py`
3. `services/decision/src/publish/gate.py`
4. `services/decision/src/publish/sim_adapter.py`
5. `services/decision/tests/test_publish.py`

本批次目的：

1. 让 `/signals/review` 不再固定返回 `hold` / `manual_review` 占位值。
2. 在 `strategy` 路由补最小发布入口，真正调用 `PublishExecutor`，而不是只停留在仓库创建/读取。
3. 让 `PublishGate` 重验持久化后的 backtest / research 资格。
4. 把 decision → sim-trading 的下游路径冻结到 `sim-trading` 既有命名空间 `/api/v1/strategy/publish`，并把 404 视为失败而非成功降级。

本批次验收标准：

1. `review_signal` 输出随真实 gate 结果变化，不再固定为占位值。
2. decision 侧存在可调用的最小发布入口，失败时返回真实失败状态。
3. `PublishGate` 会因为回测证书 / 研究快照无效而拒绝发布。
4. 下游路由缺失或拒绝时，decision 返回失败，不再伪造 `success=True`。

#### 补充批次 H5：decision_web rewrites 收口

- 批次标识：`TASK-0021-H5`
- 执行 Agent：决策 Agent
- 保护级别：**P1**
- 是否可并行：可独立推进；不得与新的 decision_web 页面改动或部署批次混写

业务白名单：

1. `services/decision/decision_web/next.config.mjs`

本批次目的：

1. 收口 decision_web → decision 的 `/api/decision/:path*` rewrite 规则。
2. 把默认后端入口冻结为 `http://localhost:8104`，并保留 `BACKEND_BASE_URL` 可覆盖机制。
3. 避免把当前 rewrite 历史脏改继续挂在 `H0` Dockerfile 单文件结论或其他后端批次名下。

本批次验收标准：

1. rewrite 仅覆盖 `/api/decision/:path* -> ${BACKEND_BASE_URL ?? http://localhost:8104}/:path*`。
2. 不扩展到 Dockerfile、compose、`.env.example`、页面代码或后端代码。
3. `decision_web` 读取 next 配置时不因该文件报错，且本地最小构建/诊断口径保持可用。

### 2026-04-09 decision 临时看板真数据化补批裁决

1. 基于 `TASK-0021-H0`~`H5` 已完成终审并锁回的既有事实，decision 临时看板去 mock + API 收口继续归属 `TASK-0021`，新增补充批次 `H6` 与 `H7`，**不新开第二个 decision 主任务**。
2. 当前架构口径继续冻结为：临时看板收口继续使用 `services/decision/decision_web/**`，**不进入 `services/dashboard/**`**；dashboard 聚合看板仍保留为后续独立任务。
3. 当前明确排除：`services/dashboard/**`、`services/decision/decision_web/next.config.mjs`、`services/decision/decision_web/package.json`、`services/decision/decision_web/Dockerfile`、`services/decision/src/api/routes/approval.py`、`services/decision/src/publish/**`、`services/decision/.env.example`、`docker-compose.dev.yml`、`shared/contracts/**` 与任一跨服务目录。
4. 当前推荐顺序冻结为：`H6` → `H7`；`H7` 依赖 `H6`，且两批不得复用 `H4` / `H5` 或 dashboard 历史白名单顺手执行。

#### 补充批次 H6：decision 临时看板只读聚合口

- 批次标识：`TASK-0021-H6`
- 执行 Agent：决策 Agent
- 保护级别：**P1**
- 是否可并行：建议最先签发；`H7` 依赖其完成

业务白名单：

1. `services/decision/src/api/routes/strategy.py`
2. `services/decision/src/api/routes/signal.py`
3. `services/decision/src/api/routes/model.py`
4. `services/decision/src/notifier/dispatcher.py`
5. `services/decision/src/reporting/daily.py`

本批次目的：

1. 为 decision 临时看板补最小只读聚合口，不再要求前端继续消费本地 mock 数据。
2. 把策略仓库、信号审阅、模型因子、通知日报等只读数据统一收口到 `services/decision/**` 单服务范围。
3. 明确本轮只做 decision 单服务读模型收口，不触碰 publish、审批或跨服务实现。

本批次验收标准：

1. 临时看板所需核心只读数据由 `services/decision/**` 内最小聚合口提供，不再依赖前端 mock 常量。
2. 不扩展到 `services/decision/src/api/routes/approval.py`、`services/decision/src/publish/**`、`services/dashboard/**` 或任一跨服务目录。
3. 不触碰 `decision_web` 的 `next.config.mjs`、`package.json`、`Dockerfile`、`.env.example`、`docker-compose.dev.yml` 或 `shared/contracts/**`。

#### 补充批次 H7：decision_web 去 mock 与布局收口

- 批次标识：`TASK-0021-H7`
- 执行 Agent：决策 Agent
- 保护级别：**P1**
- 是否可并行：依赖 `H6`；不可与 `H6` 并行

业务白名单：

1. `services/decision/decision_web/lib/api.ts`
2. `services/decision/decision_web/app/page.tsx`
3. `services/decision/decision_web/components/decision/overview.tsx`
4. `services/decision/decision_web/components/decision/strategy-repository.tsx`
5. `services/decision/decision_web/components/decision/signal-review.tsx`
6. `services/decision/decision_web/components/decision/models-factors.tsx`
7. `services/decision/decision_web/components/decision/research-center.tsx`
8. `services/decision/decision_web/components/decision/notifications-report.tsx`
9. `services/decision/decision_web/components/decision/config-runtime.tsx`

本批次目的：

1. 去掉 decision_web 临时看板中的本地 mock 数据与硬编码占位流程。
2. 统一接入 `H6` 提供的 decision 单服务只读聚合口，并完成首页与 7 个决策页面的布局收口。
3. 明确该批次仍属于 `decision_web` 临时看板真数据化，不转入 `services/dashboard/**` 聚合看板。

本批次验收标准：

1. 上述 9 个前端文件通过 `lib/api.ts` 消费真实 decision 只读聚合口，不再内置 mock 数据源。
2. 不扩展到 `services/decision/decision_web/next.config.mjs`、`services/decision/decision_web/package.json`、`services/decision/decision_web/Dockerfile`。
3. 不触碰 `services/dashboard/**`、`services/decision/src/api/routes/approval.py`、`services/decision/src/publish/**`、`services/decision/.env.example`、`docker-compose.dev.yml`、`shared/contracts/**` 或任一跨服务目录。

#### 跨服务拆任务协同说明

1. `TASK-0021-H4` 只修正 decision 侧发布入口与 adapter 命名空间，不写 `services/sim-trading/**`。
2. sim-trading 接收端独立拆为 `TASK-0023-A`；本轮只允许消费 `strategy_package.md` 已冻结字段，不得私增跨服务字段。

---

## 七、Token / 保护级别策略

1. 当前轮次：P-LOG，仅治理账本，不申请代码 Token。
2. 后续批次 A：`shared/contracts/**`，**P0**。
3. 后续批次 B：`integrations/legacy-botquant/**`，**P0**。
4. 后续批次 C、D：`services/decision/**`，**P1**。
5. 后续批次 E：`services/dashboard/**`，**P1**。
6. 后续批次 F：`services/decision/**` 通知体系，**P1**。
7. 任意 `.env.example` 改动，必须另拆 **P0** 批次。
8. `TASK-0021-H0` 为 `services/decision/decision_web/Dockerfile` 单文件 **P0**。
9. `TASK-0021-H1`、`H2`、`H3`、`H4`、`H5`、`H6`、`H7` 均为 **P1**，其中 `H1` / `H2` 共享 `state_store.py`，不得并行混写，`H7` 依赖 `H6`。
10. `TASK-0023-A` 为独立 sim-trading 单服务 **P1** 任务，不得借用 `H4` 白名单。

---

## 八、当前轮次验收标准

1. 已确认本事项必须独立建为 `TASK-0021`。
2. 已冻结 `TASK-0021` 与 `TASK-0016`、`TASK-0012` 的边界。
3. 已冻结当前轮次白名单仅限治理账本区，全部代码目录继续锁定。
4. 已冻结未来最小拆批、保护级别与执行顺序。
5. 已冻结决策端清洗原则、模型矩阵、研究主线、因子/回测门禁、7 页看板结构与策略仓库动作。
6. 已明确当前轮次不申请代码 Token，不进入任何代码实施。

---

## 九、交接给决策 Agent 前必须满足的前置条件

1. Atlas 必须先完成 `task / review / lock / rollback / handoff` 五份账本建档。
2. 项目架构师必须同步公共项目提示词到“已预审、未执行、待首批文件级白名单”的状态。
3. 首份交接单的性质必须冻结为“只读拆解与首批白名单草案”，不是实施指令。
4. 交接单必须先明确 legacy 四分法清单：保留迁移、清洗重写、删除淘汰、暂留兼容。
5. 交接单必须先明确跨服务归属矩阵与首批候选批次文件范围。
6. 未建白名单、未签 Token、未获实施口径前，决策 Agent 不得进入写操作。

---

## 十、预审结论

1. **`TASK-0021` 正式成立。**
2. **本轮只做立项、治理和拆批冻结，不进入代码实施。**
3. **下一检查点不是写代码，而是冻结首批契约批次的文件级白名单与 Token 申请草案。**
4. **基于实际代码结构，decision 收口继续挂在 `TASK-0021` 下新增 `H0`~`H7` 补充批次，不新开第二个 decision 任务。**
5. **`sim-trading` 发布接收接口必须拆成独立 `TASK-0023`，不得并入 `TASK-0021`。**
6. **当前既有事实为 `H0`~`H5` 已锁回；本次新增 `H6` / `H7` 已完成预审待签发，且明确属于 `decision_web` 临时看板真数据化，不属于 `services/dashboard/**` 聚合看板。**