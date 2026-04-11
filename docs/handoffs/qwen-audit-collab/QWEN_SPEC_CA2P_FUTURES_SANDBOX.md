# QWEN_SPEC_CA2P_FUTURES_SANDBOX.md

## §1 任务摘要

本规格书定义CA2'期货沙箱回测引擎，这是一个内置于决策服务中的快速回测引擎，用于提供内部循环的期货策略回测能力。该沙箱引擎不同于外部的backtest服务，它专为决策服务内部使用而设计，提供更快的反馈循环和更低的延迟。

## §2 锚点声明

已存在：
- services/decision/src/research/factor_loader.py（因子数据加载器，供沙箱使用）
- services/decision/src/api/app.py（API应用入口）
- services/decision/src/api/routes/strategy.py（策略相关路由）

新建（本任务产出）：
- services/decision/src/research/sandbox_engine.py（期货沙箱核心引擎，支持 asset_type）
- services/decision/src/api/routes/sandbox.py（沙箱路由文件，不存在，本任务新建）

修改：
- services/decision/src/api/app.py（注册 sandbox_router）

planned-placeholder（不在本任务范围，不得引用）：
- （无，此任务不依赖任何 placeholder）

> **[Atlas 补漏 2026-04-11]** 原草稿将 `sandbox.py` 列于"修改"节，但该文件在当前代码库中不存在，已移至"新建"节。

## §3 沙箱引擎架构设计

### 3.1 沙箱引擎组件
沙箱引擎包含以下核心组件：
- DataProxy：负责从data service获取期货数据
- ExecutionEngine：模拟期货交易执行逻辑
- RiskManager：内置风险管理模块
- PerformanceCalculator：实时绩效计算

### 3.2 与外部Backtest服务的区别
- 沙箱引擎运行在决策服务内部，无需网络调用
- 使用内存中的数据缓存，访问速度更快
- 专注于短期回测和快速验证，而非长期复杂回测
- 资源消耗更少，适合高频调用

### 3.3 沙箱引擎接口定义
```python
class FuturesSandbox:
    def run_backtest(self, strategy_config: dict, 
                     start_time: str, end_time: str,
                     initial_capital: float = 1000000) -> dict:
        """
        在沙箱环境中运行期货策略回测
        :param strategy_config: 策略配置
        :param start_time: 回测开始时间
        :param end_time: 回测结束时间
        :param initial_capital: 初始资金
        :return: 包含回测结果的字典
        """
        pass
    
    def optimize_parameters(self, strategy_config: dict,
                           param_space: dict,
                           optimization_target: str = 'sharpe_ratio') -> dict:
        """
        在沙箱环境中进行参数优化
        :param strategy_config: 策略配置
        :param param_space: 参数搜索空间
        :param optimization_target: 优化目标
        :return: 最优参数及对应结果
        """
        pass
```

## §4 沙箱回测流程（含Sequence Diagram）

### 4.1 沙箱回测执行流程
当决策服务需要对期货策略进行快速回测时，将调用沙箱引擎的run_backtest方法。以下是详细的执行流程：

```
sequenceDiagram
    participant Client as 客户端
    participant API as API层
    participant Router as 路由层
    participant Sandbox as 沙箱引擎
    participant FactorLoader as 因子加载器
    participant DataService as 数据服务

    Client->>API: POST /api/v1/sandbox/futures/backtest
    API->>Router: 路由请求
    Router->>Sandbox: run_backtest()
    Sandbox->>FactorLoader: load_data()
    FactorLoader->>DataService: 获取期货数据
    DataService-->>FactorLoader: 返回数据
    FactorLoader-->>Sandbox: 返回整理后的数据
    Sandbox->>Sandbox: 执行回测逻辑
    Sandbox-->>Router: 返回回测结果
    Router-->>API: 返回结果
    API-->>Client: 返回响应
```

### 4.2 参数优化流程
沙箱引擎还支持在内部进行参数优化：

```
sequenceDiagram
    participant Client as 客户端
    participant API as API层
    participant Router as 路由层
    participant Sandbox as 沙箱引擎
    participant Optimizer as 优化器

    Client->>API: POST /api/v1/sandbox/futures/optimize
    API->>Router: 路由请求
    Router->>Sandbox: optimize_parameters()
    Sandbox->>Optimizer: 执行参数优化
    loop 对每个参数组合
        Optimizer->>Sandbox: run_backtest_with_params()
        Sandbox-->>Optimizer: 返回该参数组合的回测结果
    end
    Optimizer-->>Sandbox: 返回最优参数组合
    Sandbox-->>Router: 返回优化结果
    Router-->>API: 返回结果
    API-->>Client: 返回响应
```

## §5 沙箱引擎实现细节

### 5.1 DataProxy实现
DataProxy是沙箱引擎与数据服务之间的桥梁，负责高效地获取期货历史数据：

