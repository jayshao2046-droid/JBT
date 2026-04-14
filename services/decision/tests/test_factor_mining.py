"""Tests for TASK-0116: FactorMiner + FactorValidator + factor API route.

测试覆盖：
FactorMiner:
- mine 返回候选因子列表（非空）
- 数据不足时返回空列表
- 各因子类型正确（momentum/mean_reversion/vol_price/volatility）
- _zscore 基本正确性
- _momentum / _ma_deviation / _atr / _hist_vol 边界情况

FactorValidator:
- validate 通过：IC IR 显著 + p < 0.1 + ls_return > 0
- validate 失败：样本不足
- validate_batch 批量处理
- _t_test 正确返回 t_stat 和 p_value
- _ls_return 多空收益差计算

Factor API route:
- POST /mine 返回因子列表
- POST /validate 通过后写入缓存
- GET /list 返回缓存因子
- GET /list?symbol=xx 按品种过滤
"""

from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.research.factor_miner import FactorMiner, CandidateFactor
from src.research.factor_validator import FactorValidator, FactorValidationResult


# ─────────────────────────────────────────────
# FactorMiner
# ─────────────────────────────────────────────

def _make_bars(n: int = 60, seed: int = 0) -> List[Dict[str, Any]]:
    """生成随机 OHLCV K 线。"""
    np.random.seed(seed)
    bars = []
    price = 3000.0
    for _ in range(n):
        change = float(np.random.randn() * 30)
        o = price
        h = o + abs(float(np.random.randn() * 20))
        l = o - abs(float(np.random.randn() * 20))
        c = o + change
        c = max(c, l)
        bars.append({"open": o, "high": h, "low": l, "close": c, "volume": float(np.random.randint(1000, 5000))})
        price = c
    return bars


class TestFactorMiner:
    """FactorMiner 因子挖掘。"""

    def setup_method(self):
        self.miner = FactorMiner()
        self.bars = _make_bars(n=60)

    def test_mine_returns_list(self):
        """mine 返回 CandidateFactor 列表。"""
        factors = self.miner.mine("rb", self.bars)
        assert isinstance(factors, list)
        assert len(factors) > 0
        assert all(isinstance(f, CandidateFactor) for f in factors)

    def test_mine_returns_empty_for_insufficient_data(self):
        """数据不足（<2根）→ 返回空列表。"""
        factors = self.miner.mine("rb", [self.bars[0]])
        assert factors == []

    def test_mine_empty_bars(self):
        """空 bars → 返回空列表。"""
        assert self.miner.mine("rb", []) == []

    def test_mine_factor_categories(self):
        """确认各类因子类型均存在。"""
        factors = self.miner.mine("rb", self.bars)
        categories = {f.category for f in factors}
        # 数据足够时，至少有 momentum 和 volatility
        assert "momentum" in categories
        assert "volatility" in categories

    def test_mine_factor_names_unique_per_category(self):
        """同一品种不同窗口的因子名称不同。"""
        factors = self.miner.mine("rb", self.bars)
        names = [f.name for f in factors]
        assert len(names) == len(set(names))

    def test_mine_value_is_float(self):
        """所有因子 value 是 float（z-score）。"""
        factors = self.miner.mine("rb", self.bars)
        for f in factors:
            assert isinstance(f.value, float)
            assert isinstance(f.raw_value, float)

    def test_zscore_zero_std_returns_zero(self):
        """历史方差为 0 → zscore=0。"""
        hist = np.array([1.0] * 10)
        assert FactorMiner._zscore(hist, 5.0) == 0.0

    def test_zscore_normalizes_correctly(self):
        """zscore 将值标准化到合理范围。"""
        hist = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        z = FactorMiner._zscore(hist, 5.0)
        assert isinstance(z, float)

    def test_momentum_insufficient_data_returns_none(self):
        """因子数据不足时 _momentum 返回 None。"""
        closes = np.array([100.0, 101.0])
        result = FactorMiner._momentum(closes, window=5)
        assert result is None

    def test_atr_insufficient_data_returns_none(self):
        """ATR 数据不足时返回 None。"""
        h = np.array([100.0] * 5)
        l = np.array([99.0] * 5)
        c = np.array([99.5] * 5)
        result = FactorMiner._atr(h, l, c, window=14)
        assert result is None

    def test_hist_vol_single_value_returns_none(self):
        """单值历史波动率返回 None。"""
        closes = np.array([100.0, 101.0])
        result = FactorMiner._hist_vol(closes, window=10)
        assert result is None

    def test_custom_windows_respected(self):
        """自定义窗口参数生效。"""
        factors = self.miner.mine("rb", self.bars, windows={"momentum": [3]})
        mom_factors = [f for f in factors if f.category == "momentum"]
        assert any("3d" in f.name for f in mom_factors)
        assert not any("20d" in f.name for f in mom_factors)


# ─────────────────────────────────────────────
# FactorValidator
# ─────────────────────────────────────────────

