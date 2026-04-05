# TASK-0003 Phase1 回测服务正式建档

## 文档信息

- 任务 ID：TASK-0003（Phase1 正式建档子文档）
- 文档类型：阶段建档（Phase1 索引文件，与 `TASK-0003-backtest-全开发任务拆解与契约登记.md` 互为补充）
- 签名：项目架构师
- 建档时间：2026-04-03
- 设备：MacBook
- 授权来源：Jay.S 2026-04-03 口头批准回测端正式建档，含五条设计决策 D-BT-01~05

---

## 一、Jay.S 已确认设计决策（D-BT-01 ～ D-BT-05）

以下五条为 Jay.S 正式确认的回测架构约束，所有 agent 均须严守，不得覆盖或绕过。

### D-BT-01 资产类型

- 第一阶段只支持期货回测，核心入口采用 `TqSim()` + `TqBacktest`。
- 股票适配器安装但不启用，保留扩展接口，等 Jay.S 后续单独启用。
- 回测 Agent 不得擅自在批次 A/B 中引入股票相关分支逻辑。

### D-BT-02 环境变量（.env）整合

- 以 `J_BotQuant/.env.example` 为基础字段参考，为 `services/backtest/` 更新 `.env.example`。
- 所有 agent 只读 `.env.example`，绝不读取真实 `.env` 文件，真实 `.env` 永不进 Git。
- `J_BotQuant/.env.example` 中的 `TUSHARE_TOKEN` 含有真实 Token，整合时必须替换为 `<your-tushare-token>`。
- 本决策同时解锁 Q2（TqAuth 认证方式），`.env.example` 已由 Jay.S 在本次建档授权更新。

### D-BT-03 策略模板与风控

- Jay.S 提供符合 `TqBacktest` 规范的固定策略模板。
- 策略运行参数由用户上传，并与风控参数一起放入同一个 YAML 文件。
- 该 YAML 文件中包含所有风控指标（止损比例、最大回撤、仓位上限等）。
- 所有回测必须严格从 YAML 策略文件读取风控参数，**禁止硬编码任何风控指标**。
- 风控参数读取与校验逻辑必须在配置层实现，优先级高于代码内置值。
- 批次 A/B 实现时须预留 YAML 策略文件读取接口，不可写死默认参数。
- 契约口径统一为“固定模板 + 用户上传参数 + 一体化 YAML 风控文件”。

### D-BT-04 回测结果与策略推送流程

- 回测结果输出完整报告（权益曲线、绩效指标、风控日志等）。
- **策略必须先在回测端完成回测并通过审核后，才能推送给决策端使用。**
- 回测端须实现"策略推送接口"（backtest → decision 跨服务契约）。
- **本轮（Phase1 建档）只登记跨服务契约需求，不写入 `shared/contracts/`。**
- 跨服务契约在批次 B 完成后由项目架构师单独在 `shared/contracts/drafts/backtest-to-decision/` 建档，须另行预审。

### D-BT-05 部署架构

- 回测后端服务 + 独立回测看板，部署在同一台独立设备上。
- 两个容器（后端 + 看板）放在**同一 docker-compose** 编排内。
- 该独立设备不与主 Studio/Mini 混部，具体主机由 Jay.S 后续指定。
- 批次 C 的 `docker-compose.dev.yml` 修改须单独申请 P0 Token，不随批次 C 代码并入。

---

## 二、三批次任务划分

### 批次 A — 后端入口骨架（P1 Token，5 文件 + README 修正）

| # | 文件 | 说明 |
|---|---|---|
| 1 | `services/backtest/src/main.py` | FastAPI 服务入口 |
| 2 | `services/backtest/src/api/app.py` | CORS + 路由注册 |
| 3 | `services/backtest/src/api/routes/health.py` | 健康检查端点 |
| 4 | `services/backtest/src/api/routes/jobs.py` | 回测任务 CRUD 路由 |
| 5 | `services/backtest/src/core/settings.py` | 环境变量配置模型（读取 .env.example 声明字段） |
| + | `services/backtest/README.md` | 口径修正（随批次 A 一并执行，已含入本次 P1 Token 申请范围） |

**Token 类型**：`services/backtest/**` P1 Token（由 Jay.S 签发给回测 Agent）

**验证标准**：`GET /api/v1/health` 返回 200 OK

**当前口径**：Q1 已确认首个可运行策略采用“固定模板 + 用户上传参数”；Q-NEW 已确认采用“策略参数 + 风控参数一体单文件 YAML”。

### 批次 B — 在线回测引擎（P1 Token，5 文件）

| # | 文件 | 说明 |
|---|---|---|
| 1 | `services/backtest/src/backtest/session.py` | TqSdk 会话管理（TqAuth + TqBacktest 注入） |
| 2 | `services/backtest/src/backtest/runner.py` | 回测任务执行器（异步任务管理） |
| 3 | `services/backtest/src/backtest/strategy_base.py` | 策略基类（含 TargetPosTask 封装） |
| 4 | `services/backtest/src/backtest/result_builder.py` | 结果汇总与绩效指标计算 |
| 5 | `services/backtest/tests/test_health.py` | 健康检查单元测试 |

**Token 类型**：`services/backtest/**` 批次 B P1 Token（单独申请）

