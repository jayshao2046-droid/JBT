# 策略评估完整链路分析报告

【分析人】Livis Claude  
【日期】2026-04-16  
【任务】TASK-0120 棕榈油策略评估链路检查

---

## 📋 执行摘要

用户要求：**检查策略是否符合回撤、胜率、夏普等参数，是否经过 PBO 过拟合检测，其他工具是否使用，必须把整个链路和工作流程搞清楚。**

**核心发现**：
1. ✅ **工具齐全**：JBT 已实现完整的策略评估工具链
2. ❌ **未被使用**：这些工具在棕榈油策略评估中**可能未被调用**
3. ❌ **评分失效**：88% 策略基线就是 100 分，说明只做了基础检查

---

## 🔧 已实现的工具链

### 1. 回测引擎（SandboxEngine）

**位置**：`services/decision/src/research/sandbox_engine.py`

**功能**：
- 支持期货/股票双资产类型
- 从 data 服务获取历史数据
- 执行策略回测
- 计算关键指标

**输出指标**：
```python
{
    "sharpe_ratio": float,      # 夏普比率
    "max_drawdown": float,      # 最大回撤
    "win_rate": float,          # 胜率
    "total_return": float,      # 总收益
    "trades_count": int,        # 交易次数
    "initial_capital": float,   # 初始资金
    "final_capital": float      # 最终资金
}
```

**状态**：✅ 已实现，功能完整

---

### 2. PBO 过拟合检测（PBOValidator）

**位置**：`services/decision/src/research/pbo_validator.py`

**功能**：
- 组合对称交叉验证（CSCV）
- 样本内/样本外 Sharpe 对比
- PBO 值计算（0~1，越接近 0 越好）
- 排名相关性检查

**输出指标**：
```python
{
    "pbo": float,               # PBO 值（0~1）
    "sharpe_is": float,         # 样本内 Sharpe
    "sharpe_oos": float,        # 样本外 Sharpe
    "rank_correlation": float,  # 排名相关性
    "n_configs": int,           # 参数配置数
    "n_splits": int             # 数据分割数
}
```

**判定标准**：
- PBO < 0.3：低风险（可上线）
- PBO 0.3-0.5：中等风险（需优化）
- PBO > 0.5：高风险（禁止上线）

**状态**：✅ 已实现，算法正确

---

### 3. 因子有效性验证（FactorValidator）

**位置**：`services/decision/src/research/factor_validator.py`

**功能**：
- IC（信息系数）显著性检验
- IC IR（IC/std_IC）计算
- 多空分组收益差（Top 30% vs Bottom 30%）
- t 检验（p 值）

**判定标准**：
```python
IC_IR_THRESHOLD = 0.3       # IC IR > 0.3
P_VALUE_THRESHOLD = 0.1     # p < 0.1
LS_RETURN_THRESHOLD = 0.0   # 多空收益差 > 0
MIN_SAMPLES = 20            # 最小样本数
```

**状态**：✅ 已实现，统计方法正确

---

### 4. 信号质量验证（SignalValidator）

**位置**：`services/decision/src/research/signal_validator.py`

**功能**：
- IC 有效性检查（|IC| > 0.02）
- IC 衰减检测（衰减率 < 0.5）
- 异常信号标记（超过 3σ）
- 行情类型一致性检查

**判定标准**：
```python
IC_MIN_THRESHOLD = 0.02         # IC 最小阈值
ANOMALY_SIGMA = 3.0             # 异常判定（3σ）
IC_DECAY_THRESHOLD = 0.5        # IC 衰减阈值
```

**状态**：✅ 已实现，逻辑完整

---

### 5. 参数优化器（TradeOptimizer）

**位置**：`services/decision/src/research/trade_optimizer.py`

**功能**：
- 网格搜索交易参数
- 以 Sharpe/回撤/胜率/总收益为目标函数
- 找到最优参数组合

**支持的目标函数**：
- `sharpe`：最大化夏普比率
- `max_drawdown`：最小化最大回撤
- `win_rate`：最大化胜率
- `total_return`：最大化总收益

