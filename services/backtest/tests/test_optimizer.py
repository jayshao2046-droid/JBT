"""测试参数优化器"""
import pytest
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from stats.optimizer import ParameterOptimizer, OptimizationResult


def objective_function(params):
    """目标函数：参数越接近 50，得分越高"""
    x = params.get("param1", 0)
    y = params.get("param2", 0)
    score = 100 - abs(x - 50) - abs(y - 50)
    return score


def test_grid_search_basic():
    """测试基本网格搜索"""
    optimizer = ParameterOptimizer(objective_function)

    param_grid = {
        "param1": [10, 30, 50, 70, 90],
        "param2": [10, 30, 50, 70, 90],
    }

    result = optimizer.grid_search(param_grid)

    assert isinstance(result, OptimizationResult)
    assert len(result.all_results) == 25  # 5 * 5 组合

    # 最优结果应该是 param1=50, param2=50
    assert result.best_params["param1"] == 50
    assert result.best_params["param2"] == 50
    assert result.best_score == 100


def test_grid_search_max_iterations():
    """测试网格搜索迭代次数限制"""
    optimizer = ParameterOptimizer(objective_function)

    param_grid = {
        "param1": list(range(0, 100, 5)),  # 20 个值
        "param2": list(range(0, 100, 5)),  # 20 个值
    }

    result = optimizer.grid_search(param_grid, max_iterations=50)

    # 应该只执行 50 次迭代
    assert result.iterations == 50
    assert len(result.all_results) == 50


def test_genetic_algorithm_basic():
    """测试基本遗传算法"""
    optimizer = ParameterOptimizer(objective_function)

    param_ranges = {
        "param1": (0, 100),
        "param2": (0, 100),
    }

    result = optimizer.genetic_algorithm(
        param_ranges,
        population_size=20,
        generations=10
    )

    assert isinstance(result, OptimizationResult)
    assert "param1" in result.best_params
    assert "param2" in result.best_params
    # 遗传算法应该找到接近最优的解
    assert abs(result.best_params["param1"] - 50) < 20
    assert abs(result.best_params["param2"] - 50) < 20
    assert result.iterations == 200  # 20 * 10


def test_genetic_algorithm_convergence():
    """测试遗传算法收敛性"""
    optimizer = ParameterOptimizer(lambda p: 100 - abs(p.get("param1", 0) - 50))

    param_ranges = {
        "param1": (0, 100),
    }

    result = optimizer.genetic_algorithm(
        param_ranges,
        population_size=10,
        generations=20
    )

    # 单参数问题应该收敛到最优解附近
    assert abs(result.best_params["param1"] - 50) < 15


def test_bayesian_optimization_basic():
    """测试基本贝叶斯优化"""
    optimizer = ParameterOptimizer(objective_function)

    param_ranges = {
        "param1": (0, 100),
        "param2": (0, 100),
    }

    result = optimizer.bayesian_optimization(
        param_ranges,
        n_iterations=20,
        n_initial_points=5
    )

    assert isinstance(result, OptimizationResult)
    assert "param1" in result.best_params
    assert "param2" in result.best_params
    # 贝叶斯优化应该找到接近最优的解
    assert abs(result.best_params["param1"] - 50) < 30
    assert abs(result.best_params["param2"] - 50) < 30
    assert result.iterations == 20


def test_optimization_with_negative_scores():
    """测试负分数优化"""
    def negative_objective(params):
        x = params.get("x", 0)
        return -abs(x - 10)  # 最优值在 x=10

    optimizer = ParameterOptimizer(negative_objective)

    param_grid = {"x": [0, 5, 10, 15, 20]}
    result = optimizer.grid_search(param_grid)

    assert result.best_params["x"] == 10
    assert result.best_score == 0


def test_single_parameter_optimization():
    """测试单参数优化"""
    optimizer = ParameterOptimizer(lambda p: 50 - abs(p.get("x", 0) - 25))

    param_grid = {"x": list(range(0, 51, 5))}
    result = optimizer.grid_search(param_grid)

    assert result.best_params["x"] == 25
    assert len(result.all_results) == 11

