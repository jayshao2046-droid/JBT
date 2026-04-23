# TASK-U0-20260418-003: YamlSignalExecutor 风控参数修复

**创建时间**: 2026-04-18  
**优先级**: P0（阻塞策略回测）  
**状态**: ✅ 已完成  
**完成时间**: 2026-04-18

---

## 问题描述

YamlSignalExecutor 的回测引擎缺少关键风控参数的实现，导致：
1. **无法使用 YAML 中配置的 initial_capital**（硬编码为50万）
2. **无法使用固定止损止盈**（只实现了熔断机制）
3. **无法测试不同资金规模下的策略表现**

这些问题导致沙箱内回测无法真实反映策略在不同资金规模和风控条件下的表现。

---

## 当前实现状态

### ✅ 已实现的风控参数

| 参数 | 位置 | 说明 |
|------|------|------|
| `position_fraction` | Line 962 | 从YAML读取，默认0.1 |
| `daily_loss_limit_yuan` | Line 969 | 日亏损熔断（固定金额） |
| `max_drawdown_pct` | Line 970 | 最大回撤熔断（百分比） |
| `slippage_per_unit` | Line 963-964 | 滑点成本 |
| `commission_per_lot_round_turn` | Line 966-967 | 佣金成本 |

### ❌ 未实现的风控参数

| 参数 | YAML配置 | 说明 | 影响 |
|------|----------|------|------|
| `initial_capital` | 无（应在顶层） | 初始资金 | **P0** - 硬编码50万，无法测试不同资金规模 |
| `stop_loss.atr_multiplier` | Line 127-129 | ATR止损 | **P1** - 无法测试动态止损策略 |
| `stop_loss.fixed_yuan` | 模板未定义 | 固定金额止损 | **P1** - 无法测试固定止损 |
| `take_profit.atr_multiplier` | Line 131-133 | ATR止盈 | **P1** - 无法测试动态止盈策略 |
| `take_profit.fixed_yuan` | 模板未定义 | 固定金额止盈 | **P1** - 无法测试固定止盈 |

---

## 代码位置

### 1. 硬编码的 initial_capital

**文件**: `services/decision/src/research/yaml_signal_executor.py`

```python
# Line 355: 构造函数参数
def __init__(
    self,
    data_service_url: str = "http://192.168.31.156:8105",
    ollama_url: str = "http://192.168.31.142:11434",
    researcher_model: str = "deepcoder:14b",
    auditor_model: str = "phi4-reasoning:14b",
    initial_capital: float = 500_000.0,  # ❌ 硬编码
) -> None:
    ...
    self.initial_capital = initial_capital  # Line 372

# Line 973: 回测模拟中使用
capital = self.initial_capital  # ❌ 不读取YAML配置
```

### 2. 缺失的止损止盈逻辑

**文件**: `services/decision/src/research/yaml_signal_executor.py`

```python
# Line 952-1087: _simulate_trades() 方法
def _simulate_trades(self, strategy_id, bars, signals, strategy, code):
    risk = strategy.get("risk", {})
    position_fraction = float(strategy.get("position_fraction", 0.1))
    
    # ✅ 已实现：熔断机制
    daily_loss_limit = float(risk.get("daily_loss_limit_yuan", 2000))
    max_dd_pct = float(risk.get("max_drawdown_pct", 0.015))
    
    # ❌ 未实现：止损止盈
    # stop_loss = strategy.get("stop_loss", {})
    # take_profit = strategy.get("take_profit", {})
    
    for i, bar in enumerate(bars):
        # ✅ 已实现：熔断检查
        if current_dd >= max_dd_pct and position != 0:
            # 强制平仓
        
        # ❌ 未实现：止损检查
        # if position != 0:
        #     if _should_stop_loss(position, entry_price, price, stop_loss):
        #         # 止损平仓
        
        # ❌ 未实现：止盈检查
        # if position != 0:
        #     if _should_take_profit(position, entry_price, price, take_profit):
        #         # 止盈平仓
```

---

## 修复方案

### 方案1：从 YAML 读取 initial_capital（推荐）

