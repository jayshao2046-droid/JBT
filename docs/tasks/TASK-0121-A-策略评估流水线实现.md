# TASK-0121-A：策略评估流水线实现

【任务ID】TASK-0121-A  
【父任务】TASK-0121  
【执行人】待分配（Claude Code / Atlas）  
【创建时间】2026-04-16  
【优先级】P0  
【状态】待预审

---

## 📋 任务目标

实现 StrategyEvaluator 类，集成回测引擎、PBO 验证器、因子验证器，完成策略完整评估流水线。

---

## 🎯 核心功能

### 1. 策略评估（evaluate_strategy）

**输入**：
- 策略 YAML 文件路径
- 回测时间范围（start_date, end_date）

**输出**：
- 综合评分（0-100）
- 等级（S/A/B/C/D）
- 各维度得分（基础合规/回测/PBO/因子/风控）
- 详细报告（JSON 格式）

### 2. 五阶段评估流程

**阶段 1：基础合规性检查（30 分）**
- 因子权重和 = 1.0（10 分）
- 阈值合理性（10 分）
- 风控参数完整性（10 分）

**阶段 2：回测评估（30 分）**
- Sharpe Ratio（10 分）
- 最大回撤（10 分）
- 胜率（10 分）

**阶段 3：PBO 过拟合检测（10 分）**
- PBO < 0.3（10 分）
- PBO < 0.5（6 分）
- PBO < 0.7（3 分）

**阶段 4：因子有效性验证（10 分）**
- IC IR ≥ 0.3（10 分）
- IC IR ≥ 0.2（6 分）
- IC IR ≥ 0.1（3 分）

**阶段 5：风控严格度评估（20 分）**
- 回撤阈值（7 分）
- 日亏损限制（7 分）
- 单品种熔断（6 分）

### 3. 风控加分/扣分

**加分项（最多 +10 分）**：
- 单品种仓位 ≤ 5%（+3）
- 日亏损限制 ≤ 0.3%（+3）
- 单品种熔断 ≤ 0.5%（+2）
- 最大回撤熔断 ≤ 1.5%（+2）

**扣分项（最多 -20 分）**：
- 单品种仓位 > 15%（-10）
- 日亏损限制 > 1.0%（-5）
- 单品种熔断 > 1.5%（-3）
- 最大回撤熔断 > 3.0%（-2）

---

## 📁 文件清单（白名单）

### 新建文件

1. **services/decision/src/research/strategy_evaluator.py**
   - StrategyEvaluator 类
   - evaluate_strategy 方法
   - 五阶段评估逻辑
   - 评分计算逻辑
   - 报告生成逻辑

2. **services/decision/tests/test_strategy_evaluator.py**
   - 基础合规性测试（5 个用例）
   - 回测评估测试（5 个用例）
   - PBO 验证测试（3 个用例）
   - 因子验证测试（3 个用例）
   - 风控评估测试（5 个用例）
   - 综合评分测试（5 个用例）

### 验证文件（只读）

3. **services/decision/src/research/sandbox_engine.py**
   - 验证 run_strategy_backtest 接口
   - 确认返回格式（metrics: sharpe_ratio, max_drawdown, win_rate）

4. **services/decision/src/research/pbo_validator.py**
   - 验证 validate 接口
   - 确认返回格式（pbo: float）

5. **services/decision/src/research/factor_validator.py**
   - 验证 validate 接口
   - 确认返回格式（ic_mean, ic_ir, ic_pvalue）

---

## 🔧 技术要求

### 代码规范

- Python 3.9+ 兼容
- 使用 `Optional[T]` 而非 `T | None`
- 所有公共方法有 docstring
- 所有异常有明确的错误信息

### 测试要求

- 测试覆盖率 ≥ 80%
- 所有测试用例独立（不依赖外部服务）
- 使用 mock 模拟 SandboxEngine/PBOValidator/FactorValidator

### 性能要求

- 单个策略评估时间 < 5 分钟（取决于回测时间范围）
- 内存占用 < 2GB

---

## 📊 验收标准

### 功能完整性

