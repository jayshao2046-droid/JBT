"""Decision 内部正式 local YAML 回测入口。"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from src.backtest.local_engine import ApiDataProvider, LocalBacktestEngine, LocalBacktestParams
from src.core.settings import get_settings

from .contract_resolver import ContractResolver

logger = logging.getLogger(__name__)


class LocalFormalBacktestError(RuntimeError):
    """本地正式回测异常。"""


class LocalFormalBacktestClient:
    """使用 decision 内聚的 formal local engine 执行 YAML 回测。"""

    def __init__(self, data_url: str | None = None) -> None:
        self._settings = get_settings()
        resolved_data_url = (data_url or self._settings.data_api_url).rstrip("/")
        self._strategy_root = self._settings.tqsdk_strategy_yaml_dir.expanduser().resolve()
        self._strategy_root.mkdir(parents=True, exist_ok=True)
        self._engine = LocalBacktestEngine(ApiDataProvider(resolved_data_url))
        self._contract_resolver = ContractResolver(resolved_data_url)

    async def run_backtest(
        self,
        yaml_path: str | Path,
        start_date: str,
        end_date: str,
        initial_capital: float = 500000.0,
    ) -> dict[str, Any]:
        source_path = Path(yaml_path).expanduser().resolve()
        if not source_path.exists():
            raise LocalFormalBacktestError(f"YAML 文件不存在: {source_path}")

        strategy = self._load_strategy(source_path)
        runtime_yaml_path, strategy_yaml_filename = self._ensure_runtime_yaml(source_path)
        requested_symbol = await self._resolve_requested_symbol(strategy)

        symbols = strategy.get("symbols") or []
        if not symbols:
            raise LocalFormalBacktestError("YAML 缺少 symbols 字段")

        transaction_costs = strategy.get("transaction_costs") or {}
        risk = strategy.get("risk") or {}
        job_id = f"local-{uuid.uuid4().hex[:12]}"
        params = LocalBacktestParams(
            job_id=job_id,
            strategy_id=str(strategy.get("name") or runtime_yaml_path.stem),
            strategy_yaml_filename=strategy_yaml_filename,
            symbols=[str(symbol) for symbol in symbols],
            requested_symbol=requested_symbol,
            start_date=date.fromisoformat(start_date),
            end_date=date.fromisoformat(end_date),
            initial_capital=float(initial_capital),
            timeframe_minutes=int(strategy.get("timeframe_minutes") or 60),
            slippage_per_unit=float(transaction_costs.get("slippage_per_unit") or 0.0),
            commission_per_lot_round_turn=float(
                transaction_costs.get("commission_per_lot_round_turn") or 0.0
            ),
            max_drawdown=float(risk.get("max_drawdown") or 1.0),
            daily_loss_limit=float(risk.get("daily_loss_limit") or 1.0),
        )

        try:
            report = await asyncio.to_thread(self._engine.run, params)
        except Exception as exc:
            raise LocalFormalBacktestError(f"本地正式回测失败: {exc}") from exc

        payload = report.to_dict()
        payload["task_id"] = job_id
        payload["status"] = str(payload.get("summary", {}).get("status") or "completed")
        return payload

    async def close(self) -> None:
        await self._contract_resolver.close()

    async def __aenter__(self) -> "LocalFormalBacktestClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def _load_strategy(self, yaml_path: Path) -> dict[str, Any]:
        try:
            with yaml_path.open("r", encoding="utf-8") as handle:
                strategy = yaml.safe_load(handle)
        except Exception as exc:
            raise LocalFormalBacktestError(f"读取 YAML 失败: {exc}") from exc

        if not isinstance(strategy, dict):
            raise LocalFormalBacktestError("YAML 顶层必须是 mapping")
        return strategy

    def _ensure_runtime_yaml(self, source_path: Path) -> tuple[Path, str]:
        if self._strategy_root == source_path.parent or self._strategy_root in source_path.parents:
            relative_path = source_path.relative_to(self._strategy_root)
            return source_path, relative_path.as_posix()

        target_path = self._strategy_root / source_path.name
        target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
        return target_path, target_path.name

    async def _resolve_requested_symbol(self, strategy: dict[str, Any]) -> str:
        symbols = strategy.get("symbols") or []
        if not symbols:
            raise LocalFormalBacktestError("YAML 缺少 symbols 字段")

        primary_symbol = str(symbols[0])
        base_symbol = primary_symbol.split(".")[-1] if "." in primary_symbol else primary_symbol
        if "_main" not in base_symbol and not base_symbol.endswith("0"):
            return primary_symbol

        resolve_symbol = primary_symbol.replace("_main", "0") if "_main" in base_symbol else primary_symbol
        try:
            resolved_symbol = await self._contract_resolver.get_main_contract(resolve_symbol)
        except Exception as exc:
            raise LocalFormalBacktestError(
                f"主力合约解析失败: {primary_symbol}: {exc}"
            ) from exc

        logger.info("local formal backtest 主力合约解析: %s -> %s", primary_symbol, resolved_symbol)
        return resolved_symbol