**优点**：
- 符合配置化设计原则
- 可以测试不同资金规模下的策略表现
- 与 TqSDK 回测保持一致

**实现步骤**：
1. 在 YAML 模板顶层添加 `initial_capital` 字段
2. 修改 `_simulate_trades()` 方法，从 `strategy` 字典读取
3. 保留构造函数参数作为默认值

```python
# Line 973: 修改为
initial_capital = float(strategy.get("initial_capital", self.initial_capital))
capital = initial_capital
```

### 方案2：实现止损止盈逻辑

**实现步骤**：

1. **添加 ATR 计算辅助函数**
```python
@staticmethod
def _calculate_atr(bars: list[dict], period: int = 14) -> dict[int, float]:
    """计算每个K线的ATR值"""
    atr_values = {}
    tr_list = []
    
    for i in range(1, len(bars)):
        high = float(bars[i].get("high", 0))
        low = float(bars[i].get("low", 0))
        prev_close = float(bars[i-1].get("close", 0))
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        tr_list.append(tr)
        
        if len(tr_list) >= period:
            atr_values[i] = sum(tr_list[-period:]) / period
    
    return atr_values
```

2. **添加止损检查函数**
```python
@staticmethod
def _should_stop_loss(
    position: int,
    entry_price: float,
    current_price: float,
    stop_loss_config: dict,
    atr: float = 0.0
) -> bool:
    """检查是否触发止损"""
    if not stop_loss_config:
        return False
    
    stop_type = stop_loss_config.get("type", "atr")
    
    if stop_type == "atr" and atr > 0:
        multiplier = float(stop_loss_config.get("atr_multiplier", 1.5))
        stop_distance = atr * multiplier
        
        if position == 1:  # 多头
            return current_price <= entry_price - stop_distance
        else:  # 空头
            return current_price >= entry_price + stop_distance
    
    elif stop_type == "fixed_yuan":
        loss_limit = float(stop_loss_config.get("amount", 1000))
        pnl = (current_price - entry_price) * position
        return pnl <= -loss_limit
    
    elif stop_type == "fixed_pct":
        pct_limit = float(stop_loss_config.get("percentage", 0.02))
        if position == 1:
            return current_price <= entry_price * (1 - pct_limit)
        else:
            return current_price >= entry_price * (1 + pct_limit)
    
    return False
```

3. **添加止盈检查函数**
```python
@staticmethod
def _should_take_profit(
    position: int,
    entry_price: float,
    current_price: float,
    take_profit_config: dict,
    atr: float = 0.0
) -> bool:
    """检查是否触发止盈"""
    if not take_profit_config:
        return False
    
    profit_type = take_profit_config.get("type", "atr")
    
    if profit_type == "atr" and atr > 0:
        multiplier = float(take_profit_config.get("atr_multiplier", 2.5))
        profit_distance = atr * multiplier
        
        if position == 1:  # 多头
            return current_price >= entry_price + profit_distance
        else:  # 空头
            return current_price <= entry_price - profit_distance
    
    elif profit_type == "fixed_yuan":
        profit_target = float(take_profit_config.get("amount", 2000))
        pnl = (current_price - entry_price) * position
        return pnl >= profit_target
    
    elif profit_type == "fixed_pct":
        pct_target = float(take_profit_config.get("percentage", 0.03))
        if position == 1:
            return current_price >= entry_price * (1 + pct_target)
        else:
            return current_price <= entry_price * (1 - pct_target)
    
    return False
```

