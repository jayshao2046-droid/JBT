# TASK-0121-B：批量评估脚本实现

【任务ID】TASK-0121-B  
【父任务】TASK-0121  
【执行人】待分配（Claude Code / Atlas）  
【创建时间】2026-04-16  
【优先级】P0  
【状态】待预审  
【依赖】TASK-0121-A 完成

---

## 📋 任务目标

实现批量评估脚本，使用 StrategyEvaluator 评估所有策略，生成 Markdown 格式报告。

---

## 🎯 核心功能

### 1. 批量评估（batch_evaluate_strategies.py）

**功能**：
- 遍历策略目录（`参考文件/因子策略库/入库标准化/oilseed/p/`）
- 调用 StrategyEvaluator 评估每个策略
- 生成 Markdown 格式报告
- 保存到输出目录

**输入**：
- 策略目录路径
- 回测时间范围
- 输出目录路径

**输出**：
- 每个策略的评估报告（Markdown）
- 汇总报告（评分分布、等级分布）

### 2. Markdown 报告格式

```markdown
# STRAT_p_trend_60m_002 策略评估报告

## 综合评分：87/100 (A 级)

### 1. 基础合规性（28/30）
- 因子权重和：1.0 ✅
- 阈值合理性：0.60/-0.60 ✅
- 风控参数完整性：完整 ✅

### 2. 回测表现（26/30）
- Sharpe Ratio：2.8 ✅
- 最大回撤：1.2% ✅
- 胜率：58% ✅

### 3. PBO 过拟合检测（8/10）
- PBO：0.35（中等风险）⚠️

### 4. 因子有效性（9/10）
- IC IR：0.28 ✅

### 5. 风控严格度（18/20）
- 回撤阈值：1.5% ✅
- 日亏损限制：0.5% ✅
- 单品种熔断：1.0% ✅

## 风控调整
- 加分：+8
- 扣分：-0

## 生产准入建议
- ✅ 可上线
- 优先级：高
- 建议：降低 PBO 风险，增加样本外验证

---
生成时间：2026-04-16 10:30:00
```

### 3. 汇总报告

```markdown
# 棕榈油策略批量评估汇总报告

## 评估概况

- 总策略数：25
- 评估时间：2024-01-01 ~ 2025-12-31
- 生成时间：2026-04-16 10:30:00

## 评分分布

| 等级 | 分数范围 | 数量 | 占比 |
|------|---------|------|------|
| S 级 | 90-100 | 2 | 8% |
| A 级 | 80-89 | 6 | 24% |
| B 级 | 70-79 | 9 | 36% |
| C 级 | 60-69 | 6 | 24% |
| D 级 | < 60 | 2 | 8% |

## 平均指标

- 平均 Sharpe Ratio：2.1
- 平均最大回撤：2.3%
- 平均胜率：52%
- 平均 PBO：0.42

## 可上线策略（S/A 级）

1. STRAT_p_trend_60m_002（87 分，A 级）
2. STRAT_p_trend_60m_005（92 分，S 级）
...

## 需优化策略（B/C/D 级）

1. STRAT_p_trend_60m_001（58 分，D 级）- 最大回撤过大
2. STRAT_p_trend_60m_003（65 分，C 级）- Sharpe 不足
...
```

---

## 📁 文件清单（白名单）

### 新建文件

1. **services/decision/batch_evaluate_strategies.py**
   - 批量评估主脚本
   - 遍历策略目录
   - 调用 StrategyEvaluator
   - 生成 Markdown 报告
   - 生成汇总报告

2. **services/decision/tests/test_batch_evaluate.py**
   - 批量评估测试（3 个用例）
   - Markdown 生成测试（3 个用例）
   - 汇总报告测试（2 个用例）

### 依赖文件（只读）

3. **services/decision/src/research/strategy_evaluator.py**
   - 依赖 TASK-0121-A

---

## 🔧 技术要求

### 代码规范

