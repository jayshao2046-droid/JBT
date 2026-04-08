# TASK-0023 Review

## Review 信息

- 任务 ID：TASK-0023
- 审核角色：项目架构师
- 审核阶段：`TASK-0023-A` 正式终审
- 审核时间：2026-04-08
- 审核结论：通过（`TASK-0023-A` 已按 2 文件白名单完成实现与自校验；本轮无阻断发现，当前可 lockback）

---

## 一、任务目标

1. 为 `sim-trading` 新增最小 decision 策略发布接收接口。
2. 统一下游命名空间到 `sim-trading` 现有 `/api/v1/**` 体系。
3. 保证上游 decision 不再把 404 当作发布成功。

## 二、当前轮次白名单

1. `docs/tasks/TASK-0023-sim-trading-decision-发布接口对接预审.md`
2. `docs/reviews/TASK-0023-review.md`
3. `docs/locks/TASK-0023-lock.md`
4. `docs/handoffs/TASK-0023-sim-trading-发布接口预审交接单.md`
5. `docs/prompts/公共项目提示词.md`
6. `docs/prompts/agents/项目架构师提示词.md`

## 三、归属与边界审核结论

1. `TASK-0023` 必须独立成立，不并入 `TASK-0021`；原因是其实际写入归属 `services/sim-trading/**`，不应继续塞在 decision 主任务中。
2. `TASK-0023` 不并入 `TASK-0017`；原因是其不属于 Docker / Mini 部署问题。
3. `TASK-0023` 也不并入 `TASK-0022`；原因是其不属于运行态 UI / 只读日志收口。
4. 当前 shared contract 已足够承接本轮实现；本轮不进入 `shared/contracts/**`。

## 四、正式冻结结论

1. 下游接收端路径正式冻结为 `POST /api/v1/strategy/publish`。
2. 接口输入只消费 `strategy_package.md` 已冻结字段，不私增跨服务临时字段。
3. 第一阶段只允许 `publish_target=sim-trading`。
4. 本轮只要求“接收 + 校验 + 回执”，不要求直接下单或 CTP 执行。

## 五、代码 Token 策略

1. `TASK-0023-A` 需要 **P1 Token**。
2. 白名单冻结为：
   - `services/sim-trading/src/api/router.py`
   - `services/sim-trading/tests/test_strategy_publish_api.py`
3. 当前不需要 **P0 Token**；若后续要触碰 `.env.example`、compose、shared contract，必须另起 **P0** 补审。

## 六、并行性结论

1. `TASK-0023-A` 可与 `TASK-0021-H4` 并行。
2. 并行前提是两边共同命名空间已冻结为 `/api/v1/strategy/publish`，且均只消费现有 `strategy_package` 正式字段。
3. 虽可并行，但端到端验收必须等两边同时完成。

## 七、预审结论

1. **`TASK-0023` 预审通过。**
2. **本事项正式归属 `services/sim-trading/**` 单服务范围。**
3. **当前仅冻结 1 个 P1 批次 `TASK-0023-A`，待 Jay.S 签发。**
4. **本轮仅完成治理冻结，不进入代码执行。**

## 八、`TASK-0023-A` 正式终审

### 1. 定向核验范围

1. 本次终审严格限于 `TASK-0023-A` 的 2 个业务白名单文件：
   - `services/sim-trading/src/api/router.py`
   - `services/sim-trading/tests/test_strategy_publish_api.py`
2. 当前 `lockctl status` 已复核 `TASK-0023-A` 存在 1 张 active token：`tok-5b6b2e00-e9ca-4263-8aa3-6f3bce66cf8d`。
3. `services/sim-trading/**` 当前同目录仍存在 `TASK-0022` 与运行态观察相关的其他 dirty files，但不属于本批 2 文件终审结论，也不得混入本批后续 lockback / 提交单元。

### 2. 行为与边界复核

1. `services/sim-trading/src/api/router.py` 当前新增 `POST /api/v1/strategy/publish`，收口目标与预审冻结口径一致：仅做接收、校验与回执，不接入真实下单链，也未扩展到第 3 个业务文件。
2. 当前业务校验与预审口径一致：`publish_target` 必须为 `sim-trading`，`allowed_targets` 必须包含 `sim-trading`，`lifecycle_status` 必须为 `publish_pending`，`live_visibility_mode` 必须为 `locked_visible`；合法请求返回 `202 accepted`，业务拒绝返回显式 `400 rejected`，缺字段或类型错误保留 FastAPI `422`。
3. 本轮未触碰 `shared/contracts/**`、`.env.example`、`docker-compose.dev.yml` 或任一前端页面文件，服务边界保持合规。

### 3. 自校验复核

1. 2 个白名单文件 `get_errors = 0` 已独立复核。
2. 已独立复跑 `PYTHONPATH=. ../../.venv/bin/pytest tests/test_strategy_publish_api.py -q`，结果为 `7 passed in 0.23s`。
3. Atlas 额外提供的本地模拟联调结果已确认：decision -> sim-trading 的最小发布闭环当前返回 `signal_status = 201`、`publish_status = 200`、`publish_body.status = success`、`adapter_response.status_code = 202`，说明本批新增接收端已不再是 404 缺口。

### 4. 终审结论

1. **本轮无阻断发现。**
2. **`TASK-0023-A` 终审通过，可 lockback。**
3. 后续若要把接收结果落盘、接入真实执行链或升级为跨服务正式回执契约，必须另起补充预审；不影响本批当前 lockback 结论。