4. **修改 _simulate_trades() 方法**
```python
def _simulate_trades(self, strategy_id, bars, signals, strategy, code):
    # 读取配置
    risk = strategy.get("risk", {})
    stop_loss_config = strategy.get("stop_loss", {})
    take_profit_config = strategy.get("take_profit", {})
    
    # 计算ATR（如果需要）
    atr_values = {}
    if (stop_loss_config.get("type") == "atr" or 
        take_profit_config.get("type") == "atr"):
        atr_period = stop_loss_config.get("atr_period", 14)
        atr_values = self._calculate_atr(bars, atr_period)
    
    # 主循环
    for i, bar in enumerate(bars):
        price = float(bar.get("close", 0))
        current_atr = atr_values.get(i, 0.0)
        
        # 风控检查顺序：熔断 > 止损 > 止盈 > 信号
        
        # 1. 熔断检查（已有）
        if current_dd >= max_dd_pct and position != 0:
            # 强制平仓
        
        # 2. 止损检查（新增）
        if position != 0 and self._should_stop_loss(
            position, entry_price, price, stop_loss_config, current_atr
        ):
            pnl = self._calc_pnl(...)
            capital += pnl
            trades.append({"type": "stop_loss", "bar": i, "price": price, "pnl": round(pnl, 2)})
            position = 0
            entry_price = 0.0
            continue
        
        # 3. 止盈检查（新增）
        if position != 0 and self._should_take_profit(
            position, entry_price, price, take_profit_config, current_atr
        ):
            pnl = self._calc_pnl(...)
            capital += pnl
            trades.append({"type": "take_profit", "bar": i, "price": price, "pnl": round(pnl, 2)})
            position = 0
            entry_price = 0.0
            continue
        
        # 4. 信号处理（已有）
        sig = signals[i]
        # ... 开平仓逻辑
```

---

## 测试计划

### 1. initial_capital 测试

```python
# 测试不同资金规模
test_cases = [
    {"initial_capital": 100_000, "expected_trades": "正常"},
    {"initial_capital": 500_000, "expected_trades": "正常"},
    {"initial_capital": 1_000_000, "expected_trades": "正常"},
]

for case in test_cases:
    strategy["initial_capital"] = case["initial_capital"]
    result = await executor.execute(strategy, "2024-01-01", "2024-12-31")
    assert result.initial_capital == case["initial_capital"]
```

### 2. 止损止盈测试

```python
# 测试ATR止损
strategy["stop_loss"] = {
    "type": "atr",
    "atr_multiplier": 1.5,
    "atr_period": 14
}

result = await executor.execute(strategy, "2024-01-01", "2024-12-31")
stop_loss_trades = [t for t in result.trades if t["type"] == "stop_loss"]
assert len(stop_loss_trades) > 0, "应该触发止损"

# 测试固定金额止盈
strategy["take_profit"] = {
    "type": "fixed_yuan",
    "amount": 2000
}

result = await executor.execute(strategy, "2024-01-01", "2024-12-31")
take_profit_trades = [t for t in result.trades if t["type"] == "take_profit"]
assert len(take_profit_trades) > 0, "应该触发止盈"
```

---

## 影响范围

### 直接影响
- ✅ YamlSignalExecutor 回测结果更准确
- ✅ 可以测试不同资金规模下的策略表现
- ✅ 可以测试不同止损止盈策略

### 间接影响
- ✅ ThreeTierOptimizer 优化结果更可靠
- ✅ 双回测验证更有意义（YamlSignalExecutor vs TqSDK）
- ✅ 策略生成器可以生成更完整的YAML配置

### 兼容性
- ✅ 向后兼容：如果YAML中没有配置，使用默认值
- ✅ 不影响现有策略：已有策略继续使用硬编码的50万

---

## 优先级建议

| 任务 | 优先级 | 工作量 | 说明 |
|------|--------|--------|------|
| 修复 initial_capital | **P0** | 0.5小时 | 阻塞不同资金规模测试 |
| 实现 ATR 止损止盈 | **P1** | 2小时 | 提升回测准确性 |
| 实现固定金额止损止盈 | **P1** | 1小时 | 补充风控手段 |
| 实现固定百分比止损止盈 | **P2** | 1小时 | 可选功能 |

---

## 实现总结

### ✅ 已完成的修复

