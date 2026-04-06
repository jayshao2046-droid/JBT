# TASK-0014 sim-trading 风控通知链路预审

## 文档信息

- 任务 ID：TASK-0014
- 文档类型：新任务预审与边界冻结
- 签名：项目架构师
- 建档时间：2026-04-06
- 设备：MacBook

---

## 一、任务目标

为 SimNow 主线建立独立的风控通知链路，冻结“独立飞书 + 独立邮件”的正式边界、最小事件结构、即时通知补充批次与敏感信息治理规则。

本任务当前轮次只做预审，不写任何服务代码。

---

## 二、任务编号与归属结论

### 编号结论

- **C 风控通知必须新建独立任务 `TASK-0014`。**

### 判定理由

1. 风控通知拥有独立凭证、独立故障模式、独立验收项，不应混入 `TASK-0010` 服务骨架任务。
2. 风控通知失败会反向影响系统风险状态，必须作为独立治理对象建档。
3. 该事项不等于 backtest 或其他服务的通知链路，不能复用旧任务号或旧默认 webhook。

### 服务归属结论

- **首轮实施归属：`services/sim-trading/**` 单服务范围。**
- **未来 live-trading 若复用通知能力，必须另建任务，不得直接扩白名单。**

### 执行 Agent

1. 预审：项目架构师
2. 实施：模拟交易 Agent

---

## 三、当前轮次白名单与保护级别

### 当前 Git 白名单

1. `docs/tasks/TASK-0014-sim-trading-风控通知链路预审.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/项目架构师提示词.md`

### 当前保护级别

- **当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。**

### 当前轮次明确禁止

1. 不得修改 `services/sim-trading/**`。
2. 不得修改 `services/live-trading/**`。
3. 不得复用其他服务的默认 webhook、默认邮箱配置或默认通知模板。
4. 不得把真实通知凭证写入 Git、`.env.example` 或治理账本。

---

## 四、前置依赖

1. `TASK-0009` 已闭环。
2. `TASK-0013` 已冻结统一风控核心与阶段预设口径。
3. `TASK-0010` 已完成最小风险事件输出与风控钩子占位。

---

## 五、正式治理冻结

### 1. 通知通道

1. 必须具备独立飞书通道与独立邮件通道。
2. 两条通道必须可分别禁用、分别测试、分别告警，不能被实现成“同一凭证的两种包装”。
3. 通知链默认只消费风控事件，不承接策略收益播报或其他非风险消息。

### 2. 最小事件结构

1. 事件至少应包含：`task_id`、`stage_preset`、`risk_level`、`account_id`、`strategy_id`、`symbol`、`signal_id`、`trace_id`、`event_code`、`reason`。
2. P0 / P1 / P2 三档映射必须与 `TASK-0009` 保持一致。
3. 通知失败必须反向写入系统风险状态，不允许静默丢弃。

### 3. 失败收口

1. 飞书失败与邮件失败必须分别留痕。
2. 单通道失败时，另一通道仍应按规则继续发送。
3. 当双通道均失败时，系统至少进入“拒绝新开仓”或更严格模式。

### 4. 即时通知补充批次冻结

1. 用户新增的“即时飞书 / 邮件告警”继续归入 `TASK-0014`，不新开任务号。
2. 补充批次 A1：通知 bootstrap 与风险钩子闭环，保护级别冻结为 **P1**；建议白名单：
	- `services/sim-trading/src/main.py`
	- `services/sim-trading/src/notifier/dispatcher.py`
	- `services/sim-trading/src/risk/guards.py`
	- `services/sim-trading/tests/test_notifier.py`
	- `services/sim-trading/tests/test_risk_hooks.py`
3. 补充批次 A2：系统事件来源接线，保护级别冻结为 **P1**；建议白名单：
	- `services/sim-trading/src/api/router.py`
	- `services/sim-trading/src/gateway/simnow.py`
	- 最多 2 个 `services/sim-trading/tests/**` 测试文件
