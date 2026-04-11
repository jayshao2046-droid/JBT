# Qwen Spec C0-2 Factor Loader Stock

## §1 任务摘要

目标：扩展 `services/decision/src/research/factor_loader.py` 中的 FactorLoader 类，使其支持股票代码的因子加载，复用 C0-1 提供的股票 bars API。

## §2 锚点声明

已存在：
- services/decision/src/research/factor_loader.py（主因子加载器，需扩展股票支持）

新建（本任务产出）：
- services/decision/src/research/stock_data_client.py（HTTP 客户端，调用 data 服务股票 API）

修改：
- services/decision/src/research/factor_loader.py（扩展 load_stock_bars 方法以支持股票数据）

planned-placeholder（本任务运行时必须已完成，不得新建）：
- services/data/src/api/routes/stock_bars.py（C0-1 产出，本任务依赖此路由正常返回；C0-2 不得在 C0-1 未完成时独立部署）

> **[Atlas 修订 2026-04-11]** 原草稿将 `stock_bars.py` 列为"已存在"属锚点错误。该文件是 C0-1（TASK-0050）的计划产出，当前代码库中尚不存在，已移至 planned-placeholder。C0-2 执行时必须确认 TASK-0050 已闭环锁回。

## §3 接口规范

### FactorLoader 类方法签名
```python
def load_stock_bars(
    self,
    symbol: str,        # 股票代码，如 "000001" 或 "SH600000"
    start: str,         # 开始时间，格式为 "YYYY-MM-DD" 或 "YYYY-MM-DD HH:mm:ss"
    end: str,           # 结束时间，格式为 "YYYY-MM-DD" 或 "YYYY-MM-DD HH:mm:ss"
    timeframe_minutes: int = 1  # 时间周期，默认为 1 分钟
) -> pandas.DataFrame
```

### StockDataClient 类方法签名
```python
def get_bars(
    self,
    symbol: str,
    start: str,
    end: str,
    timeframe_minutes: int = 1
) -> dict[str, Any]
```

### 返回数据类型定义
- 返回 pandas.DataFrame，包含以下必需字段：
  - datetime: 时间戳，ISO 8601 格式
  - open: 开盘价，数值类型
  - high: 最高价，数值类型
  - low: 最低价，数值类型
  - close: 收盘价，数值类型
  - volume: 成交量，数值类型
  - open_interest: 持仓量，数值类型（股票通常为 0）

## §4 HTTP 客户端设计

### StockDataClient 实现
```python
import httpx
from typing import Any, Dict, Optional
import os
from tenacity import retry, stop_after_attempt, wait_exponential

class StockDataClient:
    def __init__(self):
        self.base_url = os.getenv("JBT_DATA_API_URL", "http://localhost:8105")
        self.timeout = httpx.Timeout(connect=3.0, read=30.0, write=30.0, pool=5.0)
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_bars(
        self,
        symbol: str,
        start: str,
        end: str,
        timeframe_minutes: int = 1
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/stocks/bars"
        params = {
            "symbol": symbol,
            "start": start,
            "end": end,
            "timeframe_minutes": timeframe_minutes
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
```

### 环境变量配置
- `JBT_DATA_API_URL`: data 服务 API 地址，默认为 "http://localhost:8105"
- `STOCK_DATA_CLIENT_TIMEOUT_CONNECT`: 连接超时，默认 3 秒
- `STOCK_DATA_CLIENT_TIMEOUT_READ`: 读取超时，默认 30 秒

## §5 错误处理清单

