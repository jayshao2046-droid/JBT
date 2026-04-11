# Qwen Spec CB5 Watchlist Collector

## §1 任务摘要

目标：扩展 `services/data/src/collectors/stock_minute_collector.py` 以支持从决策服务获取动态 watchlist，并相应更新调度管道。由于检查发现 decision 服务目前没有提供 watchlist API 端点，因此在 §2 中将该部分标记为 planned-placeholder。

## §2 锚点声明

已存在：
- services/data/src/collectors/stock_minute_collector.py（主采集器，需扩展）
- services/data/src/scheduler/pipeline.py（调度，需扩展）

新建（本任务产出）：
- services/data/src/collectors/watchlist_client.py（HTTP 调用 decision watchlist API）

修改：
- services/data/src/collectors/stock_minute_collector.py（动态 symbol 支持）
- services/data/src/scheduler/pipeline.py（新增 watchlist 刷新调度）

planned-placeholder（本任务依赖，需前置实现）：
- decision 服务 API 路由：`GET /api/v1/strategies/watchlist`（CB5 前置：需 decision 服务先提供 watchlist API）
- services/decision/src/api/routes/watchlist.py（决策服务 watchlist 路由文件）

## §3 接口规范

### Decision 服务 watchlist API（待实现）
```
GET /api/v1/strategies/watchlist
```

#### Query 参数
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| status | string | 否 | 过滤策略状态，如 "active", "paused", "archived" |
| symbol_type | string | 否 | 过滤标的类型，如 "stock", "futures" |

#### 响应 JSON Schema
```json
{
  "watchlist": [
    {
      "strategy_id": "string",
      "strategy_name": "string",
      "symbol": "string",
      "exchange": "string",
      "status": "string",
      "created_at": "string",
      "updated_at": "string"
    }
  ],
  "total_count": "integer",
  "generated_at": "string"
}
```

### WatchlistClient 类方法签名
```python
def fetch_watchlist(
    self,
    status_filter: Optional[str] = None,
    symbol_type: Optional[str] = None
) -> dict[str, Any]
```

### 降级策略
当 decision 服务不可达时，WatchlistClient 应读取本地缓存文件：
- 默认路径：`~/jbt-data/watchlist_cache.json`
- 文件格式与上述 API 响应相同
- 缓存有效期：24小时

## §4 WatchlistClient 实现设计

### HTTP 客户端实现
```python
import httpx
import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

class WatchlistClient:
    def __init__(self, decision_service_url: str = None, cache_path: str = None):
        self.decision_service_url = decision_service_url or os.getenv("JBT_DECISION_API_URL", "http://localhost:8104")
        self.cache_path = Path(cache_path or "~/jbt-data/watchlist_cache.json").expanduser()
        self.timeout = httpx.Timeout(connect=3.0, read=30.0)
        
    def fetch_watchlist(
        self,
        status_filter: Optional[str] = None,
        symbol_type: Optional[str] = None
    ) -> Dict[str, Any]:
        # 尝试从决策服务获取
        try:
            params = {}
            if status_filter:
                params["status"] = status_filter
            if symbol_type:
                params["symbol_type"] = symbol_type
                
            url = f"{self.decision_service_url}/api/v1/strategies/watchlist"
            
            response = httpx.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            watchlist_data = response.json()
            
            # 更新本地缓存
            self._update_cache(watchlist_data)
            
            return watchlist_data
            
        except httpx.RequestError as e:
            print(f"Warning: Failed to fetch watchlist from decision service: {e}")
            # 降级到本地缓存
            return self._fetch_from_cache()
    
    def _update_cache(self, data: Dict[str, Any]) -> None:
        """更新本地缓存文件"""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        data["cached_at"] = datetime.now().isoformat()
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _fetch_from_cache(self) -> Dict[str, Any]:
        """从本地缓存获取数据"""
        if not self.cache_path.exists():
            print(f"Cache file does not exist: {self.cache_path}")
            return {"watchlist": [], "total_count": 0, "generated_at": datetime.now().isoformat()}
        
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                
            # 检查缓存是否过期（24小时）
            cached_at = datetime.fromisoformat(cached_data.get("cached_at", datetime.now().isoformat()))
            if datetime.now() - cached_at > timedelta(hours=24):
                print("Warning: Cache is older than 24 hours")
                
            return cached_data
        except Exception as e:
            print(f"Error reading cache file: {e}")
            return {"watchlist": [], "total_count": 0, "generated_at": datetime.now().isoformat()}
```

