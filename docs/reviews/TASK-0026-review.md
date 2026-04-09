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

## 五、批次 A 回归结果（2026-04-10）

- review-id：`REVIEW-TASK-0026-A`
- token_id：`tok-81a76988-7317-42a5-b0e0-5c10b3587a14`
- 执行 Agent：回测 Agent
- 修改文件：
  1. `services/backtest/src/backtest/factor_registry.py`
  2. `services/backtest/tests/test_factor_registry_aliases.py`
- 测试结果：**6 tests passed, 0 errors**
- 实施摘要：
  - 新增 `Spread`、`Spread_RSI` 两个因子，已注册并可计算。
  - 修复了 `return rows` 重复死代码。
- 结论：**批次 A 通过**

## 六、批次 B 回归结果（2026-04-10）

- review-id：`REVIEW-TASK-0026-B`
- token_id：`tok-8ac60661-f8bd-47da-b2fc-02c677e94898`
- 执行 Agent：回测 Agent
- 修改文件：
  1. `services/backtest/src/backtest/factor_registry.py`
  2. `services/backtest/src/backtest/generic_strategy.py`
  3. `services/backtest/src/api/routes/support.py`
  4. `services/backtest/tests/test_factor_registry_aliases.py`
- 测试结果：**10 tests passed（含 4 个新增别名测试）, 0 errors**
- 全量回测测试：**60 passed, 2 failed**（2 个失败为既有异步竞态问题，与本次修改无关）
- 实施摘要：
  - 新增 `resolve_factor_name()` 方法，统一 snake_case 到 PascalCase 映射。
  - 策略层（`generic_strategy.py`）与 API 层（`support.py`）已完成兼容接入。
- 结论：**批次 B 通过**

## 七、批次 C 审计留痕（2026-04-10）

- review-id：`REVIEW-TASK-0026-C`
- token_id：`tok-96414cea`
- 执行 Agent：项目架构师
- 操作文件：
  1. `docs/reviews/TASK-0026-review.md`（本文件，回归结果补齐）
  2. `docs/locks/TASK-0026-lock.md`（A/B/C 状态锁回）
  3. `docs/handoffs/TASK-0026-实施交接与回归结果.md`（新建，实施交接）
- 结论：**批次 C 通过**

## 八、当前状态字段

1. `TASK-0026-A`：`locked_back`
2. `TASK-0026-B`：`locked_back`
3. `TASK-0026-C`：`locked_back`

## 九、最终结论

1. `TASK-0026` 三批次（A/B/C）全部通过。
2. 服务归属始终限于 `services/backtest/**` 单服务，无白名单越界。
3. A 批次新增因子与死代码修复已闭环。
4. B 批次全量下划线别名兼容已闭环。
5. C 批次回归留痕与锁回已闭环。
6. 全量回测中 2 个既有异步竞态失败与本任务无关，列为非阻断遗留。
7. **TASK-0026 全部通过，已完成锁回。**
