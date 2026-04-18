"""XGBoost 信号质量过滤器 — 学习哪些交易特征组合更可能盈利。

工作流：
1. 从回测交易记录中收集特征快照（开仓时刻的技术指标）
2. 标注标签：pnl > 0 → 1（盈利），pnl ≤ 0 → 0（亏损）
3. 训练 XGBoost 二分类模型
4. 用训练好的模型过滤未来信号：只保留预测为"大概率盈利"的信号
5. 支持多轮迭代：回测→训练→过滤→再回测→再训练...
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

# 特征列名（与 yaml_signal_executor._capture_trade_features 对齐）
FEATURE_COLUMNS = [
    "rsi", "atr", "atr_pct", "adx", "volume_ratio",
    "bb_width", "bb_position", "macd_hist", "hour",
]


class XGBoostSignalFilter:
    """基于 XGBoost 的交易信号质量过滤器。"""

    def __init__(
        self,
        symbol: str,
        strategy_name: str,
        evidence_dir: str = "llm_generated",
        min_samples: int = 30,
        predict_threshold: float = 0.5,
    ) -> None:
        self.symbol = symbol
        self.strategy_name = strategy_name
        self.evidence_dir = Path(evidence_dir)
        self.min_samples = min_samples
        self.predict_threshold = predict_threshold
        self.model: Any = None
        self._model_path = (
            self.evidence_dir / symbol / strategy_name / "xgboost_model.json"
        )

    def collect_trade_features(self, trades: list[dict]) -> tuple[np.ndarray, np.ndarray]:
        """从交易记录中提取特征矩阵和标签向量。

        trades 格式：yaml_signal_executor._simulate_trades 的输出。
        开仓记录携带 'features' 字段，平仓记录携带 'pnl' 字段。
        将它们配对：open → close → 一条训练样本。

        Returns:
            (X, y) — X shape (n_samples, n_features), y shape (n_samples,)
        """
        X_rows: list[list[float]] = []
        y_labels: list[int] = []

        pending_features: Optional[dict] = None

        for t in trades:
            trade_type = t.get("type", "")

            # 开仓记录（有 features）
            if trade_type.startswith("open_") and "features" in t:
                pending_features = t["features"]
                continue

            # 平仓记录（有 pnl）
            if pending_features is not None and "pnl" in t:
                pnl = float(t["pnl"])
                row = [float(pending_features.get(col, 0.0)) for col in FEATURE_COLUMNS]
                X_rows.append(row)
                y_labels.append(1 if pnl > 0 else 0)
                pending_features = None

        if not X_rows:
            return np.empty((0, len(FEATURE_COLUMNS))), np.empty(0)

        return np.array(X_rows, dtype=np.float32), np.array(y_labels, dtype=np.int32)

    def train(self, X: np.ndarray, y: np.ndarray) -> dict[str, Any]:
        """训练 XGBoost 二分类模型。

        Returns:
            训练报告 dict（accuracy, n_samples, feature_importance 等）
        """
        try:
            import xgboost as xgb
        except ImportError:
            logger.error("xgboost 未安装，请 pip install xgboost")
            return {"error": "xgboost not installed"}

        if len(X) < self.min_samples:
            return {
                "error": f"样本不足: {len(X)} < {self.min_samples}",
                "n_samples": len(X),
            }

        # 类别平衡
        n_pos = int(y.sum())
        n_neg = len(y) - n_pos
        scale_pos = n_neg / max(1, n_pos) if n_pos > 0 else 1.0

        dtrain = xgb.DMatrix(X, label=y, feature_names=FEATURE_COLUMNS)

        params = {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "max_depth": 4,
            "eta": 0.1,
            "scale_pos_weight": scale_pos,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "seed": 42,
        }

        self.model = xgb.train(params, dtrain, num_boost_round=100)

        # 训练集自评（仅诊断用）
        preds = self.model.predict(dtrain)
        pred_labels = (preds > self.predict_threshold).astype(int)
        accuracy = float((pred_labels == y).mean())

        # 特征重要性
        importance = self.model.get_score(importance_type="gain")

        report = {
            "n_samples": len(X),
            "n_positive": n_pos,
            "n_negative": n_neg,
            "train_accuracy": round(accuracy, 4),
            "feature_importance": importance,
            "threshold": self.predict_threshold,
        }

        # 保存模型
        self._save_model()
        logger.info(
            "XGBoost 训练完成: %s/%s — %d 样本, 准确率 %.2f%%",
            self.symbol, self.strategy_name, len(X), accuracy * 100,
        )

        return report

    def filter_signals(
        self,
        signals: list[int],
        bars: list[dict],
        feature_snapshots: Optional[list[dict]] = None,
    ) -> list[int]:
        """用训练好的模型过滤信号：只保留预测为盈利的开仓信号。

        Args:
            signals: 原始信号列表 (0, 1, -1)
            bars: K 线数据（用于实时计算特征）
            feature_snapshots: 预计算的特征快照（如果有的话）

        Returns:
            过滤后的信号列表
        """
        if self.model is None:
            if not self._load_model():
                return signals  # 无模型则不过滤

        try:
            import xgboost as xgb
        except ImportError:
            return signals

        filtered = list(signals)
        indices_to_check = [i for i, s in enumerate(signals) if s != 0]

        if not indices_to_check:
            return filtered

        # 为每个非零信号构建特征
        from .yaml_signal_executor import (
            _ta_rsi, _ta_atr, _ta_adx, _ta_volume_ratio,
            _ta_bollinger, _ta_macd,
        )

        closes = [float(b.get("close", 0)) for b in bars]
        highs = [float(b.get("high", 0)) for b in bars]
        lows = [float(b.get("low", 0)) for b in bars]
        volumes = [float(b.get("volume", 0)) for b in bars]
        rsi = _ta_rsi(closes, 14)
        atr = _ta_atr(highs, lows, closes, 14)
        adx = _ta_adx(highs, lows, closes, 14)
        vol_ratio = _ta_volume_ratio(volumes, 10)
        bb_upper, bb_mid, bb_lower = _ta_bollinger(closes, 20, 2.0)
        _, _, macd_hist = _ta_macd(closes)

        rows: list[list[float]] = []
        for idx in indices_to_check:
            close = closes[idx] if idx < len(closes) else 0.0
            bb_w = (
                (bb_upper[idx] - bb_lower[idx]) / bb_mid[idx]
                if idx < len(bb_mid) and bb_mid[idx] > 0 else 0.0
            )
            bb_p = (
                (close - bb_lower[idx]) / (bb_upper[idx] - bb_lower[idx])
                if idx < len(bb_upper) and (bb_upper[idx] - bb_lower[idx]) > 0 else 0.5
            )
            dt_str = str(bars[idx].get("datetime", ""))
            hour = -1
            try:
                if len(dt_str) >= 13:
                    hour = int(dt_str[11:13])
            except (ValueError, IndexError):
                pass

            row = [
                rsi[idx] if idx < len(rsi) else 50.0,
                atr[idx] if idx < len(atr) else 0.0,
                atr[idx] / close if idx < len(atr) and close > 0 else 0.0,
                adx[idx] if idx < len(adx) else 0.0,
                vol_ratio[idx] if idx < len(vol_ratio) else 1.0,
                bb_w,
                bb_p,
                macd_hist[idx] if idx < len(macd_hist) else 0.0,
                float(hour),
            ]
            rows.append(row)

        if not rows:
            return filtered

        X_pred = np.array(rows, dtype=np.float32)
        dmat = xgb.DMatrix(X_pred, feature_names=FEATURE_COLUMNS)
        probs = self.model.predict(dmat)

        n_filtered = 0
        for j, idx in enumerate(indices_to_check):
            if probs[j] < self.predict_threshold:
                filtered[idx] = 0
                n_filtered += 1

        logger.info(
            "XGBoost 过滤: %d/%d 信号被过滤 (阈值 %.2f)",
            n_filtered, len(indices_to_check), self.predict_threshold,
        )

        return filtered

    def _save_model(self) -> None:
        if self.model is None:
            return
        self._model_path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save_model(str(self._model_path))
        logger.info("XGBoost 模型保存到 %s", self._model_path)

    def _load_model(self) -> bool:
        if not self._model_path.exists():
            return False
        try:
            import xgboost as xgb
            self.model = xgb.Booster()
            self.model.load_model(str(self._model_path))
            logger.info("XGBoost 模型加载自 %s", self._model_path)
            return True
        except Exception as e:
            logger.warning("XGBoost 模型加载失败: %s", e)
            return False

    def save_round_evidence(self, round_num: int, report: dict, run_id: str) -> None:
        """保存每轮 XGBoost 训练证据。"""
        evidence_path = (
            self.evidence_dir / self.symbol / self.strategy_name
            / "xgboost_evidence" / run_id / f"round_{round_num}.json"
        )
        evidence_path.parent.mkdir(parents=True, exist_ok=True)

        evidence = {
            "round": round_num,
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "symbol": self.symbol,
            "strategy": self.strategy_name,
            "report": report,
        }

        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump(evidence, f, ensure_ascii=False, indent=2)

        logger.info("XGBoost 第 %d 轮证据保存到 %s", round_num, evidence_path)