| 错误场景 | 异常类型 | 处理方式 |
|----------|----------|----------|
| data 服务返回 404 | DataServiceNotFoundError | FactorLoader 抛出 DataNotFoundError |
| data 服务超时 | DataServiceTimeoutError | 抛出 DataServiceTimeoutError，带重试机制 |
| data 服务返回非预期格式 | DataParseError | 抛出 DataParseError，包含原始响应信息 |
| HTTP 请求失败 | httpx.RequestError | 抛出 FactorLoadError，包装原始异常 |
| 股票代码格式无效 | InvalidSymbolError | 抛出 FactorLoadError，提示符号格式问题 |
| 时间范围无效 | InvalidTimeRangeError | 抛出 FactorLoadError，提示时间格式问题 |

### 异常类定义
```python
class DataServiceError(Exception):
    """数据服务相关异常基类"""
    pass

class DataServiceNotFoundError(DataServiceError):
    """数据服务找不到指定资源"""
    pass

class DataServiceTimeoutError(DataServiceError):
    """数据服务超时"""
    pass

class DataParseError(DataServiceError):
    """数据解析错误"""
    pass
```

## §6 测试用例（最少 8 条）

| 用例ID | 前置条件 | 输入 | 预期输出 | 测试类型 |
|--------|----------|------|----------|----------|
| TC001 | data 服务正常运行 | symbol="000001", start="2023-01-01", end="2023-01-02" | 成功返回股票K线DataFrame | happy |
| TC002 | data 服务正常运行 | symbol="SH600000", start="2023-01-01 09:30:00", end="2023-01-01 15:00:00" | 成功返回股票K线DataFrame | happy |
| TC003 | data 服务正常运行 | symbol="000001", start="2023-01-01", end="2023-01-02", timeframe_minutes=5 | 成功返回5分钟股票K线DataFrame | happy |
| TC004 | data 服务正常运行 | mock HTTP 请求，模拟期货数据 | load_futures_bars 方法不受影响 | regression |
| TC005 | data 服务不可达 | symbol="000001", start="2023-01-01", end="2023-01-02" | 抛出 DataServiceTimeoutError，经过3次重试 | error |
| TC006 | data 服务返回格式错误 | mock HTTP 响应，返回无效JSON | 抛出 DataParseError | error |
| TC007 | 股票代码格式错误 | symbol="", start="2023-01-01", end="2023-01-02" | 抛出 FactorLoadError | error |
| TC008 | 时间范围错误 | symbol="000001", start="2023-01-02", end="2023-01-01" | 抛出 FactorLoadError | error |

## §7 依赖关系

### 前置依赖
- C0-1: 股票 bars API 路由扩展（已完成）
- C0-3: 策略导入解析器（已完成）

### 解锁任务
- CA2': 期货沙箱回测引擎（依赖本任务）
- CB2': 股票沙箱回测引擎（依赖本任务）

### 服务间依赖
- 依赖 data 服务的 `/api/v1/stocks/bars` 端点
- 通过 HTTP 客户端调用，不直接依赖代码
- 遵循松耦合原则，通过 API 约定进行通信

## §8 扩展性设计

### 插件化数据源
- FactorLoader 支持多种数据源插件
- 可通过配置选择不同的数据客户端
- 支持期货和股票数据源的统一接口

### 缓存机制
- 实现 LRU 缓存以减少重复请求
- 支持基于 symbol + 时间范围的缓存键
- 缓存失效策略基于数据新鲜度

### 监控与日志
- 记录每次数据请求的性能指标
- 监控数据服务的可用性和响应时间
- 提供详细的错误日志用于调试

## §9 性能优化

### 批量请求
- 支持批量获取多个股票的数据
- 减少网络往返次数
- 优化并发请求控制

### 数据压缩
- 在传输层启用 gzip 压缩
- 减少网络带宽占用
- 提升大数据量传输效率

### 连接池管理
- 使用连接池复用 HTTP 连接
- 控制最大并发连接数
- 避免连接泄露

## §10 安全考虑

### 认证授权
- 支持 API 密钥认证（预留接口）
- 实现请求频率限制
- 防止恶意大量请求

### 数据验证
- 验证返回数据的完整性
- 防止注入攻击
- 对外部数据进行清理和验证