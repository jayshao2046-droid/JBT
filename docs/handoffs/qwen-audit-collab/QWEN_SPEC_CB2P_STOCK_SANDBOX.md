# QWEN_SPEC_CB2P_STOCK_SANDBOX.md

## §1 任务摘要

本规格书定义CB2'股票沙箱回测引擎，这是对CA2'期货沙箱回测引擎的扩展，通过在同一个sandbox_engine.py文件中增加asset_type参数分支来支持股票策略的快速回测。这种合并设计避免了重复的引擎代码，提高了维护效率。

## §2 锚点声明

已存在：
- services/decision/src/research/factor_loader.py（因子数据加载器，供沙箱使用）
- services/decision/src/api/app.py（API应用入口）
- services/decision/src/api/routes/strategy.py（策略相关路由）

修改：
- services/decision/src/research/sandbox_engine.py（扩展 asset_type 分支支持股票；CA2' 产出，本任务激活时必须已完成）
- services/decision/src/api/routes/sandbox.py（扩展沙箱路由以支持股票；CA2' 产出，本任务激活时必须已完成）

planned-placeholder（本任务依赖，激活时必须已存在）：
- services/decision/src/research/sandbox_engine.py（CA2'/TASK-0056 产出，CB2' 必须在 CA2' 完成后执行）
- services/decision/src/api/routes/sandbox.py（CA2'/TASK-0056 产出）

> **[Atlas 补漏 2026-04-11]** 原草稿将 `sandbox_engine.py` 列于"已存在"，但该文件是 CA2'（TASK-0056）的计划产出，当前代码库中不存在。已移至 planned-placeholder 并说明激活条件。CB2' 前置条件：TASK-0056（CA2'）必须完成。

## §3 合并设计理由

CB2'股票沙箱与CA2'期货沙箱合并为一个引擎的原因：
1. **代码复用**：大部分回测逻辑相同，只有在处理特定市场规则时才需要分支
2. **维护效率**：统一的引擎便于bug修复和功能增强
3. **一致性**：确保两种资产类型的回测逻辑保持一致
4. **资源节约**：减少重复代码，降低内存占用

## §4 沙箱回测流程（含Sequence Diagram）

### 4.1 股票沙箱回测执行流程
当决策服务需要对股票策略进行快速回测时，将调用沙箱引擎的run_backtest方法并指定asset_type为"stock"。以下是详细的执行流程：

```
sequenceDiagram
    participant Client as 客户端
    participant API as API层
    participant Router as 路由层
    participant Sandbox as 沙箱引擎
    participant FactorLoader as 因子加载器
    participant DataService as 数据服务

    Client->>API: POST /api/v1/sandbox/stock/backtest
    API->>Router: 路由请求
    Router->>Sandbox: run_backtest(asset_type="stock")
    Sandbox->>FactorLoader: load_stock_data()
    FactorLoader->>DataService: 获取股票数据
    DataService-->>FactorLoader: 返回数据
    FactorLoader-->>Sandbox: 返回整理后的数据
    Sandbox->>Sandbox: 执行股票回测逻辑（T+1等特殊处理）
    Sandbox-->>Router: 返回回测结果
    Router-->>API: 返回结果
    API-->>Client: 返回响应
```

### 4.2 资产类型分支处理
沙箱引擎根据asset_type参数执行不同的处理逻辑：

```
sequenceDiagram
    participant Sandbox as 沙箱引擎
    participant Validator as 参数验证器
    participant Executor as 执行器

    Sandbox->>Validator: 验证asset_type参数
    Validator-->>Sandbox: 返回验证结果
    alt asset_type == "futures"
        Sandbox->>Executor: 使用期货执行逻辑
        Executor-->>Sandbox: 期货回测结果
    else asset_type == "stock"
        Sandbox->>Executor: 使用股票执行逻辑（T+1等）
        Executor-->>Sandbox: 股票回测结果
    end
    Sandbox-->>Sandbox: 计算绩效指标
```

## §5 沙箱引擎扩展实现

