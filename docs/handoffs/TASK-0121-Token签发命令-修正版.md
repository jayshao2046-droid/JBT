# TASK-0121 Token 批量签发命令（修正版）

【创建人】Livis Claude
【创建时间】2026-04-16
【执行方式】Jay.S 在终端执行

---

## 📋 正确的 Token 签发命令

请在终端执行以下命令，一次性签发 3 枚 Token：

```bash
cd /Users/jayshao/JBT

# Token 1: TASK-0121-A 策略评估流水线（5 文件，480 分钟）
python governance/jbt_lockctl.py issue \
  --task TASK-0121-A \
  --agent "Claude-Code" \
  --action "实现策略评估流水线（StrategyEvaluator）" \
  --ttl-minutes 480 \
  --files \
    services/decision/src/research/strategy_evaluator.py \
    services/decision/tests/test_strategy_evaluator.py \
    services/decision/src/research/sandbox_engine.py \
    services/decision/src/research/pbo_validator.py \
    services/decision/src/research/factor_validator.py

echo ""
echo "=========================================="
echo "Token 1 已签发"
echo "=========================================="
echo ""

# Token 2: TASK-0121-B 批量评估脚本（2 文件，180 分钟）
python governance/jbt_lockctl.py issue \
  --task TASK-0121-B \
  --agent "Claude-Code" \
  --action "实现批量评估脚本（batch_evaluate_strategies.py）" \
  --ttl-minutes 180 \
  --files \
    services/decision/batch_evaluate_strategies.py \
    services/decision/tests/test_batch_evaluate.py

echo ""
echo "=========================================="
echo "Token 2 已签发"
echo "=========================================="
echo ""

# Token 3: TASK-0121-C 参数调优工具（2 文件，300 分钟）
python governance/jbt_lockctl.py issue \
  --task TASK-0121-C \
  --agent "Claude-Code" \
  --action "验证参数调优工具（TradeOptimizer）" \
  --ttl-minutes 300 \
  --files \
    services/decision/src/research/trade_optimizer.py \
    services/decision/tests/test_trade_optimizer.py

echo ""
echo "=========================================="
echo "所有 Token 已签发完成！"
echo "=========================================="
echo ""
echo "请将 3 个 Token 字符串（最后一行的长字符串）复制给 Livis"
```

---

## 📝 执行说明

1. **复制上述命令**到终端
2. **输入密码**（3 次，每个 Token 一次）
3. **复制 3 个 Token 字符串**（每个命令输出的最后一行）
4. 将 Token 字符串发送给 Livis

---

## 🎯 预期输出

每个 Token 签发后会显示：

```
请输入密码: ******
Token 已生成
token_id: tok-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
task_id: TASK-0121-A
agent: Claude-Code
files: services/decision/src/research/strategy_evaluator.py, ...
expires_at: 1713276000

eyJhbGci...（这是 Token 字符串，请复制这一行）
```

---

## 🔑 关键修正

- ✅ 使用 `--ttl-minutes` 而非 `--duration`
- ✅ Token 1: 480 分钟（8 小时）
- ✅ Token 2: 180 分钟（3 小时）
- ✅ Token 3: 300 分钟（5 小时）
- ✅ 会提示输入密码（3 次）

---

**签名**：Livis Claude
**日期**：2026-04-16
