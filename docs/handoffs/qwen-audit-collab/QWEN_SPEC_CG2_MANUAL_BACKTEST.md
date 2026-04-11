# Qwen Spec CG2 Manual Backtest

## §1 任务摘要

目标：在 `services/backtest/` 实现人工手动回测功能，包括 human-in-the-loop 审核流程，扩展 CG1 建立的策略队列，增加审核状态层。

## §2 锚点声明

已存在：
- services/backtest/src/backtest/runner.py（回测执行核心，只调用不修改）
- services/backtest/src/backtest/strategy_queue.py（CG1 建立，本任务消费）
- services/backtest/src/api/app.py（路由注册）

新建（本任务产出）：
- services/backtest/src/backtest/manual_runner.py
- services/backtest/src/api/routes/approval.py

修改：
- services/backtest/src/api/app.py（注册 approval router）
- services/backtest/src/backtest/strategy_queue.py（CG1 的 strategy_queue 需要扩展 running 状态）

planned-placeholder（不在本任务范围，不得引用）：
- （无，此任务不依赖任何 placeholder）

## §3 状态机（必须完整定义）

```
queued → running → completed / failed
                 ↘ approved / rejected  (审核层，叠加在 completed 之上)
```

### 状态详细定义
- `queued`: 策略刚加入队列，等待处理
- `running`: 策略正在被回测执行器处理
- `completed`: 回测执行完成，等待人工审核
- `failed`: 回测执行失败
- `approved`: 人工审核通过
- `rejected`: 人工审核拒绝

### 状态转换规则
- `queued` → `running`: 由回测执行器自动触发
- `running` → `completed`: 回测成功完成
- `running` → `failed`: 回测执行失败
- `completed` → `approved`: 人工审核通过
- `completed` → `rejected`: 人工审核拒绝
- `approved`/`rejected` → 不能再转换（终态）

## §4 human-in-the-loop 流程

### 手动回测触发流程
```
POST /api/v1/backtest/manual/run → 触发 manual_runner → 调用 runner.py → 返回 run_id
```

### 审核流程
1. `GET /api/v1/backtest/approval/{run_id}` → 获取回测结果摘要（含绩效指标）
2. `POST /api/v1/backtest/approval/{run_id}/approve` → 审核通过
3. `POST /api/v1/backtest/approval/{run_id}/reject` → 拒绝，附 reason 字段

### 审核决策依据
- 回测绩效指标（年化收益率、夏普比率、最大回撤等）
- 风险指标（VaR、最大亏损等）
- 策略稳定性（收益分布、波动性等）
- 业务合理性（是否符合投资逻辑等）

## §5 ManualRunner 实现设计

