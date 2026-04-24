# TASK-P1-20260424F3 — Decision macro 评分识别 source_report.data_coverage

## 任务类型
- P1 标准流程
- 服务归属：services/decision
- 母任务（评估溯源）：2026-04-24 Atlas researcher 24h 只读评估
- 当前状态：待项目架构师预审 → 待 Jay.S 文件级 Token 签发
- 执行设备：MacBook 改代码 → rsync 同步 Studio → 重启 decision 服务

## 根因
`researcher_qwen3_scorer.py` 中 `_normalize_report` 函数只提取：
- `futures_summary.symbols_covered`
- `stocks_summary.symbols_covered`
- `crawler_stats.news_items`

对于 `report_type == "macro"` 的宏观报告，所有真实数据都存在 `source_report.data_coverage` 里（采集自 Mini）：
```
macro: 140, news_api: 140, rss: 100, sentiment: 70,
weather: 105, options: 70, position: 70, futures_minute: 83
```

但 `_normalize_report` 完全忽略了这个字段，导致 `observed_content` 传给 LLM 时显示：
```
类型=macro;期货品种=0;股票数量=0;新闻条数=0;紧急新闻=0
```

LLM 看到"全 0"打出 25 分。实际上这是一份数据覆盖极为丰富的报告。

## 改动范围（极小）
`_normalize_report` 函数中，在 macro 分支增加 `data_coverage` 的提取和格式化：

```python
# ── macro 报告：从 source_report.data_coverage 提取真实覆盖数据 ──
if report_type == "macro":
    source_report = report.get("source_report") or {}
    data_coverage = source_report.get("data_coverage") or {}
    if data_coverage:
        coverage_parts = [f"{k}={v}" for k, v in data_coverage.items() if v]
        observed_parts.append("数据覆盖=" + ",".join(coverage_parts))
    # 提取宏观 LLM 分析字段（若有）
    macro_analysis = source_report.get("analysis") or {}
    if macro_analysis.get("macro_trend"):
        observed_parts.append(f"宏观趋势={macro_analysis['macro_trend']}")
    if macro_analysis.get("risk_level"):
        observed_parts.append(f"风险等级={macro_analysis['risk_level']}")
    key_drivers = macro_analysis.get("key_drivers") or []
    if key_drivers:
        observed_parts.append(f"驱动因子={'/'.join(key_drivers[:3])}")
```

效果：LLM 收到的 `observed_content` 变为：
```
类型=macro;期货品种=0;股票数量=0;新闻条数=0;紧急新闻=0;
数据覆盖=macro=140,news_api=140,rss=100,sentiment=70,weather=105,options=70,position=70,futures_minute=83;
宏观趋势=震荡;风险等级=medium;驱动因子=美元偏弱/国内宏观政策/大宗商品需求回暖
```

打分预期从 25 → 70+（数据覆盖极厚 + 有趋势判断）

## 冻结白名单（仅 1 文件）
1. `services/decision/src/llm/researcher_qwen3_scorer.py`

## 明确排除
1. `services/decision/src/research/research_store.py` — 不改存储结构
2. `services/decision/src/api/routes/research_query.py` — 不改查询接口
3. `shared/contracts/**`
4. 任何 data 服务、Mini 上的文件
5. `runtime/**`、`logs/**`、真实 `.env`

## 验收标准
1. 改完后在 Studio 重启 decision，向 `/api/v1/research/facts/latest` 查询 intelligence 组，`score` 字段 ≥ 60（基线 25）。
2. `fact_record.observed_content` 中包含 `数据覆盖=` 字段。
3. 其余 data / sentiment 组的 fact score 不受影响（只改了 macro 分支）。
4. decision 日志无新增 ERROR。

## 建议最小验证
```bash
# 1. 语法检查
python -m py_compile services/decision/src/llm/researcher_qwen3_scorer.py

# 2. Studio 重启 decision 服务
ssh jaybot@192.168.31.142 'docker restart JBT-DECISION-8104'

# 3. 等 researcher 推送一次新宏观报告（或手动触发评分）
curl http://192.168.31.142:8104/api/v1/research/facts/latest/intelligence | python3 -m json.tool | grep -E "score|observed_content|data_coverage"
```

## 执行责任
- 实施 Agent：`决策`
- 复核：Atlas → 项目架构师终审 → Lockback → rsync 同步 Studio → docker restart

## 与 F2 的关系
- F3 完全在 decision 服务，与 F2（data 服务）**无交集，可并行执行**
- 建议 F3 与 F2 同时提预审、同时签 Token，各自独立实施
