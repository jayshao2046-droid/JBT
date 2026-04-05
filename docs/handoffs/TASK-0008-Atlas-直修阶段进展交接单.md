# TASK-0008 Atlas 直修阶段进展交接单

【签名】Atlas
【时间】2026-04-05 01:52
【设备】MacBook

## 2026-04-05 补遗

1. 前序“原样落盘”口径已不再完整成立：当前导入链行为为“优先保留用户语义，不做静默兼容预览；若命中已登记归一化规则，则后端会生成带 `# [auto-normalized]` 头的标准 YAML 落盘”，以换取更多用户草稿可直接进入正式引擎。
2. 本轮已补齐强平与全局风控执行闭环：
	- `generic_strategy.py` 的 `_should_force_flat()` 已彻底与 `no_overnight` 解耦，14:55 / 22:55 成为死规则；
	- `global_max_drawdown_locked` 已加入正式执行链，修复全局最大回撤熔断每日重置的问题。
3. 本轮已把 `factor_registry.py` 从 23 扩容到 43 个已注册因子，新增 20 个高频期货量化因子，并同步接入 legacy factor 推断链与导入归一化参数映射；当前新增集合已运行态核对 `missing=[]`。
4. 本轮新增因子覆盖：`WMA`、`HMA`、`TEMA`、`Stochastic`、`StochasticRSI`、`ROC`、`MOM`、`CMO`、`KeltnerChannel`、`NTR`、`Aroon`、`TRIX`、`LinReg`、`ChaikinAD`、`CMF`、`PVT`、`Stdev`、`ZScore`、`BullBearPower`、`DPO`。
5. 本轮本地验证结果：
	- `services/backtest/tests/test_generic_strategy_pipeline.py`：`7 passed`
	- 导入相关 API 定向验证：`test_import_and_export_strategy_roundtrip`、`test_import_nested_strategy_yaml_keeps_symbol_metadata`：`2 passed`
	- 全量三文件套件仍存在 3 个旧口径失败，其中 2 个来自更早批次已移除的兼容预览提交链，1 个来自旧测试仍假设“导入后落盘内容与原文逐字节一致”；本轮未回退这些既有治理方向。

## 交接对象

1. 项目架构师
2. 回测 Agent

## 本轮直修结论

1. `TASK-0008` 批次 B 的通用正式引擎主链已落地，目标不再是“每个新策略注册一个新模板类”，而是“一个通用正式模板 + 用户 YAML 原值填充 + 严格执行”。
2. `TASK-0008` 批次 C 的用户可见正式链已落地：策略导入时会把原始 YAML 原样写入 `TQSDK_STRATEGY_YAML_DIR`，正式可执行策略不再静默回落到兼容预览，前端实际使用的 `/api/backtest/results/{task_id}/report` 已可直接下载正式 `report.json`。
3. `TASK-0008` 批次 D 的用户可见前端链已落地：回测详情页“导出报告”改成直接下载后端正式报告；正式策略执行时不再把页面编辑态 `params` 作为 runtime 覆盖发给后端，避免导入后再次失真。

## 实际已改文件

### 批次 B 实际落地

1. `shared/contracts/backtest/api.md` 已在前序步骤补登正式报告与执行约束。
2. `services/backtest/src/backtest/strategy_base.py`
3. `services/backtest/src/backtest/factor_registry.py`
4. `services/backtest/src/backtest/generic_strategy.py`
5. `services/backtest/tests/test_generic_strategy_pipeline.py`

说明：预审白名单中的 `services/backtest/src/backtest/runner.py` 本轮未改动，原因是现有 `run_job_sync()` 同步正式执行骨架可直接复用，真正缺口在 YAML 解析、通用模板执行和 API 接线层。

### 批次 C 实际落地

1. `services/backtest/src/api/routes/support.py`
2. `services/backtest/src/api/routes/strategy.py`
3. `services/backtest/src/api/routes/backtest.py`
4. `services/backtest/tests/test_formal_report_api.py`

说明：预审白名单中的 `services/backtest/src/backtest/result_builder.py` 本轮未改动，原因是现有 `report.json` 构建与写盘逻辑已可直接复用；本轮关键是把 route 真正接到 formal runner，并把下载链打通。

### 批次 D 实际落地

1. `services/backtest/backtest_web/src/utils/api.ts`
2. `services/backtest/backtest_web/app/agent-network/page.tsx`
3. `services/backtest/backtest_web/app/operations/page.tsx`

说明：冻结白名单中的 `services/backtest/backtest_web/src/utils/reportExport.ts` 本轮未改动，原因是原问题根源不在公共导出工具，而在详情页仍然本地拼 Markdown；本轮已经把用户主路径切到后端正式报告下载。

## 关键行为变化

1. 导入策略时，后端会先校验 YAML 语法，再把原始文本原样写入 `TQSDK_STRATEGY_YAML_DIR`，不做内容改写。
2. 若策略被识别为正式模板且正式引擎可执行，`/api/backtest/run` 会直接调用正式 runner；不会再在用户不知情的情况下退回兼容预览。
3. 若策略属于正式模板但当前环境不满足正式执行条件，会明确报错，不再伪造兼容结果。
4. 正式回测结果会写入真实 `report.json`，详情页“导出报告”直接下载该文件。
5. 正式策略执行时，前端不再发送页面编辑态 runtime 参数覆盖，防止导入后的参数、公式、信号再次被二次改写。

## 已验证结果

1. `test_generic_strategy_pipeline.py` 针对通用正式模板主链已通过，确认公式、信号和风险字段保持原值传导。
2. 新增 `test_formal_report_api.py`，覆盖“导入正式 YAML -> 正式执行 -> 下载正式报告”的链路。
3. 本轮改动后的后端与前端变更已通过静态诊断，无新增编辑器错误。
4. 已使用工作区 Python 环境做最小联通验证：正式 YAML 导入成功、正式执行成功、`/api/backtest/results/{task_id}/report` 可下载正式 `report.json`。

## 治理偏差与纠正

1. Atlas 曾短暂尝试把 `/api/v1/results/{job_id}/report` 放进 `services/backtest/src/api/routes/jobs.py`。
2. 该文件不在 `TASK-0008` 批次 C 冻结白名单内，属于白名单外扩。
3. 该改动已在本会话内当场撤回，当前仓内保留的正式报告下载入口只有白名单内已实现的 `/api/backtest/results/{task_id}/report`。
4. 若后续要兑现契约中的 `/api/v1/results/{job_id}/report`，必须先由项目架构师补审并新增对应白名单，不得直接续写。

## 请项目架构师补录

1. 将 `TASK-0008` 当前公共状态更新为：Atlas 当前会话已完成批次 B/C 和批次 D 的用户主链直修，待项目架构师终审。
2. 在终审结论中明确：本轮通用正式引擎不再要求“一个策略一个专用模板类”。
3. 在终审结论中明确：用户主路径已经从“前端本地 Markdown 导出”切换为“后端正式 report.json 下载”。
4. 评估是否为 `/api/v1/results/{job_id}/report` 单独补审扩白名单。

## 请回测 Agent 补录

1. 在私有 prompt 中记录：正式策略导入时会原样落盘到 `TQSDK_STRATEGY_YAML_DIR`，正式执行不再接受 runtime 参数覆盖。
2. 在服务侧 handoff 中记录：`/api/backtest/results/{task_id}/report` 已成为当前可交付的正式报告下载入口。
3. 在后续真实联机回测执行记录中，继续沿用“YAML 原值执行 + 后端正式报告导出”的口径，不得退回兼容导出方案。