### ManualRunner 类定义
```python
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from ..backtest.runner import Runner
from ..backtest.strategy_queue import StrategyQueue, QueueItem

class ManualRunner:
    def __init__(self, strategy_queue: StrategyQueue):
        self.queue = strategy_queue
        self.runner = Runner()
        
    def run_manual_backtest(
        self,
        strategy_id: str,
        strategy_content: str,
        priority: int = 0,
        callback_url: Optional[str] = None
    ) -> str:
        """触发手动回测，返回 run_id"""
        # 将策略加入队列
        queue_id = self.queue.enqueue(
            strategy_id=strategy_id,
            strategy_content=strategy_content,
            priority=priority,
            callback_url=callback_url
        )
        
        # 立即启动回测（跳过常规调度）
        self._execute_backtest(queue_id)
        
        return queue_id
    
    def _execute_backtest(self, queue_id: str):
        """执行回测并将状态更新为 completed"""
        item = self.queue.get_item(queue_id)
        if not item:
            raise ValueError(f"Queue item {queue_id} not found")
        
        # 更新状态为 running
        self.queue.update_status(queue_id, "running")
        
        try:
            # 执行回测
            result = self.runner.run(item.strategy_content)
            
            # 更新状态为 completed，并保存结果
            self.queue.update_status(queue_id, "completed", result)
            
        except Exception as e:
            # 更新状态为 failed
            self.queue.update_status(queue_id, "failed", {"error": str(e)})
    
    def approve_run(self, run_id: str, approver_id: str = None) -> Dict[str, Any]:
        """批准回测结果"""
        item = self.queue.get_item(run_id)
        if not item:
            raise ValueError(f"Run {run_id} not found")
        
        if item.status != "completed":
            raise ValueError(f"Run {run_id} is not in completed state, current: {item.status}")
        
        # 更新状态为 approved
        approval_data = {
            "approved_at": datetime.now().isoformat(),
            "approver_id": approver_id,
            "previous_status": item.status
        }
        
        self.queue.update_status(run_id, "approved", {**item.result, "approval": approval_data})
        
        return {
            "run_id": run_id,
            "status": "approved",
            "approved_at": approval_data["approved_at"],
            "approver_id": approver_id
        }
    
    def reject_run(self, run_id: str, reason: str, approver_id: str = None) -> Dict[str, Any]:
        """拒绝回测结果"""
        item = self.queue.get_item(run_id)
        if not item:
            raise ValueError(f"Run {run_id} not found")
        
        if item.status != "completed":
            raise ValueError(f"Run {run_id} is not in completed state, current: {item.status}")
        
        # 更新状态为 rejected
        rejection_data = {
            "rejected_at": datetime.now().isoformat(),
            "approver_id": approver_id,
            "reason": reason,
            "previous_status": item.status
        }
        
        self.queue.update_status(run_id, "rejected", {**item.result, "rejection": rejection_data})
        
        return {
            "run_id": run_id,
            "status": "rejected",
            "rejected_at": rejection_data["rejected_at"],
            "reason": reason,
            "approver_id": approver_id
        }
    
    def get_run_result(self, run_id: str) -> Dict[str, Any]:
        """获取回测结果摘要"""
        item = self.queue.get_item(run_id)
        if not item:
            raise ValueError(f"Run {run_id} not found")
        
        return {
            "run_id": run_id,
            "strategy_id": item.strategy_id,
            "status": item.status,
            "queued_at": item.queued_at,
            "started_at": item.started_at,
            "completed_at": item.completed_at,
            "result": item.result,
            "priority": item.priority
        }
```

## §6 接口规范

### 手动回测触发路由路径
```
POST /api/v1/backtest/manual/run
```

#### 请求体 JSON Schema
```json
{
  "strategy_id": "string",
  "strategy_content": "string",
  "priority": "integer",
  "callback_url": "string"
}
```

#### 响应 JSON Schema
```json
{
  "run_id": "string",
  "status": "string",
  "message": "string",
  "queued_at": "string"
}
```

### 获取回测结果路由路径
```
GET /api/v1/backtest/approval/{run_id}
```

#### Query 参数
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| include_details | boolean | 否 | 是否包含详细结果，默认为 false |

#### 响应 JSON Schema
```json
{
  "run_id": "string",
  "strategy_id": "string",
  "status": "string",
  "queued_at": "string",
  "started_at": "string",
  "completed_at": "string",
  "result_summary": {
    "performance": {
      "annual_return": "number",
      "sharpe_ratio": "number",
      "max_drawdown": "number",
      "win_rate": "number"
    },
    "risk_metrics": {
      "var_95": "number",
      "max_loss": "number",
      "volatility": "number"
    }
  },
  "result_details": {}
}
```

### 审核通过路由路径
```
POST /api/v1/backtest/approval/{run_id}/approve
```

#### 请求体 JSON Schema
```json
{
  "approver_id": "string"
}
```

#### 响应 JSON Schema
```json
{
  "run_id": "string",
  "status": "approved",
  "approved_at": "string",
  "approver_id": "string",
  "message": "string"
}
```

### 审核拒绝路由路径
```
POST /api/v1/backtest/approval/{run_id}/reject
```

#### 请求体 JSON Schema
```json
{
  "reason": "string",
  "approver_id": "string"
}
```

