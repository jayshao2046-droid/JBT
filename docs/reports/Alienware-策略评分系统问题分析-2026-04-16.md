# 棕榈油策略评分系统问题分析报告

【分析人】Livis Claude  
【日期】2026-04-16  
【来源】TASK-0120 棕榈油策略优化报告

---

## 📋 问题描述

用户反馈：**所有策略给出的结果都一样**

经过分析，发现以下严重问题：

---

## 🔍 数据分析

### 统计数据

- **总策略数**: 25 个
- **基线评分为 100 的策略**: 22 个（88%）
- **优化后评分为 100 的策略**: 25 个（100%）
- **评分有变化的策略**: 仅 3 个（12%）

### 评分变化详情

只有 3 个策略评分有变化：

1. **STRAT_p_trend_60m_001**: 95 → 100
2. **STRAT_p_trend_60m_002**: 85 → 100
3. **STRAT_p_trend_60m_003**: 95 → 100

其余 22 个策略：**100 → 100**（无变化）

---

## ⚠️ 核心问题

### 问题 1：评分标准过于宽松

**现象**：88% 的策略基线评分就已经是满分 100

**原因分析**：
- 评分标准设置过低，大部分策略轻易达到满分
- 缺乏区分度，无法识别策略质量差异
- 可能只检查了基本格式，没有实质性评估

**影响**：
- 无法识别真正优秀的策略
- 无法发现潜在风险
- 优化工作失去意义

---

### 问题 2：优化无效果

**现象**：只有 3 个策略（12%）评分有变化

**原因分析**：
- 优化前后参数变化，但评分逻辑没有捕捉到差异
- 评分函数可能只检查固定字段，不考虑参数合理性
- 优化可能只是形式上的调整，没有实质改进

**证据**：
查看 `STRAT_p_trend_5m_001` 的基线和完成报告：
- **基线**: 100/100，日亏损阈值 2000.0，单品种熔断 160.0
- **完成**: 100/100，日亏损阈值 1500.0，单品种熔断 160.0
- **结论**: 参数有变化，但评分不变

---

### 问题 3：评分系统失效

**现象**：所有策略优化后都是 100 分

**原因分析**：
评分函数可能采用**二元判断**（通过/不通过），而非**连续评分**：

```python
# 错误的评分逻辑（推测）
def calculate_score(strategy):
    score = 100
    
    # 只做减分，不做细分
    if weight_sum != 1.0:
        score -= 10
    if position > 0.2:
        score -= 10
    if max_drawdown > 0.02:
        score -= 5
    # ...
    
    return score
```

**问题**：
- 只要策略满足基本条件，就是 100 分
- 没有考虑参数的优劣程度
- 没有考虑风险收益比
- 没有考虑策略的实际表现

---

## 🎯 根本原因

### 评分维度缺失

当前评分可能只检查：
1. ✅ 权重和是否为 1.0
2. ✅ 阈值是否在合理范围
3. ✅ 风控参数是否存在

**缺失的关键维度**：
1. ❌ 参数的合理性（如回撤阈值 0.01 vs 0.008）
2. ❌ 风控的严格程度（如日亏损 2000 vs 1500）
3. ❌ 策略的复杂度和稳定性
4. ❌ 历史回测表现
5. ❌ 风险收益比

---

## 💡 解决方案

### 方案 1：重新设计评分函数（推荐）

```python
def calculate_production_readiness_score(strategy: dict) -> int:
    """
    生产准备评分：0-100 分
    
    评分维度：
    1. 基础合规性（30 分）
    2. 风控严格度（30 分）
    3. 参数合理性（20 分）
    4. 策略稳定性（20 分）
    """
    score = 0
    
    # 1. 基础合规性（30 分）
    if check_weight_sum(strategy):
        score += 10
    if check_thresholds(strategy):
        score += 10
    if check_risk_params_exist(strategy):
        score += 10
    
    # 2. 风控严格度（30 分）
    score += evaluate_risk_strictness(strategy)  # 0-30
    
    # 3. 参数合理性（20 分）
    score += evaluate_param_quality(strategy)  # 0-20
    
    # 4. 策略稳定性（20 分）
    score += evaluate_stability(strategy)  # 0-20
    
    return min(100, max(0, score))


def evaluate_risk_strictness(strategy: dict) -> int:
    """评估风控严格度：0-30 分"""
    score = 30
    
    # 回撤阈值评分
    max_dd = strategy['risk']['max_drawdown_pct']
    if max_dd > 0.01:
        score -= 10  # 太宽松
    elif max_dd <= 0.008:
        score += 0   # 合理
    
    # 日亏损阈值评分
    daily_loss = strategy['risk']['daily_loss_limit_yuan']
    if daily_loss > 2000:
        score -= 10  # 太宽松
    elif daily_loss <= 1500:
        score += 0   # 合理
    
    # 单品种熔断评分
    fuse = strategy['risk']['per_symbol_fuse_yuan']
    if fuse > 200:
        score -= 10  # 太宽松
    elif fuse <= 180:
        score += 0   # 合理
    
    return max(0, score)
```

