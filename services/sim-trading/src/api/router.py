from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["sim-trading"])


@router.get("/status")
def get_status():
    """返回服务运行状态（骨架阶段占位）。"""
    return {"status": "sim-trading running", "stage": "skeleton"}


@router.get("/positions")
def get_positions():
    """持仓查询接口（骨架阶段占位，尚未实现）。"""
    return {"positions": [], "note": "not implemented yet"}


@router.get("/orders")
def get_orders():
    """订单查询接口（骨架阶段占位，尚未实现）。"""
    return {"orders": [], "note": "not implemented yet"}


@router.post("/orders")
def create_order():
    """下单接口（骨架阶段占位，尚未实现）。"""
    return {"result": "not implemented yet"}