#### 响应 JSON Schema
```json
{
  "run_id": "string",
  "status": "rejected",
  "rejected_at": "string",
  "reason": "string",
  "approver_id": "string",
  "message": "string"
}
```

## §7 StrategyQueue 扩展

### 扩展后的状态枚举
```python
from enum import Enum

class RunStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    APPROVED = "approved"
    REJECTED = "rejected"
```

### 扩展后的队列项
```python
@dataclass
class QueueItem:
    queue_id: str
    strategy_id: str
    strategy_content: str
    status: str  # queued, running, completed, failed, approved, rejected
    priority: int
    callback_url: Optional[str] = None
    queued_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_at: Optional[str] = None
    result: Optional[Dict] = field(default_factory=dict)
    approval_info: Optional[Dict] = field(default_factory=dict)
```

### 扩展后的队列方法
```python
class StrategyQueue:
    # ... 现有方法 ...
    
    def get_completed_items(self) -> List[QueueItem]:
        """获取所有已完成但未审核的项目"""
        return [item for item in self._items.values() 
                if item.status == "completed"]
    
    def get_approved_items(self) -> List[QueueItem]:
        """获取所有已批准的项目"""
        return [item for item in self._items.values() 
                if item.status == "approved"]
    
    def get_rejected_items(self) -> List[QueueItem]:
        """获取所有已拒绝的项目"""
        return [item for item in self._items.values() 
                if item.status == "rejected"]
```

## §8 Approval 路由实现

### approval.py 路由文件
```python
from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..backtest.manual_runner import ManualRunner
from ..backtest.strategy_queue import StrategyQueue

router = APIRouter(prefix="/backtest", tags=["approval"])

class ManualRunRequest(BaseModel):
    strategy_id: str
    strategy_content: str
    priority: int = 0
    callback_url: Optional[str] = None

class ApproveRequest(BaseModel):
    approver_id: Optional[str] = None

class RejectRequest(BaseModel):
    reason: str
    approver_id: Optional[str] = None

# 全局实例（在实际实现中应该通过依赖注入）
manual_runner = ManualRunner(StrategyQueue())

@router.post("/manual/run", status_code=status.HTTP_201_CREATED)
def run_manual_backtest(req: ManualRunRequest) -> dict[str, Any]:
    """触发手动回测"""
    try:
        run_id = manual_runner.run_manual_backtest(
            strategy_id=req.strategy_id,
            strategy_content=req.strategy_content,
            priority=req.priority,
            callback_url=req.callback_url
        )
        
        return {
            "run_id": run_id,
            "status": "running",
            "message": f"Manual backtest started with run_id: {run_id}",
            "queued_at": manual_runner.queue.get_item(run_id).queued_at
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start manual backtest: {str(e)}"
        )

@router.get("/approval/{run_id}")
def get_approval_result(run_id: str, include_details: bool = False) -> dict[str, Any]:
    """获取回测结果用于审核"""
    try:
        result = manual_runner.get_run_result(run_id)
        
        # 构建结果摘要
        result_summary = {}
        if result.get("result") and isinstance(result["result"], dict):
            backtest_result = result["result"]
            result_summary = {
                "performance": {
                    "annual_return": backtest_result.get("annual_return", 0),
                    "sharpe_ratio": backtest_result.get("sharpe_ratio", 0),
                    "max_drawdown": backtest_result.get("max_drawdown", 0),
                    "win_rate": backtest_result.get("win_rate", 0)
                },
                "risk_metrics": {
                    "var_95": backtest_result.get("var_95", 0),
                    "max_loss": backtest_result.get("max_loss", 0),
                    "volatility": backtest_result.get("volatility", 0)
                }
            }
        
        response = {
            "run_id": run_id,
            "strategy_id": result["strategy_id"],
            "status": result["status"],
            "queued_at": result["queued_at"],
            "started_at": result.get("started_at"),
            "completed_at": result.get("completed_at"),
            "result_summary": result_summary
        }
        
        if include_details:
            response["result_details"] = result.get("result", {})
        
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get approval result: {str(e)}"
        )

@router.post("/approval/{run_id}/approve")
def approve_run(run_id: str, req: ApproveRequest) -> dict[str, Any]:
    """批准回测结果"""
    try:
        result = manual_runner.approve_run(run_id, req.approver_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve run: {str(e)}"
        )

@router.post("/approval/{run_id}/reject")
def reject_run(run_id: str, req: RejectRequest) -> dict[str, Any]:
    """拒绝回测结果"""
    try:
        result = manual_runner.reject_run(run_id, req.reason, req.approver_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject run: {str(e)}"
        )
```

