# TASK-0019 sim-trading 收盘统计邮件预审

## 文档信息

- 任务 ID：TASK-0019
- 文档类型：新任务预审与边界冻结
- 签名：项目架构师
- 建档时间：2026-04-07
- 设备：MacBook

---

## 一、任务目标

为 SimNow 主线建立独立的“收盘统计邮件 / 定时报表”任务，冻结其与即时通知、定时编排、报表数据面和凭证治理的边界。

本任务当前轮次只做预审，不写任何服务代码。

---

## 二、任务编号与归属结论

### 编号结论

- **收盘统计邮件 / 定时报表必须新建独立任务 `TASK-0019`。**

### 判定理由

1. `TASK-0014` 处理的是单条风险事件消费与即时通知，不承接定时调度与报表汇总。
2. 收盘统计邮件涉及 scheduler、时间窗、账本汇总与报表数据面，属于另一类故障模式与验收口径。
3. 若把定时报表并入 `TASK-0014`，会把“事件驱动通知”和“时间驱动报表”混成同一任务，违反“一件事一审核一上锁”。

### 服务归属结论

- **首轮实施归属：`services/sim-trading/**` 单服务范围。**
- **未来若看板或其他服务需要消费报表结果，必须另建任务，不得直接扩白名单。**

### 执行 Agent

1. 预审：项目架构师
2. 实施：模拟交易 Agent

---

## 三、当前轮次白名单与保护级别

### 当前 Git 白名单

1. `docs/tasks/TASK-0019-sim-trading-收盘统计邮件预审.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/项目架构师提示词.md`

### 当前保护级别

- **当前轮次只涉及 P-LOG 协同账本区，不申请代码 Token。**

### 当前轮次明确禁止

1. 不得修改 `services/sim-trading/**`。
2. 不得修改 `services/sim-trading/.env.example`。
3. 不得修改 `shared/contracts/**`。
4. 不得把真实 Secret、真实收件人或真实 SMTP 凭证写入 Git。
5. 不得在服务代码中耦合 `/Users/jayshao/J_BotQuant/.env` 路径。

---

## 四、前置依赖

1. `TASK-0009` 已闭环。
2. `TASK-0013` 已冻结统一风控核心与阶段预设口径。
3. `TASK-0010` 已提供最小账户 / 持仓 / 成交数据面与基础运行骨架。
4. `TASK-0014-A1` 与 `TASK-0014-A2` 应先于本任务进入执行。

---

## 五、正式治理冻结

### 1. 与 `TASK-0014` 的边界

1. `TASK-0014` 负责即时风控通知，不承接定时报表。
2. `TASK-0019` 负责 scheduler、时间窗和收盘统计邮件，不承接单条风险事件消费。
3. **本任务独立于 `TASK-0014`，因为它属于定时编排 + 报表数据面。**

### 2. 报表时间窗

1. 建议时间窗先冻结为：`15:20`、`23:10`（或 `23:40`）、`02:40`。
2. `23:10` 与 `23:40` 的最终值仍待 Jay.S 确认。
3. 未获确认前，不得在代码中擅自硬编码新的第 4 个时间窗。

### 3. 批次拆分

1. **B0**：如需统一补齐剩余通知 / 报表模板占位，则把 `services/sim-trading/.env.example` 作为 **P0** 单文件批次；本批默认由 Atlas / Jay.S 处理，不派发模拟交易 Agent。
2. **B1**：scheduler 与最小邮件报表骨架，保护级别冻结为 **P1**；白名单冻结为：
   - `services/sim-trading/src/main.py`
   - `services/sim-trading/src/notifier/email.py`
   - `services/sim-trading/src/ledger/service.py`
   - `services/sim-trading/tests/test_notifier.py`
   - `services/sim-trading/tests/test_report_scheduler.py`（允许新增）
3. **B2**：账户 / 持仓 / 成交报表充实，保护级别冻结为 **P1**；白名单冻结为：
   - `services/sim-trading/src/gateway/simnow.py`
   - `services/sim-trading/src/ledger/service.py`
   - `services/sim-trading/src/api/router.py`
   - `services/sim-trading/tests/test_ctp_notify.py`
   - `services/sim-trading/tests/test_report_scheduler.py`
4. 执行顺序冻结为 `TASK-0019-B0`（如需要）→ `TASK-0019-B1` → `TASK-0019-B2`。
5. `TASK-0019-B1` 与 `TASK-0019-B2` 均不得先于 `TASK-0014-A4`、`TASK-0017-A4`、`TASK-0022-B` 启动。
6. `TASK-0019-B0` 可一次性预签，但若启用，必须单独提交、单独锁回，并在 B1 启动前完成。

### 4. legacy env 映射建议

1. Jay.S 已明确允许 legacy `J_BotQuant/.env` 只作为“凭证来源”。
2. 推荐采用部署侧 env mapping / fallback，不得在服务代码中读取 `/Users/jayshao/J_BotQuant/.env`。
3. webhook 映射建议：`FEISHU_ALERT_WEBHOOK_URL` 优先于 `FEISHU_WEBHOOK_URL`。
4. 邮件映射建议：`SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` / `FROM_ADDR` / `TO_ADDRS` 映射到 JBT 的 `ALERT_EMAIL_*` 变量。

---

## 六、Token / 保护级别策略

1. 当前轮次：P-LOG，仅治理账本，不申请代码 Token。
2. `TASK-0019-B0` 若进入实施：`services/sim-trading/.env.example` 单文件按 **P0** 处理。
3. `TASK-0019-B1` 若进入实施：`services/sim-trading/src/main.py`、`src/notifier/email.py`、`src/ledger/service.py`、`tests/test_notifier.py`、`tests/test_report_scheduler.py`（允许新增）按 **P1** 处理。
4. `TASK-0019-B2` 若进入实施：`services/sim-trading/src/gateway/simnow.py`、`src/ledger/service.py`、`src/api/router.py`、`tests/test_ctp_notify.py`、`tests/test_report_scheduler.py` 按 **P1** 处理。
5. 若未来需要补跨服务报表契约到 `shared/contracts/**`：**P0**。

---

## 七、敏感信息治理

1. 真实收件人、SMTP 用户名、SMTP 密码、发件地址与 webhook 只能作为运行时 Secret 注入，不得写入 Git、`.env.example` 或治理账本。
2. `.env.example` 只能写占位符与字段说明，不能写真实邮箱地址、真实密码或真实 webhook。
3. legacy `J_BotQuant/.env` 只提供凭证来源与映射依据，不得在仓内留存真实秘密值。

---

## 八、验收标准

1. 已明确 `TASK-0019` 独立于 `TASK-0014`。
2. 已冻结 `TASK-0019-B0` / `B1` / `B2` 的批次边界与保护级别。
3. 已冻结报表建议时间窗与 legacy env 映射建议。
4. 已明确真实 Secret 不得入库，且不得耦合外部 `.env` 路径。

---

## 九、预审结论

1. **`TASK-0019` 正式成立。**
2. **`TASK-0019` 独立于 `TASK-0014`，因为它属于定时编排 + 报表数据面，不再是单条风险事件消费。**
3. **执行顺序冻结为 `TASK-0014-A3` → `TASK-0014-A4`；`TASK-0017-A4` 可并行；`TASK-0022-B` 收口后再进入 `TASK-0019-B0`（如需要）→ `TASK-0019-B1` → `TASK-0019-B2`。**
4. **当前轮次仅完成治理冻结，不进入代码 Token 申请。**