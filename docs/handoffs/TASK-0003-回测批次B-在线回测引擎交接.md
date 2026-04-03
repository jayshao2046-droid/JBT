# TASK-0003 回测批次 B 在线回测引擎交接

【签名】回测 Agent
【时间】2026-04-03
【设备】MacBook

## 任务信息

- 任务 ID：TASK-0003
- 批次：B
- token_id 摘要：tok-60193dc1-e1be-459b-8133-c49e454adc0c
- 执行范围：仅限批次 B 五个白名单文件

## 本轮完成动作

1. 新建 `services/backtest/src/backtest/session.py`，实现基于 `TqSim()` + `TqBacktest` + `TqAuth` + `TqApi` 的会话管理器，并在配置层强制校验第一阶段仅允许 `online` + `sim`。
2. 新建 `services/backtest/src/backtest/strategy_base.py`，实现固定模板框架、模板注册表、一体化 YAML 读取与风险模型、权益曲线/风险违规观测结构。
3. 新建 `services/backtest/src/backtest/result_builder.py`，实现完整报告结果结构：权益曲线、绩效指标、风控摘要，并支持 `completed` / `failed` / `strategy_input_required` 三种状态。
4. 新建 `services/backtest/src/backtest/runner.py`，实现在线回测执行器、YAML 路径解析、异步提交/等待骨架，以及“缺策略输入时明确返回检查点状态”的收口逻辑。
5. 新建 `services/backtest/tests/test_health.py`，覆盖 app 包路径导入、健康检查路由存在性与健康响应元数据。
6. 本轮未改动批次 A 已锁回文件、看板目录、Docker、远端部署或 `shared/contracts/**`。

## 实际修改文件

1. `services/backtest/src/backtest/session.py`
2. `services/backtest/src/backtest/runner.py`
3. `services/backtest/src/backtest/strategy_base.py`
4. `services/backtest/src/backtest/result_builder.py`
5. `services/backtest/tests/test_health.py`

## 本地自校验结果

1. VS Code 诊断：批次 B 五个文件无错误。
2. `py_compile`：批次 A/B 相关 Python 文件全部编译通过。
3. 现有 FastAPI app 导入：`services.backtest.src.main` 包路径导入成功，`app_import_ok True`。
4. `pytest services/backtest/tests/test_health.py -q`：结果 `3 passed`。
5. 伪运行验证 1：使用临时 YAML、dummy session manager 和 smoke template，执行器返回 `completed`，报告结构可产出 `final_equity`、风险参数快照与 notes。
6. 伪运行验证 2：缺少策略 YAML 时，执行器稳定返回 `strategy_input_required`，错误信息为“策略 YAML 文件 missing.yaml 尚未提供，当前已到达需要 Jay.S 提供策略输入的检查点”。
7. 本轮未伪造真实回测结果，也未连真实 TqSdk 会话。

## 当前检查点

- **已达到“需要策略输入”检查点。**
- 当前引擎层面已具备：会话配置校验、固定模板框架、一体化 YAML 风控读取、报告结果结构、最小测试与导入校验。
- 当前尚未具备的唯一业务输入是：Jay.S 提供首轮真实策略实现/模板与配套一体化 YAML 文件。

## 待审问题

1. 首轮真实回测前，运行环境仍需提供有效的 `TQSDK_AUTH_USERNAME` / `TQSDK_AUTH_PASSWORD`。
2. 本轮白名单不包含批次 A 路由文件，因此在线引擎与结果结构尚未接到 `/api/v1/jobs` 和 `/api/v1/results/{job_id}` 的 HTTP 路径上；当前已把内部执行链推进到策略输入检查点，但对外 API 接线需后续单独授权。
3. backtest 契约草稿仍是早期通用口径，项目架构师可评估是否需要在后续授权批次中收敛到“固定模板 + 用户上传一体化 YAML”模型。

## 向 Jay.S 汇报摘要

- TASK-0003 批次 B 五个白名单文件已完成，实现了回测会话管理、固定模板框架、一体化 YAML 风控读取、结果汇总结构和最小测试。
- 本轮本地自校验通过：Python 可编译，现有 FastAPI app 可导入，`pytest` 最小健康检查通过，并完成一次不依赖真实策略/真实 TqSdk 的伪运行验证。
- 回测端已推进到**“需要策略输入”**检查点；如果 Jay.S 提供首轮真实策略实现/模板和对应 YAML，就可以进入首轮正式回测准备。

## 建议下一步

1. 请项目架构师终审批次 B 五个白名单文件，并在通过后立即执行 lockback。
2. 终审通过并锁回后，请立即向 Jay.S 汇报：回测端已到“需要策略输入”检查点，请提供首轮真实策略输入。
3. Jay.S 提供策略后，先执行首轮真实回测并输出完整报告；看板、Docker、远端交付保持后置，不在本批次处理。