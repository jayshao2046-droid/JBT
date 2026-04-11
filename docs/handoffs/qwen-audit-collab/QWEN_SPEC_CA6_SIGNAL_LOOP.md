# QWEN_SPEC_CA6_SIGNAL_LOOP.md

## §1 任务摘要

本规格书定义CA6信号真闭环→sim-trading接口，建立从信号生成到模拟交易的完整闭环链路。该接口将使决策服务能够将生成的交易信号可靠地传递给sim-trading服务执行，形成完整的信号闭环流程。

## §2 锚点声明

已存在：
- services/decision/src/api/app.py（决策服务API应用入口）
- services/decision/src/api/routes/signal.py（信号相关路由，本任务在此扩展）
- services/decision/src/api/routes/strategy.py（策略相关路由）
- services/sim-trading/src/main.py（sim-trading服务主入口）
- services/sim-trading/src/api/router.py（sim-trading API路由）

新建（本任务产出）：
- services/decision/src/core/signal_dispatcher.py（信号分发核心逻辑，含 httpx 调用 sim-trading）
- tests/decision/test_signal_dispatcher.py
- tests/sim_trading/test_signal_receive.py

修改：
- services/decision/src/api/routes/signal.py（新增 POST /api/v1/signals/dispatch 端点）
- services/decision/src/api/app.py（确认信号路由注册，无需重复注册可跳过）
- services/sim-trading/src/api/router.py（新增 POST /api/v1/signals/receive 端点）【需独立Token（sim-trading侧）】

planned-placeholder（不在本任务范围，不得引用）：
- （无，此任务不依赖任何 placeholder）

> **[Atlas 补漏 2026-04-11]** 原草稿新建了 `signals.py`（复数），与已存在 `signal.py`（单数）命名冲突；同时在 sim-trading 中新建 `routes/signals.py`，但 sim-trading 当前架构为单文件 `router.py`，不存在 `routes/` 子目录。已修正为：decision 侧修改现有 `signal.py`，sim-trading 侧直接修改 `router.py`，并新建 `signal_dispatcher.py` 承载跨服务调用逻辑。

> **[架构预审补充 2026-04-11]** 跨服务信号体需登记到 `shared/contracts/decision/signal_dispatch.py`（Pydantic model），TASK-0059 实施时需额外 contracts Token。Decision 路由实际前缀为 `/signals`（无 `/api/v1`），已修正 §3.1。

## §3 接口约定

### 3.1 信号传递路由路径
- Decision侧: `/signals/dispatch` (POST)（注：decision 服务无 /api/v1 全局前缀）
- Sim-trading侧: `/api/v1/signals/receive` (POST)
- 信号状态查询: `/signals/status/{signal_id}` (GET)

### 3.2 HTTP方法
- POST: 发布交易信号
- GET: 查询信号执行状态

### 3.3 信号发布请求体JSON Schema
```json
{
  "signal_id": "string",
  "strategy_id": "string",
  "symbol": "string",
  "direction": "string",
  "quantity": "number",
  "timestamp": "string",
  "price": "number",
  "order_type": "string",
  "valid_until": "string",
  "account_id": "string",
  "risk_level": "string",
  "meta_data": {}
}
```

### 3.4 批量信号发布请求体JSON Schema
```json
{
  "signals": [
    {
      "signal_id": "string",
      "strategy_id": "string",
      "symbol": "string",
      "direction": "string",
      "quantity": "number",
      "timestamp": "string",
      "price": "number",
      "order_type": "string",
      "valid_until": "string",
      "account_id": "string",
      "risk_level": "string",
      "meta_data": {}
    }
  ]
}
```

### 3.5 信号发布响应JSON Schema
```json
{
  "status": "string",
  "signal_id": "string",
  "execution_id": "string",
  "message": "string",
  "timestamp": "string",
  "errors": []
}
```

### 3.6 批量信号发布响应JSON Schema
```json
{
  "status": "string",
  "total_count": "integer",
  "accepted_count": "integer",
  "rejected_count": "integer",
  "results": []
}
```

### 3.7 信号状态查询响应JSON Schema
```json
{
  "signal_id": "string",
  "status": "string",
  "execution_status": {},
  "created_at": "string",
  "updated_at": "string",
  "expires_at": "string",
  "error_message": "string"
}
```

## §4 信号传递流程

