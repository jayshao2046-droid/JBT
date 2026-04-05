from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

if __package__:
    from .support import append_event_log
    from .support import append_system_log
    from .support import get_compat_state
    from .support import get_strategy_record
    from .support import save_strategy_record
    from .support import serialize_strategy
else:
    from support import append_event_log
    from support import append_system_log
    from support import get_compat_state
    from support import get_strategy_record
    from support import save_strategy_record
    from support import serialize_strategy

router = APIRouter(prefix="/api", tags=["strategy"])


class StrategyImportPayload(BaseModel):
    name: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


@router.get("/strategies")
def list_strategies(request: Request) -> list[dict[str, Any]]:
    state = get_compat_state(request)
    strategies = [
        serialize_strategy(state, record)
        for record in state["strategies"].values()
    ]
    return sorted(strategies, key=lambda item: item.get("created_at", 0), reverse=True)


@router.post("/strategy/import", status_code=status.HTTP_201_CREATED)
def import_strategy(payload: StrategyImportPayload, request: Request) -> dict[str, Any]:
    state = get_compat_state(request)
    try:
        record, created = save_strategy_record(state, payload.name, payload.content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    symbols = record.get("symbols") or [None]
    contract = symbols[0]

    append_event_log(
        state,
        strategy=payload.name,
        action="导入策略" if created else "覆盖策略",
        contract=contract,
    )
    append_system_log(
        state,
        f"strategy {payload.name} {'imported' if created else 'updated'} via compatibility layer",
    )
    return serialize_strategy(state, record)


@router.delete("/strategy/{name}")
def delete_strategy(name: str, request: Request) -> dict[str, Any]:
    state = get_compat_state(request)
    record = get_strategy_record(state, name)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")

    state["strategies"].pop(name, None)

    # 同步删除磁盘 YAML 文件，防止 autoload 时重新加载
    yaml_filename = record.get("strategy_yaml_filename")
    if yaml_filename:
        try:
            from .support import get_settings
            from pathlib import Path
            settings = get_settings()
            strategy_root = settings.tqsdk_strategy_yaml_dir.expanduser().resolve()
            yaml_path = (strategy_root / yaml_filename).resolve()
            if strategy_root in yaml_path.parents and yaml_path.exists():
                yaml_path.unlink()
        except Exception:
            pass  # 磁盘删除失败不影响内存删除结果

    append_event_log(
        state,
        strategy=name,
        action="删除策略",
        contract=(record.get("symbols") or [None])[0],
    )
    append_system_log(state, f"strategy {name} deleted from compatibility store")
    return {"name": name, "deleted": True}


@router.get("/strategy/export/{name}", response_class=PlainTextResponse)
def export_strategy(name: str, request: Request) -> PlainTextResponse:
    state = get_compat_state(request)
    record = get_strategy_record(state, name)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    return PlainTextResponse(record["content"])