# QWEN_SPEC_CG3_STOCK_BACKTEST_BOARD.md

## §1 任务摘要

本规格书定义CG3回测端股票手动回测与看板调整功能，旨在增强backtest服务的股票手动回测能力，并优化相关看板显示。该功能将允许用户对股票策略进行手动审批和干预，同时提供更直观的可视化界面来监控和管理回测过程。路由前缀遵循CG2已建立的模式。

## §2 锚点声明

已存在：
- services/backtest/src/backtest/runner.py（回测执行核心，只调用不修改）
- services/backtest/src/api/app.py（路由注册）

新建（本任务产出）：
- services/backtest/src/backtest/stock_runner.py（股票手动回测执行器，对称 CG2 的 manual_runner.py）
- services/backtest/src/api/routes/stock_approval.py（股票审批路由）
- tests/backtest/api/test_stock_approval.py

修改：
- services/backtest/src/api/app.py（注册 stock_approval_router）

planned-placeholder（本任务依赖，激活时必须已存在）：
- services/backtest/src/backtest/strategy_queue.py（CG1/TASK-0052 产出，CG3 激活时必须已存在）
- services/backtest/src/backtest/manual_runner.py（CG2/TASK-0055 产出，CG3 激活时必须已存在）
- services/backtest/src/api/routes/approval.py（CG2/TASK-0055 产出，CG3 在此基础上追加股票路由）

> **[Atlas 补漏 2026-04-11]** 原草稿将 `strategy_queue.py`（CG1 产出）和 `approval.py`（CG2 产出）列于"已存在"，但两者均为计划产出，当前代码库中均不存在。已移至 planned-placeholder 并注明来源任务。CG3 激活前置：TASK-0052（CG1）+ TASK-0055（CG2）均完成。

## §3 接口规范

### 3.1 手动回测触发路由路径
- `/api/v1/backtest/manual/stock/run` (POST)

### 3.2 看板调整路由路径
- `/api/v1/backtest/manual/stock/status/{request_id}` (GET)
- `/api/v1/backtest/manual/stock/approve/{request_id}` (POST)
- `/api/v1/backtest/manual/stock/reject/{request_id}` (POST)
- `/api/v1/dashboard/stock/backtests` (GET)
- `/api/v1/dashboard/stock/backtests/{backtest_id}` (GET)
- `/api/v1/dashboard/stock/backtests/{backtest_id}/results` (GET)
- `/api/v1/dashboard/stock/backtests/{backtest_id}/performance` (GET)

### 3.3 HTTP方法
- POST: 触发手动回测、审批、拒绝操作
- GET: 查询状态、获取看板数据

### 3.4 手动回测触发请求体JSON Schema
```json
{
  "strategy_id": "string",
  "start_time": "string",
  "end_time": "string",
  "initial_capital": "number",
  "symbols": ["string"],
  "notes": "string",
  "priority": "string"
}
```

### 3.5 手动回测触发响应JSON Schema
```json
{
  "status": "string",
  "request_id": "string",
  "message": "string",
  "estimated_completion": "string"
}
```

### 3.6 审批请求体JSON Schema
```json
{
  "approver_id": "string",
  "comments": "string"
}
```

### 3.7 审批响应JSON Schema
```json
{
  "status": "string",
  "message": "string",
  "processed_at": "string"
}
```

### 3.8 看板股票回测列表响应JSON Schema
```json
[
  {
    "backtest_id": "string",
    "strategy_id": "string",
    "strategy_name": "string",
    "status": "string",
    "start_time": "string",
    "end_time": "string",
    "initial_capital": "number",
    "current_pnl": "number",
    "progress": "number",
    "created_at": "string",
    "updated_at": "string",
    "requested_by": "string",
    "approved_by": "string",
    "symbols": ["string"]
  }
]
```

## §4 看板UI调整设计

### 4.1 股票回测概览面板
- 显示股票策略总数、运行中数量、待审批数量
- 展示最近回测的绩效指标
- 提供快速操作按钮（新建回测、审批队列）

### 4.2 股票回测详情面板
- 策略基本信息（名称、类型、参数）
- 回测进度可视化（进度条、时间轴）
- 实时绩效图表（收益曲线、最大回撤、夏普比率）
- 交易明细表格（时间、标的、方向、盈亏）

### 4.3 审批队列面板
- 待审批的股票回测请求列表
- 每个请求的基本信息和风险指标
- 快速审批操作按钮

## §5 状态机（必须完整定义）

