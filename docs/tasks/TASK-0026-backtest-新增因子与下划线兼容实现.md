# TASK-0026 backtest 新增因子与下划线兼容实现预审

## 文档信息

- 任务 ID：TASK-0026
- 文档类型：新任务预审与分批冻结
- 签名：项目架构师
- 建档时间：2026-04-08
- 设备：MacBook

---

## 一、任务目标

为回测服务建立“新增因子 + 全量下划线别名兼容”的正式治理任务，确保后续实施可按批次申请 Token、执行、回归与锁回。

本任务当前轮次仅做预审建档，不进入 `services/backtest/**` 业务代码修改。

---

## 二、服务归属与边界结论

1. 任务归属冻结为：**`services/backtest/**` 单服务范围**。
2. 当前事项不得并入 `TASK-0018` 或其他历史回测批次，必须独立以 `TASK-0026` 管理。
3. 本轮不修改 `shared/contracts/**`，不扩展到 `services/data/**`、`services/decision/**`、`services/dashboard/**`。

---

## 三、分批设计（A/B/C）

### 批次 A：新增因子 Spread、Spread_RSI（P1）

- 批次标识：`TASK-0026-A`
- 保护级别：P1
- 当前状态：`pending_token`
- 目标：在因子注册层补齐 `Spread`、`Spread_RSI`，并补最小回归测试。

白名单（最小文件集）：

1. `services/backtest/src/backtest/factor_registry.py`
2. `services/backtest/tests/test_factor_registry_aliases.py`

验收标准：

1. `Spread`、`Spread_RSI` 可被注册并参与计算。
2. 异常输入可解释，不得出现不可控崩溃。
3. 相关测试可覆盖新增因子最小路径。

### 批次 B：全量下划线别名兼容（P1）

- 批次标识：`TASK-0026-B`
- 保护级别：P1
- 当前状态：`pending_token`
- 目标：统一回测因子别名兼容策略，补齐 snake_case（下划线）别名链路。

白名单（最小文件集）：

1. `services/backtest/src/backtest/factor_registry.py`
2. `services/backtest/src/backtest/generic_strategy.py`
3. `services/backtest/src/api/routes/support.py`
4. `services/backtest/tests/test_factor_registry_aliases.py`

验收标准：

1. 下划线别名输入可被统一解析。
2. 既有 CamelCase 行为不回归。
3. 注册层、策略执行层、导入扫描层口径一致。

### 批次 C：回归与锁回（P1）

- 批次标识：`TASK-0026-C`
- 保护级别：P1
- 当前状态：`pending_token`
- 目标：完成本任务回归留痕、终审收口与锁回账本。

白名单（最小文件集）：

1. `docs/reviews/TASK-0026-review.md`
2. `docs/locks/TASK-0026-lock.md`
3. `docs/handoffs/TASK-0026-实施交接与回归结果.md`

验收标准：

1. A/B 批次目标回归结果写入 review。
2. lock 账本补齐 token 与锁回留痕。
3. handoff 输出实施结果、风险与下一步建议。

---

## 四、当前轮次治理白名单（P-LOG）

1. `docs/tasks/TASK-0026-backtest-新增因子与下划线兼容实现.md`
2. `docs/reviews/TASK-0026-review.md`
3. `docs/locks/TASK-0026-lock.md`
4. `docs/handoffs/TASK-0026-架构预审交接单.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

---

## 五、执行约束

1. 当前仅完成建档，**A/B/C 三批均为 `pending_token`**。
2. 未签发前，不得修改任何 `services/backtest/**` 白名单业务文件。
3. 若执行中需要新增业务文件，必须先回交补充预审并更新白名单。
4. 不得顺手修复 `TASK-0026` 范围外问题。

---

## 六、预审结论

1. `TASK-0026` 正式成立。
2. 范围固定为 `services/backtest/**` 单服务任务。
3. 批次 A/B/C 已冻结，当前统一状态为 `pending_token`。
4. 在 Jay.S 签发对应 Token 前，不进入服务代码实施。
