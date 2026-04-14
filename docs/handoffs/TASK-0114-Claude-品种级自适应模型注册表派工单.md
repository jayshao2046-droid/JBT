# TASK-0114 Claude 派工单 — 决策端 35 品种自适应模型注册表

【任务ID】TASK-0114  
【服务】`services/decision/`  
【Token】`tok-d0112f40-fa4d-4368-9f4b-12e20952d6e7`  
【执行人】Claude-Code  
【复核人】Atlas  
【前置条件】TASK-0112 Batch C 完成后执行（trainer.py 真实 Sharpe 前置）

---

## 背景

当前所有 35 个期货品种共用一个 XGBoost 分类器，导致不同品种因子体系不匹配、假信号率高。本任务为每个品种建立独立模型注册表 + 行情检测器，以品种 × 行情类型矩阵切换最优参数集。

---

## 白名单文件（4 个）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/decision/src/research/model_registry.py` | **新建** | ModelRegistry：品种级 XGBClassifier 存储，支持 register/get/list/retire |
| `services/decision/src/research/regime_detector.py` | **新建** | RegimeDetector：调 phi4-reasoning 检测行情类型（trend/oscillation/high_vol） |
| `services/decision/src/research/trainer.py` | **修改** | 升级为品种级训练 + 方案B增量训练 + 真实收益序列 Sharpe |
| `services/decision/tests/test_model_registry.py` | **新建** | 注册/获取/注销/品种隔离测试；mock 行情检测；增量训练不跨品种 |

---

## 详细实现规格

### 1. `model_registry.py` — 品种级模型注册表

```python
from dataclasses import dataclass, field
from typing import Dict, Optional, List
import xgboost as xgb

@dataclass
class ModelEntry:
    symbol: str
    regime: str  # "trend" | "oscillation" | "high_vol"
    model: xgb.XGBClassifier
    best_params: dict
    trained_at: str  # ISO8601
    sharpe: float
    version: int = 1

class ModelRegistry:
    """品种级 XGBoost 模型注册表（内存 + 可选持久化）"""
    
    def __init__(self, persist_dir: Optional[str] = None):
        self._registry: Dict[str, Dict[str, ModelEntry]] = {}
        # key: symbol -> {regime -> ModelEntry}
        self._persist_dir = persist_dir
    
    def register(self, symbol: str, regime: str, model: xgb.XGBClassifier,
                 best_params: dict, sharpe: float) -> ModelEntry: ...
    
    def get(self, symbol: str, regime: str) -> Optional[ModelEntry]: ...
    
    def list_symbols(self) -> List[str]: ...
    
    def retire(self, symbol: str, regime: str) -> bool: ...
    
    def get_best_regime(self, symbol: str) -> Optional[ModelEntry]:
        """返回该品种所有 regime 中 Sharpe 最高的模型"""
        ...
```

**持久化**（可选，当 `persist_dir` 非 None）：
- 每个 (symbol, regime) 组合保存为 `{persist_dir}/{symbol}_{regime}.json`（参数）+ `{symbol}_{regime}.ubj`（模型权重）
- `load_from_disk()` 启动时自动加载

### 2. `regime_detector.py` — 行情类型检测器

```python
from enum import Enum
from typing import Optional
import httpx

class Regime(str, Enum):
    TREND = "trend"
    OSCILLATION = "oscillation"
    HIGH_VOL = "high_vol"

@dataclass
class RegimeResult:
    symbol: str
    regime: Regime
    confidence: float  # 0.0-1.0
    reasoning: str
    source: str  # "phi4" | "fallback"

class RegimeDetector:
    """调 phi4-reasoning 判断行情类型（趋势/震荡/高波动）"""
    
    OLLAMA_URL = "http://192.168.31.142:11434"
    MODEL = "phi4-reasoning:14b"
    TIMEOUT = 15.0  # 超时降级为 trend
    FALLBACK_REGIME = Regime.TREND  # 保守降级策略
    
    def detect(self, symbol: str, bars_5d: list, bars_20d: list) -> RegimeResult:
        """
        输入：5日日线 + 20日日线 K 线数据（OHLCV 格式）
        输出：RegimeResult
        超时或报错 → 自动降级为 trend + source="fallback"
        """
        try:
            prompt = self._build_prompt(symbol, bars_5d, bars_20d)
            response = httpx.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={"model": self.MODEL, "prompt": prompt, "stream": False},
                timeout=self.TIMEOUT
            )
            return self._parse_response(symbol, response.json())
        except Exception:
            return RegimeResult(symbol=symbol, regime=self.FALLBACK_REGIME,
                                confidence=0.5, reasoning="fallback", source="fallback")
    
    def _build_prompt(self, symbol: str, bars_5d: list, bars_20d: list) -> str:
        """构造结构化提示词，要求 phi4 输出 JSON: {regime, confidence, reasoning}"""
        ...
```

