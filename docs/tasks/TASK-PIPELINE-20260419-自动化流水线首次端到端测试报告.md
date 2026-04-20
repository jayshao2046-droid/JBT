# TASK-PIPELINE-20260419 — 自动化流水线首次端到端测试报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 测试日期 | 2026-04-19 12:57 ~ 13:05 |
| 测试品种 | rb（螺纹钢）|
| 策略数量 | 1（max-strategies 1）|
| 回测区间 | 2025-11-20 ~ 2025-12-31 |
| Optuna 试验 | 30 trials |
| TqSdk 模式 | final-only |
| 退出码 | **0（成功）** |
| 总耗时 | **8 分 19 秒** |

## 结果总览

| 阶段 | 状态 | 耗时 | 备注 |
|------|------|------|------|
| 品种特征分析 | ⚠ 回退 | 1s | 日线数据不足，使用默认特征 |
| 策略设计（gpt-5.4）| ✅ | 40s | EMA_Cross + ADX + ATR, trend_following |
| YAML 生成（deepseek-v3.2）| ✅ | 17s | rb_trend_60m_v1.yaml |
| [1/5] 首轮调优 Round 1 | ⚠ 零交易 | 120s | 代码 atr_pct > 0.006 过严 |
| [1/5] Critic 修正 + Round 2 | ✅ | 99s | best_value=259, Critic 修正 atr 0.006→0.0006 |
| [2/5] 本地回测 | ✅ | 106s | 233 笔交易，23.7% 信号覆盖率 |
| [2b] XGBoost 训练 | ✅ | 2s | 233 样本，99.14% 准确率 |
| [3/5] TqSdk 回测 | ⚠ 0 笔交易 | 21s | **Bug #13**: 策略注册成功但无交易 |
| [4/5] 策略评分 | ✅ | 89s | 57 分，D 等级 |
| [5/5] 分桶归档 | ✅ | <1s | → 小于60分/rb/rb_trend_60m_v1 |
| [6/6] 飞书通知 | ✅ | <1s | HTTP 200 OK |

## 策略评分明细

| 维度 | 得分 | 满分 | 备注 |
|------|------|------|------|
| 基础合规 (basic) | 25 | 30 | threshold 范围警告 |
| 回测绩效 (backtest) | 13 | 30 | Sharpe -1.15, 胜率 47.6%, 总回报 -0.7% |
| 过拟合检验 (PBO) | 0 | 10 | 4 个季度全部 Sharpe 为负 |
| 因子有效性 (factor) | 0 | 10 | EMA_Cross IC 均值 -0.30 |
| 风险管理 (risk) | 15 | 20 | ATR 倍数 1.0 低于建议范围 1.5~3.5 |
| 风险调整奖励 | +4 | — | |
| **总分** | **57** | **100** | **D 等级，不可部署** |

## 本地回测 vs TqSdk 回测对比

| 指标 | 本地回测 | TqSdk 回测 |
|------|---------|-----------|
| 交易笔数 | 233 | **0** ⚠ |
| 最终权益 | ¥496,456 | ¥500,000 |
| 总回报 | -0.71% | 0.00% |
| Sharpe | -1.15 | 0.00 |
| 胜率 | 47.6% | N/A |
| 最大回撤 | 0.81% | 0.00% |

## LLM 成本明细

| 阶段 | 模型 | 耗时 | 费用 |
|------|------|------|------|
| 策略设计 | gpt-5.4 | 40s | ¥0.012 |
| YAML 生成 | deepseek-v3.2 | 17s | ¥0.006 |
| Round 1 代码生成 | gpt-5.4 | 114s | ¥0.036 |
| Round 1 代码审核 | gpt-5.4 | 6s | ¥0.002 |
| Round 2 代码生成 | gpt-5.4 | 89s | ¥0.030 |
| Round 2 代码审核 | gpt-5.4 | 6s | ¥0.002 |
| 本地回测代码生成 | gpt-5.4 | 100s | ¥0.032 |
| 本地回测代码审核 | gpt-5.4 | 6s | ¥0.002 |
| 评分代码生成 | gpt-5.4 | 78s | ¥0.026 |
| 评分代码审核 | gpt-5.4 | 10s | ¥0.002 |
| **合计** | — | — | **¥0.150** |

> 计费系统记录：8 calls, 14870 in + 21019 out tokens, ¥0.132（不含 deepseek-v3.2 的 ¥0.006 和策略设计 ¥0.012）

## 发现的问题清单

### Bug #8 — httpx 共享客户端 TCP 挂死 [已修复]
- **表现**: 多次 API 调用后 httpx 共享连接池死亡
- **修复**: 改为每次请求创建独立 `httpx.AsyncClient`
- **状态**: ✅ 已验证

