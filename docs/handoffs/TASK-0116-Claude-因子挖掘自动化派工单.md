# TASK-0116 Claude 派工单 — 决策端因子挖掘自动化

【任务ID】TASK-0116  
【服务】`services/decision/`  
【Token】`tok-bc3f9282-fb3e-4c90-8484-680d6be0e752`  
【执行人】Claude-Code  
【复核人】Atlas  
【前置条件】无（可独立执行，但注册的因子由 TASK-0115 factor_monitor 持续监控）

---

## 背景

实现两条因子挖掘路线：
1. **AI 提案驱动**：Jay.S 给意图 → deepcoder 生成因子代码 → IC 验证 → 注册
2. **数据驱动**：候选特征池自动组合 → IC 排序 → SHAP 剪枝 → 注册

---

## 白名单文件（4 个）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/decision/src/research/factor_miner.py` | **新建** | FactorMiner：双路挖掘（AI提案 + 数据驱动），输出 FactorCandidate 列表 |
| `services/decision/src/research/factor_validator.py` | **新建** | FactorValidator：IC 计算、衰减分析、OOS 验证、自动注册 |
| `services/decision/src/api/routes/factor.py` | **新建** | 因子挖掘 API：触发挖掘、查看候选、手动验证、查看注册表 |
| `services/decision/tests/test_factor_mining.py` | **新建** | IC 达标注册、IC 不达标拒绝、OOS 失败降级、factor_loader 注册后可查询 |

---

## 详细实现规格

### 1. `factor_miner.py` — 双路因子挖掘

```python
from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd

@dataclass
class FactorCandidate:
    factor_id: str
    name: str
    formula: str  # 因子计算逻辑（Python 代码字符串）
    symbols: List[str]  # 适用品种
    regimes: List[str]  # 适用行情类型（"trend"/"oscillation"/"high_vol"）
    source: str  # "ai_proposal" | "data_driven"
    ic_estimate: Optional[float] = None  # 预估IC，AI提案模式先给估值

class FactorMiner:
    """双路因子挖掘器"""
    
    # 候选特征池（期货专用）
    BASE_FEATURES = [
        "open", "high", "low", "close", "volume",  # OHLCV
        "open_interest", "oi_change",                # OI/仓差
        "basis",                                      # 基差（近月-连续）
        "term_structure_slope",                       # 期限结构斜率
        "spread_rb_i", "spread_hc_rb", "spread_p_y", # 跨品种价差
    ]
    
    MAX_CANDIDATES = 200  # 防组合爆炸
    
    def __init__(self, ollama_client, data_client):
        self.ollama = ollama_client
        self.data = data_client
    
    def mine_ai_proposal(self, intent: str,
                         symbols: List[str]) -> List[FactorCandidate]:
        """
        AI提案模式：
        1. 将 intent 发给 deepcoder:14b
        2. deepcoder 返回因子计算代码（Python lambda 或函数）
        3. 沙箱安全 eval（禁止 import os/sys/subprocess）
        4. 计算结果应为 pd.Series（与价格序列等长）
        5. 返回 FactorCandidate 列表
        """
        prompt = self._build_ai_prompt(intent, symbols)
        response = self.ollama.generate("deepcoder:14b", prompt)
        candidates = self._parse_ai_response(response, symbols)
        return candidates
    
    def mine_data_driven(self, symbols: List[str],
                         top_k: int = 20) -> List[FactorCandidate]:
        """
        数据驱动模式：
        1. 从特征池生成候选组合（单特征 + 双特征交互，上限200个）
        2. 对每个候选计算 IC（Spearman，预测方向 vs 实际涨跌）
        3. 按 IC 均值排序，取前 top_k
        4. 返回 FactorCandidate 列表
        """
        ...
    
    def _safe_eval_factor(self, code: str, bars: pd.DataFrame) -> Optional[pd.Series]:
        """
        安全 eval：
        - 只允许 pandas / numpy 操作
        - 禁止 import os/sys/subprocess/socket 等系统模块
        - 超时 5 秒
        - 返回 None 表示 eval 失败
        """
        FORBIDDEN = ["import os", "import sys", "import subprocess",
                     "import socket", "__import__", "exec(", "eval("]
        for pattern in FORBIDDEN:
            if pattern in code:
                return None
        # 在受限 namespace 中执行
        ns = {"pd": pd, "np": __import__("numpy")}
        try:
            result = eval(code, {"__builtins__": {}}, ns)
            return result if isinstance(result, pd.Series) else None
        except Exception:
            return None
```

### 2. `factor_validator.py` — IC 验证 + OOS 测试