- Python 3.9+ 兼容
- 使用 `pathlib.Path` 处理文件路径
- 使用 `asyncio` 处理异步评估
- 所有异常有明确的错误信息

### 性能要求

- 支持并行评估（可选）
- 单个策略失败不影响其他策略
- 进度显示（已评估 X/25）

---

## 📊 验收标准

### 功能完整性

- [ ] 批量评估脚本实现完成
- [ ] Markdown 报告生成正确
- [ ] 汇总报告生成正确
- [ ] 错误处理完善

### 测试通过

- [ ] 至少 8 个测试用例
- [ ] 所有测试通过

### 实际运行

- [ ] 可以评估 25 个棕榈油策略
- [ ] 生成 25 个 Markdown 报告
- [ ] 生成 1 个汇总报告

---

## 📝 实施步骤

### 步骤 1：实现批量评估脚本

```python
# services/decision/batch_evaluate_strategies.py
"""批量评估策略脚本 — 2026-04-16"""
import asyncio
from pathlib import Path
from datetime import datetime
from src.research.strategy_evaluator import StrategyEvaluator


async def main():
    evaluator = StrategyEvaluator()
    
    # 策略目录
    strategy_dir = Path("参考文件/因子策略库/入库标准化/oilseed/p")
    
    # 回测时间范围
    start_date = "2024-01-01"
    end_date = "2025-12-31"
    
    # 输出目录
    output_dir = Path("../../docs/handoffs/TASK-0121-棕榈油策略评估报告-新标准")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # 遍历所有策略
    results = []
    for i, strategy_file in enumerate(strategy_dir.rglob("*.yaml"), 1):
        print(f"[{i}/25] 评估策略：{strategy_file.name}")
        
        try:
            # 评估
            report = await evaluator.evaluate_strategy(
                strategy_path=str(strategy_file),
                start_date=start_date,
                end_date=end_date,
            )
            
            # 生成报告
            md_report = generate_markdown_report(report)
            
            # 保存
            output_file = output_dir / f"{strategy_file.stem}-评估报告.md"
            output_file.write_text(md_report, encoding='utf-8')
            
            print(f"  评分：{report['final_score']}/100 ({report['grade']} 级)")
            
            results.append(report)
            
        except Exception as e:
            print(f"  评估失败：{e}")
    
    # 生成汇总报告
    summary_report = generate_summary_report(results)
    summary_file = output_dir / "汇总报告.md"
    summary_file.write_text(summary_report, encoding='utf-8')
    
    print(f"\n批量评估完成！共评估 {len(results)} 个策略")


def generate_markdown_report(report: dict) -> str:
    """生成 Markdown 格式报告"""
    # 实现逻辑...


def generate_summary_report(results: list[dict]) -> str:
    """生成汇总报告"""
    # 实现逻辑...


if __name__ == "__main__":
    asyncio.run(main())
```

### 步骤 2：编写测试

```python
# services/decision/tests/test_batch_evaluate.py
import pytest
from pathlib import Path
from batch_evaluate_strategies import generate_markdown_report, generate_summary_report


def test_generate_markdown_report():
    """测试 Markdown 报告生成"""
    # 实现测试...


def test_generate_summary_report():
    """测试汇总报告生成"""
    # 实现测试...
```

### 步骤 3：运行批量评估

```bash
# 在 Studio 上执行
cd ~/JBT/services/decision
source .venv/bin/activate
python batch_evaluate_strategies.py
```

---

## 🎯 交付物

1. **代码文件**：
   - `services/decision/batch_evaluate_strategies.py`
   - `services/decision/tests/test_batch_evaluate.py`

2. **评估报告**：
   - 25 个策略的 Markdown 报告
   - 1 个汇总报告

3. **执行日志**：
   - 评估过程日志
   - 错误日志（如果有）

---

## 📅 时间估算

- **脚本实现**：2 小时
- **测试编写**：1 小时
- **实际运行**：2-4 小时（取决于回测速度）
- **总计**：5-7 小时

---

**签名**：Livis Claude  
**日期**：2026-04-16  
**状态**：待预审
