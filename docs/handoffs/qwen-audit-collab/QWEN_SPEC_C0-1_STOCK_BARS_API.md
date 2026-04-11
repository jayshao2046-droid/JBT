# Qwen Spec C0-1 Stock Bars API

## §1 任务摘要

目标：在 `services/data/` 新增股票 bars 查询 API，复用现有 stock_minute 存储。

## §2 锚点声明

已存在：
- services/data/src/main.py（主 FastAPI 应用，现有路由均可作为参考模式）
- services/data/src/data/storage.py（存储层，可复用读取逻辑）
- services/data/src/utils/config.py

新建（本任务产出）：
- services/data/src/api/__init__.py
- services/data/src/api/routes/__init__.py
- services/data/src/api/routes/stock_bars.py
- tests/data/api/test_stock_bars.py

planned-placeholder（不在本任务范围，不得引用）：
- （无，此任务不依赖任何 placeholder）

## §3 接口规范

### 路由路径
```
GET /api/v1/stocks/bars
```

> Atlas 补漏（2026-04-11）：路径统一为 `/api/v1/stocks/bars`，与 TASK-0050 白名单一致。原稿 `/api/v1/stock-bars` 已修正。

### HTTP 方法
```
GET
```

### Query 参数
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| symbol | string | 是 | 股票代码，如 "000001" 或 "SH600000" |
| timeframe_minutes | integer | 否 | 时间周期，默认为 1，表示 1 分钟 K 线 |
| start | string | 是 | 开始时间，格式为 "YYYY-MM-DD HH:mm:ss" 或 "YYYY-MM-DD" |
| end | string | 是 | 结束时间，格式为 "YYYY-MM-DD HH:mm:ss" 或 "YYYY-MM-DD" |

### 响应 JSON Schema
```json
{
  "requested_symbol": "string",
  "resolved_symbol": "string",
  "source_kind": "string",
  "timeframe_minutes": "integer",
  "count": "integer",
  "bars": [
    {
      "datetime": "string",
      "open": "number",
      "high": "number",
      "low": "number",
      "close": "number",
      "volume": "number",
      "open_interest": "number"
    }
  ]
}
```

## §4 数据读取设计

### stock_minute 目录结构说明
根据 `main.py` 中的 `SOURCE_OUTPUT_DIRS["stock_minute"]` = `"stock_minute"`，股票分钟数据存储在 `~/jbt-data/stock_minute/` 目录下，每个股票一个子目录，子目录内包含多个 parquet 格式的 K 线数据文件。

### 读取逻辑伪代码
```python
def get_stock_bars(
    symbol: str,
    start: str,
    end: str,
    timeframe_minutes: int = 1
) -> dict[str, Any]:
    # 解析时间范围
    parsed_start = _parse_requested_time(start, field_name="start", is_end=False)
    parsed_end = _parse_requested_time(end, field_name="end", is_end=True)
    
    # 验证时间范围
    if parsed_end.timestamp < parsed_start.timestamp:
        raise HTTPException(status_code=422, detail="end must be greater than or equal to start")
    
    # 解析股票代码
    symbol_request = _parse_symbol_request(symbol)
    
    # 获取股票数据目录
    stock_root = _storage_root() / "stock_minute"
    symbol_dir = stock_root / symbol_request.exact_symbol
    
    # 加载股票数据
    frame = _load_symbol_frame(symbol_dir)
    
    # 过滤时间范围内的数据
    filtered = frame.loc[
        (frame["datetime"] >= parsed_start.timestamp)
        & (frame["datetime"] <= parsed_end.timestamp)
    ].copy()
    
    # 重新采样（如果需要）
    if timeframe_minutes > 1 and not filtered.empty:
        filtered = _resample_bars(filtered, timeframe_minutes)
    
    # 序列化返回结果
    bars = _serialize_bars(filtered)
    
    return {
        "requested_symbol": symbol,
        "resolved_symbol": symbol_request.exact_symbol,
        "source_kind": "stock_minute",
        "timeframe_minutes": timeframe_minutes,
        "count": len(bars),
        "bars": bars,
    }
```

## §5 错误处理清单

| 错误场景 | HTTP 状态码 | 响应体格式 |
|----------|-------------|------------|
| symbol 参数为空 | 422 | {"detail": "symbol is required"} |
| start 参数为空 | 422 | {"detail": "start is required"} |
| end 参数为空 | 422 | {"detail": "end is required"} |
| 时间格式无效 | 422 | {"detail": "invalid start/end: [具体值]"} |
| end 时间早于 start 时间 | 422 | {"detail": "end must be greater than or equal to start"} |
| 不支持的股票代码格式 | 422 | {"detail": "unsupported symbol format: [具体值]"} |
| 指定股票数据不存在 | 404 | {"detail": "no minute data directory found for [股票代码]"} |
| 读取数据时发生内部错误 | 500 | {"detail": "failed to load data for [股票代码]: [错误详情]"} |

## §6 单元测试用例设计

| 用例ID | 前置条件 | 输入 | 预期输出 | 测试类型 |
|--------|----------|------|----------|----------|
| TC001 | 股票数据存在 | symbol="000001", start="2023-01-01", end="2023-01-02" | 成功返回K线数据 | happy |
| TC002 | 股票数据存在 | symbol="SH600000", start="2023-01-01 09:30:00", end="2023-01-01 15:00:00" | 成功返回K线数据 | happy |
| TC003 | 股票数据存在 | symbol="000001", start="2023-01-01", end="2023-01-02", timeframe_minutes=5 | 成功返回5分钟K线数据 | happy |
| TC004 | 股票数据不存在 | symbol="999999", start="2023-01-01", end="2023-01-02" | HTTP 404 错误 | error |
| TC005 | symbol 参数为空 | symbol="", start="2023-01-01", end="2023-01-02" | HTTP 422 错误 | error |
| TC006 | start 参数为空 | symbol="000001", start="", end="2023-01-02" | HTTP 422 错误 | error |
| TC007 | end 参数为空 | symbol="000001", start="2023-01-01", end="" | HTTP 422 错误 | error |
| TC008 | end 时间早于 start 时间 | symbol="000001", start="2023-01-02", end="2023-01-01" | HTTP 422 错误 | error |

## §7 依赖关系确认

- 本任务无前置依赖（Lane-A 首发）
- 解锁：CB5（依赖本任务）、C0-2（依赖本任务 + C0-3 双完成）