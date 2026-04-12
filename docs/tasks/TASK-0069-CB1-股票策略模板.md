# TASK-0069 — CB1 股票策略模板（短/中/长期）

【签名】Atlas
【时间】2026-04-12 15:10
【设备】MacBook
【优先级】P1
【状态】执行中

---

## 任务背景

Decision Phase C CB（股票研究链路）中的基础模板层。CB1 提供面向日线的三类股票策略模板，作为研究中心股票研究的起点，供后续 CB4（股票池管理器）、CB6~CB8（盘中跟踪/盘后评估/晚间再选）以及 decision_web stock 看板页面调用。

## 验收标准

1. 新增 `services/decision/src/research/stock_templates.py`：
   - `ShortTermStockTemplate` — 短期（1~5日），基于动量/成交量因子
   - `MidTermStockTemplate` — 中期（5~20日），基于趋势/均线因子
   - `LongTermStockTemplate` — 长期（20日+），基于价值/基本面因子
   - 每个模板有 `name`, `holding_days`, `required_factors`, `entry_signal()`, `exit_signal()` 接口
   - 模板支持从 factor_loader 加载历史日线数据
2. 新增 `services/decision/src/api/routes/stock_template.py`：
   - `GET /api/v1/stock/templates` — 列出三类模板定义
   - `POST /api/v1/stock/templates/{name}/backtest` — 对指定模板跑沙箱回测（调用 CB2' sandbox）
3. 更新 `services/decision/src/api/routes/__init__.py`：注册 stock_template 路由
4. 新增 `services/decision/tests/test_stock_templates.py`：≥ 10 个测试用例

## 文件白名单

- `services/decision/src/research/stock_templates.py`（新建）
- `services/decision/src/api/routes/stock_template.py`（新建）
- `services/decision/src/api/routes/__init__.py`（更新路由注册）
- `services/decision/tests/test_stock_templates.py`（新建）

## 依赖

- CB2'（股票沙箱回测引擎）✅ TASK-0057 已完成
- C0-2（FactorLoader 股票支持）✅ TASK-0053 已完成
- C0-1（股票 bars API 路由）✅ TASK-0050 已完成

## 执行 Agent

Claude-Code
Token: 待签发（TASK-0069）

## 备注

- 模板只定义因子组合与信号逻辑，不包含选股排名（CB3 已完成）
- 持仓天数是参考值，实际止损由 CS1 / 执行层控制
- entry_signal / exit_signal 接收 pd.DataFrame（日线 K 线），返回 bool
