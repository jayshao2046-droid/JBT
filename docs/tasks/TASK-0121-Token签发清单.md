# TASK-0121 Token 签发清单

【任务ID】TASK-0121  
【创建时间】2026-04-16  
【状态】待签发

---

## 📋 Token 签发清单

### Token 1：TASK-0121-A 策略评估流水线

**任务ID**：TASK-0121-A  
**服务**：decision  
**优先级**：P0  
**预计时长**：480 分钟（8 小时）

**白名单**（5 文件）：
1. `services/decision/src/research/strategy_evaluator.py`（新建）
2. `services/decision/tests/test_strategy_evaluator.py`（新建）
3. `services/decision/src/research/sandbox_engine.py`（只读验证）
4. `services/decision/src/research/pbo_validator.py`（只读验证）
5. `services/decision/src/research/factor_validator.py`（只读验证）

**验收标准**：
- [ ] StrategyEvaluator 类实现完成
- [ ] 五阶段评估逻辑全部实现
- [ ] 至少 26 个测试用例全部通过
- [ ] 测试覆盖率 ≥ 80%

---

### Token 2：TASK-0121-B 批量评估脚本

**任务ID**：TASK-0121-B  
**服务**：decision  
**优先级**：P0  
**预计时长**：180 分钟（3 小时）  
**依赖**：Token 1 完成

**白名单**（2 文件）：
1. `services/decision/batch_evaluate_strategies.py`（新建）
2. `services/decision/tests/test_batch_evaluate.py`（新建）

**验收标准**：
- [ ] 批量评估脚本实现完成
- [ ] 至少 8 个测试用例全部通过
- [ ] 可以生成 Markdown 报告

---

### Token 3：TASK-0121-C 参数调优工具

**任务ID**：TASK-0121-C  
**服务**：decision  
**优先级**：P1  
**预计时长**：300 分钟（5 小时）  
**依赖**：Token 1 完成

**白名单**（2 文件）：
1. `services/decision/src/research/trade_optimizer.py`（验证 + 补充）
2. `services/decision/tests/test_trade_optimizer.py`（新建）

**验收标准**：
- [ ] TradeOptimizer 验证完成
- [ ] 至少 12 个测试用例全部通过
- [ ] 可以调优 1 个策略

---

## 📊 Token 签发顺序

### 第一批（并行）

- **Token 1**：TASK-0121-A（策略评估流水线）

### 第二批（依赖第一批）

- **Token 2**：TASK-0121-B（批量评估脚本）
- **Token 3**：TASK-0121-C（参数调优工具）

---

## 🎯 总时间估算

- **第一批**：8 小时
- **第二批**：8 小时（并行）
- **总计**：16 小时

---

## 📝 签发流程

### 步骤 1：项目架构师预审

- [ ] 审核任务拆分
- [ ] 审核文件清单
- [ ] 审核验收标准
- [ ] 审核时间估算

### 步骤 2：Jay.S 确认

- [ ] 确认任务优先级
- [ ] 确认执行顺序
- [ ] 确认白名单

### 步骤 3：签发 Token

```bash
# Token 1
mcp__jbt-governance__issue_token \
  --task-id TASK-0121-A \
  --agent "Claude Code" \
  --action "实现策略评估流水线" \
  --files services/decision/src/research/strategy_evaluator.py \
         services/decision/tests/test_strategy_evaluator.py \
         services/decision/src/research/sandbox_engine.py \
         services/decision/src/research/pbo_validator.py \
         services/decision/src/research/factor_validator.py \
  --duration 480

# Token 2（待 Token 1 完成）
mcp__jbt-governance__issue_token \
  --task-id TASK-0121-B \
  --agent "Claude Code" \
  --action "实现批量评估脚本" \
  --files services/decision/batch_evaluate_strategies.py \
         services/decision/tests/test_batch_evaluate.py \
  --duration 180

# Token 3（待 Token 1 完成）
mcp__jbt-governance__issue_token \
  --task-id TASK-0121-C \
  --agent "Claude Code" \
  --action "验证参数调优工具" \
  --files services/decision/src/research/trade_optimizer.py \
         services/decision/tests/test_trade_optimizer.py \
  --duration 300
```

---

## 🚨 注意事项

1. **Token 2 和 Token 3 依赖 Token 1**
   - 必须等 Token 1 完成并锁回后，才能签发 Token 2 和 Token 3

2. **只读验证文件**
   - `sandbox_engine.py`、`pbo_validator.py`、`factor_validator.py` 只能读取，不能修改
   - 如果发现接口不兼容，需要单独建任务

3. **测试覆盖率要求**
   - 所有新增代码测试覆盖率 ≥ 80%
   - 所有测试用例必须通过

4. **执行环境**
   - 代码实现：MacBook（本地开发）
   - 批量评估：Studio（执行环境）

---

**签名**：Livis Claude  
**日期**：2026-04-16  
**状态**：待签发
