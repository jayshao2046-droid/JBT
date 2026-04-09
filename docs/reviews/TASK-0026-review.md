# TASK-0026 Review

## Review 信息

- 任务 ID：TASK-0026
- 审核角色：项目架构师
- 审核阶段：建档预审
- 审核时间：2026-04-08
- 审核结论：通过（建档通过；A/B/C 三批待 Token）

---

## 一、预审范围

1. 仅审核任务归属、分批边界、白名单与锁控状态。
2. 当前轮次不进入 `services/backtest/**` 业务代码执行。
3. 当前轮次不修改 `shared/contracts/**` 与其他服务目录。

## 二、归属与边界审核结论

1. `TASK-0026` 归属冻结为 **`services/backtest/** 单服务范围**。
2. 当前事项独立建档，不并入既有回测主线执行批次。
3. 任务目标冻结为两部分：
   - 新增因子：`Spread`、`Spread_RSI`
   - 全量下划线别名兼容：snake_case 兼容链路

## 三、分批与白名单审核结论

### 批次 A（P1）：新增因子 Spread、Spread_RSI

- 状态：`pending_token`
- 白名单：
  1. `services/backtest/src/backtest/factor_registry.py`
  2. `services/backtest/tests/test_factor_registry_aliases.py`
- 结论：白名单最小可执行，满足“新增因子 + 最小测试”边界。

### 批次 B（P1）：全量下划线别名兼容

- 状态：`pending_token`
- 白名单：
  1. `services/backtest/src/backtest/factor_registry.py`
  2. `services/backtest/src/backtest/generic_strategy.py`
  3. `services/backtest/src/api/routes/support.py`
  4. `services/backtest/tests/test_factor_registry_aliases.py`
- 结论：白名单覆盖注册、执行、扫描与回归最小链路，符合本批目标。

### 批次 C（P1）：回归与锁回

- 状态：`pending_token`
- 白名单：
  1. `docs/reviews/TASK-0026-review.md`
  2. `docs/locks/TASK-0026-lock.md`
  3. `docs/handoffs/TASK-0026-实施交接与回归结果.md`
- 结论：白名单用于回归收口与锁回留痕，不扩展服务业务文件。

## 四、风险与阻断条件

1. 未签发 Token 前，不得写入任一 `services/backtest/**` 白名单业务文件。
2. 批次间不得擅自扩白名单；如需新增文件必须补充预审。
3. 不得借本任务顺手修改 `services/backtest/**` 非白名单文件。

## 五、当前状态字段

1. `TASK-0026-A`：`pending_token`
2. `TASK-0026-B`：`pending_token`
3. `TASK-0026-C`：`pending_token`

## 六、预审结论

1. `TASK-0026` 建档预审通过。
2. 服务归属固定为 `services/backtest/**` 单服务。
3. A/B/C 三批均已冻结为 `pending_token`。
4. 当前可执行动作仅为治理留痕与待签发，不进入代码实施。

---

## 七、二次签发复核（2026-04-08）

1. `TASK-0026-A` 已签发并 validate 通过：`tok-81a76988-7317-42a5-b0e0-5c10b3587a14`。
2. `TASK-0026-B` 已签发并 validate 通过：`tok-8ac60661-f8bd-47da-b2fc-02c677e94898`。
3. `TASK-0026-C` 已签发并 validate 通过：`tok-ec5919b9-1b95-4588-ad5d-b3ab9c6ec4a0`。
4. 当前三批状态：A/B/C 全部 `active`。
5. 允许执行范围：仅 A/B/C 对应白名单文件；禁止扩展到非白名单路径。
