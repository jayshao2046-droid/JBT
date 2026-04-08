# TASK-0022 sim-trading 运行态交互收口与只读日志预审

## 文档信息

- 任务 ID：TASK-0022
- 文档类型：新任务预审与范围冻结
- 签名：项目架构师
- 建档时间：2026-04-08
- 设备：MacBook

---

## 一、任务目标

为 sim-trading 当前新增的 4 个运行态问题建立独立预审任务，冻结服务归属、字段边界、最小白名单与只读日志查看的最小实现范围。

本任务当前轮次只做预审建档，不写任何 `services/**` 业务代码，不申请任何代码 Token。

本任务收口的 4 项需求为：

1. 快速下单“品种”自动补齐只显示期货合约，不再混入期权或杂项字段。
2. 账户金额主卡片按“本地虚拟盘总本金 50 万”口径展示；CTP / SimNow 真实账户余额只能作为次级快照信息。
3. 风控监控页 L2 日内盈亏曲线下方红线 / 黄线说明居中收口，并写清触发含义。
4. “查看日志 / 参看日志”必须补最小只读日志查看能力，不再继续 toast 占位。

---

## 二、任务编号与归属结论

### 编号结论

- **本事项独立建档为 `TASK-0022`，不得并入 `TASK-0017`。**

### 判定理由

1. `TASK-0017` 已冻结为 Docker 化、Mini 部署与开盘验证事项；当前 4 项均属于 sim-trading 运行态 UI / API 行为修正，不是部署治理续批。
2. 若并入 `TASK-0017`，会把“部署验证”和“新一轮服务行为改动”混成同一回滚单元，违反“一件事一审核一上锁”。
3. 当前问题与 `TASK-0020` 的 ECS / 域名入口、`TASK-0014` 的通知链路、`TASK-0019` 的收盘报表也都不是同一事项，不能复用其白名单或 Token。

### 对 `TASK-0015` 的归属裁决

1. `TASK-0015` 历史文档冻结的是 dashboard 正式归属与 `/tmp` 临时看板验证口径，不等于当前仓内真实运行的 sim-trading 控制台。
2. 当前实际前端代码位于 `services/sim-trading/sim-trading_web/**`，并且直接消费 `services/sim-trading/src/api/router.py` 提供的单服务 API。
3. 因此，本轮归属明确裁定为：**`services/sim-trading/**` 单服务范围**，不走 `services/dashboard/**`，也不复用 `TASK-0015`。
4. `TASK-0015` 继续保留为历史临时看板治理留痕，不自动获得当前任务的任何白名单或 Token。

### 服务归属结论

- **任务归属：`services/sim-trading/**` 单服务范围。**
- **当前前端落点：`services/sim-trading/sim-trading_web/**`。**
- **当前后端落点：`services/sim-trading/src/**`。**

### 执行 Agent

1. 预审：项目架构师
2. 实施：模拟交易 Agent

---

## 三、当前轮次白名单与保护级别

### 当前 Git 白名单

