"""Prompt 模板"""

# /no_think 指令用于关闭 qwen3 系列的 <think>...</think> 长推理段，
# 配合 OLLAMA_NUM_PREDICT 把单条推理压到 token 上限内。
NO_THINK_DIRECTIVE = "/no_think"

KLINE_ANALYSIS_PROMPT = """/no_think
分析以下期货品种的K线走势：
品种：{symbol}
涨跌幅：{change_pct:.2f}%
请简要分析原因和后续走势。
"""

NEWS_ANALYSIS_PROMPT = """/no_think
分析以下期货新闻：
标题：{title}
请判断影响的品种和利多利空。
"""

# F1（2026-04-24）— 两段式管线第一段：小模型快速打分
# 输出严格控制在单行 JSON，避免 7B 模型胡乱发散
NEWS_PREFILTER_PROMPT = """/no_think
你是期货市场新闻预筛选器。判断以下新闻对中国期货市场（35 个主流品种：螺纹 热卷 铜 铝 锌 金 银 橡胶 不锈钢 纸浆 铁矿 豆粕 PP PVC LLDPE 玉米 鸡蛋 豆油 棕榈 豆一 焦煤 焦炭 苯乙烯 LPG 生猪 PTA 甲醇 棉花 白糖 菜油 菜粕 玻璃 纯碱 涤纶短纤 尿素）是否值得深度分析。

评分规则（0-10 整数）：
- 9-10：直接影响某品种价格的硬消息（政策/库存/供需突变/事故）
- 7-8：明显相关的宏观/上下游/突发事件
- 4-6：弱相关或重复转载
- 0-3：无关、广告、纯财经资讯

新闻标题：{title}
新闻内容：{content}

只输出一行 JSON，不要任何解释、不要 markdown：
{{"score":整数,"reason":"理由(20字内)"}}"""