---

### 方案 2：引入回测验证

在评分中加入实际回测结果：

```python
def calculate_score_with_backtest(strategy: dict, backtest_result: dict) -> int:
    """结合回测结果的评分"""
    
    # 基础评分（50 分）
    base_score = calculate_production_readiness_score(strategy)
    base_score = base_score * 0.5  # 占 50%
    
    # 回测表现评分（50 分）
    backtest_score = 0
    
    # Sharpe Ratio（20 分）
    sharpe = backtest_result.get('sharpe_ratio', 0)
    if sharpe >= 2.0:
        backtest_score += 20
    elif sharpe >= 1.5:
        backtest_score += 15
    elif sharpe >= 1.0:
        backtest_score += 10
    elif sharpe >= 0.5:
        backtest_score += 5
    
    # 最大回撤（15 分）
    max_dd = backtest_result.get('max_drawdown', 1.0)
    if max_dd <= 0.05:
        backtest_score += 15
    elif max_dd <= 0.10:
        backtest_score += 10
    elif max_dd <= 0.15:
        backtest_score += 5
    
    # 胜率（15 分）
    win_rate = backtest_result.get('win_rate', 0)
    if win_rate >= 0.6:
        backtest_score += 15
    elif win_rate >= 0.5:
        backtest_score += 10
    elif win_rate >= 0.4:
        backtest_score += 5
    
    return int(base_score + backtest_score)
```

---

### 方案 3：分级评分体系

不使用 0-100 的连续评分，改用分级：

- **S 级（90-100）**: 生产就绪，可直接上线
- **A 级（80-89）**: 良好，需小幅调整
- **B 级（70-79）**: 合格，需优化
- **C 级（60-69）**: 勉强通过，需大幅优化
- **D 级（<60）**: 不合格，禁止上线

---

## 🔧 立即行动

### 短期修复（紧急）

1. **找到评分函数代码**
   - 搜索关键字：`生产准备评分`、`production_readiness_score`
   - 可能位置：`services/decision/src/research/` 或某个脚本

2. **修改评分逻辑**
   - 增加风控严格度评分
   - 增加参数合理性评分
   - 降低基础分，提高区分度

3. **重新运行评分**
   - 对 25 个策略重新评分
   - 验证评分分布是否合理

---

### 长期改进

1. **建立回测验证流程**
   - 每个策略必须通过回测
   - 回测结果纳入评分

2. **建立策略分级体系**
   - S/A/B/C/D 五级
   - 只有 S 级和 A 级可上线

3. **定期审查评分标准**
   - 每季度审查一次
   - 根据实际表现调整

---

## 📊 预期效果

修复后，评分分布应该是：

- **S 级（90-100）**: 5-10%（真正优秀的策略）
- **A 级（80-89）**: 20-30%（良好策略）
- **B 级（70-79）**: 30-40%（合格策略）
- **C 级（60-69）**: 20-30%（需优化）
- **D 级（<60）**: 5-10%（不合格）

---

## 🎯 结论

**当前问题**：评分系统失效，88% 的策略基线就是满分，优化后 100% 满分。

**根本原因**：评分标准过于宽松，只检查基本格式，不评估参数质量和风控严格度。

**解决方案**：重新设计评分函数，增加风控严格度、参数合理性、回测表现等维度。

**优先级**：P0（紧急），影响策略上线决策。

---

**签名**：Livis Claude  
**日期**：2026-04-16  
**状态**：待修复