### 4.1 信号发布流程
1. 决策服务生成交易信号
2. 通过HTTP POST请求向sim-trading服务发送信号
3. sim-trading服务验证信号的有效性
4. sim-trading服务接受信号并返回确认
5. sim-trading服务执行交易
6. 更新信号执行状态

### 4.2 信号验证规则
- 验证策略ID是否有效
- 验证交易标的是否支持
- 验证交易数量是否合理
- 验证账户资金是否充足
- 验证风险等级是否符合限制

### 4.3 信号状态流转
```
GENERATED -> SENT -> RECEIVED -> VALIDATED -> SUBMITTED -> EXECUTED
                                    ↓
                                REJECTED/EXPIRED/CANCELLED
```

## §5 信号适配器实现

### 5.1 SignalPublisher类定义
```python
import requests
import json
import time
import uuid
from typing import Dict, List, Optional
from enum import Enum

class SignalStatus(Enum):
    GENERATED = "generated"
    SENT = "sent"
    RECEIVED = "received"
    VALIDATED = "validated"
    SUBMITTED = "submitted"
    EXECUTED = "executed"
    PARTIALLY_EXECUTED = "partially_executed"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class SignalPublisher:
    def __init__(self, sim_trading_url: str, api_key: str = None):
        self.sim_trading_url = sim_trading_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
        
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def publish_signal(self, signal_data: Dict) -> Dict:
        """发布单个交易信号"""
        url = f"{self.sim_trading_url}/api/v1/signals/receive"
        
        # 添加信号ID（如果未提供）
        if 'signal_id' not in signal_data:
            signal_data['signal_id'] = self._generate_signal_id()
        
        # 设置默认时间戳
        if 'timestamp' not in signal_data:
            signal_data['timestamp'] = self._get_current_timestamp()
        
        try:
            response = self.session.post(url, json=signal_data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result
        except requests.exceptions.RequestException as e:
            return {
                "status": "rejected",
                "signal_id": signal_data.get('signal_id', 'unknown'),
                "message": f"网络请求失败: {str(e)}"
            }
        except json.JSONDecodeError:
            return {
                "status": "rejected", 
                "signal_id": signal_data.get('signal_id', 'unknown'),
                "message": "响应格式错误"
            }
    
    def publish_batch_signals(self, signals: List[Dict]) -> Dict:
        """批量发布交易信号"""
        url = f"{self.sim_trading_url}/api/v1/signals/receive"
        
        # 为每个信号添加ID和时间戳
        for signal in signals:
            if 'signal_id' not in signal:
                signal['signal_id'] = self._generate_signal_id()
            if 'timestamp' not in signal:
                signal['timestamp'] = self._get_current_timestamp()
        
        batch_data = {
            "signals": signals
        }
        
        try:
            response = self.session.post(url, json=batch_data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result
        except requests.exceptions.RequestException as e:
            return {
                "status": "all_rejected",
                "total_count": len(signals),
                "accepted_count": 0,
                "rejected_count": len(signals),
                "message": f"批量发布失败: {str(e)}"
            }
    
    def get_signal_status(self, signal_id: str) -> Dict:
        """查询信号执行状态"""
        url = f"{self.sim_trading_url}/api/v1/signals/status/{signal_id}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result
        except requests.exceptions.RequestException as e:
            return {
                "signal_id": signal_id,
                "status": "unknown",
                "message": f"查询失败: {str(e)}"
            }
    
    def _generate_signal_id(self) -> str:
        """生成唯一信号ID"""
        return f"sig_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.utcnow().isoformat() + "Z"
```

### 5.2 信号发布器使用示例
```python
# 初始化信号发布器
publisher = SignalPublisher(sim_trading_url="http://sim-trading-service:8000", api_key="your-api-key")

# 创建交易信号
signal = {
    "strategy_id": "strat_abc123",
    "symbol": "IF2103",
    "direction": "buy",
    "quantity": 1,
    "price": 5000.0,
    "order_type": "limit",
    "account_id": "acc_sim_001",
    "risk_level": "medium"
}

# 发布信号
result = publisher.publish_signal(signal)
print(f"信号发布结果: {result}")

# 批量发布信号
signals = [
    {
        "strategy_id": "strat_abc123",
        "symbol": "IF2103",
        "direction": "buy",
        "quantity": 1,
        "price": 5000.0
    },
    {
        "strategy_id": "strat_def456", 
        "symbol": "IC2103",
        "direction": "sell",
        "quantity": 2,
        "price": 6000.0
    }
]

batch_result = publisher.publish_batch_signals(signals)
print(f"批量发布结果: {batch_result}")

# 查询信号状态
status = publisher.get_signal_status(result['signal_id'])
print(f"信号状态: {status}")
```

