"""测试批量策略评估脚本 — TASK-0121-B

测试覆盖：
1. 批量评估功能
2. 并发控制
3. 报告生成
4. 错误处理
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import yaml

from batch_evaluate_strategies import BatchEvaluator


@pytest.fixture
def temp_dir():
    """创建临时目录。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_strategies(temp_dir):
    """创建示例策略文件。"""
    strategies_dir = temp_dir / 'strategies'
    strategies_dir.mkdir()

    # 创建 3 个策略文件
    for i in range(3):
        strategy = {
            'factors': {
                'momentum': {'weight': 0.5},
                'volatility': {'weight': 0.5},
            },
            'thresholds': {'long': 0.6, 'short': -0.6},
            'risk_control': {
                'max_position_per_symbol': 0.05,
                'daily_loss_limit_yuan': 2500,
                'per_symbol_fuse_yuan': 5000,
                'max_drawdown_pct': 0.015,
            },
        }
        strategy_file = strategies_dir / f'strategy_{i+1}.yaml'
        strategy_file.write_text(yaml.dump(strategy), encoding='utf-8')

    return list(strategies_dir.glob('*.yaml'))


@pytest.fixture
def mock_evaluation_results():
    """模拟评估结果。"""
    return [
        {
            'strategy_file': 'strategy_1.yaml',
            'grade': 'S',
            'final_score': 95,
            'stages': {
                'basic_compliance': {'score': 30},
                'backtest': {'score': 30},
                'pbo': {'score': 10},
                'factor': {'score': 10},
                'risk': {'score': 15},
            },
            'conclusion': {'can_deploy': True},
        },
        {
            'strategy_file': 'strategy_2.yaml',
            'grade': 'A',
            'final_score': 85,
            'stages': {
                'basic_compliance': {'score': 30},
                'backtest': {'score': 25},
                'pbo': {'score': 8},
                'factor': {'score': 8},
                'risk': {'score': 14},
            },
            'conclusion': {'can_deploy': True},
        },
        {
            'strategy_file': 'strategy_3.yaml',
            'grade': 'B',
            'final_score': 75,
            'stages': {
                'basic_compliance': {'score': 30},
                'backtest': {'score': 20},
                'pbo': {'score': 6},
                'factor': {'score': 6},
                'risk': {'score': 13},
            },
            'conclusion': {'can_deploy': False},
        },
    ]


# =============================================================================
# 1. 批量评估功能测试
# =============================================================================

@pytest.mark.asyncio
async def test_evaluate_strategies_success(sample_strategies, mock_evaluation_results):
    """测试批量评估 - 成功。"""
    evaluator = BatchEvaluator(concurrency=2)

    with patch.object(
        evaluator.evaluator, 'evaluate_strategy', new_callable=AsyncMock
    ) as mock_eval:
        mock_eval.side_effect = mock_evaluation_results

        results = await evaluator.evaluate_strategies(
            sample_strategies, '2024-01-01', '2024-12-31'
        )

    assert len(results) == 3
    assert results[0]['grade'] == 'S'
    assert results[1]['grade'] == 'A'
    assert results[2]['grade'] == 'B'


@pytest.mark.asyncio
async def test_evaluate_strategies_with_failure(sample_strategies):
    """测试批量评估 - 部分失败。"""
    evaluator = BatchEvaluator(concurrency=2)

    async def mock_evaluate(strategy_file, start_date, end_date):
        if 'strategy_2' in strategy_file:
            raise Exception('回测数据不足')
        return {
            'strategy_file': Path(strategy_file).name,
            'grade': 'A',
            'final_score': 85,
        }

    with patch.object(
        evaluator.evaluator, 'evaluate_strategy', new_callable=AsyncMock
    ) as mock_eval:
        mock_eval.side_effect = mock_evaluate

        results = await evaluator.evaluate_strategies(
            sample_strategies, '2024-01-01', '2024-12-31'
        )

    assert len(results) == 3
    # 检查失败的策略
    failed = [r for r in results if r['grade'] == 'F']
    assert len(failed) == 1
    assert 'error' in failed[0]


