# TASK-0121-C：参数调优工具验证与补充

【任务ID】TASK-0121-C  
【父任务】TASK-0121  
【执行人】待分配（Claude Code / Atlas）  
【创建时间】2026-04-16  
【优先级】P1  
【状态】待预审  
【依赖】TASK-0121-A 完成

---

## 📋 任务目标

验证 TradeOptimizer 可用性，补充缺失功能，确保参数调优工具链完整。

---

## 🎯 核心功能

### 1. TradeOptimizer 验证

**验证项**：
- [ ] 类是否存在
- [ ] optimize 方法是否实现
- [ ] 支持的参数类型（入场阈值、因子权重、止盈止损、仓位大小）
- [ ] 优化算法（网格搜索、贝叶斯优化、遗传算法）
- [ ] 返回格式（最优参数、优化前后对比）

### 2. 参数调优流程

**输入**：
- 策略 YAML 文件
- 参数搜索空间
- 优化目标（Sharpe、回撤、胜率）

**输出**：
- 最优参数组合
- 优化前后对比（Sharpe、回撤、胜率）
- 参数敏感性分析

### 3. 调优示例

**场景 1：入场阈值调优**
```yaml
# 原始参数
entry_threshold: 0.60

# 搜索空间
entry_threshold: [0.50, 0.55, 0.60, 0.65, 0.70]

# 优化结果
best_entry_threshold: 0.65
sharpe_improvement: 2.3 → 2.8 (+0.5)
```

**场景 2：因子权重调优**
```yaml
# 原始参数
factor_weights:
  trend: 0.4
  momentum: 0.3
  volatility: 0.3

# 搜索空间
trend: [0.3, 0.4, 0.5]
momentum: [0.2, 0.3, 0.4]
volatility: [0.2, 0.3, 0.4]

# 优化结果
best_weights:
  trend: 0.5
  momentum: 0.3
  volatility: 0.2
sharpe_improvement: 2.3 → 2.7 (+0.4)
```

---

## 📁 文件清单（白名单）

### 验证文件（只读）

1. **services/decision/src/research/trade_optimizer.py**
   - 验证 TradeOptimizer 类
   - 验证 optimize 方法
   - 验证参数搜索空间定义

### 补充文件（如果需要）

2. **services/decision/src/research/trade_optimizer.py**
   - 补充缺失的优化算法
   - 补充参数敏感性分析
   - 补充优化报告生成

3. **services/decision/tests/test_trade_optimizer.py**
   - 入场阈值调优测试（3 个用例）
   - 因子权重调优测试（3 个用例）
   - 止盈止损调优测试（2 个用例）
   - 仓位大小调优测试（2 个用例）
   - 参数敏感性测试（2 个用例）

---

## 🔧 技术要求

### 代码规范

- Python 3.9+ 兼容
- 使用 `Optional[T]` 而非 `T | None`
- 所有公共方法有 docstring
- 所有异常有明确的错误信息

### 性能要求

- 网格搜索：支持并行评估
- 单次优化时间 < 30 分钟（取决于搜索空间大小）
- 内存占用 < 4GB

---

## 📊 验收标准

### 功能完整性

- [ ] TradeOptimizer 类验证完成
- [ ] 支持 4 种参数类型调优
- [ ] 支持至少 1 种优化算法（网格搜索）
- [ ] 优化报告生成完整

### 测试通过

- [ ] 至少 12 个测试用例
- [ ] 所有测试通过
- [ ] 测试覆盖率 ≥ 80%

### 实际运行

- [ ] 可以调优 1 个策略的入场阈值
- [ ] 可以调优 1 个策略的因子权重
- [ ] Sharpe 提升 ≥ 0.2

---

## 📝 实施步骤

### 步骤 1：验证 TradeOptimizer（只读）

```bash
# 1. 检查类是否存在
grep -n "class TradeOptimizer" services/decision/src/research/trade_optimizer.py

# 2. 检查 optimize 方法
grep -n "def optimize" services/decision/src/research/trade_optimizer.py

# 3. 检查参数搜索空间
grep -n "search_space" services/decision/src/research/trade_optimizer.py
```

### 步骤 2：补充缺失功能（如果需要）

```python
# services/decision/src/research/trade_optimizer.py
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Optional
from itertools import product

from .sandbox_engine import SandboxEngine


class TradeOptimizer:
    """策略参数调优工具 — 网格搜索"""
    
    def __init__(self, data_service_url: str = "http://localhost:8105"):
        self.sandbox = SandboxEngine(data_service_url)
    
    async def optimize(
        self,
        strategy_path: str,
        search_space: dict[str, list[Any]],
        objective: str = "sharpe_ratio",
        start_date: str = "2024-01-01",
        end_date: str = "2025-12-31",
    ) -> dict[str, Any]:
        """参数调优 — 网格搜索
        
        Args:
            strategy_path: 策略 YAML 文件路径
            search_space: 参数搜索空间
            objective: 优化目标（sharpe_ratio/max_drawdown/win_rate）
            start_date: 回测开始日期
            end_date: 回测结束日期
        
        Returns:
            优化结果（最优参数、优化前后对比）
        """
        # 实现逻辑...
```

### 步骤 3：编写测试

```python
# services/decision/tests/test_trade_optimizer.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.research.trade_optimizer import TradeOptimizer


@pytest.fixture
def optimizer():
    return TradeOptimizer()


@pytest.mark.asyncio
async def test_optimize_entry_threshold(optimizer):
    """测试入场阈值调优"""
    # 实现测试...


@pytest.mark.asyncio
async def test_optimize_factor_weights(optimizer):
    """测试因子权重调优"""
    # 实现测试...
```

### 步骤 4：运行调优示例

```bash
# 在 Studio 上执行
cd ~/jbt/services/decision
source .venv/bin/activate

# 调优示例
python -c "
import asyncio
from src.research.trade_optimizer import TradeOptimizer

async def main():
    optimizer = TradeOptimizer()
    
    result = await optimizer.optimize(
        strategy_path='参考文件/因子策略库/入库标准化/oilseed/p/STRAT_p_trend_60m_001.yaml',
        search_space={
            'entry_threshold': [0.50, 0.55, 0.60, 0.65, 0.70],
        },
        objective='sharpe_ratio',
    )
    
    print(f'最优参数：{result[\"best_params\"]}')
    print(f'Sharpe 提升：{result[\"improvement\"]}')

asyncio.run(main())
"
```

---

## 🎯 交付物

1. **验证报告**：
   - TradeOptimizer 类验证结果
   - 支持的参数类型
   - 支持的优化算法

2. **代码文件**（如果需要补充）：
   - `services/decision/src/research/trade_optimizer.py`
   - `services/decision/tests/test_trade_optimizer.py`

3. **调优示例**：
   - 1 个入场阈值调优示例
   - 1 个因子权重调优示例

---

## 📅 时间估算

- **验证 TradeOptimizer**：1 小时
- **补充缺失功能**：2 小时（如果需要）
- **测试编写**：1 小时
- **调优示例**：1 小时
- **总计**：5 小时

---

**签名**：Livis Claude  
**日期**：2026-04-16  
**状态**：待预审