### 5.1 扩展后的SandboxEngine类
```python
from typing import Literal

class SandboxEngine:
    def run_backtest(self, 
                     strategy_config: dict, 
                     start_time: str, 
                     end_time: str,
                     asset_type: Literal["futures", "stock"],
                     initial_capital: float = 1000000) -> dict:
        """
        在沙箱环境中运行策略回测
        :param strategy_config: 策略配置
        :param start_time: 回测开始时间
        :param end_time: 回测结束时间
        :param asset_type: 资产类型（futures或stock）
        :param initial_capital: 初始资金
        :return: 包含回测结果的字典
        """
        if asset_type == "futures":
            return self._run_futures_backtest(strategy_config, start_time, end_time, initial_capital)
        elif asset_type == "stock":
            return self._run_stock_backtest(strategy_config, start_time, end_time, initial_capital)
        else:
            raise ValueError(f"Unsupported asset type: {asset_type}")
    
    def _run_futures_backtest(self, strategy_config: dict, start_time: str, end_time: str, initial_capital: float) -> dict:
        """执行期货回测逻辑"""
        # 期货特有的回测逻辑
        pass
    
    def _run_stock_backtest(self, strategy_config: dict, start_time: str, end_time: str, initial_capital: float) -> dict:
        """执行股票回测逻辑"""
        # 股票特有的回测逻辑（T+1、涨跌停等）
        pass
```

### 5.2 股票特有逻辑处理
股票沙箱引擎需要特别处理以下股票市场特性：

- **T+1交易制度**：买入的股票当天不能卖出
- **涨跌停限制**：价格变动不能超过涨跌停板限制
- **交易时间**：仅在交易时间内执行交易
- **最小变动单位**：价格变动需符合股票的最小变动单位

### 5.3 StockExecutionEngine实现（作为SandboxEngine的内部逻辑）
```python
from datetime import datetime, timedelta

class StockExecutionEngine:
    def __init__(self):
        self.positions = {}  # 持仓信息
        self.available_cash = 0  # 可用现金
        self.frozen_cash = 0  # 冻结现金
        self.trades_history = []  # 交易历史
        self.t1_restrictions = {}  # T+1限制
        
    def execute_strategy(self, strategy_config: dict, data: dict):
        # 初始化账户
        self.available_cash = strategy_config.get('initial_capital', 1000000)
        
        # 遍历历史数据，执行策略
        for timestamp, bars in data.items():
            # 更新T+1限制（前一天买入的股票今天可以卖出）
            self.update_t1_restrictions(timestamp)
            
            signals = self.generate_signals(strategy_config, bars)
            
            for signal in signals:
                trade = self.create_trade_from_signal(signal)
                
                # 验证交易合规性
                if self.validate_and_execute_trade(trade, timestamp):
                    self.update_account(trade, timestamp)
                    
        return {
            'trades': self.trades_history,
            'final_balance': self.available_cash,
            'positions': self.positions
        }
    
    def validate_and_execute_trade(self, trade: dict, timestamp: str) -> bool:
        # 检查T+1限制
        if trade['side'] == 'sell':
            if trade['symbol'] in self.t1_restrictions:
                buy_date = self.t1_restrictions[trade['symbol']]
                if datetime.fromisoformat(timestamp.replace('Z', '+00:00')) < \
                   datetime.fromisoformat(buy_date.replace('Z', '+00:00')) + timedelta(days=1):
                    return False  # T+1限制，不能卖出
        
        # 检查是否有足够资金或股票
        if trade['side'] == 'buy':
            cost = trade['quantity'] * trade['price']
            if cost > self.available_cash:
                return False  # 资金不足
        elif trade['side'] == 'sell':
            if trade['symbol'] not in self.positions or \
               self.positions[trade['symbol']] < trade['quantity']:
                return False  # 持仓不足
        
        return True
    
    def update_t1_restrictions(self, current_timestamp: str):
        # 移除过期的T+1限制
        expired_symbols = []
        current_date = datetime.fromisoformat(current_timestamp.replace('Z', '+00:00')).date()
        
        for symbol, buy_date_str in self.t1_restrictions.items():
            buy_date = datetime.fromisoformat(buy_date_str.replace('Z', '+00:00')).date()
            if current_date >= buy_date + timedelta(days=1):
                expired_symbols.append(symbol)
        
        for symbol in expired_symbols:
            del self.t1_restrictions[symbol]
    
    def update_account(self, trade: dict, timestamp: str):
        if trade['side'] == 'buy':
            cost = trade['quantity'] * trade['price']
            self.available_cash -= cost
            
            # 更新持仓
            if trade['symbol'] in self.positions:
                self.positions[trade['symbol']] += trade['quantity']
            else:
                self.positions[trade['symbol']] = trade['quantity']
            
            # 记录T+1限制
            self.t1_restrictions[trade['symbol']] = timestamp
        elif trade['side'] == 'sell':
            revenue = trade['quantity'] * trade['price']
            self.available_cash += revenue
            
            # 更新持仓
            self.positions[trade['symbol']] -= trade['quantity']
            if self.positions[trade['symbol']] <= 0:
                del self.positions[trade['symbol']]
        
        # 记录交易历史
        self.trades_history.append({
            'timestamp': timestamp,
            'symbol': trade['symbol'],
            'side': trade['side'],
            'quantity': trade['quantity'],
            'price': trade['price'],
            'amount': trade['quantity'] * trade['price']
        })
```