@pytest.mark.asyncio
async def test_evaluate_strategies_concurrency(sample_strategies):
    """测试并发控制。"""
    evaluator = BatchEvaluator(concurrency=1)  # 限制并发为 1

    call_times = []

    async def mock_evaluate(strategy_file, start_date, end_date):
        import asyncio
        call_times.append(asyncio.get_event_loop().time())
        await asyncio.sleep(0.1)  # 模拟耗时操作
        return {
            'strategy_file': Path(strategy_file).name,
            'grade': 'A',
            'final_score': 85,
        }

    with patch.object(
        evaluator.evaluator, 'evaluate_strategy', new_callable=AsyncMock
    ) as mock_eval:
        mock_eval.side_effect = mock_evaluate

        await evaluator.evaluate_strategies(
            sample_strategies, '2024-01-01', '2024-12-31'
        )

    # 验证调用是串行的（时间间隔 >= 0.1s）
    assert len(call_times) == 3
    for i in range(1, len(call_times)):
        assert call_times[i] - call_times[i-1] >= 0.09  # 允许小误差


# =============================================================================
# 2. 报告生成测试
# =============================================================================

def test_generate_summary_report(temp_dir, mock_evaluation_results):
    """测试汇总报告生成。"""
    evaluator = BatchEvaluator()
    evaluator.results = mock_evaluation_results

    output_file = temp_dir / 'summary.md'
    evaluator.generate_summary_report(output_file)

    assert output_file.exists()
    content = output_file.read_text(encoding='utf-8')

    # 验证报告内容
    assert '策略批量评估报告' in content
    assert '等级分布' in content
    assert 'S 级策略' in content
    assert 'A 级策略' in content
    assert 'B 级策略' in content
    assert 'strategy_1.yaml' in content
    assert 'strategy_2.yaml' in content
    assert 'strategy_3.yaml' in content


def test_generate_summary_report_with_failures(temp_dir):
    """测试汇总报告生成 - 包含失败。"""
    evaluator = BatchEvaluator()
    evaluator.results = [
        {
            'strategy_file': 'strategy_1.yaml',
            'grade': 'S',
            'final_score': 95,
            'stages': {},
            'conclusion': {'can_deploy': True},
        },
        {
            'strategy_file': 'strategy_2.yaml',
            'grade': 'F',
            'final_score': 0,
            'error': '回测数据不足',
        },
    ]

    output_file = temp_dir / 'summary.md'
    evaluator.generate_summary_report(output_file)

    content = output_file.read_text(encoding='utf-8')
    assert '评估失败' in content
    assert '回测数据不足' in content


def test_format_strategy_summary():
    """测试策略摘要格式化。"""
    evaluator = BatchEvaluator()
    result = {
        'strategy_file': 'test_strategy.yaml',
        'grade': 'A',
        'final_score': 85,
        'stages': {
            'basic_compliance': {'score': 30},
            'backtest': {'score': 25},
            'pbo': {'score': 8},
            'factor': {'score': 8},
            'risk': {'score': 14},
        },
        'conclusion': {'can_deploy': True},
    }

    lines = evaluator._format_strategy_summary(result)
    text = '\n'.join(lines)

    assert 'test_strategy.yaml' in text
    assert '等级**: A' in text
    assert '总分**: 85' in text
    assert '基础合规**: 30/30' in text
    assert '回测表现**: 25/30' in text
    assert '可上线' in text


