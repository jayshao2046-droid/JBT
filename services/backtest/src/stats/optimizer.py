"""
策略参数优化器

支持三种优化算法：
1. 网格搜索（Grid Search）
2. 遗传算法（Genetic Algorithm）
3. 贝叶斯优化（Bayesian Optimization）
"""

import itertools
import random
from typing import Any, Callable, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class OptimizationResult:
    """优化结果"""
    best_params: Dict[str, Any]
    best_score: float
    all_results: List[Dict[str, Any]]
    iterations: int


class ParameterOptimizer:
    """策略参数优化器"""

    def __init__(self, objective_function: Callable[[Dict[str, Any]], float]):
        """
        初始化优化器

        Args:
            objective_function: 目标函数，接收参数字典，返回评分（越高越好）
        """
        self.objective_function = objective_function

    def grid_search(
        self,
        param_grid: Dict[str, List[Any]],
        max_iterations: int = 100
    ) -> OptimizationResult:
        """
        网格搜索优化

        Args:
            param_grid: 参数网格，例如 {"param1": [1, 2, 3], "param2": [0.1, 0.2]}
            max_iterations: 最大迭代次数

        Returns:
            OptimizationResult: 优化结果
        """
        # 生成所有参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        all_combinations = list(itertools.product(*param_values))

        # 限制迭代次数
        if len(all_combinations) > max_iterations:
            all_combinations = random.sample(all_combinations, max_iterations)

        best_params = None
        best_score = float('-inf')
        all_results = []

        for combination in all_combinations:
            params = dict(zip(param_names, combination))
            score = self.objective_function(params)

            all_results.append({
                "params": params.copy(),
                "score": score
            })

            if score > best_score:
                best_score = score
                best_params = params.copy()

        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            all_results=all_results,
            iterations=len(all_combinations)
        )

    def genetic_algorithm(
        self,
        param_ranges: Dict[str, Tuple[float, float]],
        population_size: int = 20,
        generations: int = 10,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7
    ) -> OptimizationResult:
        """
        遗传算法优化

        Args:
            param_ranges: 参数范围，例如 {"param1": (0, 100), "param2": (0.0, 1.0)}
            population_size: 种群大小
            generations: 迭代代数
            mutation_rate: 变异率
            crossover_rate: 交叉率

        Returns:
            OptimizationResult: 优化结果
        """
        param_names = list(param_ranges.keys())

        # 初始化种群
        population = []
        for _ in range(population_size):
            individual = {
                name: random.uniform(param_ranges[name][0], param_ranges[name][1])
                for name in param_names
            }
            population.append(individual)

        best_params = None
        best_score = float('-inf')
        all_results = []

        for generation in range(generations):
            # 评估种群
            scores = []
            for individual in population:
                score = self.objective_function(individual)
                scores.append(score)
                all_results.append({
                    "params": individual.copy(),
                    "score": score,
                    "generation": generation
                })

                if score > best_score:
                    best_score = score
                    best_params = individual.copy()

            # 选择（轮盘赌选择）
            total_score = sum(max(0, s) for s in scores)
            if total_score == 0:
                probabilities = [1.0 / len(scores)] * len(scores)
            else:
                probabilities = [max(0, s) / total_score for s in scores]

            new_population = []

            # 精英保留
            elite_count = max(1, population_size // 10)
            elite_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:elite_count]
            for idx in elite_indices:
                new_population.append(population[idx].copy())

            # 生成新个体
            while len(new_population) < population_size:
                # 选择父母
                parent1 = random.choices(population, weights=probabilities)[0]
                parent2 = random.choices(population, weights=probabilities)[0]

                # 交叉
                if random.random() < crossover_rate:
                    child = {}
                    for name in param_names:
                        child[name] = random.choice([parent1[name], parent2[name]])
                else:
                    child = parent1.copy()

                # 变异
                if random.random() < mutation_rate:
                    mutate_param = random.choice(param_names)
                    min_val, max_val = param_ranges[mutate_param]
                    child[mutate_param] = random.uniform(min_val, max_val)

                new_population.append(child)

            population = new_population

        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            all_results=all_results,
            iterations=population_size * generations
        )

    def bayesian_optimization(
        self,
        param_ranges: Dict[str, Tuple[float, float]],
        n_iterations: int = 20,
        n_initial_points: int = 5
    ) -> OptimizationResult:
        """
        贝叶斯优化（简化版，使用随机采样 + 局部搜索）

        Args:
            param_ranges: 参数范围
            n_iterations: 迭代次数
            n_initial_points: 初始随机采样点数

        Returns:
            OptimizationResult: 优化结果
        """
        param_names = list(param_ranges.keys())

        best_params = None
        best_score = float('-inf')
        all_results = []

        # 初始随机采样
        for _ in range(n_initial_points):
            params = {
                name: random.uniform(param_ranges[name][0], param_ranges[name][1])
                for name in param_names
            }
            score = self.objective_function(params)
            all_results.append({
                "params": params.copy(),
                "score": score
            })

            if score > best_score:
                best_score = score
                best_params = params.copy()

        # 局部搜索
        for iteration in range(n_iterations - n_initial_points):
            # 在最佳参数附近采样
            params = {}
            for name in param_names:
                min_val, max_val = param_ranges[name]
                range_size = max_val - min_val

                # 随着迭代减小搜索范围
                search_radius = range_size * 0.2 * (1 - iteration / n_iterations)

                new_val = best_params[name] + random.uniform(-search_radius, search_radius)
                new_val = max(min_val, min(max_val, new_val))
                params[name] = new_val

            score = self.objective_function(params)
            all_results.append({
                "params": params.copy(),
                "score": score
            })

            if score > best_score:
                best_score = score
                best_params = params.copy()

        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            all_results=all_results,
            iterations=n_iterations
        )