### Bug #9 — 日志噪音过大 [已修复]
- **表现**: Optuna 30 trials 每次都打印完整代码（logger.info）
- **修复**: `logger.info` → `logger.debug` 用于代码打印
- **状态**: ✅ 已验证

### Bug #10 — LLM 生成代码含 import 语句被 AST 拒绝 [已修复]
- **表现**: GPT-5.4 生成 `import math` 导致 `_ast_whitelist_check()` 拒绝
- **修复**: (1) prompt 添加 "DO NOT use any import statements!" (2) 正则自动剥离 `import math` / `from math import`
- **状态**: ✅ 已验证（3 次代码生成全部 attempt 1 通过）

### Bug #11 — GPT-5.4 代码中 atr 阈值偏差 [已缓解]
- **表现**: YAML 指定 `atr > 0.0006 * close`，但 GPT-5.4 生成代码硬编码 `atr_pct > 0.006`（10 倍偏差）
- **影响**: Round 1 必然零交易，需要 Critic 修正后 Round 2 才能成功
- **缓解**: Critic 自动检测零交易 + 修正 atr 阈值
- **状态**: ⚠ 未根治，每次多耗一轮 LLM 调用（~90s + ¥0.032）
- **建议**: 在 prompt 中明确添加 "atr 阈值必须与 YAML market_filter.conditions 完全一致" 或在代码生成后自动替换

### Bug #12 — TqSdk 客户端不识别 "submitted" 状态 [低优先级]
- **表现**: `未知回测状态: submitted`
- **影响**: 仅一条 WARNING 日志，不阻塞（继续轮询后成功）
- **建议**: 在 `tqsdk_backtest_client.py` 中添加 "submitted" 到已知状态列表

### Bug #13 — TqSdk 回测 0 笔交易（本地有 233 笔）[高优先级]
- **表现**: TqSdk 回测引擎成功接收策略、成功运行，但产生 0 笔交易
- **影响**: TqSdk 回测结果无参考价值，评分仅依赖本地回测
- **可能原因**: (1) YAML → TqSdk 策略翻译缺失信号逻辑 (2) TqSdk 引擎未正确解析 LLM 生成的 compute_signals (3) 合约代码 rb2505 在回测区间可能未上市
- **建议**: 需检查 `services/backtest/` 中策略执行路径

### Bug #14 — SymbolProfiler 日线数据不足 [低优先级]
- **表现**: `品种 SHFE.rb 数据不足` → 使用默认特征
- **影响**: 策略设计缺少真实品种特征指导，使用通用模板
- **原因**: 数据服务 `KQ_m_SHFE_rb` 日线数据缺失或不足
- **建议**: 检查数据服务日线数据源

## 性能基准

| 操作 | 耗时 |
|------|------|
| GPT-5.4 代码生成 | 78~114s |
| GPT-5.4 代码审核 | 6~10s |
| GPT-5.4 策略设计 | 40s |
| deepseek-v3.2 YAML 生成 | 17s |
| Optuna 30 trials（有交易）| 3s |
| Optuna 30 trials（零交易）| 3s |
| TqSdk 提交+完成 | 21s |
| 数据拉取（60m, 1个月）| <1s |
| XGBoost 训练 | 2s |
| 飞书通知 | <1s |

## 文件产出

- `strategies/llm_ranked/小于60分/rb/rb_trend_60m_v1/strategy.yaml`
- `strategies/llm_ranked/小于60分/rb/rb_trend_60m_v1/reports/`
  - `evaluator_report.json` — 评分报告
  - `local_backtest_report.json` — 本地回测（含生成代码）
  - `tqsdk_backtest_report.json` — TqSdk 回测
  - `optimization_report.json` — Optuna 调优报告
  - `generation_report.json` — 策略生成报告
- `runtime/billing/billing_20260419_1300.json` — 计费记录
- `runtime/strategy_attribution/rb_trend_60m_v1.json` — 归档归因

## 结论

**流水线首次全流程跑通，6/6 阶段全部完成，exit code 0。** 策略得分 57 分（D 等级），虽然不满足上线标准（≥60 分），但证明：

1. ✅ 端到端流程可工作
2. ✅ LLM 代码生成 + AST 安全沙箱正常
3. ✅ Optuna 参数调优有效
4. ✅ XGBoost 信号过滤训练正常
5. ✅ TqSdk 回测服务可连接
6. ✅ 评分系统正确计算
7. ✅ 分桶归档正确执行
8. ✅ 飞书通知正常发送

**下一步建议**:
1. **P0**: 排查 Bug #13（TqSdk 0 交易 vs 本地 233 交易）
2. **P1**: 根治 Bug #11（atr 阈值偏差），减少无效 Round 1
3. **P2**: 修复 Bug #12（submitted 状态识别）
4. **P2**: 扩大测试：多品种、多策略模板
