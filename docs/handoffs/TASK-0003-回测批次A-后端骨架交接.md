# TASK-0003 回测批次 A 后端骨架交接

【签名】回测 Agent
【时间】2026-04-03 17:59
【设备】MacBook

## 任务信息

- 任务 ID：TASK-0003
- 批次：A
- token_id 摘要：tok-311d1a36-0cff-4141-939a-e96acadb9a38
- 执行范围：仅限批次 A 六个白名单文件

## 本轮完成动作

1. 在 `services/backtest/src/` 新增 FastAPI 服务入口、应用装配、健康检查路由、任务路由骨架与配置读取模块。
2. `jobs.py` 已明确采用“固定策略模板 + 用户上传一体化 YAML 文件”的任务创建入口，并限制第一阶段只接受期货回测。
3. 所有风控来源已在接口骨架和 README 口径中明确为 YAML，未写入任何硬编码风控参数。
4. `README.md` 已对齐当前已确认口径：在线回测主路径、固定模板 + 用户参数、一体化 YAML 风控、回测后推送决策端、同机同 compose 部署。
5. 未触碰 `tests/`、`configs/`、`src/backtest/session.py`、`runner.py`、`strategy_base.py`、`result_builder.py`、`shared/contracts/**` 与 `backtest_web/`。

## 实际修改文件

1. `services/backtest/src/main.py`
2. `services/backtest/src/api/app.py`
3. `services/backtest/src/api/routes/health.py`
4. `services/backtest/src/api/routes/jobs.py`
5. `services/backtest/src/core/settings.py`
6. `services/backtest/README.md`

## 最小自校验结果

1. VS Code 诊断：上述 5 个 Python 文件无错误。
2. `py_compile`：5 个 Python 文件语法编译通过。
3. 真实 app 构建检查：当前终端 Python 环境未安装 `fastapi`，因此无法在本机完成 `import services.backtest.src.main` 的运行态校验。
4. 代码层已定义的路由骨架为：`GET /api/v1/health`、`POST /api/v1/jobs`、`GET /api/v1/jobs`、`GET /api/v1/jobs/{job_id}`。

## 待审问题

1. 当前工作区终端缺少 `fastapi` 依赖；项目架构师终审时需在目标运行环境或镜像内补做一次实际启动校验。
2. `shared/contracts/drafts/backtest/backtest_job.md` 仍是早期通用字段口径，尚未收敛到 Jay.S 最新确认的“固定模板 + 用户上传一体化 YAML”模型；本轮未获授权修改契约草稿，仅先在服务骨架内按最新决策落地。

## 向 Jay.S 汇报摘要

- TASK-0003 批次 A 已按白名单完成后端骨架六文件写入，未越权触碰批次 B/C、共享契约或看板目录。
- 任务创建入口已明确采用“固定策略模板 + 用户上传一体化 YAML 文件”，并锁定第一阶段仅支持期货回测，所有风控来源均指向 YAML。
- 当前已完成静态自校验；由于本机终端未安装 FastAPI，实际 app 启动校验需在目标运行环境继续补做。

## 建议下一步

1. 先交项目架构师终审，确认无越权、无服务边界污染，并完成批次 A 锁回。
2. 终审通过后，申请 TASK-0003 批次 B 的 P1 Token，范围限定为 `session.py`、`runner.py`、`strategy_base.py`、`result_builder.py`、`tests/test_health.py`。
3. 由项目架构师补做一次契约口径核对，评估是否需要在后续批次前更新 backtest 任务契约草稿以对齐最新 YAML 决策。