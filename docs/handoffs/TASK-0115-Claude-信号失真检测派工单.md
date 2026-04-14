# TASK-0115 Claude 派工单 — 决策端信号失真检测 + 因子漂移监控（G8）

【任务ID】TASK-0115  
【服务】`services/decision/`  
【Token】`tok-48fd42a7-96d5-441e-8da2-2b047a49cbaa`  
【执行人】Claude-Code  
【复核人】Atlas  
【前置条件】无（可独立执行，但在 TASK-0114 之后执行更有意义）

---

## 背景

当前缺少 G8 能力：XGBoost 预测信号失真检测（预测 vs 实际对比）+ 因子分布漂移监控（PSI/KS 检验）。出现失真或漂移时通过飞书 P1 报警并触发再训练标记。

---

## 白名单文件（3 个）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/decision/src/research/signal_validator.py` | **新建** | SignalValidator：30日滚动回测 → 准确率连续5日 < 55% → 飞书P1 |
| `services/decision/src/research/factor_monitor.py` | **新建** | FactorMonitor：KS 检验 + PSI 监控 → 漂移超阈值 → 飞书P1 + deprecated |
| `services/decision/tests/test_signal_validator.py` | **新建** | 失真超阈值触发报警、漂移检验通过/不通过、状态转换测试 |

---

## 详细实现规格

### 1. `signal_validator.py` — 信号失真检测

```python
from dataclasses import dataclass
from typing import List, Optional
import numpy as np

@dataclass
class ValidationResult:
    symbol: str
    window_days: int
    accuracy: float
    consecutive_below_threshold: int
    triggered_alert: bool
    retrain_flag: bool

class SignalValidator:
    """
    30日滚动回测：比对 XGBoost 预测方向 vs 实际价格涨跌
    连续 5 日准确率 < 55% → 飞书 P1 报警 + retrain_flag=True
    """
    
    ACCURACY_THRESHOLD: float = 0.55
    ALERT_CONSECUTIVE_DAYS: int = 5
    WINDOW_DAYS: int = 30
    
    def __init__(self, notifier):
        """notifier: 已有的 DecisionFeishuNotifier 实例"""
        self.notifier = notifier
        self._consecutive_count: dict = {}  # symbol -> consecutive below count
    
    def validate(self, symbol: str, predictions: List[int],
                 actuals: List[int]) -> ValidationResult:
        """
        predictions: 模型预测方向 1=看涨 0=看跌
        actuals: 实际次日涨跌 1=涨 0=跌
        """
        accuracy = np.mean(np.array(predictions) == np.array(actuals))
        
        if accuracy < self.ACCURACY_THRESHOLD:
            self._consecutive_count[symbol] = self._consecutive_count.get(symbol, 0) + 1
        else:
            self._consecutive_count[symbol] = 0
        
        consecutive = self._consecutive_count[symbol]
        triggered = consecutive >= self.ALERT_CONSECUTIVE_DAYS
        
        if triggered:
            self._send_alert(symbol, accuracy, consecutive)
        
        return ValidationResult(
            symbol=symbol,
            window_days=self.WINDOW_DAYS,
            accuracy=accuracy,
            consecutive_below_threshold=consecutive,
            triggered_alert=triggered,
            retrain_flag=triggered
        )
    
    def _send_alert(self, symbol: str, accuracy: float, consecutive: int) -> None:
        """飞书 P1 (orange ⚠️) 报警"""
        self.notifier.send(
            level="P1",
            title=f"⚠️ [PROD-P1] 信号失真报警 {symbol}",
            content={
                "品种": symbol,
                "近30日准确率": f"{accuracy:.1%}",
                "连续低于阈值": f"{consecutive} 日",
                "阈值": f"{self.ACCURACY_THRESHOLD:.0%}",
                "处置": "触发再训练标记，建议检查因子质量"
            }
        )
```

### 2. `factor_monitor.py` — 因子漂移监控