### 5.1 状态详细定义
- `SUBMITTED`: 回测请求已提交，等待审批
- `PENDING_APPROVAL`: 请求正在审批队列中
- `APPROVED`: 请求已获得审批，等待执行
- `RUNNING`: 回测正在执行中
- `COMPLETED`: 回测成功完成
- `FAILED`: 回测执行失败
- `REJECTED`: 请求被拒绝
- `CANCELLED`: 请求被取消

### 5.2 状态转换规则
```
SUBMITTED -> PENDING_APPROVAL (自动转换)
PENDING_APPROVAL -> APPROVED (审批通过)
PENDING_APPROVAL -> REJECTED (审批拒绝)
APPROVED -> RUNNING (开始执行)
RUNNING -> COMPLETED (执行完成)
RUNNING -> FAILED (执行失败)
ANY_STATE -> CANCELLED (手动取消)
```

### 5.3 股票手动回测触发流程
1. 用户通过UI或API提交股票手动回测请求
2. 系统验证请求参数的有效性
3. 创建回测任务并设置状态为SUBMITTED
4. 自动转换为PENDING_APPROVAL并进入审批队列
5. 等待审批人员操作

### 5.4 审核流程
1. 审批人员查看待审批队列
2. 查看回测请求的详细信息和风险指标
3. 做出批准或拒绝决定
4. 系统记录审批决策和审批人信息

### 5.5 审核决策依据
- 策略的历史表现
- 风险指标（最大回撤、波动率等）
- 市场环境适应性
- 资金规模合理性

## §6 测试用例（最少6条）

### 6.1 基础功能测试
- TC_CG3_001: 验证股票手动回测请求的正常提交流程
- TC_CG3_002: 验证审批流程（批准和拒绝）的正确执行
- TC_CG3_003: 验证回测状态的正确转换

### 6.2 看板功能测试
- TC_CG3_004: 验证股票回测列表在看板上的正确显示
- TC_CG3_005: 验证回测详情页面的数据准确性
- TC_CG3_006: 验证审批队列的实时更新

### 6.3 边界条件测试
- TC_CG3_007: 验证无效参数的错误处理
- TC_CG3_008: 验证并发审批请求的处理

## §7 ManualRunner类定义（股票专用）