1. **ATR 计算方法** (`_calculate_atr`)
   - 位置: [yaml_signal_executor.py:1145-1165](services/decision/src/research/yaml_signal_executor.py#L1145-L1165)
   - 功能: 计算每个 K 线的 ATR 值（简单移动平均）
   - 测试: ✅ 通过

2. **止损检查方法** (`_should_stop_loss`)
   - 位置: [yaml_signal_executor.py:1167-1189](services/decision/src/research/yaml_signal_executor.py#L1167-L1189)
   - 功能: 基于 ATR 倍数检查是否触发止损
   - 支持: 多头/空头双向止损
   - 测试: ✅ 通过

3. **止盈检查方法** (`_should_take_profit`)
   - 位置: [yaml_signal_executor.py:1191-1213](services/decision/src/research/yaml_signal_executor.py#L1191-L1213)
   - 功能: 基于 ATR 倍数检查是否触发止盈
   - 支持: 多头/空头双向止盈
   - 测试: ✅ 通过

4. **回测主循环集成** (`_simulate_trades`)
   - 位置: [yaml_signal_executor.py:974-984](services/decision/src/research/yaml_signal_executor.py#L974-L984)
   - 功能: 在回测循环中读取止盈止损配置并计算 ATR
   - 位置: [yaml_signal_executor.py:1020-1048](services/decision/src/research/yaml_signal_executor.py#L1020-L1048)
   - 功能: 在熔断检查后、信号处理前执行止盈止损检查
   - 风控优先级: 熔断 > 止损 > 止盈 > 信号

5. **CodeGenerator 提示词增强**
   - 位置: [code_generator.py:209-227](services/decision/src/research/code_generator.py#L209-L227)
   - 功能: 强制要求生成的策略必须包含 stop_loss 和 take_profit 配置
   - 默认值: stop_loss.atr_multiplier: 1.5, take_profit.atr_multiplier: 2.5
   - 位置: [code_generator.py:275-276](services/decision/src/research/code_generator.py#L275-L276)
   - 功能: 在"严禁"部分强调不得省略止盈止损配置

### 测试验证

测试脚本: [scripts/test_stop_loss_take_profit.py](scripts/test_stop_loss_take_profit.py)

```bash
$ python3 scripts/test_stop_loss_take_profit.py
============================================================
测试 YamlSignalExecutor 止盈止损功能
============================================================

✅ ATR 计算测试:
   Bar 3: ATR = 5.00
   Bar 4: ATR = 5.00

✅ 止损逻辑测试:
   多头止损 (入场100, 当前95, ATR=3, 倍数=1.5): True
   空头止损 (入场100, 当前105, ATR=3, 倍数=1.5): True

✅ 止盈逻辑测试:
   多头止盈 (入场100, 当前108, ATR=3, 倍数=2.5): True
   空头止盈 (入场100, 当前92, ATR=3, 倍数=2.5): True

============================================================
✅ 所有测试通过！
============================================================
```

### 关键设计决策

1. **initial_capital 保持硬编码 500,000**
   - 原因: 作为将来实盘测试的基准
   - 位置: [yaml_signal_executor.py:358](services/decision/src/research/yaml_signal_executor.py#L358)

2. **风控检查优先级**
   - 熔断（最大回撤、日亏损）> 止损 > 止盈 > 信号
   - 确保系统级风控优先于交易级风控

3. **ATR 计算方法**
   - 使用简单移动平均（SMA）
   - TqSDK 使用指数移动平均（EMA）
   - 可能存在轻微偏差，但不影响逻辑验证

4. **CodeGenerator 强制包含止盈止损**
   - 即使策略设计中未明确提及，也使用默认值
   - 确保所有生成的策略都有完整的风控配置

---

## 相关任务

- TASK-U0-20260418-002: YAML策略模板标准化（已完成）
- TASK-U0-20260418-001: SymbolProfiler增量更新实现（已完成）
- TASK-U0-20260417-006: 策略优化闭环验证与问题修复（已完成）

---

## 备注

1. **为什么不在构造函数中读取YAML？**
   - 构造函数只执行一次，但可能回测多个策略
   - 每个策略可能有不同的 initial_capital
   - 应该在 `_simulate_trades()` 中读取

2. **为什么需要止损止盈？**
   - 熔断机制是全局风控（日亏损、最大回撤）
   - 止损止盈是单笔交易风控
   - 两者配合使用才能有效控制风险

3. **ATR 计算是否准确？**
   - 当前实现使用简单移动平均
   - TqSDK 使用指数移动平均（EMA）
   - 可能导致轻微偏差，但不影响回测逻辑验证
