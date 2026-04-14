"""研究员专用飞书卡片和邮件 HTML 模板"""

from typing import Dict, Any, List
from datetime import datetime


def build_report_card(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    构建研究报告完成卡片（blue 模板 - 资讯类，精炼版）

    Args:
        report: ResearchReport.dict()

    Returns:
        飞书卡片 JSON
    """
    # 提取小时（用于标题）
    hour = report.get('hour', '00')

    # 构建精炼的期货研判（按偏多/偏空/震荡分组）
    futures_brief = _build_futures_brief(report.get('futures_summary', {}))

    # 构建要闻摘要（最多5条，标注来源）
    news_brief = _build_news_brief(report.get('crawler_stats', {}))

    # 综合研判
    market_view = report.get('futures_summary', {}).get('market_overview', '市场平稳运行')

    # 采集统计
    sources_count = report['crawler_stats'].get('sources_crawled', 0)
    articles_count = report['crawler_stats'].get('articles_processed', 0)

    card = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"📈 [JBT 数据研究员-{hour}:00] {report['date']}"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**期货研判**\n{futures_brief}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**要闻摘要**\n{news_brief}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**综合研判**\n{market_view}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"JBT 数据研究员 | {hour}:{report.get('minute', '00')} | 采集{sources_count}源{articles_count}篇 | Alienware"
                        }
                    ]
                }
            ]
        }
    }

    return card


def _build_futures_brief(futures_summary: Dict[str, Any]) -> str:
    """构建精炼的期货研判（按偏多/偏空/震荡分组）"""
    symbols = futures_summary.get('symbols', {})

    bullish = []
    bearish = []
    neutral = []

    for sym, detail in symbols.items():
        trend = detail.get('trend', '震荡')
        change_pct = detail.get('change_pct', 0.0)

        # 简化品种名（去掉交易所前缀）
        sym_short = sym.split('@')[-1].split('.')[-1] if '@' in sym else sym

        if '偏多' in trend or '上涨' in trend:
            bullish.append(f"{sym_short} +{change_pct:.1f}%")
        elif '偏空' in trend or '下跌' in trend:
            bearish.append(f"{sym_short} {change_pct:.1f}%")
        else:
            neutral.append(sym_short)

    lines = []
    if bearish:
        lines.append(f"🔴 偏空: {', '.join(bearish[:5])}")
    if bullish:
        lines.append(f"🟢 偏多: {', '.join(bullish[:5])}")
    if neutral:
        lines.append(f"⚪ 震荡: {', '.join(neutral[:5])}")

    return '\n'.join(lines) if lines else '市场平稳'


def _build_news_brief(crawler_stats: Dict[str, Any]) -> str:
    """构建要闻摘要（最多5条，标注来源）"""
    # TODO: 从 crawler_stats 中提取实际新闻
    # 当前版本返回占位符
    news_items = crawler_stats.get('news_items', [])

    if not news_items:
        return '• 暂无重要资讯'

    lines = []
    for item in news_items[:5]:
        source = item.get('source', '未知')
        title = item.get('title', '')
        lines.append(f"• {source}: {title}")

    return '\n'.join(lines)


def build_failure_card(hour: str, error: str) -> Dict[str, Any]:
    """
    构建研究报告失败卡片（orange 模板 - 报警类）

    Args:
        hour: 小时（如 "08"）
        error: 错误信息

    Returns:
        飞书卡片 JSON
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"⚠️ [JBT 数据研究员-报警] 执行失败"
                },
                "template": "orange"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**时段**: {hour}:00\n**错误**: {error}\n**时间**: {timestamp}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"JBT 数据研究员 | {timestamp} | Alienware"
                        }
                    ]
                }
            ]
        }
    }