### 3. `trainer.py` — 升级品种级训练

在已有 `Trainer` 类基础上新增：

```python
def train_for_symbol(
    self,
    symbol: str,
    regime: str,
    X: pd.DataFrame,
    y: pd.Series,
    registry: ModelRegistry,
    incremental: bool = True
) -> ModelEntry:
    """
    品种级训练：
    1. 若 incremental=True 且 registry 中已有该 (symbol, regime) 模型，
       用 xgb_model 参数追加（增量训练），保留已学习结构
    2. 若未有或 incremental=False，全量训练
    3. cross_validate 改用真实收益序列计算 Sharpe（修复 TASK-0112-C 需求）
    4. 训练完成后注册到 registry
    
    增量训练防灾难性遗忘：
    - 验证集准确率下降 > 5% 时回滚
    """
    existing = registry.get(symbol, regime)
    xgb_model_param = existing.model if (incremental and existing) else None
    
    model = xgb.XGBClassifier(**self._get_params(symbol, regime))
    model.fit(X_train, y_train, xgb_model=xgb_model_param,
              eval_set=[(X_val, y_val)], early_stopping_rounds=10)
    
    sharpe = self._calc_real_sharpe(model, X_val, y_val)
    
    # 回滚检查
    if existing and sharpe < existing.sharpe * 0.95:
        return existing  # 增量训练变差，保留原模型
    
    return registry.register(symbol, regime, model, model.get_params(), sharpe)

def _calc_real_sharpe(self, model, X_val, y_val) -> float:
    """使用预测信号乘以实际收益率计算真实 Sharpe（非代理指标）"""
    pred = model.predict(X_val)
    returns = y_val.values * pred  # 实际持仓收益
    if returns.std() == 0:
        return 0.0
    return (returns.mean() / returns.std()) * (252 ** 0.5)
```

### 4. `test_model_registry.py` — 测试

覆盖场景：
- `register()` → `get()` 返回正确模型
- 两个品种互不干扰（rb 模型不影响 cu 模型）
- 增量训练：模型版本递增，Sharpe 下降时回滚
- `retire()` 后 `get()` 返回 None
- `get_best_regime()` 返回 Sharpe 最高的 regime
- `RegimeDetector` 超时后降级为 trend + source="fallback"（mock httpx）
- `RegimeDetector` 正常响应解析 JSON 格式

---

## 品种列表（35 个）

```
rb, hc, i, j, jm, cu, al, zn, ni, ss,
au, ag, sc, fu, bu, ru, sp, ap, cf, sr,
ma, ta, eg, pp, l, v, eb, pg, lh, p,
y, a, c, cs, m
```

---

## 质量标准

1. `get_errors` 白名单文件 = 0
2. `pytest tests/test_model_registry.py -v` 全部通过
3. 增量训练不覆盖其他品种
4. RegimeDetector 超时（mock 15s timeout）→ 返回 fallback regime
5. Sharpe 计算使用真实收益序列（非 accuracy 代理）

---

## 禁止事项

- 不得修改 `.env` 或 `.env.example`
- 不得修改白名单外任何文件
- 不得跨服务 import
- 不得硬编码 Ollama 主机（已在 OLLAMA_URL 常量中）