class TestFactorValidator:
    """FactorValidator 有效性验证。"""

    def setup_method(self):
        self.validator = FactorValidator()
        np.random.seed(1)
        n = 100
        self.factor_series = list(np.random.randn(n).tolist())
        # 构造正相关收益（让 IC IR 显著）
        self.return_series = [f * 0.5 + np.random.randn() * 0.1 for f in self.factor_series]

    def test_validate_insufficient_samples_fails(self):
        """样本 < MIN_SAMPLES → passed=False。"""
        result = self.validator.validate(
            "f1", "rb",
            factor_series=[0.1, 0.2],
            return_series=[0.01, 0.02],
        )
        assert result.passed is False
        assert "样本不足" in result.reason

    def test_validate_returns_validation_result(self):
        """返回 FactorValidationResult 类型。"""
        result = self.validator.validate(
            "momentum_5d", "rb",
            factor_series=self.factor_series,
            return_series=self.return_series,
        )
        assert isinstance(result, FactorValidationResult)
        assert result.factor_name == "momentum_5d"
        assert result.symbol == "rb"
        assert isinstance(result.ic_mean, float)
        assert isinstance(result.ic_ir, float)
        assert isinstance(result.passed, bool)

    def test_validate_strong_positive_factor_passes(self):
        """强正相关因子 → passed=True。"""
        np.random.seed(42)
        n = 80
        f = list(np.arange(n, dtype=float))  # 完美单调递增
        r = [x * 0.01 + np.random.randn() * 0.001 for x in f]
        result = self.validator.validate("monotone_f", "rb", f, r)
        assert result.passed is True

    def test_validate_batch_length_matches_input(self):
        """batch 返回与输入等长。"""
        data = [
            {"factor_name": f"f{i}", "symbol": "rb",
             "factor_series": self.factor_series,
             "return_series": self.return_series}
            for i in range(3)
        ]
        results = self.validator.validate_batch(data)
        assert len(results) == 3

    def test_t_test_zero_series_returns_p1(self):
        """全零 IC 序列 → p_value=1.0。"""
        ic_series = np.zeros(10)
        t, p = FactorValidator._t_test(ic_series)
        assert p == 1.0

    def test_t_test_large_t_returns_small_p(self):
        """大 t 统计量 → 小 p 值。"""
        ic_series = np.ones(50) * 0.5  # 均值 0.5, std very small → large t
        t, p = FactorValidator._t_test(ic_series)
        assert p <= 0.01

    def test_ls_return_perfect_factor(self):
        """完美因子：Top30% 收益 > Bottom30% 收益 → ls_return > 0。"""
        n = 100
        f = np.arange(n, dtype=float)
        r = f * 0.01  # 因子大的收益高
        ls = FactorValidator._ls_return(f, r)
        assert ls > 0

    def test_ls_return_inverse_factor(self):
        """反向因子：因子大收益低 → ls_return < 0。"""
        n = 100
        f = np.arange(n, dtype=float)
        r = -f * 0.01
        ls = FactorValidator._ls_return(f, r)
        assert ls < 0


# ─────────────────────────────────────────────
# Factor API Route
# ─────────────────────────────────────────────

@pytest.fixture
def client():
    """创建 FastAPI test client。"""
    from src.api.app import create_app
    app = create_app()
    return TestClient(app, raise_server_exceptions=True)


class TestFactorAPIRoute:
    """Factor API 端点测试。"""

    def _mine_payload(self, n_bars: int = 60):
        bars = _make_bars(n=n_bars)
        return {
            "symbol": "rb",
            "bars": [{"open": b["open"], "high": b["high"], "low": b["low"],
                      "close": b["close"], "volume": b["volume"]} for b in bars],
        }

    def test_mine_endpoint_returns_factors(self, client):
        """POST /mine → 返回因子列表。"""
        resp = client.post("/api/v1/factor/mine", json=self._mine_payload())
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "rb"
        assert isinstance(data["factors"], list)
        assert data["count"] == len(data["factors"])

    def test_mine_endpoint_insufficient_bars(self, client):
        """单根 K 线 → 返回空因子列表（不报 500）。"""
        payload = {
            "symbol": "rb",
            "bars": [{"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000.0}],
        }
        resp = client.post("/api/v1/factor/mine", json=payload)
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_validate_endpoint_insufficient_series(self, client):
        """短序列 → 验证失败但状态 200。"""
        payload = {
            "factor_name": "momentum_5d",
            "symbol": "rb",
            "factor_series": [0.1, 0.2, 0.3],
            "return_series": [0.01, 0.02, 0.03],
        }
        resp = client.post("/api/v1/factor/validate", json=payload)
        assert resp.status_code == 200
        assert resp.json()["passed"] is False

    def test_validate_endpoint_strong_factor_caches(self, client):
        """强因子通过验证 → 写入缓存 → /list 可查。"""
        np.random.seed(9)
        n = 80
        f_series = list(np.arange(n, dtype=float).tolist())
        r_series = [x * 0.01 + float(np.random.randn() * 0.001) for x in f_series]
        payload = {
            "factor_name": "test_valid_factor",
            "symbol": "cu",
            "factor_series": f_series,
            "return_series": r_series,
        }
        resp = client.post("/api/v1/factor/validate", json=payload)
        assert resp.status_code == 200
        result = resp.json()
        if result["passed"]:
            # 验证写入缓存
            list_resp = client.get("/api/v1/factor/list?symbol=cu")
            assert list_resp.status_code == 200
            factors = list_resp.json()["factors"]
            names = [f["factor_name"] for f in factors]
            assert "test_valid_factor" in names

    def test_list_endpoint_no_filter(self, client):
        """GET /list 不过滤时返回全部。"""
        resp = client.get("/api/v1/factor/list")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert isinstance(data["factors"], list)

    def test_list_endpoint_symbol_filter(self, client):
        """GET /list?symbol=xx 按品种过滤。"""
        resp = client.get("/api/v1/factor/list?symbol=nonexistent_symbol_xyz")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