## §6 沙箱引擎API定义

### 6.1 沙箱回测路由路径
- `/api/v1/sandbox/stock/backtest` (POST)
- `/api/v1/sandbox/stock/optimize` (POST)
- `/api/v1/sandbox/stock/validate` (POST)

### 6.2 HTTP方法
- POST: 执行回测或参数优化
- GET: 查询沙箱状态或历史回测结果

### 6.3 请求体JSON Schema（回测）
```json
{
  "strategy_id": "string",
  "start_time": "string",
  "end_time": "string",
  "initial_capital": "number",
  "symbols": ["string"],
  "asset_type": "stock"
}
```

### 6.4 响应JSON Schema（回测）
```json
{
  "status": "string",
  "backtest_id": "string",
  "start_time": "string",
  "end_time": "string",
  "initial_capital": "number",
  "final_capital": "number",
  "total_return": "number",
  "sharpe_ratio": "number",
  "max_drawdown": "number",
  "win_rate": "number",
  "trades_count": "integer",
  "t1_violations": "integer",
  "limit_violations": "integer",
  "trades": [],
  "performance_metrics": {},
  "risk_metrics": {}
}
```

### 6.5 请求体JSON Schema（参数优化）
```json
{
  "strategy_config": {},
  "param_space": {},
  "optimization_target": "string",
  "asset_type": "stock"
}
```

## §7 错误处理清单

### 7.1 数据获取错误
- `STOCK_DATA_FETCH_ERROR`: 无法从数据服务获取所需股票数据
  - 原因：网络问题、数据服务不可用、请求参数错误、股票代码不存在
  - 处理：返回错误信息，记录日志，尝试重试

### 7.2 策略执行错误
- `STOCK_STRATEGY_EXECUTION_ERROR`: 股票策略执行过程中发生错误
  - 原因：策略逻辑错误、数据格式不匹配、T+1违规等
  - 处理：捕获异常，返回详细错误信息

### 7.3 风险控制错误
- `STOCK_RISK_LIMIT_EXCEEDED`: 交易违反股票风险控制规则
  - 原因：头寸超限、T+1违规、涨跌停限制等
  - 处理：拒绝交易，返回风险警告

### 7.4 资源限制错误
- `RESOURCE_LIMIT_EXCEEDED`: 沙箱资源超出限制
  - 原因：内存不足、CPU使用过高、回测时间过长
  - 处理：终止回测，返回资源限制警告

## §8 测试用例（最少6条，重点交集验证CA2'期货路径不回归）

### 8.1 基础回测功能测试
- TC_CB2P_001: 验证简单的均线穿越策略能否在股票沙箱中正确执行
- TC_CB2P_002: 验证多股票组合策略的回测功能
- TC_CB2P_003: 验证T+1交易制度的正确实施

### 8.2 与期货沙箱兼容性测试
- TC_CB2P_004: 验证期货沙箱CA2'的回测功能不受股票沙箱实现影响（回归测试）
- TC_CB2P_005: 验证合并后的沙箱引擎可以同时处理期货和股票回测而不产生冲突
- TC_CB2P_006: 验证asset_type参数的正确分支处理

### 8.3 股票特有功能测试
- TC_CB2P_007: 验证涨跌停限制的正确处理
- TC_CB2P_008: 验证交易时间限制的正确处理