def test_save_detailed_reports(temp_dir, mock_evaluation_results):
    """测试详细报告保存。"""
    evaluator = BatchEvaluator()
    evaluator.results = mock_evaluation_results

    with patch.object(
        evaluator.evaluator, 'generate_markdown_report'
    ) as mock_gen:
        mock_gen.return_value = '# 详细报告\n\n测试内容'

        output_dir = temp_dir / 'details'
        evaluator.save_detailed_reports(output_dir)

    assert output_dir.exists()
    assert (output_dir / 'strategy_1.yaml.md').exists()
    assert (output_dir / 'strategy_2.yaml.md').exists()
    assert (output_dir / 'strategy_3.yaml.md').exists()


# =============================================================================
# 3. 等级分布测试
# =============================================================================

def test_grade_distribution_all_grades(temp_dir):
    """测试等级分布 - 所有等级。"""
    evaluator = BatchEvaluator()
    evaluator.results = [
        {'strategy_file': 's1.yaml', 'grade': 'S', 'final_score': 95},
        {'strategy_file': 's2.yaml', 'grade': 'A', 'final_score': 85},
        {'strategy_file': 's3.yaml', 'grade': 'B', 'final_score': 75},
        {'strategy_file': 's4.yaml', 'grade': 'C', 'final_score': 65},
        {'strategy_file': 's5.yaml', 'grade': 'D', 'final_score': 55},
        {'strategy_file': 's6.yaml', 'grade': 'F', 'final_score': 0, 'error': 'test'},
    ]

    output_file = temp_dir / 'summary.md'
    evaluator.generate_summary_report(output_file)

    content = output_file.read_text(encoding='utf-8')
    assert '| S | 1 | 16.7% |' in content
    assert '| A | 1 | 16.7% |' in content
    assert '| B | 1 | 16.7% |' in content
    assert '| C | 1 | 16.7% |' in content
    assert '| D | 1 | 16.7% |' in content
    assert '| F | 1 | 16.7% |' in content


def test_grade_distribution_empty(temp_dir):
    """测试等级分布 - 空结果。"""
    evaluator = BatchEvaluator()
    evaluator.results = []

    output_file = temp_dir / 'summary.md'
    evaluator.generate_summary_report(output_file)

    content = output_file.read_text(encoding='utf-8')
    assert '策略总数**: 0' in content
    assert '平均分数**: 0.0' in content


def test_grade_distribution_many_strategies(temp_dir):
    """测试等级分布 - 大量策略。"""
    evaluator = BatchEvaluator()
    # 创建 10 个 S 级策略
    evaluator.results = [
        {'strategy_file': f's{i}.yaml', 'grade': 'S', 'final_score': 95}
        for i in range(10)
    ]

    output_file = temp_dir / 'summary.md'
    evaluator.generate_summary_report(output_file)

    content = output_file.read_text(encoding='utf-8')
    # 验证只显示前 5 个，其余用 ... 表示
    assert '... (+5)' in content


# =============================================================================
# 4. 边界条件测试
# =============================================================================

@pytest.mark.asyncio
async def test_evaluate_empty_list():
    """测试空策略列表。"""
    evaluator = BatchEvaluator()
    results = await evaluator.evaluate_strategies([], '2024-01-01', '2024-12-31')
    assert results == []


def test_generate_report_no_results(temp_dir):
    """测试无结果时生成报告。"""
    evaluator = BatchEvaluator()
    evaluator.results = []

    output_file = temp_dir / 'summary.md'
    evaluator.generate_summary_report(output_file)

    assert output_file.exists()
    content = output_file.read_text(encoding='utf-8')
    assert '策略总数**: 0' in content


@pytest.mark.asyncio
async def test_evaluate_with_invalid_date():
    """测试无效日期。"""
    evaluator = BatchEvaluator()

    with patch.object(
        evaluator.evaluator, 'evaluate_strategy', new_callable=AsyncMock
    ) as mock_eval:
        mock_eval.side_effect = ValueError('Invalid date format')

        results = await evaluator.evaluate_strategies(
            [Path('test.yaml')], 'invalid-date', '2024-12-31'
        )

    assert len(results) == 1
    assert results[0]['grade'] == 'F'
    assert 'error' in results[0]