- [ ] StrategyEvaluator 类实现完成
- [ ] 五阶段评估逻辑全部实现
- [ ] 评分计算逻辑正确
- [ ] 报告生成逻辑完整

### 测试通过

- [ ] 至少 26 个测试用例
- [ ] 所有测试通过
- [ ] 测试覆盖率 ≥ 80%

### 接口验证

- [ ] SandboxEngine 接口验证通过
- [ ] PBOValidator 接口验证通过
- [ ] FactorValidator 接口验证通过

---

## 🚨 风险提示

1. **SandboxEngine 接口不兼容**
   - 风险：接口签名或返回格式与预期不符
   - 应对：先验证接口，再实现 StrategyEvaluator

2. **PBOValidator 未实现**
   - 风险：PBOValidator 可能只是 STUB
   - 应对：验证实现，如果是 STUB 则降级为警告

3. **FactorValidator 未实现**
   - 风险：FactorValidator 可能只是 STUB
   - 应对：验证实现，如果是 STUB 则降级为警告

---

## 📝 实施步骤

### 步骤 1：验证依赖工具（只读）

```bash
# 1. 验证 SandboxEngine
grep -n "class SandboxEngine" services/decision/src/research/sandbox_engine.py
grep -n "def run_strategy_backtest" services/decision/src/research/sandbox_engine.py

# 2. 验证 PBOValidator
grep -n "class PBOValidator" services/decision/src/research/pbo_validator.py
grep -n "def validate" services/decision/src/research/pbo_validator.py

# 3. 验证 FactorValidator
grep -n "class FactorValidator" services/decision/src/research/factor_validator.py
grep -n "def validate" services/decision/src/research/factor_validator.py
```

### 步骤 2：实现 StrategyEvaluator

```python
# services/decision/src/research/strategy_evaluator.py
from __future__ import annotations

import yaml
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from .sandbox_engine import SandboxEngine
from .pbo_validator import PBOValidator
from .factor_validator import FactorValidator


class StrategyEvaluator:
    """策略完整评估流水线 — 2026-04-16 新标准"""
    
    def __init__(self, data_service_url: str = "http://localhost:8105"):
        self.sandbox = SandboxEngine(data_service_url)
        self.pbo_validator = PBOValidator()
        self.factor_validator = FactorValidator()
    
    async def evaluate_strategy(
        self,
        strategy_path: str,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """完整评估单个策略
        
        Args:
            strategy_path: 策略 YAML 文件路径
            start_date: 回测开始日期（YYYY-MM-DD）
            end_date: 回测结束日期（YYYY-MM-DD）
        
        Returns:
            评估报告（JSON 格式）
        """
        # 实现逻辑...
```

### 步骤 3：编写测试

```python
# services/decision/tests/test_strategy_evaluator.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.research.strategy_evaluator import StrategyEvaluator


@pytest.fixture
def evaluator():
    return StrategyEvaluator()


@pytest.mark.asyncio
async def test_basic_compliance_pass(evaluator):
    """测试基础合规性检查 - 通过"""
    # 实现测试...


@pytest.mark.asyncio
async def test_backtest_evaluation_high_sharpe(evaluator):
    """测试回测评估 - 高 Sharpe"""
    # 实现测试...
```

### 步骤 4：集成测试

```bash
# 运行测试
cd services/decision
pytest tests/test_strategy_evaluator.py -v

# 检查覆盖率
pytest tests/test_strategy_evaluator.py --cov=src/research/strategy_evaluator --cov-report=term-missing
```

---

## 🎯 交付物

1. **代码文件**：
   - `services/decision/src/research/strategy_evaluator.py`
   - `services/decision/tests/test_strategy_evaluator.py`

2. **测试报告**：
   - 测试用例数量
   - 测试通过率
   - 测试覆盖率

3. **接口验证报告**：
   - SandboxEngine 接口验证结果
   - PBOValidator 接口验证结果
   - FactorValidator 接口验证结果

---

## 📅 时间估算

- **接口验证**：1 小时
- **StrategyEvaluator 实现**：4 小时
- **测试编写**：2 小时
- **集成测试**：1 小时
- **总计**：8 小时

---

**签名**：Livis Claude  
**日期**：2026-04-16  
**状态**：待预审
