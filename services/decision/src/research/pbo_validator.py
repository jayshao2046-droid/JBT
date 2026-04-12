"""PBO 检验器 — TASK-0075 CA7

Probability of Backtest Overfitting (PBO) 检验，用于评估策略参数是否过拟合。

参考文献：
Bailey, D. H., Borwein, J., López de Prado, M., & Zhu, Q. J. (2014).
"Probability of Backtest Overfitting". Journal of Computational Finance.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Any


class PBOValidator:
    """PBO 检验器。

    通过组合对称交叉验证 (CSCV) 评估策略参数的稳健性。
    """

    def __init__(self, n_splits: int = 16):
        """初始化 PBO 检验器。

        Args:
            n_splits: 数据分割数量，必须是偶数（默认 16）。
        """
        if n_splits % 2 != 0:
            raise ValueError("n_splits must be even")
        self.n_splits = n_splits

    def validate(
        self,
        returns: pd.Series,
        param_configs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """执行 PBO 检验。

        Args:
            returns: 策略收益率序列（索引为日期）。
            param_configs: 参数配置列表，每个配置对应一组参数的回测结果。

        Returns:
            包含 PBO 指标的字典：
            - pbo: PBO 值（0~1，越接近 0 越好）
            - sharpe_is: 样本内最优参数的 Sharpe
            - sharpe_oos: 样本外对应参数的 Sharpe
            - rank_correlation: 样本内外排名相关性
        """
        if len(returns) < self.n_splits:
            raise ValueError(f"returns length {len(returns)} < n_splits {self.n_splits}")

        # 分割数据为 n_splits 个子集
        split_size = len(returns) // self.n_splits
        splits = [
            returns.iloc[i * split_size : (i + 1) * split_size]
            for i in range(self.n_splits)
        ]

        # 组合对称交叉验证：前半作为样本内 (IS)，后半作为样本外 (OOS)
        is_indices = list(range(self.n_splits // 2))
        oos_indices = list(range(self.n_splits // 2, self.n_splits))

        is_returns = pd.concat([splits[i] for i in is_indices])
        oos_returns = pd.concat([splits[i] for i in oos_indices])

        # 计算每个参数配置的样本内和样本外 Sharpe
        sharpe_is_list = []
        sharpe_oos_list = []

        for config in param_configs:
            # 假设 config 包含该参数对应的收益率序列
            config_returns = config.get("returns", returns)

            is_subset = config_returns.loc[is_returns.index]
            oos_subset = config_returns.loc[oos_returns.index]

            sharpe_is = self._calculate_sharpe(is_subset)
            sharpe_oos = self._calculate_sharpe(oos_subset)

            sharpe_is_list.append(sharpe_is)
            sharpe_oos_list.append(sharpe_oos)

        # 找到样本内最优参数
        best_is_idx = int(np.argmax(sharpe_is_list))
        sharpe_is_best = sharpe_is_list[best_is_idx]
        sharpe_oos_best = sharpe_oos_list[best_is_idx]

        # 计算 PBO：样本外表现劣于样本内中位数的概率
        sharpe_is_median = np.median(sharpe_is_list)
        pbo = np.mean([1 if s < sharpe_is_median else 0 for s in sharpe_oos_list])

        # 计算排名相关性（Spearman）
        rank_is = np.argsort(np.argsort(sharpe_is_list))
        rank_oos = np.argsort(np.argsort(sharpe_oos_list))
        rank_correlation = np.corrcoef(rank_is, rank_oos)[0, 1]

        return {
            "pbo": float(pbo),
            "sharpe_is": float(sharpe_is_best),
            "sharpe_oos": float(sharpe_oos_best),
            "rank_correlation": float(rank_correlation),
            "n_configs": len(param_configs),
            "n_splits": self.n_splits,
        }

    def _calculate_sharpe(self, returns: pd.Series) -> float:
        """计算 Sharpe 比率（年化）。

        Args:
            returns: 收益率序列。

        Returns:
            Sharpe 比率。
        """
        if len(returns) == 0:
            return 0.0

        mean_return = returns.mean()
        std_return = returns.std()

        # 标准差接近 0 时返回 0（避免除零，阈值 1e-10）
        if std_return < 1e-10 or np.isnan(std_return):
            return 0.0

        # 假设日频数据，年化因子为 sqrt(252)
        sharpe = (mean_return / std_return) * np.sqrt(252)
        return float(sharpe)

    def interpret(self, result: dict[str, Any]) -> str:
        """解释 PBO 检验结果。

        Args:
            result: validate() 返回的结果字典。

        Returns:
            解释文本。
        """
        pbo = result["pbo"]
        rank_corr = result["rank_correlation"]

        if pbo < 0.3:
            pbo_level = "低风险"
        elif pbo < 0.5:
            pbo_level = "中等风险"
        else:
            pbo_level = "高风险"

        if rank_corr > 0.7:
            corr_level = "强相关"
        elif rank_corr > 0.3:
            corr_level = "中等相关"
        else:
            corr_level = "弱相关"

        return (
            f"PBO = {pbo:.2%} ({pbo_level})，"
            f"排名相关性 = {rank_corr:.2f} ({corr_level})。"
            f"样本内 Sharpe = {result['sharpe_is']:.2f}，"
            f"样本外 Sharpe = {result['sharpe_oos']:.2f}。"
        )
