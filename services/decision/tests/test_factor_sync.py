"""测试因子双地同步功能。

TASK-0084 / Token: tok-966162da
"""
import pytest


def test_compare_registries_consistent():
    """测试两端因子完全一致的场景。"""
    try:
        from shared.python_common.factors.sync import compare_registries
    except ImportError:
        pytest.skip("共享因子库未安装")

    decision_factors = {
        "MA": "abc123def456",
        "RSI": "def456ghi789",
        "MACD": "ghi789jkl012",
    }
    backtest_factors = {
        "MA": "abc123def456",
        "RSI": "def456ghi789",
        "MACD": "ghi789jkl012",
    }

    result = compare_registries(decision_factors, backtest_factors)

    assert len(result["consistent"]) == 3
    assert len(result["missing_in_decision"]) == 0
    assert len(result["missing_in_backtest"]) == 0
    assert len(result["hash_mismatch"]) == 0


def test_compare_registries_missing():
    """测试因子缺失的场景。"""
    try:
        from shared.python_common.factors.sync import compare_registries
    except ImportError:
        pytest.skip("共享因子库未安装")

    decision_factors = {
        "MA": "abc123def456",
        "RSI": "def456ghi789",
    }
    backtest_factors = {
        "MA": "abc123def456",
        "MACD": "ghi789jkl012",
    }

    result = compare_registries(decision_factors, backtest_factors)

    assert "RSI" in result["missing_in_backtest"]
    assert "MACD" in result["missing_in_decision"]
    assert "MA" in result["consistent"]


def test_compare_registries_hash_mismatch():
    """测试因子 hash 不一致的场景。"""
    try:
        from shared.python_common.factors.sync import compare_registries
    except ImportError:
        pytest.skip("共享因子库未安装")

    decision_factors = {
        "MA": "abc123def456",
        "RSI": "def456ghi789",
    }
    backtest_factors = {
        "MA": "abc123def456",
        "RSI": "xxx999yyy888",  # 不同的 hash
    }

    result = compare_registries(decision_factors, backtest_factors)

    assert len(result["hash_mismatch"]) == 1
    assert result["hash_mismatch"][0]["name"] == "RSI"
    assert result["hash_mismatch"][0]["decision_hash"] == "def456ghi789"
    assert result["hash_mismatch"][0]["backtest_hash"] == "xxx999yyy888"


def test_compare_registries_with_callback():
    """测试 on_mismatch 回调功能。"""
    try:
        from shared.python_common.factors.sync import compare_registries
    except ImportError:
        pytest.skip("共享因子库未安装")

    decision_factors = {"MA": "abc123"}
    backtest_factors = {"RSI": "def456"}

    callback_called = []

    def on_mismatch(result):
        callback_called.append(result)

    result = compare_registries(decision_factors, backtest_factors, on_mismatch=on_mismatch)

    assert len(callback_called) == 1
    assert callback_called[0] == result


def test_generate_sync_report():
    """测试同步报告生成。"""
    try:
        from shared.python_common.factors.sync import generate_sync_report
    except ImportError:
        pytest.skip("共享因子库未安装")

    result = {
        "consistent": ["MA", "RSI", "MACD"],
        "missing_in_decision": ["ATR", "BOLL"],
        "missing_in_backtest": ["EMA"],
        "hash_mismatch": [
            {"name": "ADX", "decision_hash": "abc123", "backtest_hash": "def456"}
        ],
    }

    report = generate_sync_report(result)

    assert "## 因子同步状态报告" in report
    assert "✅ 一致因子" in report
    assert "3 个" in report
    assert "⚠️ Decision 端缺失" in report
    assert "ATR" in report
    assert "⚠️ Backtest 端缺失" in report
    assert "EMA" in report
    assert "❌ Hash 不一致" in report
    assert "ADX" in report


def test_export_hash_map():
    """测试 FactorRegistry.export_hash_map() 方法。"""
    try:
        from shared.python_common.factors.registry import FactorRegistry
    except ImportError:
        pytest.skip("共享因子库未安装")

    registry = FactorRegistry()

    def dummy_calculator(bars, params):
        return []

    registry.register("TestFactor", dummy_calculator, version="1.0.0")

    hash_map = registry.export_hash_map()

    assert isinstance(hash_map, dict)
    assert "TestFactor" in hash_map
    assert isinstance(hash_map["TestFactor"], str)
    assert len(hash_map["TestFactor"]) == 16  # SHA-256 前 16 位


def test_get_global_registry():
    """测试全局注册表访问器。"""
    try:
        from shared.python_common.factors.registry import get_global_registry, register_global
    except ImportError:
        pytest.skip("共享因子库未安装")

    def dummy_calculator(bars, params):
        return []

    # 注册到全局注册表
    register_global("TestGlobalFactor", dummy_calculator, version="1.0.0")

    # 获取全局注册表
    global_registry = get_global_registry()
    assert global_registry is not None

    # 验证因子已注册
    hash_map = global_registry.export_hash_map()
    assert "TestGlobalFactor" in hash_map