**验证标准**：`POST /api/v1/jobs` 触发在线回测任务，`GET /api/v1/results/{job_id}` 可返回绩效结果

### 批次 C — 部署骨架（P1 + P0，需单独预审）

| # | 文件 | 类型 | Token |
|---|---|---|---|
| 1 | `services/backtest/Dockerfile` | P1 | 批次 C P1 Token |
| 2 | `services/backtest/requirements.txt` | P1 | 批次 C P1 Token |
| 3 | `services/backtest/configs/logging.yaml` | P1 | 批次 C P1 Token |
| 4 | `services/backtest/configs/backtest.default.yaml` | P1 | 批次 C P1 Token |
| 5 | `docker-compose.dev.yml` | P0 | **单独 P0 Token，不并入批次 C** |

**注意**：`docker-compose.dev.yml` 须在批次 C 开始前单独走 P0 预审流程。

---

## 三、当前阶段白名单（Phase1 建档）

本阶段（正式建档，Jay.S 直接授权）允许修改的文件：

### P-LOG 区（无需 Token）

- `docs/tasks/TASK-0003-backtest-Phase1-正式建档.md`（本文件）
- `docs/tasks/TASK-0003-backtest-全开发任务拆解与契约登记.md`
- `docs/reviews/TASK-0003-review.md`
- `docs/locks/TASK-0003-lock.md`
- `docs/rollback/TASK-0003-rollback.md`
- `docs/prompts/公共项目提示词.md`
- `docs/prompts/agents/项目架构师提示词.md`

### 服务根级文件（Jay.S 本次建档直接授权）

- `services/backtest/README.md`（已纳入批次 A 范围，随批次 A P1 Token 一并修正）
- `services/backtest/.env.example`（P0 文件，D-BT-02 授权，本次建档由架构师执行）

### P0 正式契约（Jay.S 本轮已签发 P0 Token）

- `shared/contracts/backtest/backtest_job.md`
- `shared/contracts/backtest/backtest_result.md`
- `shared/contracts/backtest/performance_metrics.md`
- `shared/contracts/backtest/api.md`

### 禁止写入（本阶段）

- `services/backtest/src/`、`tests/`、`configs/`、`backtest_web/`（等 P1 Token）
- `shared/contracts/backtest/` 白名单之外其他文件
- `shared/contracts/drafts/backtest-to-decision/`（D-BT-04，批次 B 后另行建档）
- `docker-compose.dev.yml`（等批次 C 前单独 P0 Token）

---

## 四、D-BT-04 跨服务契约需求登记

- 接口名称：策略推送接口（backtest → decision）
- 方向：回测端 `POST /api/v1/strategies/{strategy_id}/push` → 决策端
- 包含内容：通过回测的策略 ID、策略配置快照、最新绩效摘要
- 建档时机：批次 B 完成后，由项目架构师单独在 `shared/contracts/drafts/backtest-to-decision/` 建档
- 本轮状态：**仅登记需求，不写入 `shared/contracts/`**

---

## 五、Token 申请清单（Phase1）

| 目标文件/目录 | 类型 | 申请方 | 当前状态 |
|---|---|---|---|
| `shared/contracts/backtest/`（四份契约迁入） | P0 | 项目架构师 | ✅ 2026-04-03 已签发并完成 lockback |
| `services/backtest/**`（批次 A，含 README） | P1 | 回测 Agent | ✅ 已签发并完成锁回 |
| `services/backtest/**`（批次 B） | P1 | 回测 Agent | ✅ 已签发并完成锁回 |
| `services/backtest/**`（批次 C，不含 P0） | P1 | 回测 Agent | ⏳ 批次 B 完成后申请 |
| `docker-compose.dev.yml` | P0 | 项目架构师（或回测 Agent） | ⏳ 批次 C 前单独预审 |

---

## 六、Jay.S 已批准的自动推进顺序

1. 完成前期搭建。
2. 达到策略介入点后通知 Jay.S 提供策略。
3. 执行首轮真实回测。
4. Jay.S 审阅后再进入看板建设。
5. 看板完成后再做 Docker 和远端交付。

---

## 七、Phase1 交付确认

- [x] Jay.S 设计决策 D-BT-01~05 已登记并完整纳入账本
- [x] 三批次任务划分（批次 A/B/C）已确认文件清单
- [x] `services/backtest/.env.example` 已按 D-BT-02 更新（架构师执行）
- [x] `services/backtest/README.md` 已纳入批次 A 白名单（随 P1 Token 修正）
- [x] D-BT-04 跨服务契约需求已登记（本轮不写入 contracts）
- [x] `shared/contracts/backtest/` P0 Token 已签发，四份正式契约进入执行态
- [x] Q1 已确认：首个可运行策略采用“固定模板 + 用户上传参数”
- [x] Q-NEW 已确认：YAML 采用“策略参数 + 风控参数一体单文件”
- [x] `shared/contracts/backtest/` 四份正式契约已迁入正式目录
- [x] 批次 A P1 Token 已签发并完成锁回
- [x] `shared/contracts/backtest/` 四份正式契约已完成 lockback
- [x] 批次 B P1 Token 已签发并完成锁回
- [x] 已达到“需要策略输入”检查点，回测主线推进到 60%