```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
import asyncio
import logging

class StockBacktestStatus(Enum):
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

@dataclass
class StockManualBacktestRequest:
    request_id: str
    strategy_id: str
    start_time: str
    end_time: str
    initial_capital: float
    symbols: List[str]
    notes: str
    priority: str
    requested_by: str
    created_at: str
    status: StockBacktestStatus
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[str] = None
    backtest_id: Optional[str] = None

class StockManualRunner:
    def __init__(self):
        self.requests: Dict[str, StockManualBacktestRequest] = {}
        self.approval_queue: List[str] = []
        self.running_tasks: List[str] = []
        self.logger = logging.getLogger(__name__)
    
    async def submit_request(self, request_data: dict) -> dict:
        """提交股票手动回测请求"""
        request_id = self._generate_request_id()
        
        new_request = StockManualBacktestRequest(
            request_id=request_id,
            strategy_id=request_data['strategy_id'],
            start_time=request_data['start_time'],
            end_time=request_data['end_time'],
            initial_capital=request_data['initial_capital'],
            symbols=request_data.get('symbols', []),
            notes=request_data.get('notes', ''),
            priority=request_data.get('priority', 'medium'),
            requested_by=request_data.get('requested_by', 'unknown'),
            created_at=self._get_current_time(),
            status=StockBacktestStatus.SUBMITTED
        )
        
        self.requests[request_id] = new_request
        
        # 自动转换为待审批状态
        await self._transition_status(request_id, StockBacktestStatus.PENDING_APPROVAL)
        
        return {
            "status": "submitted",
            "request_id": request_id,
            "message": "股票手动回测请求已提交，等待审批"
        }
    
    async def approve_request(self, request_id: str, approver_id: str, comments: str) -> dict:
        """批准股票手动回测请求"""
        if request_id not in self.requests:
            return {"status": "error", "message": "请求ID不存在"}
        
        request = self.requests[request_id]
        
        if request.status != StockBacktestStatus.PENDING_APPROVAL:
            return {"status": "error", "message": f"请求状态不是待审批，当前状态: {request.status.value}"}
        
        await self._transition_status(request_id, StockBacktestStatus.APPROVED)
        
        # 记录审批信息
        request.approved_by = approver_id
        request.approved_at = self._get_current_time()
        
        # 开始执行回测
        asyncio.create_task(self._execute_backtest(request_id))
        
        return {
            "status": "approved",
            "message": "股票手动回测请求已批准，开始执行"
        }
    
    async def reject_request(self, request_id: str, approver_id: str, comments: str) -> dict:
        """拒绝股票手动回测请求"""
        if request_id not in self.requests:
            return {"status": "error", "message": "请求ID不存在"}
        
        request = self.requests[request_id]
        
        if request.status != StockBacktestStatus.PENDING_APPROVAL:
            return {"status": "error", "message": f"请求状态不是待审批，当前状态: {request.status.value}"}
        
        request.rejected_by = approver_id
        request.rejected_at = self._get_current_time()
        
        await self._transition_status(request_id, StockBacktestStatus.REJECTED)
        
        return {
            "status": "rejected",
            "message": "股票手动回测请求已被拒绝"
        }
    
    async def get_request_status(self, request_id: str) -> dict:
        """获取请求状态"""
        if request_id not in self.requests:
            return {"status": "error", "message": "请求ID不存在"}
        
        request = self.requests[request_id]
        
        return {
            "request_id": request.request_id,
            "strategy_id": request.strategy_id,
            "status": request.status.value,
            "start_time": request.start_time,
            "end_time": request.end_time,
            "initial_capital": request.initial_capital,
            "symbols": request.symbols,
            "notes": request.notes,
            "priority": request.priority,
            "requested_by": request.requested_by,
            "created_at": request.created_at,
            "approved_by": request.approved_by,
            "approved_at": request.approved_at,
            "rejected_by": request.rejected_by,
            "rejected_at": request.rejected_at,
            "backtest_id": request.backtest_id
        }
    
    async def _transition_status(self, request_id: str, new_status: StockBacktestStatus):
        """状态转换"""
        if request_id in self.requests:
            old_status = self.requests[request_id].status
            self.requests[request_id].status = new_status
            
            # 更新队列
            if old_status == StockBacktestStatus.PENDING_APPROVAL:
                if request_id in self.approval_queue:
                    self.approval_queue.remove(request_id)
            elif new_status == StockBacktestStatus.PENDING_APPROVAL:
                if request_id not in self.approval_queue:
                    self.approval_queue.append(request_id)
            
            self.logger.info(f"Request {request_id} status changed from {old_status.value} to {new_status.value}")
    
    async def _execute_backtest(self, request_id: str):
        """执行回测任务"""
        if request_id not in self.requests:
            return
        
        request = self.requests[request_id]
        await self._transition_status(request_id, StockBacktestStatus.RUNNING)
        
        try:
            # 这里调用实际的回测执行逻辑
            # 模拟回测执行
            await asyncio.sleep(2)  # 模拟执行时间
            
            # 生成回测ID
            backtest_id = self._generate_backtest_id()
            request.backtest_id = backtest_id
            
            await self._transition_status(request_id, StockBacktestStatus.COMPLETED)
            
            self.logger.info(f"Backtest {backtest_id} for request {request_id} completed successfully")
        except Exception as e:
            self.logger.error(f"Backtest execution failed for request {request_id}: {str(e)}")
            await self._transition_status(request_id, StockBacktestStatus.FAILED)
    
    def _generate_request_id(self) -> str:
        """生成请求ID"""
        import uuid
        return f"stock_manual_{uuid.uuid4().hex[:8]}"
    
    def _generate_backtest_id(self) -> str:
        """生成回测ID"""
        import uuid
        return f"stock_bt_{uuid.uuid4().hex[:12]}"
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
```

## §8 看板调整实现