1. `docs/tasks/TASK-0022-sim-trading-运行态交互收口与只读日志预审.md`
2. `docs/reviews/TASK-0022-review.md`
3. `docs/locks/TASK-0022-lock.md`
4. `docs/handoffs/TASK-0022-sim-trading-运行态交互预审交接单.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

### 当前保护级别

- **当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。**

### 当前轮次明确禁止

1. 不得修改 `services/sim-trading/**`。
2. 不得修改 `services/dashboard/**`。
3. 不得修改 `shared/contracts/**`。
4. 不得修改 `docker-compose.dev.yml`、任一 `.env.example` 或其他全部非白名单文件。
5. 不得申请或执行 `lockctl`。

---

## 四、只读现状与根因结论

基于当前仓内只读复核，冻结以下现状结论：

1. `services/sim-trading/sim-trading_web/app/operations/page.tsx` 当前把 `ALL_CONTRACTS` 与 `/api/v1/ticks` 返回的键集合并为自动补齐候选，输入匹配逻辑为包含匹配，缺少“期货合约专属过滤”。
2. `services/sim-trading/src/gateway/simnow.py` 当前近月合约发现逻辑按 `InstrumentID` 尾部 4 位数字提取到期月，存在把期权样式代码误判为期货近月合约的风险；用户已给出例子 `MA605P2650`。
3. `services/sim-trading/src/api/router.py` 当前 `/api/v1/account` 直接把 CTP 返回的 `balance` 暴露为 `equity`；`services/sim-trading/sim-trading_web/app/operations/page.tsx` 又直接以该字段渲染“动态权益”主卡片，因此真实 CTP 账户余额被误展示为系统主权益口径。
4. `services/sim-trading/sim-trading_web/app/intelligence/page.tsx` 当前 L2 警戒线说明分散在曲线下方左右两侧，触发含义不明确；同页“查看日志”按钮仍是 toast 占位，不具备任何只读查看能力。
5. `shared/contracts/sim-trading/account.md` 当前定义的是跨服务账户快照契约；本轮问题属于 sim-trading 单服务内部 UI / API 收口，**当前不进入 `shared/contracts/**`**。若后续要把“本地虚拟盘主卡片 / CTP 快照”正式上升为跨服务契约，再另行发起 P0 补充预审。

---

## 五、正式治理冻结

### 1. 自动补齐边界

1. 快速下单自动补齐必须只显示期货合约候选。
2. 不得继续显示期权样式代码、执行中间态键名、产品分组占位值或其他杂项字段。
3. 当前问题不允许只做前端文案遮挡；至少要把“候选集来源”收口到期货合约范围，避免 `MA605P2650` 一类值继续进入候选链路。

### 2. 主卡片与 CTP 快照字段边界

1. **主卡片** 冻结为“本地虚拟盘总本金 50 万”口径，对应当前 stage preset `sim_50w`。
2. 当前批次不要求实现新的本地账本结算引擎；若本地虚拟盘动态权益暂不可得，主卡片至少应展示固定本金 `500000 CNY`，不得再把 CTP `balance` 当作系统主权益。
3. 所有直接来源于 CTP / SimNow 的 `balance`、`available`、`margin`、`margin_rate`、`floating_pnl`、`close_pnl`、`commission` 等字段，只能归入 **CTP 快照 / CTP 账户快照** 次级展示区。
4. 本轮明确禁止继续把真实账户资金包装为“系统权益”“本地虚拟盘权益”或其他主口径字段。

### 3. L2 曲线说明口径

1. 警告线与熔断线说明必须居中收口到曲线下方同一视觉组。
2. 文案必须明确写出阈值来源和触发动作，例如“触碰暂停交易”“触碰强制平仓”。
3. 本轮只收口说明位置与注释，不扩展新的风控规则。

### 4. 最小只读日志查看口径

1. 本轮“查看日志 / 参看日志”只允许实现 **最小只读** 能力。
2. 建议最小实现为：在 `src/main.py` 内挂一个进程内循环缓冲日志 handler，在 `src/api/router.py` 暴露最近若干行的只读端点，由 `app/intelligence/page.tsx` 拉取并展示。
3. **禁止** 提供文件路径参数、目录浏览、下载、删除、清空、执行或任何写操作。
4. **禁止** 直接把 `services/sim-trading/logs/**` 或其他运行态目录开放为可遍历资源。
5. 若 Jay.S 要求“跨容器持久日志”“按文件名查看历史日志”“下载日志文件”，当前最小批次立即失效，必须重新补充预审。

---

## 六、批次拆分与白名单冻结

根据“单批尽量不超过 5 个业务文件”的约束，当前建议拆为 2 个 P1 批次，默认顺序执行。

### 批次 A：自动补齐 + 账户口径 + L2 说明收口

- 批次标识：`TASK-0022-A`
- 执行 Agent：模拟交易 Agent
- 保护级别：**P1**
- 是否需要 Token：**需要 P1 Token；不需要 P0 Token**
- 是否可并行：**不可与批次 B 并行**

#### 业务白名单

1. `services/sim-trading/src/api/router.py`
2. `services/sim-trading/src/gateway/simnow.py`
3. `services/sim-trading/sim-trading_web/app/operations/page.tsx`
4. `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`
5. `services/sim-trading/tests/test_console_runtime_api.py`

#### 本批次目标

1. 把自动补齐候选集收口为期货合约。
2. 把“主卡片 = 本地虚拟盘 50 万”“CTP 数值 = 次级快照”的展示边界冻结并落地。
3. 把 L2 红线 / 黄线说明集中化，并写清触发含义。

#### 本批次验收标准

1. 输入 `P2` 或其他期权样式前缀时，不再出现 `MA605P2650` 一类期权 / 杂项候选。
2. `services/sim-trading/sim-trading_web/app/operations/page.tsx` 不再把 CTP `balance` 作为主卡片“系统权益 / 动态权益”直接展示。
3. 页面主卡片明确显示“本地虚拟盘总本金 50 万”或同义口径；真实 CTP 账户数值被降级为“CTP 快照 / 账户快照”。
4. `services/sim-trading/sim-trading_web/app/intelligence/page.tsx` 的 L2 曲线说明位置集中、文案清晰，且不引入新的风控规则。
5. 未触碰 `shared/contracts/**`、`.env.example`、`docker-compose.dev.yml` 或其他白名单外文件。

### 批次 B：最小只读日志查看

- 批次标识：`TASK-0022-B`
- 执行 Agent：模拟交易 Agent
- 保护级别：**P1**
- 是否需要 Token：**需要 P1 Token；不需要 P0 Token**
- 是否可并行：**不可与批次 A 并行**

#### 业务白名单

1. `services/sim-trading/src/main.py`
2. `services/sim-trading/src/api/router.py`
3. `services/sim-trading/sim-trading_web/app/intelligence/page.tsx`
4. `services/sim-trading/tests/test_log_view_api.py`

#### 本批次目标

1. 为 sim-trading 当前进程补最小只读日志缓冲。
2. 提供最近若干行日志的只读查询接口。
3. 把 intelligence 页的“查看日志”从 toast 占位替换为真实只读查看面板。

#### 本批次验收标准

1. “查看日志 / 参看日志”按钮不再只弹 toast。
2. 前端可以读取并展示后端最近若干行日志，具备加载中 / 空状态 / 失败态。
3. 后端接口不接受文件路径参数，不暴露目录遍历，不提供写操作。
4. 日志查看仅限当前服务的只读最近日志，不扩展为通用文件浏览器。

---

## 七、Token 策略

1. 当前任务 **仅涉及 P1 服务文件**；批次 A 与批次 B 都不需要 P0 Token。
2. `services/sim-trading/src/api/router.py` 与 `services/sim-trading/sim-trading_web/app/intelligence/page.tsx` 在 A / B 两批均被引用，因此两批默认 **顺序执行**，不并行签发。
3. 若执行中要求把 50 万本金改成可配置项并写入 `services/sim-trading/.env.example`，当前批次立即失效，必须补充 **P0** 预审。
4. 若执行中要求修改 `shared/contracts/sim-trading/account.md` 或新增跨服务字段，也必须另行补充 **P0** 预审。

---

## 八、当前继续锁定的路径

1. `shared/contracts/**`
2. `services/dashboard/**`
3. `services/sim-trading/.env.example`
4. `docker-compose.dev.yml`
5. `services/sim-trading/tests/**` 白名单外文件
6. 其他全部非白名单文件

---

## 九、预审结论

1. **`TASK-0022` 正式成立。**
2. **本事项不并入 `TASK-0017`，也不复用 `TASK-0015`；当前明确归属 `services/sim-trading/**` 单服务范围。**
3. **当前 4 项需求已冻结为 2 个 P1 批次：A 为自动补齐 + 账户口径 + L2 说明收口，B 为最小只读日志查看。**
4. **两批默认顺序执行，均待 Jay.S 为模拟交易 Agent 签发 P1 Token 后方可进入服务代码实施。**
5. **当前轮次仅完成治理冻结，不进入代码执行，不申请 `lockctl`。**