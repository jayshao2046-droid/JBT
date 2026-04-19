# TASK-U0-20260419-011 — decision 流水线七项逻辑缺陷修复

| 字段 | 值 |
|------|-----|
| 模式 | U0 事后审计 |
| 服务 | decision（单服务） |
| 触发 | Jay.S 直修指令 — 2026-04-19 |
| 状态 | ✅ 已完成，待确认 |

## 修复清单

### Bug 1（P0 致命）：Optuna 最优参数从未写回 YAML
- **根因**：`process_one_strategy()` 中 `if "parameters" in strategy_data:` 判断永远为 False，LLM 生成的 YAML 用 `factors[i].params` 存参数，没有 `parameters` 顶层键
- **后果**：TqSdk 提交的 YAML 始终是原始未调优参数，100 次 Optuna 试验完全浪费
- **修复**：改为遍历 `factors[i]["params"]`，同时处理 `stop_loss.atr_multiplier`、`take_profit.atr_multiplier`、`position_fraction`
- **文件**：`scripts/run_full_pipeline_35_symbols.py`

### Bug 2（P0）：Step 2 本地回测忽略最优参数
- **根因**：`executor.execute(strategy, start_date, end_date)` 未传 `params_override`
- **修复**：`executor.execute(strategy, start_date, end_date, params_override=best_params)`
- **文件**：`scripts/run_full_pipeline_35_symbols.py`

### Bug 3（P1）：`_extract_param_space` 找不到止损止盈
- **根因**：代码用 `risk.get("stop_loss")` 查找，但 YAML 中 `stop_loss`/`take_profit` 是顶层字段
- **修复**：改为 `strategy.get("stop_loss")`
- **文件**：`src/research/strategy_param_optimizer.py`

### Bug 4（P1）：fast/slow 约束遗漏 MACD 命名
- **根因**：约束只检查 `fast_period/slow_period`，遗漏 `fast/slow`
- **修复**：两种命名都检查，`reoptimize_recycled` 的 objective 中同步修复
- **文件**：`src/research/strategy_param_optimizer.py`

### Bug 5（P1）：XGBoost — SignalBacktestResult 无 trades 字段
- **根因**：`local_result.to_dict().get("trade_features", [])` 永远返回 `[]`
- **修复**：在 `SignalBacktestResult` 新增 `trades: list` 字段，`_simulate_trades()` 写入原始交易记录
- **文件**：`src/research/yaml_signal_executor.py`

### Bug 6（P1）：XGBoost — train() API 调用错误
- **根因**：直接传 raw trades 给 `train()`，但签名需要 `(X: ndarray, y: ndarray)`
- **修复**：先调 `collect_trade_features(trades)` 得到 `(X, y)`
- **文件**：`scripts/run_full_pipeline_35_symbols.py`

### Bug 7（P1）：XGBoost — filter_signals() API 调用错误
- **根因**：传入参数类型和个数都不匹配
- **修复**：Step 2b 改为纯训练环节
- **文件**：`scripts/run_full_pipeline_35_symbols.py`

## 涉及文件（3 个）

| 文件 | 修改类型 |
|------|----------|
| `services/decision/scripts/run_full_pipeline_35_symbols.py` | Bug 1, 2, 6, 7 |
| `services/decision/src/research/strategy_param_optimizer.py` | Bug 3, 4 |
| `services/decision/src/research/yaml_signal_executor.py` | Bug 5 |

## 验证

```
✓ src/research/strategy_param_optimizer.py — AST 语法通过
✓ scripts/run_full_pipeline_35_symbols.py — AST 语法通过
✓ src/research/yaml_signal_executor.py — AST 语法通过
✓ xgboost 2.1.4 import OK
✓ SignalBacktestResult.trades field OK, to_dict() clean
✓ XGBoostSignalFilter.train(X, y) API correct
✓ stop_loss from strategy (not risk)
✓ fast/slow both naming variants
✓ zero_trades detection in optimize()
✓ enqueue_trial warm start
✓ suggest_float with step
✓ best_params write-back to factors[i][params]
✓ executor.execute with params_override
✓ early exit on optimization failure
✓ previous_params warm-start tracking
✓ zero_trades diagnosis retry
```

## 待用户确认后操作
- 补提交 + 锁回 + 同步
