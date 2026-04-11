# Qwen Spec CG1 Strategy Queue

## §1 任务摘要

目标：在 `services/backtest/` 新增策略导入队列（内存实现，无持久化）。

## §2 锚点声明

已存在：
- services/backtest/src/api/routes/strategy.py（现有路由，新队列路由需避免路径冲突）
- services/backtest/src/main.py（FastAPI应用入口，需注册新路由）
- services/backtest/src/backtest/runner.py（回测执行器，队列消费者）
- services/backtest/src/backtest/session.py（回测会话，可能与队列交互）

新建（本任务产出）：
- services/backtest/src/api/routes/queue.py
- services/backtest/src/backtest/strategy_queue.py
- tests/backtest/test_strategy_queue.py

修改（本任务需追加注册）：
- services/backtest/src/api/app.py（在 create_app() 中追加 app.include_router(queue_router)，**不是 main.py**）

planned-placeholder（不在本任务范围，不得引用）：
- （无，此任务不依赖任何 placeholder）

## §3 接口规范

### 队列入队路由路径
```
POST /api/v1/strategy-queue/enqueue
```

### 队列查询路由路径
```
GET /api/v1/strategy-queue/status
```

### 队列清空路由路径
```
DELETE /api/v1/strategy-queue/clear
```

### HTTP 方法
- POST（入队）
- GET（查询状态）
- DELETE（清空队列）

### 请求体 JSON Schema（入队）
```json
{
  "strategy_id": "string",
  "strategy_content": "string",
  "priority": "integer",
  "callback_url": "string"
}
```

### Query 参数（查询状态）
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| status | string | 否 | 过滤状态：queued/running/completed/failed |

### 响应 JSON Schema（入队）
```json
{
  "queue_id": "string",
  "strategy_id": "string",
  "status": "string",
  "message": "string",
  "queued_at": "string"
}
```

### 响应 JSON Schema（查询状态）
```json
{
  "total_count": "integer",
  "queued_count": "integer",
  "running_count": "integer",
  "completed_count": "integer",
  "failed_count": "integer",
  "items": [
    {
      "queue_id": "string",
      "strategy_id": "string",
      "status": "string",
      "priority": "integer",
      "queued_at": "string",
      "started_at": "string",
      "completed_at": "string",
      "result": {}
    }
  ]
}
```

## §4 数据读取设计

### 队列实现逻辑
使用内存队列实现，采用先进先出（FIFO）原则，支持优先级调度。

### 队列逻辑伪代码
```python
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import threading

@dataclass
class QueueItem:
    queue_id: str
    strategy_id: str
    strategy_content: str
    status: str  # queued, running, completed, failed
    priority: int
    callback_url: Optional[str] = None
    queued_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict] = field(default_factory=dict)

class StrategyQueue:
    def __init__(self):
        self._queue: deque = deque()
        self._items: Dict[str, QueueItem] = {}
        self._lock = threading.Lock()
    
    def enqueue(self, strategy_id: str, strategy_content: str, priority: int = 0, callback_url: str = None) -> str:
        with self._lock:
            queue_id = self._generate_queue_id()
            item = QueueItem(
                queue_id=queue_id,
                strategy_id=strategy_id,
                strategy_content=strategy_content,
                status="queued",
                priority=priority,
                callback_url=callback_url
            )
            self._items[queue_id] = item
            
            # 按优先级插入队列
            self._insert_by_priority(item)
            
            return queue_id
    
    def _insert_by_priority(self, item: QueueItem):
        # 按优先级插入，高优先级在前
        temp_list = []
        inserted = False
        
        while self._queue:
            front_item = self._queue.popleft()
            if not inserted and item.priority > front_item.priority:
                temp_list.append(item)
                inserted = True
            temp_list.append(front_item)
        
        if not inserted:
            temp_list.append(item)
        
        for queue_item in temp_list:
            self._queue.append(queue_item)
    
    def dequeue(self) -> Optional[QueueItem]:
        with self._lock:
            if not self._queue:
                return None
            queue_id = self._queue.popleft()
            return self._items.get(queue_id)
    
    def get_item(self, queue_id: str) -> Optional[QueueItem]:
        return self._items.get(queue_id)
    
    def update_status(self, queue_id: str, status: str, result: Optional[Dict] = None):
        with self._lock:
            item = self._items.get(queue_id)
            if not item:
                return
            item.status = status
            if status == "running":
                item.started_at = datetime.now().isoformat()
            elif status in ["completed", "failed"]:
                item.completed_at = datetime.now().isoformat()
            if result is not None:
                item.result = result
    
    def get_all_items(self, status_filter: Optional[str] = None) -> List[QueueItem]:
        with self._lock:
            items = list(self._items.values())
            if status_filter:
                items = [item for item in items if item.status == status_filter]
            return items
    
    def clear_queue(self):
        with self._lock:
            self._queue.clear()
            self._items.clear()
    
    def _generate_queue_id(self) -> str:
        import uuid
        return str(uuid.uuid4())
```

## §5 错误处理清单

| 错误场景 | HTTP 状态码 | 响应体格式 |
|----------|-------------|------------|
| 入队请求体格式错误 | 422 | {"detail": "JSON schema validation failed"} |
| 必需字段缺失 | 422 | {"detail": "Missing required field: [字段名]"} |
| 策略ID格式无效 | 422 | {"detail": "Invalid strategy_id format"} |
| 队列已满 | 429 | {"detail": "Queue is full, please try again later"} |
| 队列项不存在 | 404 | {"detail": "Queue item [ID] not found"} |
| 内部处理错误 | 500 | {"detail": "Failed to process queue request: [错误详情]"} |

## §6 单元测试用例设计

| 用例ID | 前置条件 | 输入 | 预期输出 | 测试类型 |
|--------|----------|------|----------|----------|
| TC001 | 队列为空 | strategy_id="test1", content="test content" | 成功入队，返回queue_id | happy |
| TC002 | 队列中有项目 | strategy_id="test2", content="test content", priority=1 | 成功入队，高优先级 | happy |
| TC003 | 队列中有项目 | strategy_id="test3", content="test content", callback_url="http://callback.com" | 成功入队，带回调 | happy |
| TC004 | 队列中有多个项目 | status="queued" | 返回所有队列中项目 | happy |
| TC005 | 队列为空 | status="any" | 返回空列表 | happy |
| TC006 | 策略ID为空 | strategy_id="", content="test content" | HTTP 422 错误 | error |
| TC007 | 策略内容为空 | strategy_id="test4", content="" | HTTP 422 错误 | error |
| TC008 | 队列项不存在 | 查询不存在的queue_id | HTTP 404 错误 | error |

## §7 依赖关系确认

- 本任务无前置依赖（Lane-A 首发）
- 解锁：CG2（依赖本任务）、CG3（依赖CG2）