# TASK-0021 H3 补充回修 — symbol 解析闭环交接单

【签名】决策 Agent  
【交接时间】2026-04-08  
【review_id】REVIEW-TASK-0021-H3  
【token_id】tok-c9b73a9a-c9aa-40a8-8d51-2e23cefe88f3

---

## 执行结果摘要

状态：已完成，待项目架构师重新终审与 lockback

---

## 任务信息

- 任务 ID：TASK-0021-H3
- 执行类型：补充回修
- 执行范围：沿用 `TASK-0021-H3` 当前 active token 3 文件白名单，不扩文件
- 补修目标：修复 `FactorLoader` 把 `strategy_id` 直接当作 data API `symbol` 的语义问题，补齐真正的 symbol 解析闭环

---

## 预执行校验

1. 已按要求读取 `WORKFLOW.md`、总调度 prompt、公共项目 prompt、决策私有 prompt，以及 `TASK-0021` 相关 task/review/lock/handoff。
2. 已执行：`python governance/jbt_lockctl.py status --task TASK-0021-H3 --agent 决策`
3. 结果：`tok-c9b73a9a-c9aa-40a8-8d51-2e23cefe88f3 | TASK-0021-H3 | 决策 | active`
4. 已按 `docs/locks/TASK-0021-lock.md` 与 `docs/reviews/TASK-0021-review.md` 核对本批业务白名单仍严格限于：
   - `services/decision/pyproject.toml`
   - `services/decision/src/research/factor_loader.py`
   - `services/decision/tests/test_research.py`

---

## 修改文件

1. `services/decision/src/research/factor_loader.py`
2. `services/decision/tests/test_research.py`
3. `docs/prompts/agents/决策提示词.md`
4. `docs/handoffs/TASK-0021-H3补充回修-symbol闭环-决策交接.md`

---

## 改动说明

1. `factor_loader.py` 新增 H3 内部 symbol 解析逻辑，不再无条件把 `strategy_id` 直接透传给 data service。
2. 当前解析顺序固定为：
   - 优先读取与 `strategy_id` 关联的回测证书 `executed_data_symbol`
   - 其次读取同一证书的 `requested_symbol`
   - 仅当 `strategy_id` 本身已符合 data 服务支持的 symbol 格式时，才回退使用 `strategy_id`
   - 若三者都不合法，则在发起 HTTP 前显式抛出 `FactorLoadError`
3. symbol 合法性判断对齐 data 服务当前支持的 3 类格式：
   - `KQ_m_EXCHANGE_product`
   - `KQ.m@EXCHANGE.product`
   - `EXCHANGE.product` / `EXCHANGE_product`（含可选月份后缀）
4. 本次未修改 `pyproject.toml`；H3 初版补的 research 依赖声明继续保留，本轮只修 symbol 解析闭环与测试覆盖。
5. `test_research.py` 调整为覆盖两条本轮必须场景：
   - 当 `strategy_id` 不是合法行情标的时，`FactorLoader` 仍可从回测证书 `executed_data_symbol` 获取 data symbol 并正常拉取 bars
   - 当回测证书无可用 symbol 且 `strategy_id` 自身也不是合法行情标的格式时，`FactorLoader` 会显式失败，且不会发起 HTTP 请求

---

## 验证结果

1. 已执行 `get_errors`：
   - `services/decision/src/research/factor_loader.py` = `No errors found`
   - `services/decision/tests/test_research.py` = `No errors found`
2. 已执行：`cd services/decision && PYTHONPATH=. ../../.venv/bin/pytest tests/test_research.py -q`
3. 结果：`14 passed in 0.26s`

---

## 待审问题

1. 本次补修已消除 H3 的 `strategy_id -> data symbol` 直接透传问题，但未扩展到 `StrategyPackage` 新增 symbol 字段；当前闭环来源明确依赖 H2 已持久化的回测证书字段。
2. `requested_symbol` 回退路径已在实现中保留，但本轮按用户要求只把测试焦点收口到 `executed_data_symbol` 与“无合法来源显式失败”两条核心场景。
3. 当前 decision 工作树仍存在与 `TASK-0021-H0` 相关的 `services/decision/decision_web/next.config.mjs` 白名单外改动；这不属于本批业务改动，但若项目架构师按整树而非 H3 定向范围复核，可能继续作为独立风险被看到。

---

## 向 Jay.S 汇报摘要

1. `TASK-0021-H3` 补充回修已在原 active token 白名单内完成，没有扩文件。
2. `FactorLoader` 现在会先从回测证书读取 `executed_data_symbol`，其次 `requested_symbol`，只有 `strategy_id` 本身已是合法行情标的格式时才回退使用；否则会在发起 data API 请求前显式失败。
3. 与本次改动直接相关的自校验已完成：两文件静态诊断为 0，`tests/test_research.py` 结果为 `14 passed`。

---

## 下一步建议

1. 由项目架构师对 `TASK-0021-H3` 执行重新终审；若通过，按原 H3 token 范围进入 lockback。
2. 在 Jay.S 未确认前，不自动进入 `TASK-0021-H4` 的任何代码写入。