# TASK-0015 dashboard SimNow 临时 Next.js 看板预审

## 文档信息

- 任务 ID：TASK-0015
- 文档类型：新任务预审与服务归属冻结
- 签名：项目架构师
- 建档时间：2026-04-06
- 设备：MacBook

---

## 一、任务目标

为 SimNow 主线建立独立的临时 Next.js 看板任务，冻结服务归属、只读边界与前端输入依赖。

本任务当前轮次只做预审，不写任何前端代码。

---

## 二、任务编号与归属结论

### 编号结论

- **D 临时看板对接必须新建独立任务 `TASK-0015`。**

### 判定理由

1. 当前仓内 backtest 看板任务 `TASK-0004` / `TASK-0008` 归属 `services/backtest/**`，不能承接 SimNow 临时看板。
2. SimNow 看板的页面、数据、权限与验收目标都不同于回测看板，混用会导致服务边界污染。
3. 临时看板仍应保持“看板服务负责只读聚合”的边界，不应反向把 Next.js 页面塞回 `services/sim-trading/**`。

### 服务归属结论

- **任务归属：`services/dashboard/**`。**
- **本任务明确不等于当前 backtest 看板任务。**

### 执行 Agent

1. 预审：项目架构师
2. 实施：看板 Agent

---

## 三、当前轮次白名单与保护级别

### 当前 Git 白名单

1. `docs/tasks/TASK-0015-dashboard-SimNow-临时Next.js看板预审.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/项目架构师提示词.md`

### 当前保护级别

- **当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。**

### 当前轮次明确禁止

1. 不得修改 `services/dashboard/**`。
2. 不得修改 `services/backtest/backtest_web/**`。
3. 不得修改 `services/sim-trading/**`。
4. 不得在前端页面中直接发起交易、清退、强平等写操作。

---

## 四、前置依赖

1. `TASK-0009` 的风控门槛与验收口径需在本任务进入代码执行前闭环。
2. `TASK-0013` 需先完成统一风控核心与阶段预设治理冻结。
3. `TASK-0010` 需先提供本看板所需的最小可读 API 面。
4. `TASK-0014` 需先冻结风险事件级别与通知口径。
5. Jay.S 已于 2026-04-06 提供本任务所需的前端参考材料，来源目录为 `services/sim-trading/参考文件/V0-模拟交易端 0406/`。

### 当前前端材料补录结论

1. 当前材料是一个完整的 Next.js 15 + React 19 参考原型。
2. 根页面 `app/page.tsx` 当前通过侧栏切换“风控监控 / 交易终端”两张主页面。
3. 当前 UI 结构可作为后续看板拆页与交互参考，重点参考页为 `app/intelligence/page.tsx` 风控监控页与 `app/operations/page.tsx` 交易终端页。
4. 正式实现归属仍然固定为 `services/dashboard/**`，不得把 `services/sim-trading/参考文件/**` 视为正式实现目录。
5. 当前材料只解除“缺前端材料”的输入阻塞，不自动获得任何代码白名单或 Token。

---

## 五、正式治理冻结

### 1. 看板边界

1. 看板只负责只读聚合，不得直接承接交易执行逻辑。
2. 看板必须显式标注当前 stage preset、风险状态、账户摘要、持仓摘要、订单摘要与通知状态。
3. 看板的目标是临时审阅与联调，不等于最终正式运营看板。

### 2. 明确不等价事项

1. 本任务不等于 `TASK-0004` backtest 看板两页收敛。
2. 本任务不等于 `TASK-0008` backtest 泛化引擎与报告导出前端链路。
3. 本任务不自动获得任何 backtest 页面、组件、白名单或 Token。
4. 本任务不自动复用 `services/sim-trading/参考文件/**` 中的代码路径、组件、依赖清单或构建配置。

### 3. 只读限制

1. 看板只允许调用已冻结的只读 API。
2. 看板不得绕过 `services/sim-trading/**` 直接读取账本、运行态目录、真实 `.env` 或数据库快照。
3. 看板若需要新增 API 字段，必须先回交预审，不得先写页面再补契约。

---

## 六、Token / 保护级别策略

1. 当前轮次：P-LOG，仅治理账本，不申请代码 Token。
2. 未来若修改 `services/dashboard/**` 前端业务文件：**P1**。
3. 未来若修改 `services/dashboard/.env.example`：**P0**。
4. 若新增跨服务只读契约到 `shared/contracts/**`：**P0**。

---

## 七、敏感信息治理

1. 看板不得存放或展示 SimNow 真实账号密码、通知凭证、签名密钥等 Secret。
2. 若前端需要环境变量，只能在 `.env.example` 中保留占位符与字段说明，不得写真实值。
3. 任何来自 J_BotQuant 的配置方案只能记录来源与注入方式，不得记录真实秘密值。

---

## 八、验收标准

1. 已冻结本任务归属 `services/dashboard/**`，不再与 backtest 看板混淆。
2. 已冻结临时看板的只读边界与输入依赖。
3. 已补录 Jay.S 提供的前端参考材料，并明确其只解除“缺前端材料”阻塞；在冻结 `services/dashboard/**` 文件级白名单与对应 Token 前，本任务仍不进入代码执行。
4. 已明确真实 Secret 不得进入前端仓库。

---

## 九、预审结论

Jay.S 明确：当前所有看板不在 `services/dashboard/` 服务端开发，先在本地建立临时看板进行验证。

### 变更结论

1. **本轮不启用 `services/dashboard/**` 路径，不申请 P1 Token。**
2. 临时看板直接基于 `services/sim-trading/参考文件/V0-模拟交易端 0406/` 在本地 `/tmp/jbt-sim-dashboard/` 独立运行。
3. 临时看板已于 2026-04-06 成功启动，访问地址：`http://localhost:3000`。
4. 不得将 `/tmp/jbt-sim-dashboard/` 的 node_modules、build 产物或运行态 log 写入 JBT Git 仓库。
5. 未来若需将临时看板迁移为正式 `services/dashboard/**` 实现，必须重新补充预审与 P1 Token。

### 当前临时看板状态

- 部署路径：`/tmp/jbt-sim-dashboard/`（本地临时，不入 Git）
- 启动命令：`cd /tmp/jbt-sim-dashboard && pnpm dev`
- 访问地址：`http://localhost:3000`
- 页面结构：侧边栏切换"风控监控 / 交易终端"，参考原型 Next.js 15 + React 19
- 后续对接：API 目标为 `services/sim-trading` 健康/状态端点（`localhost:8101`）

---

## 九、预审结论

1. **`TASK-0015` 正式成立。**
2. **D 临时看板对接不通过 `services/dashboard/**` 正式路径推进，而是在本地 `/tmp/jbt-sim-dashboard/` 临时运行验证。**
3. **Jay.S 已提供前端参考材料，临时看板已成功启动，访问地址 `http://localhost:3000`。**
4. **临时看板不入 Git，不申请代码 Token；未来若迁移到正式 `services/dashboard/**`，必须重新预审与解锁。**