### 环境变量配置
- `JBT_DECISION_API_URL`: 决策服务 API 地址，默认为 `http://localhost:8104`（PORT_REGISTRY.md 冻结值，不得改写为 8003）
- `WATCHLIST_CACHE_PATH`: 本地缓存文件路径，默认为 "~/jbt-data/watchlist_cache.json"

## §5 Stock Minute Collector 扩展

### 扩展后的采集器类
```python
class StockMinuteCollector(BaseCollector):
    def __init__(
        self,
        *,
        symbols: list[str] | None = None,
        use_watchlist: bool = False,  # 新增：是否使用动态 watchlist
        watchlist_client: WatchlistClient | None = None,  # 新增：watchlist 客户端
        period: str = "1",
        batch_size: int = 100,
        batch_sleep: float = 30.0,
        per_stock_sleep: float = 0.5,
        **kwargs: Any,
    ) -> None:
        kwargs.pop('name', None)
        super().__init__(name="stock_minute", **kwargs)
        self.use_watchlist = use_watchlist
        self.watchlist_client = watchlist_client or WatchlistClient()
        self.symbols = symbols or []
        self.period = period
        self.batch_size = batch_size
        self.batch_sleep = batch_sleep
        self.per_stock_sleep = per_stock_sleep

    def collect(
        self,
        *,
        symbols: list[str] | None = None,
        use_watchlist: bool | None = None,  # 新增参数
        period: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        as_of: str | None = None,
    ) -> list[dict[str, Any]]:
        """扩展采集方法以支持动态 watchlist"""
        # 确定使用的股票列表
        if use_watchlist is not None:
            current_use_watchlist = use_watchlist
        else:
            current_use_watchlist = self.use_watchlist
            
        if current_use_watchlist:
            # 从 watchlist 获取股票列表
            watchlist_data = self.watchlist_client.fetch_watchlist(symbol_type="stock")
            symbol_list = [item["symbol"] for item in watchlist_data.get("watchlist", []) if item.get("symbol")]
        elif symbols is not None:
            symbol_list = symbols
        else:
            symbol_list = self.symbols
            
        # 如果仍然没有股票列表，获取全部 A 股
        if not symbol_list:
            symbol_list = self.get_all_a_stock_codes()
            
        cur_period = period or self.period
        return self._fetch_batch(
            symbol_list=symbol_list,
            period=cur_period,
            start_date=start_date,
            end_date=end_date,
        )
```

## §6 Pipeline 调度扩展

### 扩展后的调度函数
```python
def run_watchlist_stock_minute_pipeline(
    *,
    use_watchlist: bool = True,  # 使用 watchlist
    status_filter: str = "active",  # 只获取活跃策略
    config: dict[str, Any] | None = None,
    storage: HDF5Storage | None = None,
) -> dict[str, int]:
    """使用 watchlist 的股票分钟采集管道"""
    resolved_config = config or get_config()
    resolved_storage = storage or _build_storage(resolved_config)

    from services.data.src.collectors.stock_minute_collector import StockMinuteCollector
    from services.data.src.collectors.watchlist_client import WatchlistClient
    
    watchlist_client = WatchlistClient()
    collector = StockMinuteCollector(
        config=resolved_config,
        storage=resolved_storage,
        use_watchlist=use_watchlist,
        watchlist_client=watchlist_client,
        batch_size=500,
        batch_sleep=10.0,
        per_stock_sleep=0.3,
    )

    result: dict[str, int] = {}
    try:
        records = collector.collect(use_watchlist=use_watchlist)
        from collections import defaultdict
        by_sym: dict[str, list] = defaultdict(list)
        for rec in records:
            by_sym[rec.get("symbol_or_indicator", "unknown")].append(rec)
        for sym, recs in by_sym.items():
            written = _save_records(storage=resolved_storage, data_type="stock_minute", symbol=sym, records=recs)
            result[sym] = written
    except Exception as exc:
        _logger.error("watchlist stock minute pipeline failed: %s", exc)

    return result
```