def build_urgent_card(headline: str, source: str, url: str, detected_at: str) -> Dict[str, Any]:
    """
    构建突发紧急卡片（red 模板 - P0报警）

    Args:
        headline: 新闻标题
        source: 来源
        url: 原文链接
        detected_at: 发现时间

    Returns:
        飞书卡片 JSON
    """
    return {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"🚨 [JBT 数据研究员-紧急] {headline[:30]}..."
                },
                "template": "red"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**标题**: {headline}\n**来源**: {source}\n**链接**: {url}\n**发现时间**: {detected_at}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"JBT 数据研究员 | 突发紧急 | Alienware"
                        }
                    ]
                }
            ]
        }
    }


def build_daily_digest_card(digest: Dict[str, Any]) -> Dict[str, Any]:
    """
    构建每日日报卡片（blue 模板）

    Args:
        digest: 日报数据

    Returns:
        飞书卡片 JSON
    """
    return {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"📈 [JBT 数据研究员-每日总结] {digest['date']}"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**执行概况**\n- 成功: {digest['success_count']}/{digest['total_count']}\n- 总耗时: {digest['total_elapsed']:.1f}秒"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**分析统计**\n- 期货品种: {digest['futures_total']}\n- 股票: {digest['stocks_total']}\n- 爬虫文章: {digest['articles_total']}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**关键建议**\n" + "\n".join([f"- {s}" for s in digest.get('suggestions', [])])
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"JBT 数据研究员 | {digest['date']} | Alienware"
                        }
                    ]
                }
            ]
        }
    }


def build_report_html(report: Dict[str, Any]) -> str:
    """
    构建研究报告 HTML 邮件

    Args:
        report: ResearchReport.dict()

    Returns:
        HTML 字符串
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #20B2AA; color: white; padding: 20px; border-radius: 5px; }}
            .section {{ margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 5px; }}
            .section h3 {{ margin-top: 0; color: #20B2AA; }}
            .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
            .stat-item {{ text-align: center; }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #20B2AA; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📊 研究员报告 — {report['date']} {report['segment']}</h2>
                <p>报告ID: {report['report_id']} | 生成时间: {report['generated_at']}</p>
            </div>

            <div class="section">
                <h3>期货市场</h3>
                <p>{report['futures_summary'].get('market_overview', '')}</p>
            </div>

            <div class="section">
                <h3>股票市场</h3>
                <p>{report['stocks_summary'].get('market_overview', '')}</p>
            </div>

            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value">{report['crawler_stats'].get('sources_crawled', 0)}</div>
                    <div>采集源数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{report['crawler_stats'].get('articles_processed', 0)}</div>
                    <div>文章数</div>
                </div>
            </div>

            {"<div class='section'><h3>变化要点</h3><ul>" + "".join([f"<li>{c}</li>" for c in report.get('change_highlights', [])]) + "</ul></div>" if report.get('change_highlights') else ""}
        </div>
    </body>
    </html>
    """
    return html


def build_daily_digest_html(digest: Dict[str, Any]) -> str:
    """
    构建每日日报 HTML 邮件

    Args:
        digest: 日报数据

    Returns:
        HTML 字符串
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #4169E1; color: white; padding: 20px; border-radius: 5px; }}
            .section {{ margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 5px; }}
            .footer {{ text-align: center; color: #666; margin-top: 30px; padding: 15px; border-top: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📅 研究员每日日报 — {digest['date']}</h2>
            </div>

            <div class="section">
                <h3>执行概况</h3>
                <p>成功: {digest['success_count']}/{digest['total_count']} | 总耗时: {digest['total_elapsed']:.1f}秒</p>
            </div>

            <div class="section">
                <h3>分析统计</h3>
                <p>期货品种: {digest['futures_total']} | 股票: {digest['stocks_total']} | 爬虫文章: {digest['articles_total']}</p>
            </div>

            <div class="section">
                <h3>关键建议</h3>
                <ul>
                    {"".join([f"<li>{s}</li>" for s in digest.get('suggestions', [])])}
                </ul>
            </div>

            <div class="footer">
                JBT 数据研究员 | {digest['date']} | Alienware
            </div>
        </div>
    </body>
    </html>
    """
    return html


