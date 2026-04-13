"""
决策看板 Web API 路由
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import asyncio

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ...decision.validator import ParameterValidator
from ...decision.progress_tracker import get_tracker
from ...stats.performance import PerformanceCalculator
from ...stats.quality import QualityCalculator

router = APIRouter(prefix="/api/v1/decision", tags=["decision_web"])

# 模拟决策历史存储（实际应使用数据库）
_decision_history: List[Dict] = []


class ValidateRequest(BaseModel):
    strategy_id: str
    params: Dict[str, Any]
    schema: Optional[Dict] = None


class BatchDecisionRequest(BaseModel):
    strategy_id: str
    param_grid: Dict[str, List[Any]]
    base_params: Optional[Dict[str, Any]] = None


@router.get("/history")
async def get_decision_history(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=1000),
) -> Dict:
    """获取决策历史记录"""
    filtered = _decision_history

    if start_date:
        filtered = [d for d in filtered if d.get("created_at", "") >= start_date]

    if end_date:
        filtered = [d for d in filtered if d.get("created_at", "") <= end_date]

    # 按时间倒序
    filtered = sorted(filtered, key=lambda x: x.get("created_at", ""), reverse=True)

    return {
        "total": len(filtered),
        "decisions": filtered[:limit],
        "start_date": start_date,
        "end_date": end_date,
    }


@router.post("/validate")
async def validate_strategy_params(request: ValidateRequest) -> Dict:
    """验证策略参数"""
    validator = ParameterValidator()

    # 默认 schema
    if not request.schema:
        request.schema = {
            "required": ["initial_capital"],
            "properties": {
                "initial_capital": {"type": "float", "min": 10000},
                "max_position_size": {"type": "float", "min": 0.01, "max": 1.0},
                "stop_loss_pct": {"type": "float", "min": 0.01, "max": 0.5},
            },
            "dependencies": [],
        }

    result = validator.validate_all(request.params, request.schema)

    return {
        "valid": result["valid"],
        "errors": result["errors"],
        "strategy_id": request.strategy_id,
    }


@router.get("/progress/{decision_id}/stream")
async def stream_decision_progress(decision_id: str):
    """SSE 流式推送决策进度"""

    async def event_generator():
        tracker = get_tracker()
        max_iterations = 60  # 最多推送 60 次（60秒）

        for i in range(max_iterations):
            progress = tracker.get(decision_id)

            if not progress:
                # 如果没有进度记录，返回初始状态
                import json
                _default = {"progress_percent": 0, "status": "pending", "current_stage": "等待中"}
                yield f"data: {json.dumps(_default)}\n\n"
            else:
                import json

                yield f"data: {json.dumps(progress)}\n\n"

                # 如果已完成或失败，停止推送
                if progress.get("status") in ["completed", "failed"]:
                    break

            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{decision_id}/performance")
async def get_decision_performance(decision_id: str) -> Dict:
    """获取决策绩效 KPI"""
    # 查找决策记录
    decision = next((d for d in _decision_history if d.get("decision_id") == decision_id), None)

    if not decision:
        raise HTTPException(status_code=404, detail="决策记录不存在")

    signals = decision.get("signals", [])

    calculator = PerformanceCalculator()
    performance = calculator.calculate_all(signals)

    return {"decision_id": decision_id, "performance": performance}


@router.get("/{decision_id}/quality")
async def get_decision_quality(decision_id: str) -> Dict:
    """获取决策质量 KPI"""
    decision = next((d for d in _decision_history if d.get("decision_id") == decision_id), None)

    if not decision:
        raise HTTPException(status_code=404, detail="决策记录不存在")

    signals = decision.get("signals", [])
    factors = decision.get("factors", [])

    calculator = QualityCalculator()
    quality = calculator.calculate_all(signals, factors)

    return {"decision_id": decision_id, "quality": quality}


@router.post("/batch")
async def create_batch_decision(request: BatchDecisionRequest) -> Dict:
    """批量决策（参数网格搜索）"""
    import itertools

    # 生成参数组合
    param_names = list(request.param_grid.keys())
    param_values = list(request.param_grid.values())

    combinations = list(itertools.product(*param_values))

    tasks = []
    for combo in combinations:
        params = dict(zip(param_names, combo))
        if request.base_params:
            params.update(request.base_params)

        task_id = f"batch_{request.strategy_id}_{len(tasks)}"
        tasks.append({"task_id": task_id, "strategy_id": request.strategy_id, "params": params, "status": "pending"})

    return {
        "batch_id": f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "total_tasks": len(tasks),
        "tasks": tasks,
    }


# 辅助函数：添加决策历史记录（供其他模块调用）
def add_decision_to_history(decision: Dict) -> None:
    """添加决策到历史记录"""
    if "created_at" not in decision:
        decision["created_at"] = datetime.now(timezone.utc).isoformat()

    _decision_history.append(decision)

    # 限制历史记录数量
    if len(_decision_history) > 10000:
        _decision_history.pop(0)
