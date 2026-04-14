"""品种级模型注册表 — TASK-0114

为每个期货品种建立独立的 XGBoost 模型注册表，支持按行情类型（regime）切换最优参数集。
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import xgboost as xgb  # type: ignore[import-untyped,import-not-found]

logger = logging.getLogger(__name__)


@dataclass
class ModelEntry:
    """模型注册条目。"""

    symbol: str
    regime: str  # "trend" | "oscillation" | "high_vol"
    best_params: dict
    trained_at: str  # ISO8601
    sharpe: float
    version: int = 1
    model: Optional[xgb.XGBClassifier] = field(default=None, repr=False)


class ModelRegistry:
    """品种级 XGBoost 模型注册表（内存 + 可选持久化）。

    存储结构：{symbol: {regime: ModelEntry}}
    """

    def __init__(self, persist_dir: Optional[str] = None):
        """初始化模型注册表。

        Args:
            persist_dir: 持久化目录，None 表示仅内存模式
        """
        self._registry: Dict[str, Dict[str, ModelEntry]] = {}
        self._persist_dir = Path(persist_dir) if persist_dir else None

        if self._persist_dir:
            self._persist_dir.mkdir(parents=True, exist_ok=True)
            self.load_from_disk()

    def register(
        self,
        symbol: str,
        regime: str,
        model: xgb.XGBClassifier,
        best_params: dict,
        sharpe: float,
    ) -> ModelEntry:
        """注册或更新品种模型。

        Args:
            symbol: 品种代码
            regime: 行情类型
            model: XGBoost 模型实例
            best_params: 最优参数
            sharpe: Sharpe 比率

        Returns:
            注册的 ModelEntry
        """
        if symbol not in self._registry:
            self._registry[symbol] = {}

        # 计算版本号
        existing = self._registry[symbol].get(regime)
        version = existing.version + 1 if existing else 1

        entry = ModelEntry(
            symbol=symbol,
            regime=regime,
            best_params=best_params,
            trained_at=datetime.now().isoformat(),
            sharpe=sharpe,
            version=version,
            model=model,
        )

        self._registry[symbol][regime] = entry

        # 持久化
        if self._persist_dir:
            self._save_entry(entry)

        logger.info(
            f"注册模型: {symbol}/{regime} v{version}, Sharpe={sharpe:.3f}"
        )

        return entry

    def get(self, symbol: str, regime: str) -> Optional[ModelEntry]:
        """获取指定品种和行情类型的模型。

        Args:
            symbol: 品种代码
            regime: 行情类型

        Returns:
            ModelEntry 或 None
        """
        return self._registry.get(symbol, {}).get(regime)

    def list_symbols(self) -> List[str]:
        """列出所有已注册品种。

        Returns:
            品种代码列表
        """
        return list(self._registry.keys())

    def retire(self, symbol: str, regime: str) -> bool:
        """注销指定品种和行情类型的模型。

        Args:
            symbol: 品种代码
            regime: 行情类型

        Returns:
            是否成功注销
        """
        if symbol not in self._registry:
            return False

        if regime not in self._registry[symbol]:
            return False

        del self._registry[symbol][regime]

        # 如果该品种没有任何 regime 了，删除品种键
        if not self._registry[symbol]:
            del self._registry[symbol]

        # 删除持久化文件
        if self._persist_dir:
            self._delete_entry(symbol, regime)

        logger.info(f"注销模型: {symbol}/{regime}")

        return True

    def get_best_regime(self, symbol: str) -> Optional[ModelEntry]:
        """返回该品种所有 regime 中 Sharpe 最高的模型。

        Args:
            symbol: 品种代码

        Returns:
            Sharpe 最高的 ModelEntry，无模型时返回 None
        """
        if symbol not in self._registry:
            return None

        regimes = self._registry[symbol]
        if not regimes:
            return None

        # 按 Sharpe 降序排序，取第一个
        best_entry = max(regimes.values(), key=lambda e: e.sharpe)

        return best_entry

    def load_from_disk(self) -> None:
        """从持久化目录加载所有模型。"""
        if not self._persist_dir:
            return

        if not self._persist_dir.exists():
            logger.info("持久化目录不存在，跳过加载")
            return

        loaded_count = 0

        for json_file in self._persist_dir.glob("*.json"):
            try:
                # 解析文件名: {symbol}_{regime}.json
                stem = json_file.stem
                parts = stem.rsplit("_", 1)
                if len(parts) != 2:
                    logger.warning(f"无效文件名格式: {json_file.name}")
                    continue

                symbol, regime = parts

                # 加载元数据
                with json_file.open("r", encoding="utf-8") as f:
                    meta = json.load(f)

                # 加载模型权重
                model_file = self._persist_dir / f"{symbol}_{regime}.ubj"
                if not model_file.exists():
                    logger.warning(f"模型文件缺失: {model_file.name}")
                    continue

                model = xgb.XGBClassifier()
                model.load_model(str(model_file))

                # 重建 ModelEntry
                entry = ModelEntry(
                    symbol=meta["symbol"],
                    regime=meta["regime"],
                    best_params=meta["best_params"],
                    trained_at=meta["trained_at"],
                    sharpe=meta["sharpe"],
                    version=meta["version"],
                    model=model,
                )

                if symbol not in self._registry:
                    self._registry[symbol] = {}

                self._registry[symbol][regime] = entry
                loaded_count += 1

            except Exception as e:
                logger.warning(f"加载模型失败 {json_file.name}: {e}", exc_info=True)
                continue

        logger.info(f"从磁盘加载 {loaded_count} 个模型")

    def _save_entry(self, entry: ModelEntry) -> None:
        """保存单个模型条目到磁盘。

        Args:
            entry: 模型条目
        """
        if not self._persist_dir:
            return

        prefix = f"{entry.symbol}_{entry.regime}"

        # 保存元数据
        meta_file = self._persist_dir / f"{prefix}.json"
        meta = {
            "symbol": entry.symbol,
            "regime": entry.regime,
            "best_params": entry.best_params,
            "trained_at": entry.trained_at,
            "sharpe": entry.sharpe,
            "version": entry.version,
        }

        with meta_file.open("w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # 保存模型权重
        if entry.model:
            model_file = self._persist_dir / f"{prefix}.ubj"
            entry.model.save_model(str(model_file))

    def _delete_entry(self, symbol: str, regime: str) -> None:
        """删除持久化文件。

        Args:
            symbol: 品种代码
            regime: 行情类型
        """
        if not self._persist_dir:
            return

        prefix = f"{symbol}_{regime}"

        meta_file = self._persist_dir / f"{prefix}.json"
        model_file = self._persist_dir / f"{prefix}.ubj"

        if meta_file.exists():
            meta_file.unlink()

        if model_file.exists():
            model_file.unlink()
