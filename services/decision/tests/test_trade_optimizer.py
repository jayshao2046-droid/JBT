"""测试交易参数调优引擎 — TASK-0121-C

测试覆盖：
1. 参数网格搜索
2. 目标函数计算
3. 回测执行
4. 结果管理
5. 边界条件
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.research.trade_optimizer import TradeOptimizer, OptimizationResult


@pytest.fixture
def optimizer():
    """创建优化器实例。"""
    return TradeOptimizer(data_service_url="http://localhost:8105")


@pytest.fixture
def sample_bars():
    """创建示例 K 线数据。"""
    # 生成 100 根 K 线，价格从 100 递增
    bars = []
    for i in range(100):
        bars.append({
            'timestamp': f'2024-01-{i+1:02d}',
            'open': 100 + i * 0.5,
            'high': 101 + i * 0.5,
            'low': 99 + i * 0.5,
            'close': 100 + i * 0.5,
            'volume': 1000,
        })
    return bars


@pytest.fixture
def param_grid():
    """创建参数网格。"""
    return {
        'fast_period': [5, 10],
        'slow_period': [20, 30],
        'position_size': [0.1, 0.2],
    }


# =============================================================================
# 1. 参数网格搜索测试
# =============================================================================

def test_optimize_basic(optimizer, sample_bars, param_grid):
    """测试基础优化功能。"""
    with patch.object(optimizer, '_fetch_bars', return_value=sample_bars):
        result = optimizer.optimize(
            strategy_id='test-strategy',
            symbol='p',
            start_date='2024-01-01',
            end_date='2024-12-31',
            param_grid=param_grid,
            objective='sharpe',
        )

    assert result.status == 'completed'
    assert result.strategy_id == 'test-strategy'
    assert result.objective == 'sharpe'
    assert result.total_trials == 8  # 2 * 2 * 2 = 8 组合
    assert len(result.all_trials) == 8
    assert result.best_params != {}
    assert result.best_score != float('-inf')


def test_optimize_empty_grid(optimizer):
    """测试空参数网格。"""
    result = optimizer.optimize(
        strategy_id='test-strategy',
        symbol='p',
        start_date='2024-01-01',
        end_date='2024-12-31',
        param_grid={},
        objective='sharpe',
    )

    assert result.status == 'completed'
    assert result.total_trials == 0
    assert result.all_trials == []
    assert result.best_params == {}


def test_optimize_single_param(optimizer, sample_bars):
    """测试单参数优化。"""
    param_grid = {'fast_period': [5, 10, 15]}

    with patch.object(optimizer, '_fetch_bars', return_value=sample_bars):
        result = optimizer.optimize(
            strategy_id='test-strategy',
            symbol='p',
            start_date='2024-01-01',
            end_date='2024-12-31',
            param_grid=param_grid,
            objective='sharpe',
        )

    assert result.total_trials == 3
    assert len(result.all_trials) == 3


def test_optimize_fetch_bars_failure(optimizer):
    """测试数据获取失败。"""
    with patch.object(optimizer, '_fetch_bars', side_effect=Exception('Data service unavailable')):
        result = optimizer.optimize(
            strategy_id='test-strategy',
            symbol='p',
            start_date='2024-01-01',
            end_date='2024-12-31',
            param_grid={'fast_period': [5, 10]},
            objective='sharpe',
        )

    assert result.status == 'failed'
    assert len(result.all_trials) == 1
    assert 'error' in result.all_trials[0]


# =============================================================================
# 2. 目标函数计算测试
# =============================================================================

def test_calculate_objective_sharpe():
    """测试 Sharpe 目标函数。"""
    metrics = {'sharpe': 2.5, 'max_drawdown': 0.1, 'win_rate': 0.6}
    score = TradeOptimizer._calculate_objective(metrics, 'sharpe')
    assert score == 2.5


def test_calculate_objective_max_drawdown():
    """测试最大回撤目标函数。"""
    metrics = {'sharpe': 2.5, 'max_drawdown': 0.1, 'win_rate': 0.6}
    score = TradeOptimizer._calculate_objective(metrics, 'max_drawdown')
    assert score == -0.1  # 负值，因为回撤越小越好


def test_calculate_objective_win_rate():
    """测试胜率目标函数。"""
    metrics = {'sharpe': 2.5, 'max_drawdown': 0.1, 'win_rate': 0.6}
    score = TradeOptimizer._calculate_objective(metrics, 'win_rate')
    assert score == 0.6


def test_calculate_objective_total_return():
    """测试总收益目标函数。"""
    metrics = {'sharpe': 2.5, 'max_drawdown': 0.1, 'total_return': 0.3}
    score = TradeOptimizer._calculate_objective(metrics, 'total_return')
    assert score == 0.3


def test_calculate_objective_unknown():
    """测试未知目标函数（默认使用 Sharpe）。"""
    metrics = {'sharpe': 2.5, 'max_drawdown': 0.1}
    score = TradeOptimizer._calculate_objective(metrics, 'unknown')
    assert score == 2.5


# =============================================================================
# 3. 回测执行测试
# =============================================================================

def test_run_single_backtest_basic(optimizer, sample_bars):
    """测试基础回测执行。"""
    params = {
        'fast_period': 5,
        'slow_period': 20,
        'position_size': 0.1,
    }

    metrics = optimizer._run_single_backtest(sample_bars, params)

    assert 'sharpe' in metrics
    assert 'max_drawdown' in metrics
    assert 'win_rate' in metrics
    assert 'total_return' in metrics
    assert 'trades_count' in metrics
    assert metrics['trades_count'] >= 0


def test_run_single_backtest_with_stop_loss(optimizer, sample_bars):
    """测试带止损的回测。"""
    params = {
        'fast_period': 5,
        'slow_period': 20,
        'position_size': 0.1,
        'stop_loss': 0.02,  # 2% 止损
    }

    metrics = optimizer._run_single_backtest(sample_bars, params)

    assert 'sharpe' in metrics
    assert metrics['trades_count'] >= 0


def test_run_single_backtest_with_take_profit(optimizer, sample_bars):
    """测试带止盈的回测。"""
    params = {
        'fast_period': 5,
        'slow_period': 20,
        'position_size': 0.1,
        'take_profit': 0.05,  # 5% 止盈
    }

    metrics = optimizer._run_single_backtest(sample_bars, params)

    assert 'sharpe' in metrics
    assert metrics['trades_count'] >= 0


def test_run_single_backtest_insufficient_data(optimizer):
    """测试数据不足的情况。"""
    bars = [{'close': 100 + i} for i in range(10)]  # 只有 10 根 K 线
    params = {'fast_period': 5, 'slow_period': 20}

    metrics = optimizer._run_single_backtest(bars, params)

    assert metrics['sharpe'] == 0.0
    assert metrics['max_drawdown'] == 0.0
    assert metrics['win_rate'] == 0.0
    assert metrics['trades_count'] == 0


def test_run_single_backtest_no_trades(optimizer):
    """测试无交易的情况。"""
    # 价格完全平稳，不会触发交易信号
    bars = [{'close': 100} for _ in range(100)]
    params = {'fast_period': 5, 'slow_period': 20}

    metrics = optimizer._run_single_backtest(bars, params)

    assert metrics['trades_count'] == 0
    assert metrics['sharpe'] == 0.0


# =============================================================================
# 4. 结果管理测试
# =============================================================================

def test_get_result(optimizer, sample_bars, param_grid):
    """测试获取优化结果。"""
    with patch.object(optimizer, '_fetch_bars', return_value=sample_bars):
        result = optimizer.optimize(
            strategy_id='test-strategy',
            symbol='p',
            start_date='2024-01-01',
            end_date='2024-12-31',
            param_grid=param_grid,
        )

    retrieved = optimizer.get_result(result.opt_id)
    assert retrieved is not None
    assert retrieved.opt_id == result.opt_id
    assert retrieved.strategy_id == 'test-strategy'


def test_get_result_not_found(optimizer):
    """测试获取不存在的结果。"""
    result = optimizer.get_result('non-existent-id')
    assert result is None


def test_list_results_all(optimizer, sample_bars):
    """测试列出所有结果。"""
    with patch.object(optimizer, '_fetch_bars', return_value=sample_bars):
        optimizer.optimize('strategy-1', 'p', '2024-01-01', '2024-12-31', {'fast_period': [5]})
        optimizer.optimize('strategy-2', 'p', '2024-01-01', '2024-12-31', {'fast_period': [10]})

    results = optimizer.list_results()
    assert len(results) == 2


def test_list_results_by_strategy(optimizer, sample_bars):
    """测试按策略 ID 筛选结果。"""
    with patch.object(optimizer, '_fetch_bars', return_value=sample_bars):
        optimizer.optimize('strategy-1', 'p', '2024-01-01', '2024-12-31', {'fast_period': [5]})
        optimizer.optimize('strategy-1', 'p', '2024-01-01', '2024-12-31', {'fast_period': [10]})
        optimizer.optimize('strategy-2', 'p', '2024-01-01', '2024-12-31', {'fast_period': [15]})

    results = optimizer.list_results(strategy_id='strategy-1')
    assert len(results) == 2
    assert all(r.strategy_id == 'strategy-1' for r in results)


# =============================================================================
# 5. 数据获取测试
# =============================================================================

def test_fetch_bars_futures(optimizer):
    """测试获取期货数据。"""
    mock_response = Mock()
    mock_response.json.return_value = [
        {'timestamp': '2024-01-01', 'close': 100},
        {'timestamp': '2024-01-02', 'close': 101},
    ]
    mock_response.raise_for_status = Mock()

    with patch('httpx.Client') as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response

        bars = optimizer._fetch_bars('p', '2024-01-01', '2024-12-31', 'futures')

    assert len(bars) == 2
    assert bars[0]['close'] == 100


def test_fetch_bars_stock(optimizer):
    """测试获取股票数据。"""
    mock_response = Mock()
    mock_response.json.return_value = {'bars': [
        {'timestamp': '2024-01-01', 'close': 100},
    ]}
    mock_response.raise_for_status = Mock()

    with patch('httpx.Client') as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response

        bars = optimizer._fetch_bars('600000', '2024-01-01', '2024-12-31', 'stock')

    assert len(bars) == 1
    assert bars[0]['close'] == 100


def test_fetch_bars_http_error(optimizer):
    """测试 HTTP 错误。"""
    with patch('httpx.Client') as mock_client:
        mock_client.return_value.__enter__.return_value.get.side_effect = Exception('Connection error')

        with pytest.raises(Exception):
            optimizer._fetch_bars('p', '2024-01-01', '2024-12-31', 'futures')


# =============================================================================
# 6. OptimizationResult 测试
# =============================================================================

def test_optimization_result_to_dict():
    """测试结果转换为字典。"""
    result = OptimizationResult(
        opt_id='opt-123',
        strategy_id='test-strategy',
        status='completed',
        created_at='2024-01-01T00:00:00Z',
        completed_at='2024-01-01T01:00:00Z',
        best_params={'fast_period': 5},
        best_score=2.5,
        objective='sharpe',
        all_trials=[],
        total_trials=10,
    )

    result_dict = result.to_dict()

    assert result_dict['opt_id'] == 'opt-123'
    assert result_dict['strategy_id'] == 'test-strategy'
    assert result_dict['status'] == 'completed'
    assert result_dict['best_score'] == 2.5


# =============================================================================
# 7. 边界条件测试
# =============================================================================

def test_optimize_large_grid(optimizer, sample_bars):
    """测试大参数网格。"""
    param_grid = {
        'fast_period': [5, 10, 15, 20],
        'slow_period': [30, 40, 50],
        'position_size': [0.1, 0.2],
    }

    with patch.object(optimizer, '_fetch_bars', return_value=sample_bars):
        result = optimizer.optimize(
            strategy_id='test-strategy',
            symbol='p',
            start_date='2024-01-01',
            end_date='2024-12-31',
            param_grid=param_grid,
        )

    assert result.total_trials == 24  # 4 * 3 * 2 = 24


def test_optimize_all_trials_fail(optimizer, sample_bars):
    """测试所有试验都失败的情况。"""
    with patch.object(optimizer, '_fetch_bars', return_value=sample_bars):
        with patch.object(optimizer, '_run_single_backtest', side_effect=Exception('Backtest error')):
            result = optimizer.optimize(
                strategy_id='test-strategy',
                symbol='p',
                start_date='2024-01-01',
                end_date='2024-12-31',
                param_grid={'fast_period': [5, 10]},
            )

    assert result.status == 'completed'
    assert result.best_score == float('-inf')
    assert all(t['score'] == float('-inf') for t in result.all_trials)


def test_backtest_with_zero_price(optimizer):
    """测试价格为零的情况。"""
    bars = [{'close': 0} for _ in range(100)]
    params = {'fast_period': 5, 'slow_period': 20}

    metrics = optimizer._run_single_backtest(bars, params)

    assert metrics['trades_count'] == 0
    assert metrics['total_return'] == 0.0
