# Atlas Phase C Step 1 Review

【签名】Atlas
【时间】2026-04-11
【设备】MacBook

## 1. 复核结论

Step 1 当前可以作为 Phase C 的首版执行矩阵继续使用，覆盖范围、任务态描述和“不直接等于代码授权”的边界基本合格。

## 2. 发现的问题

1. 协同阻断项：`ATLAS_TO_QWEN_PHASE_C_STEP2.md` 与 `ATLAS_TO_QWEN_PHASE_C_STEP3.md` 原本把 `QWEN_PHASE_C_STEP1_REPORT.md` 当成必需输入，但当前协同目录中不存在该文件，若不修正会直接卡住后续轮动。
2. 锚点严谨性问题：Step 1 中部分路径当前并不存在，后续不得再把它们写成“真实已存在锚点”。已抽样确认不存在的路径包括：
   - `services/backtest/src/backtest/manual_runner.py`
   - `services/decision/src/publish/strategy_importer.py`
   - `services/decision/src/publish/yaml_importer.py`
   - `services/decision/src/notify/feishu_bot.py`
   - `services/decision/src/research/nlp_strategy_generator.py`
   - `shared/python-common/src/**`
3. 首批候选方向未见明显偏航：`C0-1`、`CB5`、`CG2` 继续作为第一批候选项是成立的，其中 `C0-1` 与 `CB5` 的现有基础最好，`CG2` 则属于回测端新增能力但主责边界清楚。

## 3. 处理决定

1. 允许直接进入 Step 2，不等待额外重写 Step 1 报告文件。
2. Step 2 起必须显式区分：`existing-anchor` 与 `planned-placeholder`。
3. 后续若某项只剩计划描述、没有真实现成锚点，Atlas 会优先把它归到“待补只读证据”或后置，而不是直接推进为首批预审包。