### 8.1 股票回测列表API实现
```python
from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()

@router.get("/dashboard/stock/backtests", response_model=List[dict])
async def get_stock_backtests(
    status: str = None,
    limit: int = 50,
    offset: int = 0
) -> List[dict]:
    """获取股票回测列表"""
    try:
        # 获取所有股票相关的回测请求
        stock_requests = []
        for req_id, request in stock_manual_runner.requests.items():
            if status is None or request.status.value == status:
                stock_requests.append({
                    "backtest_id": request.backtest_id,
                    "request_id": request.request_id,
                    "strategy_id": request.strategy_id,
                    "strategy_name": f"Stock_Strategy_{request.strategy_id}",
                    "status": request.status.value,
                    "start_time": request.start_time,
                    "end_time": request.end_time,
                    "initial_capital": request.initial_capital,
                    "current_pnl": 0,  # 这里应该是实时计算的值
                    "progress": 0,  # 进度百分比
                    "created_at": request.created_at,
                    "updated_at": request.created_at,
                    "requested_by": request.requested_by,
                    "approved_by": request.approved_by,
                    "symbols": request.symbols
                })
        
        # 应用分页
        paginated = stock_requests[offset:offset+limit]
        
        return paginated
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票回测列表失败: {str(e)}")

@router.get("/dashboard/stock/backtests/{backtest_id}")
async def get_stock_backtest_detail(backtest_id: str):
    """获取股票回测详情"""
    try:
        # 查找对应的请求
        target_request = None
        for req in stock_manual_runner.requests.values():
            if req.backtest_id == backtest_id:
                target_request = req
                break
        
        if not target_request:
            raise HTTPException(status_code=404, detail="未找到对应的回测请求")
        
        return {
            "backtest_id": target_request.backtest_id,
            "request_id": target_request.request_id,
            "strategy_id": target_request.strategy_id,
            "strategy_config": {},  # 策略配置详情
            "status": target_request.status.value,
            "start_time": target_request.start_time,
            "end_time": target_request.end_time,
            "initial_capital": target_request.initial_capital,
            "symbols": target_request.symbols,
            "notes": target_request.notes,
            "priority": target_request.priority,
            "requested_by": target_request.requested_by,
            "approved_by": target_request.approved_by,
            "approved_at": target_request.approved_at,
            "rejected_by": target_request.rejected_by,
            "rejected_at": target_request.rejected_at,
            "created_at": target_request.created_at,
            "updated_at": target_request.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票回测详情失败: {str(e)}")
```

### 8.2 审批队列API实现
```python
@router.get("/dashboard/stock/approval-queue")
async def get_stock_approval_queue():
    """获取股票回测审批队列"""
    try:
        queue_items = []
        for req_id in stock_manual_runner.approval_queue:
            request = stock_manual_runner.requests[req_id]
            queue_items.append({
                "request_id": request.request_id,
                "strategy_id": request.strategy_id,
                "strategy_name": f"Stock_Strategy_{request.strategy_id}",
                "start_time": request.start_time,
                "end_time": request.end_time,
                "initial_capital": request.initial_capital,
                "symbols": request.symbols,
                "notes": request.notes,
                "priority": request.priority,
                "requested_by": request.requested_by,
                "created_at": request.created_at
            })
        
        return queue_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票审批队列失败: {str(e)}")
```

## §9 错误处理清单

### 9.1 请求提交错误
- `INVALID_REQUEST_PARAMS`: 请求参数无效
  - 原因：缺少必要参数、参数格式错误
  - 处理：返回400错误，提供具体错误信息

- `STRATEGY_NOT_FOUND`: 策略ID不存在
  - 原因：提供的策略ID在系统中找不到
  - 处理：返回404错误

### 9.2 审批错误
- `REQUEST_NOT_PENDING_APPROVAL`: 请求不在待审批状态
  - 原因：尝试审批一个已经处理过的请求
  - 处理：返回400错误

- `INSUFFICIENT_PERMISSIONS`: 权限不足
  - 原因：审批人没有足够的权限执行操作
  - 处理：返回403错误

### 9.3 执行错误
- `BACKTEST_EXECUTION_FAILED`: 回测执行失败
  - 原因：策略执行错误、数据获取失败等
  - 处理：记录错误日志，更新状态为失败

## §10 安全考虑

### 10.1 访问控制
- 手动回测功能仅对具有相应权限的用户开放
- 审批操作需要特定的角色权限
- 所有操作都记录操作人和时间戳

### 10.2 数据安全
- 敏感的策略参数在传输和存储时加密
- 审批决策记录不可篡改

## §11 性能优化

### 11.1 缓存策略
- 回测结果缓存以提高看板响应速度
- 常用的策略配置信息缓存

### 11.2 异步处理
- 回测执行采用异步方式，避免阻塞主线程
- 状态更新采用事件驱动模式

## §12 监控与告警

### 12.1 关键指标
- 手动回测请求成功率
- 平均审批时间
- 回测执行时间
- 系统资源使用率

### 12.2 告警规则
- 当审批队列积压超过阈值时发出告警
- 当回测失败率超过阈值时发出告警

## §13 扩展性设计

### 13.1 插件化审批流程
审批流程设计为可插拔，支持不同的审批策略。

### 13.2 多市场支持
设计上支持扩展到其他市场（如期货、外汇）的手动回测功能。

## §14 依赖关系确认

### 14.1 前置依赖
- CG2 手动回测基础功能: 股票手动回测基于通用手动回测框架
- Backtest服务核心功能: 依赖回测引擎执行实际回测

### 14.2 后续依赖
- 看板服务: 需要在看板中展示股票回测相关信息
- 通知服务: 需要发送审批通知和回测完成通知