# TASK-0023 sim-trading decision 发布接口对接预审

## 文档信息

- 任务 ID：TASK-0023
- 文档类型：新任务预审与范围冻结
- 签名：项目架构师
- 建档时间：2026-04-08
- 设备：MacBook

---

## 一、任务目标

为 `sim-trading` 提供最小 decision 策略发布接收接口，使 decision 侧不再把 404 误判为发布成功，并把该事项严格冻结在 `services/sim-trading/**` 单服务边界内。

本任务当前轮次只做预审建档，不写任何 `services/**` 业务代码，不申请任何代码 Token。

---

## 二、任务编号与归属结论

### 编号结论

- **本事项必须新建独立任务 `TASK-0023`，不得并入 `TASK-0021`、`TASK-0017` 或 `TASK-0022`。**

### 判定理由

1. `TASK-0021` 的主归属是 decision 迁移主线；一旦把 `services/sim-trading/**` 发布接收接口塞回 `TASK-0021`，就会破坏跨服务回滚边界。
2. `TASK-0017` 的边界是 sim-trading Docker / Mini 部署，不承接新的业务 API 接口。
3. `TASK-0022` 的边界是 sim-trading 运行态 UI / 只读日志收口，不承接上游 decision 发布接收语义。

### 服务归属结论

- **任务归属：`services/sim-trading/**` 单服务范围。**
- **执行主体：模拟交易 Agent。**

---

## 三、当前轮次白名单与保护级别

### 当前 Git 白名单

1. `docs/tasks/TASK-0023-sim-trading-decision-发布接口对接预审.md`
2. `docs/reviews/TASK-0023-review.md`
3. `docs/locks/TASK-0023-lock.md`
4. `docs/handoffs/TASK-0023-sim-trading-发布接口预审交接单.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

### 当前保护级别

- **当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。**

### 当前轮次明确禁止

1. 不得修改 `services/sim-trading/**`。
2. 不得修改 `services/decision/**`。
3. 不得修改 `shared/contracts/**`。
4. 不得修改 `docker-compose.dev.yml`、任一 `.env.example` 或其他全部非白名单文件。
5. 不得申请或执行 `lockctl`。

---

## 四、只读现状与根因结论

1. decision 当前 `SimTradingAdapter` 仍指向 `/api/sim/v1/strategy/publish`，并把 404 当成成功降级。
2. `sim-trading` 当前真实 API 命名空间统一在 `/api/v1/**`，不存在任何策略发布接收接口。
3. `shared/contracts/decision/strategy_package.md` 与 `decision_result.md` 已冻结 `publish_target`、`publish_workflow_status` 等正式字段；本轮不需要先改 shared contract。
4. 因此，本轮正式治理裁决为：**sim-trading 接收端采用现有服务命名空间 `/api/v1/strategy/publish`，由 `TASK-0021-H4` 同步修正 decision 侧 adapter 命名空间，不新增跨服务临时字段。**

---

## 五、正式治理冻结

### 1. 接口边界

1. 接收端正式路径冻结为：`POST /api/v1/strategy/publish`。
2. 接口只接收 decision 已冻结的 `strategy_package` 正式字段，不私增跨服务临时字段。
3. 第一阶段只允许 `publish_target=sim-trading`；任何 `live-trading` 或未知目标都必须拒绝。

### 2. 本轮实现边界

1. 本轮只要求“接收 + 校验 + 确认回执”，不要求直接下单，不要求自动接入 CTP 交易流程。
2. 本轮不纳入 `.env.example`、compose、部署文件、看板页面、shared contract。
3. 若实施中证明必须新增第 3 个业务文件、必须修改 `.env.example`，或必须补 shared contract，本轮批次立即失效，必须回交补充预审。

---

## 六、批次拆分与白名单冻结

### 批次 A：最小发布接收接口

- 批次标识：`TASK-0023-A`
- 执行 Agent：模拟交易 Agent
- 保护级别：**P1**
- 是否需要 Token：**需要 P1 Token；不需要 P0 Token**
- 是否可并行：**可与 `TASK-0021-H4` 并行**

#### 业务白名单

1. `services/sim-trading/src/api/router.py`
2. `services/sim-trading/tests/test_strategy_publish_api.py`

#### 本批次目标

1. 在 `sim-trading` 现有 `/api/v1` 命名空间下提供最小策略发布接收接口。
2. 对 `publish_target`、策略包关键字段与响应语义做最小校验。
3. 返回可供 decision 判定“已接收 / 已拒绝”的正式回执，不再让上游依赖 404 或伪成功。

#### 本批次验收标准

1. `POST /api/v1/strategy/publish` 存在，且不再返回 404。
2. 当 `publish_target != sim-trading`、关键字段缺失或载荷非法时，接口返回显式 4xx 拒绝。
3. 当载荷合法时，接口返回 2xx 回执，并带 `strategy_id`、接收结果与时间戳等最小确认信息。
4. 本批次不触碰 `.env.example`、`docker-compose.dev.yml`、`shared/contracts/**` 或任何看板文件。

---

## 七、Token 策略

1. 当前任务只涉及 **P1** 服务文件。
2. `TASK-0023-A` 不得复用 `TASK-0021`、`TASK-0017`、`TASK-0022` 的任何白名单或 Token。
3. 若实施中要求把 publish 接收记录落到配置文件、数据库模板或 compose，本轮立即失效，必须另起 **P0** 补审。

---

## 八、当前继续锁定的路径

1. `services/decision/**`
2. `shared/contracts/**`
3. `services/sim-trading/.env.example`
4. `docker-compose.dev.yml`
5. `services/sim-trading/tests/**` 白名单外文件
6. 其他全部非白名单文件

---

## 九、预审结论

1. **`TASK-0023` 正式成立。**
2. **本事项正式归属 `services/sim-trading/**` 单服务范围，不并入 `TASK-0021`、`TASK-0017` 或 `TASK-0022`。**
3. **首轮冻结为 1 个 P1 批次：`TASK-0023-A`，仅处理最小策略发布接收接口。**
4. **当前轮次仅完成治理冻结，不进入代码执行，不申请 `lockctl`。**