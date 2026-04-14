# TASK-0114 — 决策端 35 品种自适应模型注册表 + 行情检测

【创建】2026-04-15
【服务归属】`services/decision/`
【执行 Agent】Claude-Code
【复核】Atlas
【状态】建档完成，待签发

## 任务概述

为期货 35 个品种建立品种级 XGBoost 模型注册表，每个品种独立训练、独立参数搜索、独立评估，并引入行情检测器（趋势/震荡/高波动）将 phi4-reasoning 作为行情分类执行者，实现每个品种对不同行情类型自适应切换最优参数集。

## 背景

当前所有品种共用一个 XGBoost 分类器，是最大隐患：
- 螺纹钢趋势性强，铜价格发现功能强，铝消费端驱动，三者参数体系不同
- regime（行情类型）不同导致同一参数组产生大量假信号
- 需要品种级模型 + 行情类型 × 参数集矩阵

## 分批计划

### Batch A — 品种模型注册表（P1，4 文件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/decision/src/research/model_registry.py` | 新建 | ModelRegistry：按品种存储 XGBClassifier，支持 register/get/list/retire；内存 + 可选持久化 |
| `services/decision/src/research/regime_detector.py` | 新建 | RegimeDetector：调 phi4-reasoning 判断行情类型（trend/oscillation/high_vol）；输入5日/20日K线；输出 regime + confidence |
| `services/decision/src/research/trainer.py` | 修改 | 升级为品种级训练：train_for_symbol(symbol, regime, X, y) + 方案B增量训练（xgb_model参数追加） + 真实收益序列 Sharpe（此改动与TASK-0112-C联动，TASK-0114执行时须以Batch C为前置） |
| `services/decision/tests/test_model_registry.py` | 新建 | 测试注册/获取/注销/品种隔离；mock行情检测；增量训练不覆盖其他品种 |

## 质量标准

- 35 品种列表：rb, hc, i, j, jm, cu, al, zn, ni, ss, au, ag, sc, fu, bu, ru, sp, ap, cf, sr, ma, ta, eg, pp, l, v, eb, pg, lh, p, y, a, c, cs, m
- 每个品种独立注册，互不干扰
- regime_detector 调 phi4 超时（15s）时降级为"trend"（保守）
- Optuna 夜间给每个品种搜索最优参数后，注册到对应品种 regime 槽位
- trainer.py 增量训练：`xgb_model` 参数追加，配合验证集监控防灾难性遗忘

## 依赖

- 必须在 TASK-0112 Batch C 完成后执行（trainer.py 真实 Sharpe 前置）
- 行情检测调用 phi4-reasoning:14b 于 Ollama `http://192.168.31.142:11434`
