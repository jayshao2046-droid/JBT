# TASK-0012 legacy 信号到 JBT 桥接预审

## 文档信息

- 任务 ID：TASK-0012
- 文档类型：兼容层任务预审与契约冻结
- 签名：项目架构师
- 建档时间：2026-04-06
- 设备：MacBook

---

## 一、任务目标

为 legacy 系统到 JBT SimNow 的信号桥接建立独立任务边界，冻结“先契约、后实现”的执行顺序，并限定所有兼容代码只能落在 `integrations/legacy-botquant/`。

本任务**只承接 legacy 兼容桥接**，不等同于“测试完成后通过 API 接入 J_BotQuant Studio 决策端”的正式接入任务；后者另行建档为 `TASK-0016`。

本任务必须同时满足：

1. 桥接契约先登记到 `shared/contracts/**`。
2. 桥接实现只允许落在 `integrations/legacy-botquant/**`。
3. 桥接必须具备鉴权、幂等、TTL、乱序/重复/过期校验和桥接失败告警。

---

## 二、任务编号与归属结论

### 编号结论

- **本事项独立建档为 `TASK-0012`。**

### 判定理由

1. 本事项同时涉及 `shared/contracts/**` 与 `integrations/legacy-botquant/**`，不属于 `services/sim-trading/**` 单服务任务。
2. 若把桥接兼容逻辑放入 `services/sim-trading/**`，会直接违反 JBT 服务隔离与 legacy 兼容层规则。
3. 本事项的风险类型、Token 类型和回滚方式均不同于 `TASK-0010` 服务骨架与 `TASK-0011` 运行态清退。

### 归属结论

- **任务归属：`shared/contracts/**` + `integrations/legacy-botquant/**`，且必须先契约后实现。**

---

## 三、强制边界

1. 兼容代码只能落在 `integrations/legacy-botquant/**`。
2. 严禁把 bridge receiver、鉴权、去重、TTL 校验、重试与告警逻辑写入 `services/sim-trading/**`。
3. 严禁在没有正式契约字段的情况下，以“临时 JSON 字段”直接硬连实现。
4. 当前轮次只做预审，不修改 `shared/contracts/**` 或 `integrations/**`。
5. 严禁把本任务描述成 `TASK-0016` 的正式 Studio API 接入，避免把兼容层与正式接入层混并。

---

## 四、执行顺序冻结

### 批次 A：P0 契约登记

目标：先把桥接请求与桥接失败响应的最小字段冻结到 `shared/contracts/**`。

建议最小 P0 触点：

1. `shared/contracts/sim-trading/api.md`
2. `shared/contracts/sim-trading/bridge_signal.md`

说明：

1. `api.md` 用于补登记 bridge ingest 的正式入口与使用限制。
2. `bridge_signal.md` 用于定义桥接信号最小字段模型。
3. 批次 A 只能在 `TASK-0009` 与 `TASK-0013` 闭环后启动。

### 批次 B：P0 桥接实现

目标：在 `integrations/legacy-botquant/**` 中实现桥接接收、鉴权、去重、TTL 校验、转换、投递与失败告警。

说明：

1. 批次 B 在 `TASK-0010` 提供最小可用服务入口前，不得启动。
2. 批次 B 落在 `integrations/legacy-botquant/**`，按现行治理同样视为 P0 保护路径，不再保留 P1 实现口径。
3. 批次 B 的白名单需在批次 A P0 契约锁回后再冻结，不得现在拍脑袋扩路径。
4. 批次 B 只负责 legacy 兼容桥接，不自动获得 `TASK-0016` 正式 Studio API 接入的白名单或 Token。

---

## 五、桥接契约最小字段清单

以下字段为当前预审冻结的最小字段，不得省略：

1. `signal_id`：信号唯一 ID，用于幂等与去重。
2. `source_system`：来源系统标识，固定区分 legacy 来源。
3. `source_instance_id`：来源实例或节点标识，用于审计与冲突排查。
4. `strategy_id`：策略标识。
5. `strategy_version`：策略版本号。
6. `trace_id`：跨链路追踪 ID。
7. `generated_at`：信号生成时间。
8. `expires_at`：信号过期时间，用于 TTL 校验。
9. `sequence_no`：来源侧单调序号，用于乱序判断。
10. `account_id`：目标账户标识。
11. `symbol`：目标合约代码。
12. `side`：买卖方向。
13. `offset`：开平标志。
14. `volume`：下单数量。
15. `order_type`：订单类型。
16. `price`：限价时的委托价格；市价场景可为空。
17. `risk_profile_hash`：风险摘要哈希，用于版本一致性检查。
18. `auth_key_id`：鉴权 key 标识。
19. `signature`：请求签名。
20. `delivery_attempt`：投递次数，用于重试与告警分级。

### 字段冻结原则

1. 幂等以 `signal_id` 为第一主键，以 `source_system + strategy_version + sequence_no` 为辅助校验维度。
2. TTL 以 `expires_at` 为唯一判定口径，不接受“未填过期时间”的裸信号。
3. 鉴权必须同时具备 `auth_key_id` 与 `signature`，不接受匿名桥接。
4. 风险摘要必须可追溯，不能只传业务字段不传风险口径。

---

## 六、桥接能力硬性要求

1. 必须校验重复信号、乱序信号、过期信号、未来时间信号。
2. 必须保留幂等存储或去重缓存，不得依赖“上游大概率不重发”的假设。
3. 必须对鉴权失败、签名失败、字段缺失、版本不兼容、投递失败、重试超限分别告警。
4. 必须能把桥接失败事件与 `signal_id`、`trace_id`、`source_system` 关联。
5. 桥接层只能做鉴权、校验、映射、投递，不得在桥接层新增择时、过滤或重新生成信号。

---

## 七、敏感信息治理

1. `auth_key_id` 对应的真实鉴权密钥、签名密钥、上游 API 凭证只能作为运行时 Secret 注入，不得写入 Git、`.env.example` 或治理账本。
2. `.env.example` 只能记录占位符、字段说明与接入方式，不能记录真实值。
3. 任何来自 J_BotQuant Studio 的连接方案只能写“来源”“注入位置”“轮换方式”，不能写明文秘密值。

---

## 八、保护级别口径冻结

1. `TASK-0012` 当前正式口径冻结为：批次 A `shared/contracts/**` 契约登记按 P0 执行。
2. 批次 B `integrations/legacy-botquant/**` 桥接实现按现行治理同样视为 P0 执行。
3. 不再保留“批次 B 按 P1 实现”或“等待 Jay.S 决策是否按 P1 执行”的旧表述。
4. 若未来要把 `integrations/**` 改成 P1，必须先由 Atlas 更新治理规则，再重新预审本任务的保护级别、白名单与执行顺序。

---

## 九、预审结论

1. **`TASK-0012` 正式成立。**
2. **桥接链必须先做 P0 契约登记，再做实现。**
3. **兼容实现只能落在 `integrations/legacy-botquant/**`，严禁写入 `services/sim-trading/**`。**
4. **桥接契约最小字段清单已冻结。**
5. **`TASK-0012` 只承接 legacy 兼容桥接，不承接 `TASK-0016` 的正式 Studio API 接入。**
6. **`TASK-0012` 当前正式保护级别已统一为：批次 A P0、批次 B P0；若未来要把 `integrations/**` 改成 P1，必须先改治理规则再重做预审。**