## §7 错误处理清单

| 错误场景 | HTTP 状态码 | 异常类型 | 处理方式 |
|----------|-------------|----------|----------|
| 决策服务不可达 | - | httpx.ConnectError | 降级到本地缓存，记录警告日志 |
| 决策服务超时 | - | httpx.TimeoutException | 降级到本地缓存，记录警告日志 |
| 决策服务返回非200状态 | 4xx/5xx | httpx.HTTPStatusError | 降级到本地缓存，记录错误日志 |
| 决策服务返回无效JSON | - | json.JSONDecodeError | 降级到本地缓存，记录错误日志 |
| 本地缓存文件不存在 | - | FileNotFoundError | 返回空 watchlist，记录信息日志 |
| 本地缓存文件格式错误 | - | json.JSONDecodeError | 返回空 watchlist，记录错误日志 |
| watchlist 为空 | - | - | 使用默认股票列表或全量 A 股 |
| 采集单个股票失败 | - | Exception | 记录错误，继续处理其他股票 |

## §8 测试用例（最少 8 条）

| 用例ID | 前置条件 | 输入 | 预期输出 | 测试类型 |
|--------|----------|------|----------|----------|
| TC001 | 决策服务正常运行 | status_filter=None, symbol_type="stock" | 成功获取 watchlist 数据 | happy |
| TC002 | 决策服务正常运行 | status_filter="active", symbol_type=None | 成功获取活跃策略的 watchlist | happy |
| TC003 | 决策服务正常运行 | status_filter="active", symbol_type="stock" | 成功获取活跃股票策略的 watchlist | happy |
| TC004 | 决策服务不可达 | mock 决策服务连接失败 | 降级到本地缓存 | error |
| TC005 | 本地缓存存在且有效 | 决策服务不可达，缓存有效 | 从缓存返回数据 | error |
| TC006 | 本地缓存不存在 | 决策服务不可达，无缓存 | 返回空 watchlist | error |
| TC007 | 空 watchlist 边界 | 决策服务返回空列表 | 使用默认股票列表或全量 A 股 | boundary |
| TC008 | 采集 symbol 列表验证 | 使用 watchlist 获取的 symbol 列表 | 成功采集对应股票数据 | happy |

## §9 依赖关系

### 前置依赖
- C0-1: 股票 bars API 路由扩展（已完成）
- CB5 前置：decision 服务需先提供 `/api/v1/strategies/watchlist` API 端点

### 服务间依赖
- 依赖 decision 服务的 watchlist API（通过 HTTP 调用）
- 不直接 import decision 代码，遵循服务间松耦合原则
- 通过本地缓存实现降级容错

## §10 配置与部署

### 配置文件扩展
在 `services/data/configs/settings.yaml` 中添加：
```yaml
watchlist:
  enabled: true
  refresh_interval_minutes: 60
  decision_service_url: "${JBT_DECISION_API_URL:-http://localhost:8104}"
  cache_path: "~/jbt-data/watchlist_cache.json"
  cache_ttl_hours: 24
  symbol_type_filter: "stock"
  status_filter: "active"
```

### 调度配置
在 `services/data/configs/mini_collection.yaml` 中添加：
```yaml
watchlist_stock_minute:
  enabled: true
  schedule: "*/30 * * * *"  # 每30分钟执行一次
  use_watchlist: true
  status_filter: "active"
```

## §11 监控与告警

### 关键指标
- 决策服务 API 调用成功率
- 本地缓存命中率
- watchlist 数据更新频率
- 采集任务执行时间

### 告警规则
- 决策服务连续失败超过5次时告警
- 缓存数据超过24小时未更新时告警
- 采集任务执行时间超过阈值时告警

## §12 安全考虑

### 认证授权
- 支持 API 密钥认证（预留接口）
- 实现请求频率限制
- 防止恶意大量请求

### 数据隐私
- 敏感信息加密存储
- 访问日志脱敏处理
- 符合数据保护法规要求