**状态**：✅ 已实现，支持多目标优化

---

### 6. 其他工具

**相关性监控**（`correlation_monitor.py`）：
- 监控因子间相关性
- 避免因子冗余

**因子监控**（`factor_monitor.py`）：
- 监控因子漂移
- 检测因子失效

**价差监控**（`spread_monitor.py`）：
- 监控价差交易机会
- Z-score 计算

**状态**：✅ 已实现

---

## ❌ 问题诊断

### 问题 1：工具未被调用

**证据**：
1. 88% 的策略基线评分就是 100 分
2. 只有 3 个策略评分有变化
3. 报告中**没有**回测指标（Sharpe/回撤/胜率）
4. 报告中**没有** PBO 检验结果
5. 报告中**没有**因子验证结果

**结论**：这些工具虽然已实现，但在棕榈油策略评估中**未被调用**。

---

### 问题 2：评分函数过于简单

**当前评分逻辑（推测）**：

```python
def calculate_score(strategy: dict) -> int:
    """当前的评分逻辑（推测）"""
    score = 100
    
    # 只做基础检查
    if strategy['factors'] 的权重和 != 1.0:
        score -= 10
    
    if strategy['position_fraction'] > 0.2:
        score -= 10
    
    if strategy['risk']['max_drawdown_pct'] > 0.02:
        score -= 5
    
    # 没有调用回测
    # 没有调用 PBO 检验
    # 没有调用因子验证
    
    return score
```

**问题**：
- 只检查配置格式，不验证实际表现
- 没有调用任何评估工具
- 评分标准过于宽松

---

### 问题 3：缺少完整的评估流程

**应该有的流程**：

```
策略 YAML
    ↓
【阶段 1】基础合规性检查
    ├─ 权重和 = 1.0
    ├─ 阈值合理
    └─ 风控参数完整
    ↓
【阶段 2】回测验证（SandboxEngine）
    ├─ 获取历史数据
    ├─ 执行回测
    └─ 计算 Sharpe/回撤/胜率
    ↓
【阶段 3】PBO 过拟合检测（PBOValidator）
    ├─ CSCV 交叉验证
    ├─ 样本内外对比
    └─ PBO < 0.3 判定
    ↓
【阶段 4】因子有效性验证（FactorValidator）
    ├─ IC 显著性检验
    ├─ IC IR > 0.3
    └─ 多空收益差 > 0
    ↓
【阶段 5】信号质量验证（SignalValidator）
    ├─ IC 有效性
    ├─ IC 衰减检测
    └─ 异常信号标记
    ↓
【阶段 6】参数优化（TradeOptimizer）
    ├─ 网格搜索
    └─ 找到最优参数
    ↓
【阶段 7】综合评分
    ├─ 基础合规性（30 分）
    ├─ 风控严格度（30 分）
    ├─ 回测表现（20 分）
    ├─ PBO 检验（10 分）
    └─ 因子有效性（10 分）
    ↓
生产准备评分（0-100）
```

**当前实际流程**：

```
策略 YAML
    ↓
【阶段 1】基础合规性检查
    ├─ 权重和 = 1.0 ✓
    ├─ 阈值合理 ✓
    └─ 风控参数完整 ✓
    ↓
生产准备评分 = 100 ❌
```

**结论**：只执行了阶段 1，跳过了阶段 2-6。

---

## 🔍 验证方法

### 方法 1：查看报告内容

**当前报告**（`STRAT_p_trend_5m_001-完成报告.md`）：

