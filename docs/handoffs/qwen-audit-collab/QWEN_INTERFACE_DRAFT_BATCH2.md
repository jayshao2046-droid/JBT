# Qwen Interface Draft Batch2

## §1 C0-1 ↔ CB5 接口约定

### C0-1 提供的数据格式规范
```json
{
  "requested_symbol": "string",
  "resolved_symbol": "string",
  "source_kind": "string",
  "timeframe_minutes": "integer",
  "count": "integer",
  "bars": [
    {
      "datetime": "string", // ISO 8601 format: YYYY-MM-DDTHH:mm:ss
      "open": "number",
      "high": "number",
      "low": "number",
      "close": "number",
      "volume": "number",
      "open_interest": "number" // 可能为 0
    }
  ]
}
```

### CB5 消费 C0-1 API 时需要的参数列表
- `symbol`: 股票代码，如 "000001" 或 "SH600000"
- `start`: 开始时间，格式为 "YYYY-MM-DD HH:mm:ss" 或 "YYYY-MM-DD"
- `end`: 结束时间，格式为 "YYYY-MM-DD HH:mm:ss" 或 "YYYY-MM-DD"
- `timeframe_minutes`: 时间周期，默认为 1

### 任何字段不匹配的风险说明
- `datetime` 字段格式必须为 ISO 8601，否则 CB5 解析时间时会失败
- `open`, `high`, `low`, `close`, `volume`, `open_interest` 必须为数值类型，否则 CB5 计算指标时会出错
- `bars` 数组不能为空，否则 CB5 无法进行回测计算

## §2 C0-1 ↔ C0-2 接口约定

### C0-1 完成后，C0-2（FactorLoader 股票代码支持）如何调用 stock_bars API
C0-2 中的 FactorLoader 需要通过 HTTP GET 请求调用 C0-1 提供的 API：

```
GET /api/v1/stocks/bars?symbol={symbol}&start={start_date}&end={end_date}&timeframe_minutes={timeframe}
```

### 参数传递规范
- `symbol`: 从因子配置中获取的股票代码
- `start_date`: 因子计算所需的开始日期，格式 "YYYY-MM-DD"
- `end_date`: 因子计算所需的结束日期，格式 "YYYY-MM-DD"
- `timeframe`: 根据因子计算需求确定的时间粒度，默认为 1（分钟）

## §3 CG1 ↔ CG2 接口约定

### CG1 队列的 `queue_id` 格式规范
- UUID v4 格式：`xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
- 示例：`550e8400-e29b-41d4-a716-446655440000`

### CG2 消费队列时需要的接口方法
- `dequeue()`: 从队列头部取出一个待处理项目
- `get_item(queue_id: str)`: 根据队列ID获取特定项目
- `update_status(queue_id: str, status: str, result: Optional[Dict] = None)`: 更新队列项目状态

### 状态机：queued → running → completed / failed
- `queued`: 项目刚加入队列，等待处理
- `running`: 项目正在被处理
- `completed`: 项目处理成功完成
- `failed`: 项目处理失败

## §4 跨任务数据类型统一映射表

| 字段 | C0-1 | C0-3 | CG1 | 统一类型定义 |
|------|------|------|-----|--------------|
| symbol | string | string | string | 股票代码，如 "000001" 或 "SH600000" |
| exchange | - | string | - | 交易所代码，如 "SSE", "SZSE", "SHFE" |
| datetime | string (ISO 8601) | - | - | 时间格式统一为 YYYY-MM-DDTHH:mm:ss |
| strategy_id | - | string | string | 策略唯一标识符 |
| queue_id | - | - | string (UUID v4) | 队列项目唯一标识符 |
| status | - | string | string | 状态枚举：draft, pending_approval, approved, rejected, archived |
| created_at | - | string (ISO 8601) | string (ISO 8601) | 创建时间格式统一为 YYYY-MM-DDTHH:mm:ss |
| updated_at | - | string (ISO 8601) | string (ISO 8601) | 更新时间格式统一为 YYYY-MM-DDTHH:mm:ss |