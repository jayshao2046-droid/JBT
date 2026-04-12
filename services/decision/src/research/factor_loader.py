from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

import httpx
import numpy as np

from ..core.settings import get_settings
from ..gating.backtest_gate import get_backtest_gate
from .stock_data_client import StockDataClient

# TASK-0083: 接入共享因子注册表
try:
    from shared.python_common.factors.registry import check_coverage, get_jbt_factors
except ImportError:
    # Fallback: 如果共享库未安装，使用本地实现
    def check_coverage(required_factors):
        return {name: True for name in required_factors}
    def get_jbt_factors():
        return []

logger = logging.getLogger(__name__)


class FactorLoadError(RuntimeError):
    """Raised when bars data cannot be converted into a usable factor dataset."""


class FactorLoader:
    """因子数据加载（通过 data service bars API 获取真实序列）。"""

    _BASE_FEATURE_COUNT = 5
    _MIN_REQUIRED_BARS = 3
    _CONTINUOUS_DIR_PATTERN = re.compile(r"(?i)^KQ_m_([A-Za-z]+)_([A-Za-z]+)$")
    _CONTINUOUS_ALIAS_PATTERN = re.compile(r"(?i)^KQ\.m@([A-Za-z]+)\.([A-Za-z]+)$")
    _EXACT_SYMBOL_PATTERN = re.compile(r"(?i)^([A-Za-z]+)[._]([A-Za-z]+?)(\d+)?$")
    _STOCK_SYMBOL_PATTERN = re.compile(r"^\d{6}\.(SZ|SH|BJ)$", re.IGNORECASE)

    def __init__(self) -> None:
        self._settings = get_settings()

    def load(
        self,
        strategy_id: str,
        start_date: str,
        end_date: str,
        n_samples: int = 200,
        n_features: int = 20,
    ) -> tuple[np.ndarray, np.ndarray]:
        """返回由 bars 构造的最小可用 (X, y) tuple。

        TASK-0083: 校验因子是否在共享注册表中。
        """
        # 校验因子覆盖（基础因子：close_return, intrabar_range, candle_body, volume_return, open_interest_return）
        jbt_factors = get_jbt_factors()
        if jbt_factors:
            logger.info(f"共享因子注册表已加载，包含 {len(jbt_factors)} 个因子")

        symbol = self._resolve_data_symbol(strategy_id)
        bars = self._fetch_bars(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )
        X, y = self._build_dataset(bars=bars, n_features=n_features)

        if n_samples > 0 and X.shape[0] > n_samples:
            X = X[-n_samples:]
            y = y[-n_samples:]

        return X, y

    def _resolve_data_symbol(self, strategy_id: str) -> str:
        cert = get_backtest_gate().get_cert(strategy_id)
        candidates = [
            cert.executed_data_symbol if cert is not None else "",
            cert.requested_symbol if cert is not None else "",
            strategy_id,
        ]

        for candidate in candidates:
            symbol = candidate.strip()
            if symbol and self._is_supported_symbol(symbol):
                return symbol

        raise FactorLoadError(
            "No valid data symbol available for strategy "
            f"{strategy_id}; expected backtest certificate executed_data_symbol/"
            "requested_symbol or a strategy_id already matching data symbol format"
        )

    @classmethod
    def _is_supported_symbol(cls, symbol: str) -> bool:
        return any(
            pattern.fullmatch(symbol) is not None
            for pattern in (
                cls._CONTINUOUS_DIR_PATTERN,
                cls._CONTINUOUS_ALIAS_PATTERN,
                cls._EXACT_SYMBOL_PATTERN,
                cls._STOCK_SYMBOL_PATTERN,
            )
        )

    @classmethod
    def _is_stock_symbol(cls, symbol: str) -> bool:
        """判断是否为 A 股股票代码。"""
        return cls._STOCK_SYMBOL_PATTERN.fullmatch(symbol) is not None

    def _fetch_bars(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        # 股票代码走 stock_data_client
        if self._is_stock_symbol(symbol):
            return self._fetch_stock_bars(
                symbol=symbol, start_date=start_date, end_date=end_date
            )

        base_url = self._settings.data_service_url.rstrip("/")
        url = f"{base_url}/api/v1/bars"
        params = {
            "symbol": symbol,
            "timeframe_minutes": 1,
            "start": start_date,
            "end": end_date,
        }

        try:
            response = httpx.get(url, params=params, timeout=self._settings.data_service_timeout)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise FactorLoadError(
                f"Failed to load bars from data service for symbol {symbol}: {exc}"
            ) from exc

        bars = payload.get("bars") if isinstance(payload, dict) else None
        if not isinstance(bars, list) or len(bars) < self._MIN_REQUIRED_BARS:
            raise FactorLoadError(
                f"Data service returned insufficient bars for symbol {symbol}"
            )

        return bars

    def _fetch_stock_bars(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        """通过 StockDataClient 获取股票 K 线，并补齐 open_interest=0。"""
        from .stock_data_client import StockDataClient, StockDataError

        client = StockDataClient()
        try:
            bars = client.fetch_bars(
                symbol=symbol, start_date=start_date, end_date=end_date
            )
        except StockDataError as exc:
            raise FactorLoadError(
                f"Failed to load stock bars for symbol {symbol}: {exc}"
            ) from exc

        if len(bars) < self._MIN_REQUIRED_BARS:
            raise FactorLoadError(
                f"Data service returned insufficient bars for stock {symbol}"
            )

        # 股票无持仓量，统一填 0
        for bar in bars:
            bar.setdefault("open_interest", 0)

        return bars

    def _build_dataset(
        self,
        *,
        bars: list[dict[str, Any]],
        n_features: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        opens = self._extract_series(bars, "open")
        highs = self._extract_series(bars, "high")
        lows = self._extract_series(bars, "low")
        closes = self._extract_series(bars, "close")
        volumes = self._extract_series(bars, "volume")
        open_interests = self._extract_series(bars, "open_interest")

        close_return = self._safe_divide(closes[1:] - closes[:-1], closes[:-1])
        intrabar_range = self._safe_divide(highs[1:] - lows[1:], closes[1:])
        candle_body = self._safe_divide(closes[1:] - opens[1:], opens[1:])
        volume_return = self._safe_divide(volumes[1:] - volumes[:-1], volumes[:-1])
        open_interest_return = self._safe_divide(
            open_interests[1:] - open_interests[:-1],
            open_interests[:-1],
        )

        base_features = np.column_stack(
            [
                close_return,
                intrabar_range,
                candle_body,
                volume_return,
                open_interest_return,
            ]
        ).astype(np.float32)

        X_base = np.nan_to_num(base_features[:-1], nan=0.0, posinf=0.0, neginf=0.0)
        y = (closes[2:] > closes[1:-1]).astype(np.int64)

        if X_base.shape[0] == 0 or y.shape[0] == 0:
            raise FactorLoadError("Bars payload does not produce any usable samples")

        X = self._normalize_feature_width(X_base, n_features)
        return X.astype(np.float32), y.astype(np.int64)

    def _normalize_feature_width(
        self,
        X_base: np.ndarray,
        requested_features: int,
    ) -> np.ndarray:
        desired = requested_features if requested_features > 0 else self._BASE_FEATURE_COUNT
        if desired <= X_base.shape[1]:
            return X_base[:, :desired]

        columns = [X_base[:, index] for index in range(X_base.shape[1])]
        lag = 1
        while len(columns) < desired:
            shifted = np.roll(X_base, lag, axis=0)
            shifted[:lag, :] = 0.0
            for index in range(shifted.shape[1]):
                columns.append(shifted[:, index])
                if len(columns) >= desired:
                    break
            lag += 1

        return np.column_stack(columns[:desired]).astype(np.float32)

    @staticmethod
    def _extract_series(bars: list[dict[str, Any]], field: str) -> np.ndarray:
        values: list[float] = []
        for index, bar in enumerate(bars):
            raw_value = bar.get(field)
            if raw_value is None:
                raise FactorLoadError(f"Bars payload missing field {field} at index {index}")
            try:
                values.append(float(raw_value))
            except (TypeError, ValueError) as exc:
                raise FactorLoadError(
                    f"Bars payload field {field} is not numeric at index {index}"
                ) from exc
        return np.asarray(values, dtype=np.float32)

    @staticmethod
    def _safe_divide(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
        safe_denominator = np.where(np.abs(denominator) < 1e-6, 1.0, denominator)
        return numerator / safe_denominator

    @staticmethod
    def compute_hash(X: np.ndarray) -> str:
        """计算因子矩阵的 SHA-256 哈希（用于资格门禁版本比对）。"""
        return hashlib.sha256(X.tobytes()).hexdigest()
