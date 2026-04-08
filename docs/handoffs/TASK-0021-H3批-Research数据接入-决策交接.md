# TASK-0021 H3 批 — research 真实 data API 接入与运行依赖交接单

【签名】决策 Agent  
【交接时间】2026-04-08  
【review_id】REVIEW-TASK-0021-H3  
【token_id】tok-c9b73a9a-c9aa-40a8-8d51-2e23cefe88f3

---

## 执行结果摘要

**状态：已完成，待项目架构师终审与 lockback**

---

## 任务信息

- 任务 ID：TASK-0021-H3
- 执行范围：仅限 3 个业务白名单文件
- 批次目标：把 `FactorLoader` 从随机 mock 升级为通过 data service bars API 获取真实序列，并补齐 research 运行依赖与定向测试

---

## 变更文件清单

1. `services/decision/pyproject.toml`
2. `services/decision/src/research/factor_loader.py`
3. `services/decision/tests/test_research.py`
4. `docs/prompts/agents/决策提示词.md`

---

## 改动说明

1. `factor_loader.py` 去掉随机 `numpy` mock，改为使用 `settings.data_service_url` 指向的 `GET /api/v1/bars` 拉取真实 bars；当前最小闭环下，将 `strategy_id` 直接作为 bars API 的 `symbol` 参数透传，后续若策略仓库补齐显式 data symbol 字段，再在此处替换映射逻辑。
2. 基于真实 bars 构造 5 维基础特征：`close_return`、`intrabar_range`、`candle_body`、`volume_return`、`open_interest_return`；标签 `y` 定义为“下一根 K 线收盘价是否高于当前收盘价”的二分类结果，形成最小可训练闭环。
3. 为兼容现有调用签名，`n_features` 大于 5 时按滞后列顺序补齐矩阵宽度；`n_samples` 仍作为最终样本上限裁剪。
4. 上游 HTTP 失败、payload 非法、关键字段缺失或 bars 数量不足时，显式抛出 `FactorLoadError`；本批不再保留任何静默回退到 mock 成功的路径。
5. `pyproject.toml` 将 `python` 归位到 `tool.poetry.dependencies`，并补齐 `numpy`、`xgboost`、`optuna`、`shap`、`onnxruntime`、`onnxmltools` 六项 research 运行依赖，覆盖当前 research 模块实际 import 面。
6. `test_research.py` 将旧的 mock load 用例替换为两条核心场景：
   - 成功从 bars API 拉取真实序列并构造稳定可测的 `X/y`；
   - data service 不可用时显式失败，不再静默返回随机矩阵。

---

## 验证结果

1. 3 个白名单业务文件 `get_errors` 结果均为 `No errors found`。
2. 已执行：`cd services/decision && PYTHONPATH=. ../../.venv/bin/pytest tests/test_research.py -q`
3. 结果：`13 passed in 0.33s`
4. 已执行：`python3 -c 'from pip._vendor import tomli; import pathlib; tomli.loads(pathlib.Path("pyproject.toml").read_text(encoding="utf-8")); print("pyproject parsed")'`
5. 结果：`pyproject parsed`

---

## 待审问题

1. 当前最小实现中，`strategy_id` 被直接当作 bars API 的 `symbol` 参数使用；这满足 H3“真实 data API + 最小特征闭环”目标，但如果后续策略 ID 与行情 symbol 分离，仍需在策略仓库或 research 输入面补显式映射，不在本批范围内扩展。
2. 本轮仅完成 research 数据接入与依赖补齐；研究快照 / 回测证书持久化以及 publish 真闭环仍分别留给 `H2`、`H4`。
3. 当前环境未执行 `poetry install --only main` 全量安装验证；已完成的是 pyproject 解析检查与定向 pytest，自校验范围满足本批直接相关要求。

---

## 向 Jay.S 汇报摘要

1. `TASK-0021-H3` 已按 3 文件白名单完成：`FactorLoader` 不再返回随机 mock，而是通过 data service 的 `/api/v1/bars` 获取真实序列并构造最小可用 `X/y`。
2. 本次没有跨服务 import，只通过 HTTP 调用 data API；默认读取现有 `data_service_url`，且上游不可用时会显式失败，不再伪装成成功。
3. 与改动直接相关的自校验已完成：3 文件静态诊断为 0，`tests/test_research.py` 结果 `13 passed`，`pyproject.toml` 解析通过。

---

## 下一步建议

1. 进入项目架构师终审；若通过，立即按 `REVIEW-TASK-0021-H3` 执行 lockback。
2. 在 Jay.S 未确认前，不自动进入 `TASK-0021-H2` 或 `TASK-0021-H4`。