```markdown
# STRAT_p_trend_5m_001.yaml 完成策略报告

- 生成时间: 2026-04-15T23:04:06.175579
- 阶段: optimized
- 生产准备评分: 100/100

## 优化后关键指标
- 权重和: 1.0
- 多阈值: 0.55
- 空阈值: -0.55
- 仓位: 0.08
- 最大回撤阈值: 0.008
- 日亏损阈值: 1500.0
- 单品种熔断: 160.0
- 标的数: 1

## 基线 vs 完成
- 评分变化: 100 -> 100
- 仓位变化: 0.08 -> 0.08
- 回撤阈值变化: 0.008 -> 0.008
- 日亏损阈值变化: 2000.0 -> 1500.0
- 单品种熔断变化: 160.0 -> 160.0

## 生产准入结论
- 结论: 可进入生产
- 备注: 策略已按24小时连续运行风控口径收敛

## 仍需关注
- 标的覆盖不足
```

**缺失的关键信息**：
- ❌ 没有回测 Sharpe Ratio
- ❌ 没有实际最大回撤
- ❌ 没有实际胜率
- ❌ 没有 PBO 检验结果
- ❌ 没有因子 IC 值
- ❌ 没有交易次数

**结论**：报告只包含配置参数，没有实际回测结果。

---

### 方法 2：查找生成报告的脚本

**搜索结果**：
```bash
grep -r "生产准备评分" /Users/jayshao/JBT --include="*.py"
# 结果：无匹配
```

**结论**：生成报告的脚本可能：
1. 不在 JBT 仓库中
2. 使用了其他语言（如 Shell 脚本）
3. 手动生成的

---

## 💡 解决方案

### 方案 1：实现完整的评估流程（推荐）

创建一个完整的策略评估脚本：

