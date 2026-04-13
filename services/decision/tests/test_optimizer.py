"""
参数优化器单元测试
"""
import pytest
from src.stats.optimizer import ParameterOptimizer


class TestParameterOptimizer:
    """参数优化器测试"""

    def test_grid_search(self):
        optimizer = ParameterOptimizer()

        def objective(params):
            return params["x"] ** 2 + params["y"] ** 2

        param_grid = {"x": [1, 2, 3], "y": [1, 2, 3]}

        results = optimizer.grid_search(param_grid, objective)
        assert len(results) == 9
        assert results[0]["score"] >= results[-1]["score"]  # 按得分排序

    def test_genetic_algorithm(self):
        optimizer = ParameterOptimizer()

        def objective(params):
            return -(params["x"] ** 2 + params["y"] ** 2)

        param_ranges = {"x": (-10, 10), "y": (-10, 10)}

        results = optimizer.genetic_algorithm(param_ranges, objective, population_size=10, generations=5)
        assert len(results) == 5  # 5 代
        assert results[-1]["generation"] == 4

    def test_bayesian_optimization(self):
        optimizer = ParameterOptimizer()

        def objective(params):
            return -(params["x"] ** 2 + params["y"] ** 2)

        param_ranges = {"x": (-10, 10), "y": (-10, 10)}

        results = optimizer.bayesian_optimization(param_ranges, objective, n_iterations=10)
        assert len(results) == 10
        assert results[0]["score"] >= results[-1]["score"]

    def test_get_best_params(self):
        optimizer = ParameterOptimizer()

        def objective(params):
            return params["x"] + params["y"]

        param_grid = {"x": [1, 2, 3], "y": [1, 2, 3]}

        optimizer.grid_search(param_grid, objective)
        best = optimizer.get_best_params()
        assert best is not None
        assert best["x"] == 3
        assert best["y"] == 3

    def test_get_top_n(self):
        optimizer = ParameterOptimizer()

        def objective(params):
            return params["x"] + params["y"]

        param_grid = {"x": [1, 2, 3], "y": [1, 2, 3]}

        optimizer.grid_search(param_grid, objective)
        top_3 = optimizer.get_top_n(3)
        assert len(top_3) == 3
        assert top_3[0]["score"] >= top_3[1]["score"]
        assert top_3[1]["score"] >= top_3[2]["score"]
