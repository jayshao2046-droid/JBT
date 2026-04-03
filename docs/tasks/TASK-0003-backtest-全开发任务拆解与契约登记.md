# TASK-0003 回测服务全开发 — 在线回测引擎、REST API 与看板启动

## 任务信息

- 任务 ID：TASK-0003
- 任务名称：回测服务全开发 — 在线回测引擎、REST API 与看板启动
- 所属服务：services/backtest（跨越 P0 契约区与 P1 服务区）
- 执行 Agent：
  - 项目架构师（阶段一：契约草稿与 P0 正式写入）
  - 回测 Agent（阶段二：Python 后端、在线回测引擎、部署骨架；阶段三：看板 API 联调）
- 前置依赖：
  - TASK-0001 已完全闭环：✅（提交 `c849c9e`）
  - TASK-0002 阶段一草稿与自校验已完成：✅（提交 `8f921b2`）
  - 回测 Agent 首轮资料研读与方案准备已完成：✅（见 `docs/handoffs/回测端-首轮方案准备交接单.md`）
  - Jay.S 已确认回测端为 TASK-0002 闭环后第一优先级：✅（见总控派发提示词）
- 允许修改文件白名单：
  - `docs/tasks/TASK-0003-*.md`（本文件，P-LOG 区）
  - `docs/reviews/TASK-0003-review.md`（P-LOG 区）
  - `docs/locks/TASK-0003-lock.md`（P-LOG 区）
  - `docs/rollback/TASK-0003-rollback.md`（P-LOG 区）
  - `docs/handoffs/TASK-0003-*.md`（P-LOG 区）
  - `docs/prompts/公共项目提示词.md`（P-LOG 区）
  - `docs/prompts/agents/项目架构师提示词.md`（P-LOG 区）
  - `docs/prompts/agents/回测提示词.md`（P-LOG 区，回测 Agent 自写）
  - `shared/contracts/drafts/backtest/`（草稿区，当前批次可写，无需 Token）
  - `shared/contracts/backtest/`（P0 区，**需 Jay.S 为项目架构师签发 P0 Token**）
  - `services/backtest/src/`（P1 区，**按批次单独申请 P1 Token，回测 Agent 执行**）
  - `services/backtest/configs/`（P1 区，**需 P1 Token**，随批次 C）
  - `services/backtest/Dockerfile`（P1 区，随批次 C）
  - `services/backtest/requirements.txt`（P1 区，随批次 C）
  - `services/backtest/README.md`（P1 区，口径修正，随批次 A 一并执行）
  - `docker-compose.dev.yml`（P0 区，**批次 C 前单独申请 P0 Token**）
  - `services/backtest/.env.example`（P0 区，**Q2 确认后单独申请 P0 Token**）
- 是否需要 Token：
  - `docs/`、草稿区：否
  - `shared/contracts/backtest/`：是（P0）
  - `services/backtest/src/`、`configs/`、`Dockerfile`、`requirements.txt`：是（P1，分批）
  - `docker-compose.dev.yml`、`services/backtest/.env.example`：是（P0，单独申请）
- 计划验证方式：
  - 阶段一：四份草稿自校验通过，P0 Token 申请清单完整
  - 批次 A：GET /api/v1/health 返回 200 OK
  - 批次 B：POST /api/v1/jobs 触发在线回测任务并可查询结果
  - 批次 C：Docker 镜像可构建，容器内健康检查通过
- 当前状态：待 P0 Token（阶段一草稿与自校验已完成）

---

## 强制约束（来自回测 Agent 首轮方案准备交接单）

1. **回测必须重开发**，不得直接搬运 legacy J_BotQuant 本地数据回测链路。
2. 回测主入口必须遵循 TqSdk 官方模式：
   - `TqApi(TqSim(), backtest=TqBacktest(start_dt=..., end_dt=...), auth=TqAuth(...))`
3. 策略循环必须使用官方接口：`wait_update()`、`get_quote()`、`get_kline_serial()`、`is_changing()`，持仓控制优先采用 `TargetPosTask`。
4. **回测必须是在线回测**，不依赖本地历史数据文件作为默认来源。
5. Python 3.9（与 TqSdk 兼容，对齐 legacy 环境）。

---

## 任务目标