```python
class DataProxy:
    def __init__(self, data_service_url: str):
        self.data_service_url = data_service_url
        self.cache = {}  # 内存缓存
        
    def fetch_data(self, start_time: str, end_time: str, symbols: list) -> dict:
        # 检查缓存
        cache_key = f"{symbols}_{start_time}_{end_time}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 从数据服务获取数据
        url = f"{self.data_service_url}/api/v1/bars"
        params = {
            "symbols": ",".join(symbols),
            "start": start_time,
            "end": end_time,
            "timeframe": "1m"  # 期货通常使用分钟级别数据
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        # 缓存数据
        self.cache[cache_key] = data
        return data
```

### 5.2 ExecutionEngine实现
ExecutionEngine模拟期货交易的执行过程：

```python
class ExecutionEngine:
    def __init__(self):
        self.positions = {}
        self.account_balance = 0
        self.trades_history = []
        
    def execute_strategy(self, strategy_config: dict, data: dict):
        # 初始化账户
        self.account_balance = strategy_config.get('initial_capital', 1000000)
        
        # 遍历历史数据，执行策略
        for timestamp, bars in data.items():
            signals = self.generate_signals(strategy_config, bars)
            
            for signal in signals:
                trade = self.create_trade_from_signal(signal)
                if self.validate_and_execute_trade(trade):
                    self.update_account(trade)
                    
        return {
            'trades': self.trades_history,
            'final_balance': self.account_balance,
            'positions': self.positions
        }
    
    def validate_and_execute_trade(self, trade: dict) -> bool:
        # 这里可以加入更多复杂的验证逻辑
        return True
```

### 5.3 RiskManager实现
RiskManager确保沙箱中的交易符合风险管理规则：

```python
class RiskManager:
    def __init__(self, risk_limits: dict):
        self.risk_limits = risk_limits
        
    def validate_trade(self, trade: dict) -> dict:
        result = {'approved': True, 'reasons': []}
        
        # 检查头寸限制
        position_limit = self.risk_limits.get('position_limit', float('inf'))
        if abs(trade['quantity']) > position_limit:
            result['approved'] = False
            result['reasons'].append(f"Position exceeds limit: {position_limit}")
            
        # 检查保证金要求
        margin_req = self.calculate_margin_requirement(trade)
        if margin_req > self.risk_limits.get('available_margin', float('inf')):
            result['approved'] = False
            result['reasons'].append("Insufficient margin")
            
        return result
```

## §6 沙箱引擎API定义

### 6.1 沙箱回测路由路径
- `/api/v1/sandbox/futures/backtest` (POST)
- `/api/v1/sandbox/futures/optimize` (POST)
- `/api/v1/sandbox/futures/validate` (POST)

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
  "symbols": ["string"]
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
  "trades": [],
  "performance_metrics": {}
}
```

### 6.5 请求体JSON Schema（参数优化）
```json
{
  "strategy_config": {},
  "param_space": {},
  "optimization_target": "string"
}
```

## §7 错误处理清单

### 7.1 数据获取错误
- `DATA_FETCH_ERROR`: 无法从数据服务获取所需数据
  - 原因：网络问题、数据服务不可用、请求参数错误
  - 处理：返回错误信息，记录日志，尝试重试

### 7.2 策略执行错误
- `STRATEGY_EXECUTION_ERROR`: 策略执行过程中发生错误
  - 原因：策略逻辑错误、数据格式不匹配
  - 处理：捕获异常，返回详细错误信息

### 7.3 风险控制错误
- `RISK_LIMIT_EXCEEDED`: 交易违反风险控制规则
  - 原因：头寸超限、保证金不足等
  - 处理：拒绝交易，返回风险警告

### 7.4 资源限制错误
- `RESOURCE_LIMIT_EXCEEDED`: 沙箱资源超出限制
  - 原因：内存不足、CPU使用过高、回测时间过长
  - 处理：终止回测，返回资源限制警告

## §8 测试用例（最少8条）

### 8.1 基础回测功能测试
- TC_CA2P_001: 验证简单的趋势跟踪策略能否在沙箱中正确执行
- TC_CA2P_002: 验证多品种期货组合策略的回测功能
- TC_CA2P_003: 验证不同时间范围的回测结果一致性

### 8.2 参数优化功能测试
- TC_CA2P_004: 验证网格搜索参数优化功能
- TC_CA2P_005: 验证随机搜索参数优化功能
- TC_CA2P_006: 验证不同优化目标函数的有效性

### 8.3 边界条件测试
- TC_CA2P_007: 验证极端市场条件下的策略表现
- TC_CA2P_008: 验证空数据或缺失数据情况下的错误处理

### 8.4 性能测试
- TC_CA2P_009: 验证沙箱引擎的响应时间是否满足毫秒级要求
- TC_CA2P_010: 验证并发回测请求的处理能力