```python
from dataclasses import dataclass
from typing import Optional
import numpy as np
from scipy.stats import spearmanr

@dataclass
class ValidationResult:
    factor_id: str
    ic_mean: float
    ic_std: float
    ic_decay_halflife_days: float
    oos_ic: float  # 样本外3个月 IC
    passed: bool
    reject_reason: Optional[str] = None

class FactorValidator:
    """
    IC 验证标准：
    - IC_mean > 0.05 (Spearman)
    - IC 半衰期 > 5 日（衰减过快的因子拒绝）
    - OOS 验证（样本外3个月）IC > 0.03
    """
    
    IC_MEAN_THRESHOLD = 0.05
    IC_HALFLIFE_MIN_DAYS = 5
    OOS_IC_THRESHOLD = 0.03
    
    def validate(self, candidate: "FactorCandidate",
                 bars_history: pd.DataFrame,
                 returns_history: pd.Series) -> ValidationResult:
        """
        bars_history: 历史 K 线（用于计算因子值）
        returns_history: 次日收益率序列（预测目标）
        """
        # 1. 计算整个历史期 IC 序列
        ic_series = self._rolling_ic(candidate, bars_history, returns_history)
        ic_mean = ic_series.mean()
        ic_std = ic_series.std()
        
        # 2. IC 半衰期估算（自相关衰减）
        halflife = self._estimate_halflife(ic_series)
        
        # 3. OOS 验证（最后 3 个月 bars 不参与训练）
        oos_ic = self._oos_validate(candidate, bars_history, returns_history)
        
        # 4. 综合判断
        if ic_mean <= self.IC_MEAN_THRESHOLD:
            return ValidationResult(..., passed=False, reject_reason=f"IC_mean={ic_mean:.4f} < {self.IC_MEAN_THRESHOLD}")
        if halflife < self.IC_HALFLIFE_MIN_DAYS:
            return ValidationResult(..., passed=False, reject_reason=f"halflife={halflife:.1f}d < {self.IC_HALFLIFE_MIN_DAYS}d")
        if oos_ic < self.OOS_IC_THRESHOLD:
            return ValidationResult(..., passed=False, reject_reason=f"OOS_IC={oos_ic:.4f} < {self.OOS_IC_THRESHOLD}")
        
        return ValidationResult(factor_id=candidate.factor_id, ic_mean=ic_mean,
                                ic_std=ic_std, ic_decay_halflife_days=halflife,
                                oos_ic=oos_ic, passed=True)
    
    def _rolling_ic(self, candidate, bars, returns, window=30) -> pd.Series: ...
    def _estimate_halflife(self, ic_series: pd.Series) -> float: ...
    def _oos_validate(self, candidate, bars, returns) -> float: ...
```

### 3. `factor.py` — API 路由

```python
from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/factor", tags=["factor"])

@router.post("/mine")
async def trigger_mine(request: MineRequest) -> MineResponse:
    """
    触发因子挖掘
    body: {mode: "ai_proposal"|"data_driven", intent?: str, symbols: list}
    """
    ...

@router.get("/candidates")
async def list_candidates() -> CandidatesResponse:
    """查看当前候选因子列表（含 IC 估值）"""
    ...

@router.post("/validate/{factor_id}")
async def validate_factor(factor_id: str) -> ValidationResponse:
    """手动触发指定因子验证（IC + OOS）"""
    ...

@router.get("/registry")
async def list_registry() -> RegistryResponse:
    """查看已注册并通过验证的因子"""
    ...
```

### 4. `test_factor_mining.py` — 测试

覆盖场景（全部 mock）：
- AI 提案模式：IC 达标 → 返回 passed=True，因子出现在注册表
- AI 提案模式：IC 不达标 → 返回 passed=False，含 reject_reason
- 数据驱动：候选数量 ≤ MAX_CANDIDATES（防组合爆炸）
- OOS 验证失败 → reject_reason 含 "OOS_IC"
- `_safe_eval_factor()` 含 `import os` → 返回 None（安全检查有效）
- `_safe_eval_factor()` 合法 pandas 代码 → 返回 pd.Series
- IC 半衰期 < 5 日 → 拒绝

---

## 质量标准

1. `get_errors` 白名单文件 = 0
2. `pytest tests/test_factor_mining.py -v` 全部通过
3. 沙箱 eval 拦截所有系统模块导入
4. 数据驱动候选组合 ≤ 200 个
5. IC 使用 Spearman 相关系数（rank-based）

---

## 候选特征池（期货专用）

| 特征 | 说明 |
|------|------|
| OHLCV | 基础价量 |
| open_interest | 持仓量 |
| oi_change | 仓差（当日OI变化） |
| basis | 基差 = 近月价格 - 连续合约价格 |
| term_structure_slope | 期限结构斜率（远月/近月价格比） |
| spread_rb_i / spread_hc_rb / spread_p_y | 跨品种价差 |

---

## 禁止事项

- 不得修改 `.env` 或 `.env.example`
- 不得修改白名单外任何文件
- 不得跨服务 import
- `_safe_eval_factor()` 必须禁止所有系统模块（OWASP 代码注入防护）