## §9 错误处理清单

| 错误场景 | HTTP 状态码 | 响应体格式 |
|----------|-------------|------------|
| 手动回测请求体格式错误 | 422 | {"detail": "JSON schema validation failed"} |
| 必需字段缺失 | 422 | {"detail": "Missing required field: [字段名]"} |
| run_id 格式无效 | 422 | {"detail": "Invalid run_id format"} |
| run_id 不存在 | 404 | {"detail": "Run [ID] not found"} |
| 尝试审核非 completed 状态的项目 | 400 | {"detail": "Run [ID] is not in completed state, current: [状态]"} |
| 重复审核同一项目 | 400 | {"detail": "Run [ID] already has approval status"} |
| 内部处理错误 | 500 | {"detail": "Failed to process request: [错误详情]"} |
| 审核原因为空 | 422 | {"detail": "Reason is required for rejection"} |

## §10 测试用例（最少 8 条）

| 用例ID | 前置条件 | 输入 | 预期输出 | 测试类型 |
|--------|----------|------|----------|----------|
| TC001 | 队列为空 | strategy_id="test1", content="test content" | 成功触发手动回测，返回run_id | happy |
| TC002 | 回测执行成功 | run_id=有效ID | 返回回测结果摘要 | happy |
| TC003 | 回测已完成待审核 | run_id=已完成ID, approver_id="user1" | 成功批准，状态变为approved | happy |
| TC004 | 回测已完成待审核 | run_id=已完成ID, reason="不符合要求" | 成功拒绝，状态变为rejected | happy |
| TC005 | 重复批准 | run_id=已批准ID | HTTP 400 错误 | error |
| TC006 | run_id 不存在 | 查询不存在的run_id | HTTP 404 错误 | error |
| TC007 | 非 completed 状态审核 | run_id=running状态 | HTTP 400 错误 | error |
| TC008 | 拒绝原因为空 | run_id=已完成ID, reason="" | HTTP 422 错误 | error |

## §11 依赖关系

### 前置依赖
- CG1: 回测端策略导入队列（已完成）

### 解锁任务
- CG3: 回测端股票手动回测与看板调整（依赖本任务）
- CA6: 信号真闭环 → sim-trading（依赖本任务）

### 服务间依赖
- 依赖 backtest 服务内部组件，无外部服务依赖
- 通过队列机制实现异步处理

## §12 审核工作流

### 审核界面需求
- 显示回测绩效指标对比图表
- 展示策略逻辑和参数配置
- 提供历史审核记录查询
- 支持批量审核操作

### 审核权限控制
- 只有授权用户可以执行审核操作
- 记录审核人员和时间戳
- 支持多级审核流程

### 审核决策支持
- AI 辅助分析工具
- 历史相似策略表现对比
- 风险预警提示

## §13 监控与告警

### 关键指标
- 手动回测成功率
- 审核平均耗时
- 审核通过率
- 队列积压情况

### 告警规则
- 队列积压超过阈值时告警
- 审核耗时过长时告警
- 连续失败回测时告警

## §14 数据持久化

### 审核记录存储
- 审核决策记录持久化存储
- 包含审核人、时间、理由等信息
- 支持审计追踪

### 性能数据归档
- 回测结果长期存储
- 支持按策略、时间等维度查询
- 数据压缩和清理策略