## §6 错误处理清单

### 6.1 网络错误
- `NETWORK_ERROR`: 网络连接失败
  - 原因：sim-trading服务不可达、网络超时
  - 处理：记录错误日志，尝试重试机制

- `CONNECTION_TIMEOUT`: 连接超时
  - 原因：sim-trading服务响应慢
  - 处理：返回超时错误，记录日志

### 6.2 业务逻辑错误
- `INVALID_SIGNAL`: 信号参数无效
  - 原因：缺少必要参数、参数值超出范围
  - 处理：返回400错误，提供具体错误信息

- `INSUFFICIENT_FUNDS`: 资金不足
  - 原因：账户余额不足以执行交易
  - 处理：返回403错误，拒绝信号

- `RISK_LIMIT_EXCEEDED`: 风险限制超限
  - 原因：交易超出风险控制限制
  - 处理：返回403错误，拒绝信号

### 6.3 系统错误
- `SERVICE_UNAVAILABLE`: sim-trading服务不可用
  - 原因：sim-trading服务宕机或过载
  - 处理：返回503错误，启用降级策略

- `INTERNAL_ERROR`: 内部错误
  - 原因：sim-trading服务内部异常
  - 处理：返回500错误，记录详细错误信息

## §7 测试用例（最少8条，含跨服务mock场景）

### 7.1 基础功能测试
- TC_CA6_001: 验证单个信号的成功发布和执行
- TC_CA6_002: 验证批量信号的成功发布和执行
- TC_CA6_003: 验证信号状态查询功能

### 7.2 错误处理测试
- TC_CA6_004: 验证无效信号参数的错误处理
- TC_CA6_005: 验证网络连接失败的处理
- TC_CA6_006: 验证sim-trading服务不可用时的降级处理

### 7.3 跨服务mock场景测试
- TC_CA6_007: 模拟sim-trading服务部分拒绝信号的场景
- TC_CA6_008: 模拟高并发信号发布的场景

### 7.4 集成测试
- TC_CA6_009: 端到端信号闭环流程测试
- TC_CA6_010: 信号时效性测试（验证过期信号的处理）

## §8 安全考虑

### 8.1 认证授权
- 所有信号发布请求必须携带有效的API密钥
- 实现IP白名单机制
- 限制信号发布频率

### 8.2 数据安全
- 传输层使用HTTPS加密
- 敏感信息在日志中脱敏处理
- 信号内容完整性校验

## §9 性能优化

### 9.1 连接池管理
- 使用连接池减少连接建立开销
- 配置合适的超时参数

### 9.2 批量处理
- 支持批量信号发布以提高吞吐量
- 实现异步信号处理

### 9.3 缓存策略
- 缓存常用的账户和策略信息
- 缓存信号状态查询结果

## §10 监控与告警

### 10.1 关键指标
- 信号发布成功率
- 平均信号传递延迟
- 信号执行成功率
- 系统资源使用率

### 10.2 告警规则
- 当信号发布失败率超过阈值时告警
- 当信号传递延迟超过阈值时告警
- 当sim-trading服务不可用时立即告警

## §11 重试与降级策略

### 11.1 重试机制
- 对于网络错误实现指数退避重试
- 设置最大重试次数限制
- 实现去重机制防止重复执行

### 11.2 降级策略
- 当sim-trading服务不可用时，暂时存储信号待后续处理
- 提供手动信号重发功能
- 在严重故障时暂停新信号发布

## §12 依赖关系确认

### 12.1 前置依赖
- 决策服务策略生成模块: 需要生成有效的交易信号
- sim-trading服务: 信号的接收和执行端

### 12.2 后续依赖
- 风控服务: 信号执行前的风险验证
- 账户服务: 交易账户信息查询

## §13 扩展性设计

### 13.1 多目标支持
设计支持同时向多个sim-trading实例发布信号。

### 13.2 协议扩展
预留接口支持其他协议（如WebSocket、消息队列）。

## §14 未来演进

### 14.1 智能路由
根据负载情况智能选择sim-trading实例。

### 14.2 信号优先级
支持不同优先级的信号处理。

### 14.3 实盘集成
扩展支持向实盘交易系统发布信号。