def build_morning_report_html(reports: List[Dict[str, Any]], date: str) -> str:
    """
    构建早报 HTML（详尽版 - 必须有信息来源+重大策略建议）

    Args:
        reports: 08:00~16:00 所有报告列表
        date: 日期 YYYY-MM-DD

    Returns:
        HTML 字符串
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 汇总期货市场数据
    futures_table = _build_futures_table(reports)

    # 汇总信息来源与要闻
    news_table = _build_news_table(reports)

    # 重大策略建议
    strategy_suggestions = _build_strategy_suggestions(reports)

    # 变化要点
    change_highlights = _build_change_highlights(reports)

    # 采集统计
    stats_table = _build_stats_table(reports)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #2980b9; color: white; padding: 20px; border-radius: 5px; }}
            .sub {{ font-size: 14px; margin-top: 5px; opacity: 0.9; }}
            .section-title {{ font-size: 18px; font-weight: bold; color: #2980b9; margin: 25px 0 10px 0; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background: #f0f0f0; font-weight: bold; }}
            .footer {{ text-align: center; color: #666; margin-top: 30px; padding: 15px; border-top: 1px solid #ddd; }}
            ul {{ margin: 10px 0; padding-left: 25px; }}
            li {{ margin: 8px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📈 [JBT 数据研究员] {date} 早报</h2>
                <div class="sub">JBT 数据研究员 日报通知</div>
            </div>

            <p class="section-title">一、市场总览</p>
            <h4>期货市场</h4>
            {futures_table}

            <p class="section-title">二、信息来源与要闻</p>
            {news_table}

            <p class="section-title">三、重大策略建议</p>
            {strategy_suggestions}

            <p class="section-title">四、变化要点</p>
            {change_highlights}

            <p class="section-title">五、采集统计</p>
            {stats_table}

            <div class="footer">
                JBT 数据研究员 | {timestamp} | Alienware
            </div>
        </div>
    </body>
    </html>
    """
    return html


def build_evening_report_html(reports: List[Dict[str, Any]], date: str) -> str:
    """
    构建晚报 HTML（详尽版 - 必须有信息来源+重大策略建议）

    Args:
        reports: 21:00~23:00 所有报告列表
        date: 日期 YYYY-MM-DD

    Returns:
        HTML 字符串
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 汇总期货市场数据
    futures_table = _build_futures_table(reports)

    # 汇总信息来源与要闻
    news_table = _build_news_table(reports)

    # 重大策略建议
    strategy_suggestions = _build_strategy_suggestions(reports)

    # 变化要点
    change_highlights = _build_change_highlights(reports)

    # 采集统计
    stats_table = _build_stats_table(reports)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #2980b9; color: white; padding: 20px; border-radius: 5px; }}
            .sub {{ font-size: 14px; margin-top: 5px; opacity: 0.9; }}
            .section-title {{ font-size: 18px; font-weight: bold; color: #2980b9; margin: 25px 0 10px 0; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background: #f0f0f0; font-weight: bold; }}
            .footer {{ text-align: center; color: #666; margin-top: 30px; padding: 15px; border-top: 1px solid #ddd; }}
            ul {{ margin: 10px 0; padding-left: 25px; }}
            li {{ margin: 8px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📈 [JBT 数据研究员] {date} 晚报</h2>
                <div class="sub">JBT 数据研究员 日报通知</div>
            </div>

            <p class="section-title">一、市场总览</p>
            <h4>期货市场</h4>
            {futures_table}

            <p class="section-title">二、信息来源与要闻</p>
            {news_table}

            <p class="section-title">三、重大策略建议</p>
            {strategy_suggestions}

            <p class="section-title">四、变化要点</p>
            {change_highlights}

            <p class="section-title">五、采集统计</p>
            {stats_table}

            <div class="footer">
                JBT 数据研究员 | {timestamp} | Alienware
            </div>
        </div>
    </body>
    </html>
    """
    return html


