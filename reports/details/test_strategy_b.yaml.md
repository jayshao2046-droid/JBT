# test_strategy_b 策略评估报告

## 综合评分：52/100 (D 级)

### 1. 基础合规性（30/30）

✅ 因子权重和：1.000
✅ 阈值合理性：long=0.60, short=-0.60
✅ 风控参数完整

### 2. 回测表现（10/30）

- Sharpe Ratio: 0.00
- 最大回撤: 0.00%
- 胜率: 0.00%
- 总收益: 0.00%
- 交易次数: 0

### 3. PBO 过拟合检测（6/10）

- PBO 值: 40.00%
- 风险等级: medium
- 备注: PBO validation requires full implementation with parameter sweep

### 4. 因子有效性（6/10）

- IC 均值: 0.050
- IC IR: 0.250
- IC p-value: 0.050
- 备注: Factor validation requires full implementation with factor series

### 5. 风控严格度（3/20）

- 最大回撤阈值: 2.50%
- 日亏损限制: 5000 元 (1.00%)
- 单品种熔断: 10000 元 (2.00%)

## 风控调整

- 加分：+0
- 扣分：-3

## 生产准入建议

❌ **不建议上线**（优先级：low）

**优化建议：**
- 优化入场时机，提高 Sharpe Ratio
- 提高入场阈值，提升胜率

**风险警告：**
- 日亏损限制过宽松，建议收紧至 0.5%
- 回撤阈值过宽松，建议收紧至 1.5%

---
生成时间：2026-04-16T04:30:00.529917
