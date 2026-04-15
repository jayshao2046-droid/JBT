"""报告格式化器 - 生成 JSON 和 Markdown 格式

职责：
1. 格式化 JSON 报告
2. 格式化 Markdown 报告
"""
import json
from typing import Dict
from datetime import datetime


class ReportFormatter:
    """报告格式化器"""

    @staticmethod
    def to_json(report: Dict) -> str:
        """转换为 JSON 格式"""
        return json.dumps(report, ensure_ascii=False, indent=2)

    @staticmethod
    def to_markdown(report: Dict) -> str:
        """转换为 Markdown 格式"""
        md = f"""# 研究员报告

**报告ID**: {report.get('report_id')}
**时段**: {report.get('segment')}
**生成时间**: {report.get('generated_at')}
**模型**: {report.get('model')}

---

## 期货市场概述

{report.get('futures_summary', {}).get('market_overview', '暂无数据')}

**覆盖品种数**: {report.get('futures_summary', {}).get('symbols_covered', 0)}

---

## 股票市场概述

{report.get('stocks_summary', {}).get('market_overview', '暂无数据')}

**覆盖品种数**: {report.get('stocks_summary', {}).get('symbols_covered', 0)}

---

## 爬虫统计

- **采集源数量**: {report.get('crawler_stats', {}).get('sources_crawled', 0)}
- **处理文章数**: {report.get('crawler_stats', {}).get('articles_processed', 0)}
- **失败源**: {', '.join(report.get('crawler_stats', {}).get('failed_sources', [])) or '无'}

---

*报告由 qwen3:14b 自动生成*
"""
        return md

    @staticmethod
    def save_to_file(report: Dict, output_dir: str = "/data/researcher/reports"):
        """保存报告到文件"""
        from pathlib import Path

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        report_id = report.get('report_id', 'unknown')

        # 保存 JSON
        json_path = output_path / f"{report_id}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(ReportFormatter.to_json(report))

        # 保存 Markdown
        md_path = output_path / f"{report_id}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(ReportFormatter.to_markdown(report))

        return str(json_path), str(md_path)