def _build_futures_table(reports: List[Dict[str, Any]]) -> str:
    """构建期货市场表格"""
    # 汇总所有品种
    all_symbols = {}
    for report in reports:
        symbols = report.get('futures_summary', {}).get('symbols', {})
        for sym, detail in symbols.items():
            if sym not in all_symbols:
                all_symbols[sym] = detail

    if not all_symbols:
        return '<p>暂无期货数据</p>'

    rows = []
    for sym, detail in list(all_symbols.items())[:20]:  # 最多20个品种
        sym_short = sym.split('@')[-1].split('.')[-1] if '@' in sym else sym
        trend = detail.get('trend', '震荡')
        change_pct = detail.get('change_pct', 0.0)
        confidence = detail.get('confidence', 0.5)
        rows.append(f"<tr><td>{sym_short}</td><td>{change_pct:+.2f}%</td><td>{trend}</td><td>{confidence:.0%}</td></tr>")

    return f"""
    <table>
        <tr><th>品种</th><th>涨跌</th><th>趋势判断</th><th>信心度</th></tr>
        {''.join(rows)}
    </table>
    """


def _build_news_table(reports: List[Dict[str, Any]]) -> str:
    """构建信息来源与要闻表格"""
    # 汇总所有新闻
    all_news = []
    for report in reports:
        news_items = report.get('crawler_stats', {}).get('news_items', [])
        all_news.extend(news_items)

    if not all_news:
        return '<p>暂无资讯数据</p>'

    rows = []
    for item in all_news[:15]:  # 最多15条
        source = item.get('source', '未知')
        title = item.get('title', '')
        summary = item.get('summary', '')[:50]  # 摘要截断
        time_str = item.get('time', '')
        rows.append(f"<tr><td>{source}</td><td>{title}</td><td>{summary}</td><td>{time_str}</td></tr>")

    return f"""
    <table>
        <tr><th>来源</th><th>标题</th><th>摘要</th><th>时间</th></tr>
        {''.join(rows)}
    </table>
    """


def _build_strategy_suggestions(reports: List[Dict[str, Any]]) -> str:
    """构建重大策略建议"""
    # TODO: 从报告中提取策略建议
    # 当前版本返回占位符
    suggestions = [
        "<li><b>黑色系</b>：库存拐点临近，螺纹钢短线偏弱但中期关注补库驱动</li>",
        "<li><b>贵金属</b>：美联储鸽派信号明确，黄金维持偏多配置</li>",
        "<li><b>能源化工</b>：原油受地缘支撑但需求端偏弱，建议观望</li>",
    ]
    return f"<ul>{''.join(suggestions)}</ul>"


def _build_change_highlights(reports: List[Dict[str, Any]]) -> str:
    """构建变化要点"""
    all_changes = []
    for report in reports:
        all_changes.extend(report.get('change_highlights', []))

    if not all_changes:
        return '<p>无重大变化</p>'

    return f"<ul>{''.join([f'<li>{c}</li>' for c in all_changes[:10]])}</ul>"


def _build_stats_table(reports: List[Dict[str, Any]]) -> str:
    """构建采集统计表格"""
    rows = []
    for report in reports:
        hour = report.get('hour', '00')
        sources = report.get('crawler_stats', {}).get('sources_crawled', 0)
        articles = report.get('crawler_stats', {}).get('articles_processed', 0)
        elapsed = report.get('elapsed_seconds', 0)
        success_rate = '100%' if sources > 0 else '0%'
        rows.append(f"<tr><td>{hour}:00</td><td>{sources}</td><td>{articles}</td><td>{success_rate}</td><td>{elapsed:.0f}s</td></tr>")

    return f"""
    <table>
        <tr><th>时段</th><th>采集源数</th><th>文章数</th><th>成功率</th><th>耗时</th></tr>
        {''.join(rows)}
    </table>
    """
