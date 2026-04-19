# HANDOFF-U0-20260419-011 — decision 流水线七项逻辑缺陷修复

| 字段 | 值 |
|------|-----|
| 任务 | TASK-U0-20260419-011 |
| 模式 | U0 事后审计 |
| 服务 | decision |
| 完成日期 | 2026-04-19 |
| 交付人 | Atlas |
| 状态 | ✅ 收口完成 |

## 交付摘要

本次 U0 修复 decision 流水线中 7 项积累逻辑缺陷（2 个 P0，5 个 P1），涉及 3 个文件。

### 核心修复内容

| Bug | 级别 | 文件 | 根因 | 修复方式 |
|-----|------|------|------|---------|
| 1 | P0 | run_full_pipeline_35_symbols.py | `if "parameters" in strategy_data` 永远为 False，Optuna 最优参数未写回 YAML | 改为遍历 `factors[i]["params"]`，同步处理 stop_loss/take_profit/position_fraction |
| 2 | P0 | run_full_pipeline_35_symbols.py | Step 2 回测未传 `params_override`，最优参数被丢弃 | 补传 `params_override=best_params` |
| 3 | P1 | strategy_param_optimizer.py | `risk.get("stop_loss")` 找不到顶层字段 | 改为 `strategy.get("stop_loss")` |
| 4 | P1 | strategy_param_optimizer.py | fast/slow 约束遗漏 MACD 命名（fast/slow vs fast_period/slow_period） | 两种命名都检查，`reoptimize_recycled` 同步修复 |
| 5 | P1 | yaml_signal_executor.py | `SignalBacktestResult` 无 trades 字段，XGBoost 永远收到空列表 | 新增 `trades: list` 字段，`_simulate_trades()` 写入原始交易记录 |
| 6 | P1 | run_full_pipeline_35_symbols.py | `train()` 需要 `(X, y)`，直接传 raw trades 导致类型错误 | 先调 `collect_trade_features(trades)` 得到 `(X, y)` |
| 7 | P1 | run_full_pipeline_35_symbols.py | `filter_signals()` 参数类型和个数不匹配 | Step 2b 改为纯训练环节 |

### 影响评估

- **Bug 1+2 影响全局**：修复前所有 Optuna 调优结果均无效（最优参数从未生效），TqSdk 提交的策略均使用原始参数。修复后所有新跑流水线将正确使用最优参数。
- **历史结果**：修复前产出的评分和 TqSdk 结果需视为无效，建议重新跑全量流水线。

## 验收记录

- AST 语法验证：3/3 通过
- 功能性检查：15/15 通过
- XGBoost import 版本：2.1.4 ✅
- REVIEW-U0-20260419-011：通过 ✅（8 项全部通过）
- Git commit：见下

## Git 提交

| 提交 | 内容 |
|------|------|
| `fix(decision): decision流水线七项逻辑缺陷修复 — Optuna参数写回+XGBoost接口对齐` | 3个业务文件 + 4个收口文档 |

## 后续建议

1. **建议立即重跑全量流水线**（`run_full_pipeline_35_symbols.py`），以获得使用真实最优参数的策略评分。
2. `reoptimize_recycled` 中的 fast/slow 约束修复（Bug 4）在回炉再调优任务中生效，下次触发再观察。
3. 本次不涉及 shared/contracts 或跨服务字段，无需通知其他服务。

## 锁控引用

- `docs/locks/lock-U0-20260419-011.md` 🔒 locked
