"""
参数优化器模块
"""
from typing import List, Dict, Any, Optional
import itertools
import logging

logger = logging.getLogger(__name__)


class ParameterOptimizer:
    """参数优化器"""

    def __init__(self):
        self.results: List[Dict] = []

    def grid_search(
        self, param_grid: Dict[str, List[Any]], objective_func: callable, base_params: Optional[Dict] = None
    ) -> List[Dict]:
        """网格搜索优化"""
        if base_params is None:
            base_params = {}

        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())

        combinations = list(itertools.product(*param_values))

        results = []
        for combo in combinations:
            params = dict(zip(param_names, combo))
            params.update(base_params)

            try:
                score = objective_func(params)
                results.append({"params": params, "score": score, "status": "success"})
            except Exception as e:
                logger.error(f"Grid search failed for params {params}: {e}")
                results.append({"params": params, "score": 0.0, "status": "failed", "error": str(e)})

        # 按得分排序
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        self.results = results

        return results

    def genetic_algorithm(
        self,
        param_ranges: Dict[str, tuple],
        objective_func: callable,
        population_size: int = 20,
        generations: int = 10,
        mutation_rate: float = 0.1,
    ) -> List[Dict]:
        """遗传算法优化（简化版）"""
        import random

        # 初始化种群
        population = []
        for _ in range(population_size):
            individual = {param: random.uniform(min_val, max_val) for param, (min_val, max_val) in param_ranges.items()}
            population.append(individual)

        best_results = []

        for gen in range(generations):
            # 评估适应度
            fitness_scores = []
            for individual in population:
                try:
                    score = objective_func(individual)
                    fitness_scores.append((individual, score))
                except Exception as e:
                    logger.error(f"Genetic algorithm evaluation failed: {e}")
                    fitness_scores.append((individual, 0.0))

            # 排序
            fitness_scores.sort(key=lambda x: x[1], reverse=True)

            # 记录最佳结果
            best_individual, best_score = fitness_scores[0]
            best_results.append({"params": best_individual.copy(), "score": best_score, "generation": gen})

            # 选择（保留前50%）
            survivors = [ind for ind, _ in fitness_scores[: population_size // 2]]

            # 交叉和变异
            new_population = survivors.copy()
            while len(new_population) < population_size:
                parent1, parent2 = random.sample(survivors, 2)
                child = {}
                for param in param_ranges.keys():
                    # 交叉
                    child[param] = (parent1[param] + parent2[param]) / 2
                    # 变异
                    if random.random() < mutation_rate:
                        min_val, max_val = param_ranges[param]
                        child[param] += random.uniform(-0.1 * (max_val - min_val), 0.1 * (max_val - min_val))
                        child[param] = max(min_val, min(max_val, child[param]))
                new_population.append(child)

            population = new_population

        self.results = best_results
        return best_results

    def bayesian_optimization(
        self, param_ranges: Dict[str, tuple], objective_func: callable, n_iterations: int = 20
    ) -> List[Dict]:
        """贝叶斯优化（简化版 - 随机搜索）"""
        import random

        results = []
        for i in range(n_iterations):
            params = {param: random.uniform(min_val, max_val) for param, (min_val, max_val) in param_ranges.items()}

            try:
                score = objective_func(params)
                results.append({"params": params, "score": score, "iteration": i, "status": "success"})
            except Exception as e:
                logger.error(f"Bayesian optimization failed: {e}")
                results.append({"params": params, "score": 0.0, "iteration": i, "status": "failed", "error": str(e)})

        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        self.results = results

        return results

    def get_best_params(self) -> Optional[Dict]:
        """获取最佳参数"""
        if not self.results:
            return None

        return self.results[0].get("params")

    def get_top_n(self, n: int = 5) -> List[Dict]:
        """获取前 N 个最佳结果"""
        return self.results[:n]