4. 执行顺序冻结为 `TASK-0014-A1` → `TASK-0014-A2`；A2 不得先于 A1 启动。

---

## 六、Token / 保护级别策略

1. 当前轮次：P-LOG，仅治理账本，不申请代码 Token。
2. 补充批次 A1 若落地：`services/sim-trading/src/main.py`、`src/risk/guards.py`、`src/notifier/dispatcher.py` 与对应测试文件均按 **P1** 处理。
3. 补充批次 A2 若落地：`services/sim-trading/src/api/router.py`、`src/gateway/simnow.py` 与最多 2 个测试文件按 **P1** 处理。
4. 若后续需要在 `services/sim-trading/.env.example` 中补充通知字段占位：**P0**。
5. 若未来需要新增跨服务通知事件契约到 `shared/contracts/**`：**P0**。

---

## 七、敏感信息治理

1. 飞书 webhook、邮箱账号、邮箱密码、SMTP 鉴权字段只能作为运行时 Secret 注入，不得写入 Git、`.env.example` 或治理账本。
2. `.env.example` 只能写占位符和字段说明，不能写真实 webhook、真实邮箱地址或真实密码。
3. Jay.S 已明确允许 legacy `J_BotQuant/.env` 只作为“凭证来源”参考，账本中不得出现真实秘密值。
4. 推荐采用部署侧 env mapping / fallback，把 legacy 变量映射到 JBT 运行时环境。
5. 不得在服务代码中耦合 `/Users/jayshao/J_BotQuant/.env` 路径，不得把真实 Secret 读写逻辑写入 Git。

---

## 八、验收标准

1. 独立飞书 + 独立邮件双通道已冻结为正式治理口径。
2. P0 / P1 / P2 的最小事件字段与失败收口逻辑已冻结。
3. 已明确即时通知继续归入 `TASK-0014` 的补充批次 A1 / A2。
4. 已明确该任务不复用 backtest 或其他服务的默认通知配置。
5. 已明确 legacy `.env` 仅可作为部署侧凭证来源，真实通知凭证不得入库。

---

## 九、预审结论

1. **`TASK-0014` 正式成立。**
2. **C 风控通知必须作为独立任务推进，不得并入 `TASK-0010` 或 `TASK-0017`。**
3. **即时通知继续归入 `TASK-0014` 的补充批次 A1 / A2；其中 `TASK-0014-A1` 已于 2026-04-07 完成实施、终审与锁回，`TASK-0014-A2` 当前保持待执行。**
4. **legacy `J_BotQuant/.env` 只可作为部署侧凭证来源，不得把外部路径耦合进服务代码。**

## 十、2026-04-07 TASK-0014-A1 收口补录

1. `TASK-0014-A1` 实际业务白名单严格限于 5 个文件：`services/sim-trading/src/main.py`、`services/sim-trading/src/notifier/dispatcher.py`、`services/sim-trading/src/risk/guards.py`、`services/sim-trading/tests/test_notifier.py`、`services/sim-trading/tests/test_risk_hooks.py`。
2. 实现收口冻结为：`main.py` 完成 notifier bootstrap；`dispatcher.py` 完成单例 register / get / clear / bootstrap；`risk/guards.py` 完成 `emit_alert` 到最小 `RiskEvent` 的映射。
3. 最小自校验结果为 `13 passed, 1 skipped`。
4. 对应代码提交为 `d4b5817`；对应 P1 token_id 为 `tok-7ab3cadf-043b-4709-b8e7-d00519f1ae81`；lockback review-id 为 `REVIEW-TASK-0014-A1`，当前状态 `locked`。
5. 本批未扩展到 scheduler、日报、CTP 事件接线或 legacy `.env` 路径读取。
6. 当前通知 / 报表子线下一执行顺序保持为 `TASK-0014-A2` → `TASK-0019-B0`（如需要）→ `TASK-0019-B1` → `TASK-0019-B2`。