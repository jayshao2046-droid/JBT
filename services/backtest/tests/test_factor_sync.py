"""测试 backtest 端因子同步功能。

TASK-0084 / Token: tok-966162da
"""
import pytest


def test_backtest_factors_registered_to_global():
    """测试 backtest 因子是否注册到共享注册表。"""
    try:
        from shared.python_common.factors.registry import get_global_registry
        from backtest.factor_registry import factor_registry
    except ImportError:
        pytest.skip("共享因子库或 backtest 模块未安装")

    global_registry = get_global_registry()
    hash_map = global_registry.export_hash_map()

    # 验证至少有 43 个因子注册到全局注册表
    assert len(hash_map) >= 43, f"全局注册表只有 {len(hash_map)} 个因子，预期至少 43 个"

    # 验证一些核心因子存在
    core_factors = ["SMA", "EMA", "MACD", "RSI", "ATR", "BollingerBands"]
    for factor in core_factors:
        assert factor in hash_map, f"核心因子 {factor} 未注册到全局注册表"


def test_export_backtest_hash_map():
    """测试 export_backtest_hash_map() 返回非空字典。"""
    try:
        from backtest.factor_registry import export_backtest_hash_map
    except ImportError:
        pytest.skip("backtest 模块未安装")

    hash_map = export_backtest_hash_map()

    assert isinstance(hash_map, dict)
    assert len(hash_map) > 0, "export_backtest_hash_map() 返回空字典"

    # 验证至少有 43 个因子
    assert len(hash_map) >= 43, f"只导出了 {len(hash_map)} 个因子，预期至少 43 个"


def test_factor_hash_format():
    """测试因子 hash 为 16 位 hex 字符串。"""
    try:
        from backtest.factor_registry import export_backtest_hash_map
    except ImportError:
        pytest.skip("backtest 模块未安装")

    hash_map = export_backtest_hash_map()

    for factor_name, factor_hash in hash_map.items():
        assert isinstance(factor_hash, str), f"{factor_name} 的 hash 不是字符串"
        assert len(factor_hash) == 16, f"{factor_name} 的 hash 长度不是 16: {factor_hash}"
        # 验证是 hex 字符串
        try:
            int(factor_hash, 16)
        except ValueError:
            pytest.fail(f"{factor_name} 的 hash 不是有效的 hex 字符串: {factor_hash}")


def test_backtest_factor_registry_list():
    """测试 backtest 本地注册表包含预期因子。"""
    try:
        from backtest.factor_registry import factor_registry
    except ImportError:
        pytest.skip("backtest 模块未安装")

    local_factors = factor_registry.list_factors()

    assert len(local_factors) >= 43, f"本地注册表只有 {len(local_factors)} 个因子"

    # 验证核心因子
    core_factors = ["sma", "ema", "macd", "rsi", "atr", "bollingerbands"]
    for factor in core_factors:
        assert factor in local_factors, f"核心因子 {factor} 未在本地注册表中"


def test_factor_registry_register_to_global():
    """测试 FactorRegistry.register() 同时注册到全局注册表。"""
    try:
        from shared.python_common.factors.registry import get_global_registry
        from backtest.factor_registry import FactorRegistry
    except ImportError:
        pytest.skip("共享因子库或 backtest 模块未安装")

    # 创建新的注册表实例
    test_registry = FactorRegistry()

    def test_calculator(bars, params):
        return []

    # 注册因子
    test_registry.register("TestSyncFactor", test_calculator)

    # 验证已注册到全局注册表
    global_registry = get_global_registry()
    hash_map = global_registry.export_hash_map()

    assert "TestSyncFactor" in hash_map, "因子未同步到全局注册表"


def test_jbt_factors_coverage():
    """测试 backtest 端覆盖 JBT 标准因子列表。"""
    try:
        from shared.python_common.factors.registry import get_jbt_factors
        from backtest.factor_registry import export_backtest_hash_map
    except ImportError:
        pytest.skip("共享因子库或 backtest 模块未安装")

    jbt_factors = get_jbt_factors()
    backtest_hash_map = export_backtest_hash_map()

    # 转换为小写进行比较（因为 backtest 注册表使用小写）
    backtest_factors_lower = {name.lower() for name in backtest_hash_map.keys()}
    jbt_factors_lower = {name.lower() for name in jbt_factors}

    missing = jbt_factors_lower - backtest_factors_lower

    # 允许少量缺失（因为 JBT 列表可能包含未实现的因子）
    assert len(missing) <= 5, f"backtest 端缺失过多 JBT 标准因子: {missing}"