### 阶段一：契约登记（项目架构师执行）

在 `shared/contracts/drafts/backtest/` 完善以下四份草稿：
1. `backtest_job.md` — 回测任务配置模型（含状态机）
2. `backtest_result.md` — 回测结果模型
3. `performance_metrics.md` — 绩效指标模型
4. `api.md` — backtest 服务 REST API 端点清单（7 个 MVP 端点）

草稿通过自校验后，申请 P0 Token，迁入 `shared/contracts/backtest/`，完成阶段一终审与锁回。

### 阶段二：Python 后端与部署骨架（回测 Agent 执行，分批次）

**批次 A — 后端入口骨架（P1 Token，5 文件）**
1. `services/backtest/src/main.py` — FastAPI 服务入口
2. `services/backtest/src/api/app.py` — CORS + 路由注册
3. `services/backtest/src/api/routes/health.py` — 健康检查端点
4. `services/backtest/src/api/routes/jobs.py` — 回测任务 CRUD 路由
5. `services/backtest/src/core/settings.py` — 环境变量配置模型

同批修正 `services/backtest/README.md` 中"离线研究与评估"描述错误为"在线回测引擎"。

**批次 B — 在线回测引擎（P1 Token，5 文件）**
1. `services/backtest/src/backtest/session.py` — TqSdk 会话管理（TqAuth + TqBacktest 注入）
2. `services/backtest/src/backtest/runner.py` — 回测任务执行器（异步任务管理）
3. `services/backtest/src/backtest/strategy_base.py` — 策略基类（含 TargetPosTask 封装）
4. `services/backtest/src/backtest/result_builder.py` — 结果归纳与绩效指标计算
5. `services/backtest/tests/test_health.py` — 健康检查单元测试

**批次 C — 部署骨架（P1 + 部分 P0，需单独预审）**
1. `services/backtest/Dockerfile`（P1）
2. `services/backtest/requirements.txt`（P1）
3. `services/backtest/configs/logging.yaml`（P1）
4. `services/backtest/configs/backtest.default.yaml`（P1）
5. `services/backtest/.env.example` 修改（P0，需单独 Token） + `docker-compose.dev.yml` 修改（P0，需单独 Token）

### 阶段三：看板 API 联调（待 Jay.S 单独确认）

- 参考 `services/backtest/V0-backtext 看板/` 中的 Next.js 原型（5 个视图页面）
- 将看板前端与后端 API 端点对接（批次 A/B 完成后）
- **本阶段在 Jay.S 单独给出调整要求后独立派发，不与阶段二混并**

---

## 待 Jay.S 确认事项（批次 A/B 开发前必须确认）

| 编号 | 问题 | 影响范围 |
|---|---|---|
| Q1 | 首个可运行策略模板：最小 SMA+TargetPosTask 官方示例，还是用户上传参数+固定策略模板？ | 决定 strategy_base.py 接口设计 |
| Q2 | TqAuth 认证凭证注入方式（决定 .env.example 字段，影响 P0 申请范围） | 影响批次 C 前的 P0 申请 |
| Q3 | `V0-backtext 看板/` 目录是否改名为 `dashboard/`（P1 操作，影响 Dockerfile 路径） | 阶段三目录结构 |
| Q4 | 阶段三看板联调：作为 TASK-0003 子阶段，还是独立 TASK-0004？ | 任务边界 |
| Q5 | 回测结果首阶段持久化方式：JSON+Parquet（沿用 legacy 归档模式）还是 SQLite/DuckDB？ | result_builder.py 设计 |

---

## 交付标准

- [ ] 阶段一：四份草稿完成并通过自校验，P0 Token 申请清单完整可执行
- [ ] 阶段一：P0 Token 获取后，契约迁入正式目录，终审通过并锁回
- [ ] 批次 A：服务可本地启动，GET /api/v1/health 返回 200 OK
- [ ] 批次 B：POST /api/v1/jobs 可触发在线回测任务，GET /api/v1/results/{job_id} 可返回绩效结果
- [ ] 批次 C：Docker 镜像构建通过，容器内健康检查通过
- [ ] 阶段三：待 Jay.S 确认 Q4 后补填
- [ ] 全程无跨服务目录读写，无旧系统代码直接搬运
