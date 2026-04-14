# TASK-0116 — 决策端因子挖掘自动化

【创建】2026-04-15
【服务归属】`services/decision/`
【执行 Agent】Claude-Code
【复核】Atlas
【状态】建档完成，待签发

## 任务概述

实现两条因子挖掘路线：(1) AI 提案驱动（Jay.S 给意图 → deepcoder 生成因子代码 → IC 验证 → 注册）；(2) 数据驱动（候选特征池自动组合 → IC 排序 → SHAP 剪枝）。因子验证后自动注册到 factor_loader，失效因子飞书报警并标记 deprecated。

## 背景

候选特征池（期货品种）：OHLC、成交量、OI/仓差、基差（近月-连续）、期限结构斜率、跨品种价差（rb-i、hc-rb、p-y）。  
因子注册后由 TASK-0115 factor_monitor 持续监控 IC 衰减。

## 分批计划

### Batch A — 因子挖掘核心（P1，4 文件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/decision/src/research/factor_miner.py` | 新建 | FactorMiner：(1) AI 提案模式：接收意图 → 调 deepcoder 生成因子代码 → 安全 eval 测试 IC；(2) 数据驱动模式：候选特征笛卡尔积 → IC 排序 → 取前 Top-K；输出 FactorCandidate 列表 |
| `services/decision/src/research/factor_validator.py` | 新建 | FactorValidator：(1) IC 计算（Information Coefficient，预测 vs 实际涨跌相关性）；(2) IC 衰减分析（半衰期估算）；(3) OOS 验证（样本外 3 个月）；(4) 通过率 IC_mean > 0.05 且 IC_decay > 5 日则注册到 factor_loader |
| `services/decision/src/api/routes/factor.py` | 新建 | API 端点：POST /api/v1/factor/mine（触发挖掘）、GET /api/v1/factor/candidates（查看候选）、POST /api/v1/factor/validate/{factor_id}（手动触发验证）、GET /api/v1/factor/registry（查看已注册因子） |
| `services/decision/tests/test_factor_mining.py` | 新建 | 测试：AI 提案 IC 达标自动注册、IC 不达标拒绝、OOS 验证失败降级、factor_loader 注册后可查询 |

## 质量标准

- IC 计算使用 Spearman 相关系数（rank-based，对异常值鲁棒）
- AI 提案模式因子代码 eval 必须在沙箱中执行（禁止 import os/sys/subprocess）
- IC 半衰期 < 3 日的因子直接拒绝
- 数据驱动模式候选组合 < 200 个（防止组合爆炸）
- 所有因子带品种标签（适用品种列表）和 regime 标签

## 依赖

- 调用 data API 拉取历史 bars 用于 IC 计算
- 调用 deepcoder:14b 生成因子代码（已有 OllamaClient）
- 不依赖 TASK-0114/0115，可独立执行