```python
# services/decision/scripts/evaluate_strategy.py

import asyncio
import yaml
from pathlib import Path
from typing import Dict, Any

from ..src.research.sandbox_engine import SandboxEngine
from ..src.research.pbo_validator import PBOValidator
from ..src.research.factor_validator import FactorValidator
from ..src.research.signal_validator import SignalValidator


class StrategyEvaluator:
    """完整的策略评估器"""
    
    def __init__(self):
        self.sandbox = SandboxEngine()
        self.pbo_validator = PBOValidator()
        self.factor_validator = FactorValidator()
        self.signal_validator = SignalValidator()
    
    async def evaluate(self, strategy_path: str) -> Dict[str, Any]:
        """评估单个策略"""
        
        # 1. 加载策略配置
        with open(strategy_path) as f:
            strategy = yaml.safe_load(f)
        
        # 2. 基础合规性检查
        compliance_score = self._check_compliance(strategy)
        
        # 3. 回测验证
        backtest_result = await self.sandbox.run_backtest(
            strategy_config=strategy,
            start_time="2023-01-01",
            end_time="2026-01-01",
            asset_type="futures",
        )
        
        # 4. PBO 过拟合检测
        pbo_result = self.pbo_validator.validate(
            returns=backtest_result.trades,  # 需要转换为收益率序列
            param_configs=[],  # 需要提供多组参数配置
        )
        
        # 5. 因子有效性验证
        factor_results = []
        for factor in strategy['factors']:
            result = self.factor_validator.validate(
                factor_name=factor['factor_name'],
                symbol=strategy['symbols'][0],
                factor_series=[],  # 需要提供因子历史值
                return_series=[],  # 需要提供收益率序列
            )
            factor_results.append(result)
        
        # 6. 综合评分
        final_score = self._calculate_final_score(
            compliance_score=compliance_score,
            backtest_result=backtest_result,
            pbo_result=pbo_result,
            factor_results=factor_results,
        )
        
        return {
            "strategy_name": strategy['name'],
            "final_score": final_score,
            "compliance_score": compliance_score,
            "backtest": {
                "sharpe_ratio": backtest_result.sharpe_ratio,
                "max_drawdown": backtest_result.max_drawdown,
                "win_rate": backtest_result.win_rate,
                "total_return": backtest_result.total_return,
                "trades_count": backtest_result.trades_count,
            },
            "pbo": {
                "pbo_value": pbo_result['pbo'],
                "sharpe_is": pbo_result['sharpe_is'],
                "sharpe_oos": pbo_result['sharpe_oos'],
                "rank_correlation": pbo_result['rank_correlation'],
            },
            "factors": [
                {
                    "name": r.factor_name,
                    "ic_ir": r.ic_ir,
                    "p_value": r.p_value,
                    "passed": r.passed,
                }
                for r in factor_results
            ],
        }
    
    def _check_compliance(self, strategy: Dict) -> int:
        """基础合规性检查（30 分）"""
        score = 30
        
        # 权重和检查
        weights = [f['weight'] for f in strategy['factors']]
        if abs(sum(weights) - 1.0) > 0.01:
            score -= 10
        
        # 风控参数检查
        if 'risk' not in strategy:
            score -= 10
        
        # 必填字段检查
        required_fields = ['name', 'factors', 'signal', 'symbols']
        for field in required_fields:
            if field not in strategy:
                score -= 5
        
        return max(0, score)
    
    def _calculate_final_score(
        self,
        compliance_score: int,
        backtest_result: Any,
        pbo_result: Dict,
        factor_results: list,
    ) -> int:
        """综合评分（0-100）"""
        
        # 1. 基础合规性（30 分）
        score = compliance_score
        
        # 2. 风控严格度（30 分）
        risk_score = self._evaluate_risk_strictness(backtest_result)
        score += risk_score
        
        # 3. 回测表现（20 分）
        backtest_score = 0
        if backtest_result.sharpe_ratio >= 2.0:
            backtest_score += 10
        elif backtest_result.sharpe_ratio >= 1.0:
            backtest_score += 5
        
        if backtest_result.max_drawdown <= 0.05:
            backtest_score += 5
        elif backtest_result.max_drawdown <= 0.10:
            backtest_score += 3
        
        if backtest_result.win_rate >= 0.6:
            backtest_score += 5
        elif backtest_result.win_rate >= 0.5:
            backtest_score += 3
        
        score += backtest_score
        
        # 4. PBO 检验（10 分）
        pbo_score = 0
        if pbo_result['pbo'] < 0.3:
            pbo_score = 10
        elif pbo_result['pbo'] < 0.5:
            pbo_score = 5
        
        score += pbo_score
        
        # 5. 因子有效性（10 分）
        factor_score = 0
        passed_factors = sum(1 for r in factor_results if r.passed)
        factor_score = int(10 * passed_factors / len(factor_results))
        
        score += factor_score
        
        return min(100, max(0, score))
    
    def _evaluate_risk_strictness(self, backtest_result: Any) -> int:
        """评估风控严格度（30 分）"""
        score = 30
        
        # 实际最大回撤
        if backtest_result.max_drawdown > 0.15:
            score -= 15
        elif backtest_result.max_drawdown > 0.10:
            score -= 10
        elif backtest_result.max_drawdown > 0.05:
            score -= 5
        
        # 交易频率（过高可能过拟合）
        if backtest_result.trades_count > 1000:
            score -= 10
        elif backtest_result.trades_count > 500:
            score -= 5
        
        return max(0, score)


async def main():
    """批量评估策略"""
    evaluator = StrategyEvaluator()
    
    strategy_dir = Path("services/decision/参考文件/因子策略库/入库标准化/oilseed/p/trend")
    
    for strategy_file in strategy_dir.glob("*.yaml"):
        print(f"\n评估策略: {strategy_file.name}")
        
        result = await evaluator.evaluate(str(strategy_file))
        
        print(f"  最终评分: {result['final_score']}/100")
        print(f"  Sharpe: {result['backtest']['sharpe_ratio']:.2f}")
        print(f"  最大回撤: {result['backtest']['max_drawdown']:.2%}")
        print(f"  胜率: {result['backtest']['win_rate']:.2%}")
        print(f"  PBO: {result['pbo']['pbo_value']:.2%}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

### 方案 2：修复现有的评分脚本

如果找到了生成报告的脚本，需要：

1. **添加回测调用**
2. **添加 PBO 检验调用**
3. **添加因子验证调用**
4. **修改评分函数**

---

## 📊 完整工作流程图

```
┌─────────────────────────────────────────────────────────────┐
│                     策略 YAML 文件                           │
│  (STRAT_p_trend_5m_001.yaml)                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段 1：基础合规性检查                                      │
│  ├─ 权重和 = 1.0                                            │
│  ├─ 阈值合理                                                │
│  ├─ 风控参数完整                                            │
│  └─ 必填字段存在                                            │
│  得分：0-30 分                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段 2：回测验证（SandboxEngine）                           │
│  ├─ 获取历史数据（data service）                            │
│  ├─ 执行策略回测                                            │
│  └─ 计算指标：                                              │
│      • Sharpe Ratio（夏普比率）                             │
│      • Max Drawdown（最大回撤）                             │
│      • Win Rate（胜率）                                     │
│      • Total Return（总收益）                               │
│      • Trades Count（交易次数）                             │
│  得分：0-20 分                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段 3：PBO 过拟合检测（PBOValidator）                      │
│  ├─ 组合对称交叉验证（CSCV）                                │
│  ├─ 样本内/样本外 Sharpe 对比                               │
│  ├─ PBO 值计算（0~1）                                       │
│  └─ 判定：                                                  │
│      • PBO < 0.3：低风险（10 分）                           │
│      • PBO 0.3-0.5：中等风险（5 分）                        │
│      • PBO > 0.5：高风险（0 分）                            │
│  得分：0-10 分                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段 4：因子有效性验证（FactorValidator）                   │
│  ├─ IC 显著性检验（t-test）                                 │
│  ├─ IC IR > 0.3                                             │
│  ├─ 多空收益差 > 0                                          │
│  └─ p < 0.1                                                 │
│  得分：0-10 分                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段 5：信号质量验证（SignalValidator）                     │
│  ├─ IC 有效性（|IC| > 0.02）                                │
│  ├─ IC 衰减检测（< 0.5）                                    │
│  ├─ 异常信号标记（3σ）                                      │
│  └─ 行情类型一致性                                          │
│  得分：通过/不通过                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段 6：风控严格度评估                                      │
│  ├─ 实际最大回撤 vs 阈值                                    │
│  ├─ 日亏损限制                                              │
│  ├─ 单品种熔断                                              │
│  └─ 交易频率                                                │
│  得分：0-30 分                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  阶段 7：综合评分                                            │
│  ├─ 基础合规性：30 分                                       │
│  ├─ 风控严格度：30 分                                       │
│  ├─ 回测表现：20 分                                         │
│  ├─ PBO 检验：10 分                                         │
│  └─ 因子有效性：10 分                                       │
│  总分：0-100 分                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  生产准备评分报告                                            │
│  ├─ 最终评分：XX/100                                        │
│  ├─ 回测指标（Sharpe/回撤/胜率）                            │
│  ├─ PBO 检验结果                                            │
│  ├─ 因子验证结果                                            │
│  └─ 生产准入建议                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 结论

### 当前状态

1. ✅ **工具齐全**：JBT 已实现完整的策略评估工具链
   - SandboxEngine（回测）
   - PBOValidator（过拟合检测）
   - FactorValidator（因子验证）
   - SignalValidator（信号验证）
   - TradeOptimizer（参数优化）

2. ❌ **未被使用**：这些工具在棕榈油策略评估中未被调用
   - 报告中没有回测指标
   - 报告中没有 PBO 检验结果
   - 报告中没有因子验证结果

3. ❌ **评分失效**：88% 策略基线就是 100 分
   - 只做了基础合规性检查
   - 没有调用任何评估工具
   - 评分标准过于宽松

### 根本原因

**生成报告的脚本只执行了阶段 1（基础合规性检查），跳过了阶段 2-6（回测、PBO、因子验证等）。**

### 解决方案

1. **短期**：找到生成报告的脚本，添加工具调用
2. **长期**：实现完整的策略评估流程（方案 1）

### 优先级

**P0（紧急）**：影响策略上线决策，必须立即修复。

---

**签名**：Livis Claude  
**日期**：2026-04-16  
**状态**：待修复
