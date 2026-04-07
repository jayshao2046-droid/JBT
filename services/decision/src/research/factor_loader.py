from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import numpy as np

from ..core.settings import get_settings


class FactorLoader:
    """因子数据加载（从 data service API 获取）。

    当前实现为 mock 版本：返回随机 numpy 数组。
    data service URL 从 settings 读取；真实 HTTP 调用在 data service 就绪后替换。
    """

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
        """返回 (X, y) tuple。

        Mock 实现：生成随机 float 特征矩阵与二分类标签。
        真实实现应调用 self._settings.data_service_url 的 HTTP 接口。
        """
        rng = np.random.default_rng(
            seed=int(hashlib.sha256(strategy_id.encode()).hexdigest()[:8], 16)
        )
        X = rng.random((n_samples, n_features)).astype(np.float32)
        y = rng.integers(0, 2, size=n_samples)
        return X, y

    @staticmethod
    def compute_hash(X: np.ndarray) -> str:
        """计算因子矩阵的 SHA-256 哈希（用于资格门禁版本比对）。"""
        return hashlib.sha256(X.tobytes()).hexdigest()
