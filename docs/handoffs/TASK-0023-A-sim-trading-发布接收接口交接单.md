# TASK-0023-A sim-trading 发布接收接口交接单

【签名】模拟交易 Agent
【时间】2026-04-08
【设备】MacBook
【状态】已完成实现与自校验；等待项目架构师终审与 lockback

## 任务信息

- 任务 ID：TASK-0023-A
- 所属任务：TASK-0023
- review-id：REVIEW-TASK-0023-A
- 执行范围：仅限 2 个业务白名单文件
- 批次目标：在现有 `/api/v1` 命名空间下提供最小策略发布接收接口，只做接收、校验与回执

## 预执行校验

1. 已按流程读取 `WORKFLOW.md`、总调度 prompt、公共项目 prompt、模拟交易私有 prompt，以及 `TASK-0023` 相关 task/review/handoff。
2. 已使用用户原样提供的 token 执行 `lockctl validate`。
3. 校验结果：通过；任务 `TASK-0023-A`、Agent `模拟交易`、action `edit` 与以下 2 个白名单文件完全匹配：
   - `services/sim-trading/src/api/router.py`
   - `services/sim-trading/tests/test_strategy_publish_api.py`

## 完成动作

1. 在 `services/sim-trading/src/api/router.py` 新增 `POST /api/v1/strategy/publish`。
2. 接口只消费 `strategy_package` 的最小字段子集：`strategy_id`、`strategy_version`、`package_hash`、`publish_target`、`allowed_targets`、`lifecycle_status`、`published_at`、`live_visibility_mode`。
3. 业务校验固定为：
   - `publish_target` 必须是 `sim-trading`
   - `allowed_targets` 必须包含 `sim-trading`
   - `lifecycle_status` 必须是 `publish_pending`
   - `live_visibility_mode` 必须是 `locked_visible`
4. 合法请求返回 `202`，回执包含：`strategy_id`、`strategy_version`、`package_hash`、`publish_target`、`result=accepted`、`received_at`。
5. 业务拒绝返回显式 `400 rejected`，缺字段或类型错误保留 FastAPI `422`。
6. 本批未接入真实下单、CTP 执行、持久化，也未新增 service / repository 或触碰第 3 个业务文件。

## 修改文件

1. `services/sim-trading/src/api/router.py`
2. `services/sim-trading/tests/test_strategy_publish_api.py`

## 验证结果

1. 已执行 `get_errors`：
   - `services/sim-trading/src/api/router.py` = `No errors found`
   - `services/sim-trading/tests/test_strategy_publish_api.py` = `No errors found`
2. 已执行：`cd /Users/jayshao/JBT/services/sim-trading && PYTHONPATH=. ../../.venv/bin/pytest tests/test_strategy_publish_api.py -q`
3. 结果：`7 passed in 0.47s`
4. 已覆盖场景：
   - 合法请求 `202`
   - `publish_target` 非 `sim-trading`
   - `allowed_targets` 不含 `sim-trading`
   - `lifecycle_status` 非 `publish_pending`
   - `live_visibility_mode` 非 `locked_visible`
   - 缺字段 `422`
   - `published_at` 非法 `422`

## 待审问题

1. 当前实现严格按最小接收接口收口，只校验并回执；若后续要把接收结果写入状态、落盘或联动真实执行链，必须另起补充预审。
2. 本批未修改 `shared/contracts/**`；若后续需要把回执或消费字段升级为跨服务正式契约，仍需 P0 补审。
3. 本批未执行 lockback，当前状态仍为待项目架构师终审。

## 向 Jay.S 汇报摘要

1. `TASK-0023-A` 已按 2 文件白名单完成，`sim-trading` 现已提供 `POST /api/v1/strategy/publish`，decision 侧后续不再需要依赖 404 降级判断。
2. 接口当前只做最小字段消费、业务校验与回执，不接入真实下单链，也没有扩展到 `.env.example`、compose、shared contract 或第 3 个业务文件。
3. 本批自校验已完成：2 个白名单文件 `get_errors = 0`，指定 `pytest` 结果为 `7 passed in 0.47s`。

## 下一步建议

1. 请项目架构师对 `TASK-0023-A` 执行定向终审；若通过，按当前 2 文件白名单执行 lockback。
2. `TASK-0023-A` 终审通过后，再与 `TASK-0021-H4` 做端到端联调验收。
3. 在 Jay.S 未确认前，不扩展到 `shared/contracts/**`、`.env.example`、`docker-compose.dev.yml` 或更多业务文件。