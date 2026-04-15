"""Prompt 模板"""

KLINE_ANALYSIS_PROMPT = """
分析以下期货品种的K线走势：
品种：{symbol}
涨跌幅：{change_pct:.2f}%
请简要分析原因和后续走势。
"""

NEWS_ANALYSIS_PROMPT = """
分析以下期货新闻：
标题：{title}
请判断影响的品种和利多利空。
"""