```python
from dataclasses import dataclass
from typing import Optional
import numpy as np
from scipy import stats

@dataclass
class FactorStatus:
    factor_name: str
    psi: float
    ks_statistic: float
    ks_pvalue: float
    is_drifted: bool
    status: str  # "healthy" | "warning" | "deprecated"

class FactorMonitor:
    """
    KS 检验（p < 0.05）+ PSI（> 0.25）双重检测因子分布漂移
    漂移确认 → 飞书 P1 报警 + status=deprecated
    每日收盘后运行
    """
    
    PSI_THRESHOLD: float = 0.25
    KS_PVALUE_THRESHOLD: float = 0.05
    
    def __init__(self, notifier):
        self.notifier = notifier
    
    def check_factor(self, factor_name: str,
                     baseline_values: np.ndarray,
                     current_values: np.ndarray) -> FactorStatus:
        """
        baseline_values: 历史基准分布（过去90-180天）
        current_values: 近期值（过去30天）
        """
        psi = self._calc_psi(baseline_values, current_values)
        ks_stat, ks_pvalue = stats.ks_2samp(baseline_values, current_values)
        
        is_drifted = (psi > self.PSI_THRESHOLD) or (ks_pvalue < self.KS_PVALUE_THRESHOLD)
        status = "deprecated" if is_drifted else (
            "warning" if psi > self.PSI_THRESHOLD * 0.6 else "healthy"
        )
        
        if is_drifted:
            self._send_alert(factor_name, psi, ks_pvalue)
        
        return FactorStatus(
            factor_name=factor_name,
            psi=psi,
            ks_statistic=ks_stat,
            ks_pvalue=ks_pvalue,
            is_drifted=is_drifted,
            status=status
        )
    
    def _calc_psi(self, baseline: np.ndarray, current: np.ndarray,
                  n_bins: int = 10) -> float:
        """计算 Population Stability Index"""
        bins = np.percentile(baseline, np.linspace(0, 100, n_bins + 1))
        bins[0] = -np.inf
        bins[-1] = np.inf
        
        baseline_pct = np.histogram(baseline, bins)[0] / len(baseline)
        current_pct = np.histogram(current, bins)[0] / len(current)
        
        # 防止 log(0)
        baseline_pct = np.clip(baseline_pct, 1e-6, None)
        current_pct = np.clip(current_pct, 1e-6, None)
        
        return np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))
    
    def _send_alert(self, factor_name: str, psi: float, ks_pvalue: float) -> None:
        """飞书 P1 (orange ⚠️) 报警"""
        self.notifier.send(
            level="P1",
            title=f"⚠️ [PROD-P1] 因子漂移报警",
            content={
                "因子": factor_name,
                "PSI": f"{psi:.4f}（阈值 {self.PSI_THRESHOLD}）",
                "KS p-value": f"{ks_pvalue:.4f}（阈值 {self.KS_PVALUE_THRESHOLD}）",
                "状态变更": "→ deprecated",
                "处置": "建议下线或重新验证该因子"
            }
        )
```

### 3. `test_signal_validator.py` — 测试

覆盖场景（全部 mock，不需要真实 Ollama）：
- 准确率 60% → 不触发报警，`triggered_alert=False`
- 连续 4 日 50% → 不触发（未到 5 日）
- 连续 5 日 50% → 触发飞书 P1 + `retrain_flag=True`
- 准确率恢复后重新计数（只需 1 日高于阈值即重置）
- `factor_monitor.check_factor()` PSI < 0.25 且 KS p > 0.05 → status="healthy"
- `factor_monitor.check_factor()` PSI > 0.25 → status="deprecated" + 飞书报警
- `factor_monitor.check_factor()` KS p < 0.05 → status="deprecated" + 飞书报警
- PSI 计算 `_calc_psi()` 值在合理范围（两个一致分布 PSI ≈ 0）

---

## 质量标准

1. `get_errors` 白名单文件 = 0
2. `pytest tests/test_signal_validator.py -v` 全部通过
3. 飞书报警使用已有 `DecisionFeishuNotifier`（orange P1 格式）
4. 测试全部 mock，不依赖真实 Ollama / 飞书
5. PSI 计算对 empty bucket 做 clip 处理，不产生 nan/inf

---

## 禁止事项

- 不得修改 `.env` 或 `.env.example`
- 不得修改白名单外任何文件
- 不得引入新的通知模块（使用已有 notifier）
- 不得跨服务 import
