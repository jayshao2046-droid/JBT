#!/usr/bin/env python3
"""批量策略评估脚本 — TASK-0121-B

功能：
1. 批量读取策略配置文件
2. 并发执行策略评估
3. 生成汇总报告（Markdown）
4. 按等级分类策略

使用方式：
    python batch_evaluate_strategies.py \
        --strategies-dir configs/strategies/palm_oil \
        --start-date 2024-01-01 \
        --end-date 2024-12-31 \
        --output reports/palm_oil_evaluation.md \
        --concurrency 5
"""
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import yaml

from src.research.strategy_evaluator import StrategyEvaluator


class BatchEvaluator:
    """批量策略评估器。"""

    def __init__(self, concurrency: int = 5):
        """初始化批量评估器。

        Args:
            concurrency: 并发评估数量
        """
        self.evaluator = StrategyEvaluator()
        self.concurrency = concurrency
        self.results: List[Dict[str, Any]] = []

    async def evaluate_strategies(
        self,
        strategy_files: List[Path],
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """批量评估策略。

        Args:
            strategy_files: 策略文件路径列表
            start_date: 回测开始日期
            end_date: 回测结束日期

        Returns:
            评估结果列表
        """
        semaphore = asyncio.Semaphore(self.concurrency)

        async def evaluate_one(strategy_file: Path) -> Dict[str, Any]:
            async with semaphore:
                try:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 评估策略: {strategy_file.name}")
                    report = await self.evaluator.evaluate_strategy(
                        str(strategy_file), start_date, end_date
                    )
                    report['strategy_file'] = strategy_file.name
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ {strategy_file.name} - {report['grade']} 级 ({report['final_score']}分)")
                    return report
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ {strategy_file.name} - 评估失败: {e}")
                    return {
                        'strategy_file': strategy_file.name,
                        'grade': 'F',
                        'final_score': 0,
                        'error': str(e),
                    }

        tasks = [evaluate_one(f) for f in strategy_files]
        self.results = await asyncio.gather(*tasks)
        return self.results

    def generate_summary_report(self, output_file: Path) -> None:
        """生成汇总报告。

        Args:
            output_file: 输出文件路径
        """
        # 按等级分类
        grade_groups = {'S': [], 'A': [], 'B': [], 'C': [], 'D': [], 'F': []}
        for result in self.results:
            grade = result.get('grade', 'F')
            grade_groups[grade].append(result)

        # 统计信息
        total = len(self.results)
        avg_score = sum(r.get('final_score', 0) for r in self.results) / total if total > 0 else 0

        # 生成 Markdown 报告
        lines = [
            '# 策略批量评估报告',
            '',
            f'**评估时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f'**策略总数**: {total}',
            f'**平均分数**: {avg_score:.1f}',
            '',
            '---',
            '',
            '## 📊 等级分布',
            '',
            '| 等级 | 数量 | 占比 | 策略列表 |',
            '|------|------|------|----------|',
        ]

        for grade in ['S', 'A', 'B', 'C', 'D', 'F']:
            count = len(grade_groups[grade])
            percentage = (count / total * 100) if total > 0 else 0
            strategies = ', '.join(r['strategy_file'] for r in grade_groups[grade][:5])
            if count > 5:
                strategies += f' ... (+{count - 5})'
            lines.append(f'| {grade} | {count} | {percentage:.1f}% | {strategies} |')

        lines.extend([
            '',
            '---',
            '',
            '## 🏆 S 级策略（可直接上线）',
            '',
        ])

        if grade_groups['S']:
            for result in grade_groups['S']:
                lines.extend(self._format_strategy_summary(result))
        else:
            lines.append('*暂无 S 级策略*')

        lines.extend([
            '',
            '---',
            '',
            '## ⭐ A 级策略（小幅调整后上线）',
            '',
        ])

        if grade_groups['A']:
            for result in grade_groups['A']:
                lines.extend(self._format_strategy_summary(result))
        else:
            lines.append('*暂无 A 级策略*')

        lines.extend([
            '',
            '---',
            '',
            '## 📋 B 级策略（需要调优）',
            '',
        ])

        if grade_groups['B']:
            for result in grade_groups['B']:
                lines.extend(self._format_strategy_summary(result))
        else:
            lines.append('*暂无 B 级策略*')

        lines.extend([
            '',
            '---',
            '',
            '## ⚠️ C/D 级策略（需要重构）',
            '',
        ])

        low_grade = grade_groups['C'] + grade_groups['D']
        if low_grade:
            for result in low_grade:
                lines.extend(self._format_strategy_summary(result))
        else:
            lines.append('*暂无 C/D 级策略*')

        lines.extend([
            '',
            '---',
            '',
            '## ❌ 评估失败',
            '',
        ])

        if grade_groups['F']:
            for result in grade_groups['F']:
                error = result.get('error', '未知错误')
                lines.append(f"- **{result['strategy_file']}**: {error}")
        else:
            lines.append('*无失败策略*')

        lines.extend([
            '',
            '---',
            '',
            '## 📈 详细评估报告',
            '',
            '每个策略的详细评估报告已保存至：',
            '',
        ])

        for result in self.results:
            if result.get('grade') != 'F':
                detail_file = output_file.parent / f"{result['strategy_file']}.md"
                lines.append(f"- [{result['strategy_file']}]({detail_file.name})")

        # 写入文件
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text('\n'.join(lines), encoding='utf-8')
        print(f"\n✓ 汇总报告已生成: {output_file}")

    def _format_strategy_summary(self, result: Dict[str, Any]) -> List[str]:
        """格式化策略摘要。

        Args:
            result: 评估结果

        Returns:
            Markdown 行列表
        """
        lines = [
            f"### {result['strategy_file']}",
            '',
            f"- **等级**: {result['grade']}",
            f"- **总分**: {result['final_score']:.1f}",
        ]

        if 'stages' in result:
            stages = result['stages']
            lines.append(f"- **基础合规**: {stages.get('basic_compliance', {}).get('score', 0)}/30")
            lines.append(f"- **回测表现**: {stages.get('backtest', {}).get('score', 0)}/30")
            lines.append(f"- **PBO 验证**: {stages.get('pbo', {}).get('score', 0)}/10")
            lines.append(f"- **因子验证**: {stages.get('factor', {}).get('score', 0)}/10")
            lines.append(f"- **风控评分**: {stages.get('risk', {}).get('score', 0)}/20")

        if 'conclusion' in result:
            conclusion = result['conclusion']
            can_deploy = '✓ 可上线' if conclusion.get('can_deploy') else '✗ 不可上线'
            lines.append(f"- **部署建议**: {can_deploy}")

        lines.append('')
        return lines

    def save_detailed_reports(self, output_dir: Path) -> None:
        """保存详细评估报告。

        Args:
            output_dir: 输出目录
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        for result in self.results:
            if result.get('grade') == 'F':
                continue

            detail_file = output_dir / f"{result['strategy_file']}.md"
            md_report = self.evaluator.generate_markdown_report(result)
            detail_file.write_text(md_report, encoding='utf-8')

        print(f"✓ 详细报告已保存至: {output_dir}")


async def main():
    """主函数。"""
    parser = argparse.ArgumentParser(description='批量策略评估脚本')
    parser.add_argument(
        '--strategies-dir',
        type=Path,
        required=True,
        help='策略配置文件目录',
    )
    parser.add_argument(
        '--start-date',
        type=str,
        required=True,
        help='回测开始日期 (YYYY-MM-DD)',
    )
    parser.add_argument(
        '--end-date',
        type=str,
        required=True,
        help='回测结束日期 (YYYY-MM-DD)',
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('reports/batch_evaluation.md'),
        help='输出报告路径',
    )
    parser.add_argument(
        '--concurrency',
        type=int,
        default=5,
        help='并发评估数量',
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.yaml',
        help='策略文件匹配模式',
    )

    args = parser.parse_args()

    # 查找策略文件
    strategy_files = list(args.strategies_dir.glob(args.pattern))
    if not strategy_files:
        print(f"错误: 在 {args.strategies_dir} 中未找到匹配 {args.pattern} 的策略文件")
        return

    print(f"找到 {len(strategy_files)} 个策略文件")
    print(f"回测区间: {args.start_date} ~ {args.end_date}")
    print(f"并发数量: {args.concurrency}")
    print()

    # 批量评估
    evaluator = BatchEvaluator(concurrency=args.concurrency)
    await evaluator.evaluate_strategies(strategy_files, args.start_date, args.end_date)

    # 生成报告
    evaluator.generate_summary_report(args.output)
    evaluator.save_detailed_reports(args.output.parent / 'details')

    print()
    print("=" * 60)
    print("批量评估完成！")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
