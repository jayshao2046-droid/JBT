# TASK-0113 Claude 派工单 — 数据研究员通知规范化 + 国际采集源

| 字段 | 值 |
|------|-----|
| 任务ID | TASK-0113 |
| 服务 | services/data |
| 执行 Agent | Claude-Code |
| 签发 | Atlas (2026-04-15) |
| 关联 | TASK-0110 (数据研究员子系统) |
| 预审 | REVIEW-TASK-0113 |

---

## 一、任务总览

对 `services/data/` 下已有的数据研究员子系统做 5 项增强：

1. **飞书通知三类分流**：报告→资讯(blue)，失败→报警(orange)，突发→紧急(red)
2. **飞书每小时推送**：工作时间内每整点执行一次研究，精炼飞书卡片（有标题、有结果、有研判）
3. **邮件只收日报**：每天两封（早报+晚报），内容详尽全中文，**必须包含信息来源和重大策略建议**
4. **国际采集源**：新增 7 个国际期货/宏观资讯源 + 解析器
5. **数据推送 Mini**：每次研究完成后，将报告 JSON 推送到 Mini data API (`http://192.168.31.76:8105`)，供 Studio 决策端消费

---

## 二、现有代码结构（只读参考）

```
services/data/
├── configs/
│   └── researcher_sources.yaml          # 采集源配置（当前 6 个国内源）
├── src/researcher/
│   ├── __init__.py
│   ├── config.py                        # 全局配置
│   ├── scheduler.py                     # 四段调度器
│   ├── staging.py                       # 暂存区管理
│   ├── summarizer.py                    # LLM 归纳器
│   ├── reporter.py                      # 双格式报告生成
│   ├── models.py                        # Pydantic 模型
│   ├── notifier.py                      # 飞书直发通知器
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── engine.py                    # 双模式爬虫引擎
│   │   ├── anti_detect.py               # 反检测
│   │   ├── source_registry.py           # 采集源注册表
│   │   └── parsers/
│   │       ├── __init__.py              # 解析器注册表
│   │       ├── futures.py               # 国内期货解析器（6 个）
│   │       └── generic.py               # 通用解析器
│   └── notify/
│       ├── __init__.py
│       ├── card_templates.py            # 飞书卡片 + 邮件 HTML 模板
│       ├── daily_digest.py              # 每日日报生成器
│       ├── feishu_sender.py             # 独立飞书发送器
│       └── email_sender.py             # 独立邮件发送器
└── tests/
    ├── test_researcher_notify.py
    ├── test_researcher_crawler.py
    ├── test_researcher_scheduler.py
    ├── test_researcher_staging.py
    └── test_researcher_reporter.py
```

---

## 三、调度模型（从四段改为每小时）

### 重大变更：废弃原有"四段制"，改为"每工作小时"

原设计的四段（盘前 08:30 / 午间 11:35 / 盘后 15:20 / 夜盘 23:10）**全部废弃**。

新调度：

| 时段 | cron | 说明 |
|------|------|------|
| 08:00 | `0 8 * * 1-5` | 开盘前准备 |
| 09:00 | `0 9 * * 1-5` | 开盘首小时 |
| 10:00 | `0 10 * * 1-5` | |
| 11:00 | `0 11 * * 1-5` | |
| 13:00 | `0 13 * * 1-5` | 午盘开盘 |
| 14:00 | `0 14 * * 1-5` | |
| 15:00 | `0 15 * * 1-5` | 收盘 |
| 16:00 | `0 16 * * 1-5` | 盘后总结 |
| 21:00 | `0 21 * * 1-5` | 夜盘开盘 |
| 22:00 | `0 22 * * 1-5` | |
| 23:00 | `0 23 * * 1-5` | 夜盘收盘 |

共 **11 个整点**，每次执行完飞书推一条精炼卡片。

### 邮件日报触发时机

| 邮件 | 触发 | 汇总范围 |
|------|------|---------|
| 早报 | 16:00 执行完成后 | 08:00~16:00 全部报告 |
| 晚报 | 23:00 执行完成后 | 21:00~23:00 全部报告 |

### 数据推送 Mini

每次研究完成后（每整点），调用 Mini data API：
```
POST http://192.168.31.76:8105/api/v1/researcher/reports
Content-Type: application/json
Body: ResearchReport.dict()
```
- 如果 Mini API 不可达，记录本地日志，不影响飞书推送
- 决策端 (Studio 192.168.31.142) 通过 data API 读取研究报告

---

## 四、飞书通知设计（三类分流）

### 规则：报警归报警，资讯归资讯，突发单推

| 卡片类型 | 飞书 template | 图标 | 标题格式 | 触发时机 |
|---------|-------------|------|---------|---------|
| 研究报告（资讯） | `blue` | 📈 | `📈 [JBT 数据研究员-{HH}:00] {date}` | 每整点研究完成 |
| 执行失败（报警） | `orange` | ⚠️ | `⚠️ [JBT 数据研究员-报警] 执行失败` | 爬虫/LLM 出错 |
| 突发紧急（P0报警） | `red` | 🚨 | `🚨ᤩ [JBT 数据研究员-紧急] {headline}` | 爬虫发现重大突发 |

### 飞书研究报告卡片（精炼版 — 每小时推送）

**原则：精炼、信息量充足、有标题有结果有研判**

```
msg_type: "interactive"
card:
  header:
    title: "📈 [JBT 数据研究员-{HH}:00] {date}"
    template: "blue"
  elements:
    - tag: div (lark_md)
      content: |
        **期货研判**
        🔴 偏空: rb(螺纹) -1.2%, i(铁矿) -0.8%
        🟢 偏多: au(黄金) +0.5%, ag(白银) +0.3%
        ⚪ 震荡: cu(铜), al(铝)

    - tag: hr

    - tag: div (lark_md)
      content: |
        **要闻摘要**
        • 金十: 美联储维持利率不变，美元指数承压
        • 东财: 螺纹钢社会库存大幅下降
        • Reuters: 原油库存低于预期

    - tag: hr

    - tag: div (lark_md)
      content: |
        **综合研判**
        黑色系短期偏弱，关注库存拐点；贵金属受降息预期支撑偏强

    - tag: hr

    - tag: note
      content: "JBT 数据研究员 | {HH}:{MM} | 采集{N}源{M}篇 | Alienware"
```

**关键要求**：
1. **不要冗长**：每个品种一行，涨跌+趋势判断
2. **要闻不超过 5 条**：只挑最重要的
3. **必须有综合研判**：一段话总结当前市场方向
4. **footer 包含采集统计**：`采集{N}源{M}篇`

### 突发紧急卡片说明

- 当爬虫采集到明确包含突发关键词（如"紧急通知"、"暂停交易"、"重大政策"、"黑天鹅"等）的资讯时
- 不等段结束，**立即**单独推送一条 red 卡片
- 内容：`headline`（新闻标题） + `source`（来源） + `url`（原文链接） + `detected_at`（发现时间）
- 这是额外推送，不影响正常的段报告推送

---

## 五、邮件日报设计（早报 + 晚报）

### 规则：邮件只收日报，不收单次报告

| 邮件类型 | 发送时机 | 汇总范围 | 主题格式 |
|---------|---------|---------|---------|
| 早报 | 16:00 研究完成后 | 08:00~16:00 所有报告 | `[JBT 数据研究员] YYYY-MM-DD 早报` |
| 晚报 | 23:00 研究完成后 | 21:00~23:00 所有报告 | `[JBT 数据研究员] YYYY-MM-DD 晚报` |

### 邮件 HTML 结构（详尽版 — 必须有来源+重大策略）

```html
<div class="card">
  <div class="header" style="background:#2980b9">
    📈 [JBT 数据研究员] YYYY-MM-DD 早报/晚报
    <div class="sub">JBT 数据研究员 日报通知</div>
  </div>
  <div class="body">
    <!-- 一、市场总览 -->
    <p class="section-title">一、市场总览</p>
    <h4>期货市场</h4>
    <table>完整品种涨跌排名、趋势判断、关键因素、信心度</table>
    <h4>股票市场</h4>
    <table>完整品种涨跌排名、趋势判断</table>

    <!-- 二、信息来源与要闻（必须标注来源） -->
    <p class="section-title">二、信息来源与要闻</p>
    <table>
      <tr><th>来源</th><th>标题</th><th>摘要</th><th>时间</th></tr>
      <tr><td>金十数据</td><td>...</td><td>...</td><td>HH:MM</td></tr>
      <tr><td>Reuters</td><td>...</td><td>...</td><td>HH:MM</td></tr>
      <tr><td>CME Group</td><td>...</td><td>...</td><td>HH:MM</td></tr>
      ...全部列出，标注每条信息的采集源
    </table>

    <!-- 三、重大策略建议 -->
    <p class="section-title">三、重大策略建议</p>
    <ul>
      <li><b>黑色系</b>：库存拐点临近，螺纹钢短线偏弱但中期关注补库驱动...</li>
      <li><b>贵金属</b>：美联储鸽派信号明确，黄金维持偏多配置...</li>
      <li><b>能源化工</b>：原油受地缘支撑但需求端偏弱，建议观望...</li>
    </ul>

    <!-- 四、变化要点（与前次对比） -->
    <p class="section-title">四、变化要点</p>
    <ul>与前次报告对比的趋势翻转、异常波动、重大新闻</ul>

    <!-- 五、采集统计 -->
    <p class="section-title">五、采集统计</p>
    <table>
      <tr><th>时段</th><th>采集源数</th><th>文章数</th><th>成功率</th><th>耗时</th></tr>
      <tr><td>08:00</td><td>13</td><td>42</td><td>100%</td><td>45s</td></tr>
      ...每个整点一行
    </table>
  </div>
  <div class="footer">JBT 数据研究员 | YYYY-MM-DD HH:MM:SS | Alienware</div>
</div>
```

### 内容要求

- **全中文**，不出现任何英文段落
- **详尽**：不是摘要，是完整分析。每个品种都要有涨跌、趋势、因素
- **必须有信息来源**：每条要闻标注从哪个采集源获取（金十/东财/Reuters/CME 等）
- **必须有重大策略建议**：按板块（黑色系/贵金属/能源化工/农产品等）给出研判方向
- 综合建议跨多个整点报告做对比分析
- 邮件只在早报/晚报时刻发送，不逐次发送

---

## 六、国际采集源（7 个新增）

### 源列表

| # | source_id | 名称 | URL | 模式 | 解析器 | 每整点均参与 | 优先级 | timeout |
|---|-----------|------|-----|------|--------|-------------|--------|---------|
| 1 | `cme_advisory` | CME Group 公告 | `https://www.cmegroup.com/market-data/advisories.html` | code | `cme_advisory` | ✅ | 7 | 60 |
| 2 | `kitco_gold` | Kitco 贵金属新闻 | `https://www.kitco.com/news/` | code | `kitco_gold` | ✅ | 7 | 30 |
| 3 | `oilprice_com` | OilPrice 能源资讯 | `https://oilprice.com/Latest-Energy-News/World-News` | code | `oilprice_com` | ✅ | 7 | 30 |
| 4 | `mining_com` | Mining.com 矿业 | `https://www.mining.com/news/` | code | `mining_com` | ✅ | 6 | 30 |
| 5 | `investing_commodities` | Investing.com 大宗商品 | `https://www.investing.com/news/commodities-news` | code | `investing_commodities` | ✅ | 8 | 60 |
| 6 | `fed_releases` | 美联储公告 | `https://www.federalreserve.gov/newsevents/pressreleases.htm` | code | `fed_releases` | ✅ | 6 | 30 |
| 7 | `reuters_commodities` | 路透社大宗商品 | `https://www.reuters.com/markets/commodities/` | code | `reuters_commodities` | ✅ | 8 | 60 |

**注意**：调度时段概念已废弃。所有源在每个整点均参与采集（YAML 中 `schedule` 字段改为 `["all"]`）。

### 解析器实现要点

每个解析器函数签名：`def parse_xxx(tree: lxml_html.HtmlElement, url: str) -> Dict[str, Any]`

返回：`{"title": str, "content": str, "published_at": datetime | None}`

| 解析器 | HTML 特征 |
|--------|----------|
| `cme_advisory` | CME 公告页，`div.advisory-list` 或 `table.advisory-table` |
| `kitco_gold` | Kitco 新闻列表，`div.article-list` + `h2 a` 标题 |
| `oilprice_com` | OilPrice 新闻列表，`div.categoryArticle` + `h2` 标题 |
| `mining_com` | Mining 新闻列表，`article.post` + `h2.entry-title` |
| `investing_commodities` | Investing 新闻，`article[data-test=article-item]` |
| `fed_releases` | 美联储公告，`div.row` + `a.ng-binding` 链接列表 |
| `reuters_commodities` | 路透社，反爬较强，尝试 `article` + `h3` 标题；失败时降级返回空 |

**注意**：所有国际源解析器必须有 `try/except` 包裹，解析失败时返回 `{"title": "XXX解析失败", "content": "", "published_at": None}` 而不是抛异常。这与国内源解析器（`futures.py`）的模式一致。

---

## 七、文件修改清单（4 批 13 文件）

### Batch A — 飞书通知三类分流（5 文件）

#### A1. `services/data/src/researcher/notifier.py` — MODIFY

改造点：
1. `_send_feishu_card()` 的 header template 从 `turquoise` 改为 `blue`
2. 标题图标从 `📊` 改为 `📈`
3. **标题格式改为小时制**：`📈 [JBT 数据研究员-{HH}:00] {date}`
4. **卡片内容改为精炼版**：
   - 期货研判：按偏多/偏空/震荡分组，每品种一行（品种名 + 涨跌%）
   - 要闻摘要：最多 5 条，标注来源
   - 综合研判：一段话总结当前市场方向
   - footer: `JBT 数据研究员 | {HH}:{MM} | 采集{N}源{M}篇 | Alienware`
5. 新增 `notify_urgent()` 方法：发送 `red` 模板的突发紧急卡片
6. `_send_feishu_alert()` 标题改为 `⚠️ [JBT 数据研究员-报警] 执行失败`

#### A2. `services/data/src/researcher/notify/card_templates.py` — MODIFY

改造点：
1. `build_report_card()`：template 改 `blue`，图标改 `📈`，标题改 `📈 [JBT 数据研究员-{HH}:00] {date}`，**精炼版内容**（研判+要闻+结论），加 note footer
2. `build_failure_card()`：标题改 `⚠️ [JBT 数据研究员-报警] 执行失败`，加 note footer
3. `build_daily_digest_card()`：template 保持 `blue`，标题改 `📈 [JBT 数据研究员-每日总结] {date}`，加 note footer
4. 新增 `build_urgent_card(headline, source, url, detected_at)` → `red` 模板 P0 卡片
5. `build_report_html()` 标题改为中文统一格式，加 footer
6. 新增 `build_morning_report_html(reports_list)` — 早报详尽 HTML（**必须有信息来源表+重大策略建议**）
7. 新增 `build_evening_report_html(reports_list)` — 晚报详尽 HTML（同上）

详尽邮件 HTML 要求：
- 完整品种涨跌排名表格（期货 + 股票）
- 爬虫要闻摘要列表
- 变化要点
- 综合建议
- 采集统计表
- 全中文
- footer: `JBT 数据研究员 | {timestamp} | Alienware`

#### A3. `services/data/src/researcher/notify/daily_digest.py` — MODIFY

改造点：
1. 保留 `generate_digest(date)` — 全天日报
2. 新增 `generate_morning_digest(date)` — 汇总 08:00~16:00 所有整点报告
3. 新增 `generate_evening_digest(date)` — 汇总 21:00~23:00 所有整点报告
4. 每种 digest 返回完整的 reports 列表 + 统计数据
5. **新增**：digest 中必须包含 `news_sources` 字段 — 所有要闻及其来源（供邮件来源表使用）
6. **新增**：digest 中必须包含 `strategy_suggestions` 字段 — 按板块汇总的重大策略建议

#### A4. `services/data/src/researcher/notify/email_sender.py` — MODIFY

改造点：
1. `send_html()` 中文主题前缀
2. 新增 `send_morning_report(date, html_content)` — 早报专用
3. 新增 `send_evening_report(date, html_content)` — 晚报专用

#### A5. `services/data/src/researcher/notify/__init__.py` — MODIFY

补充导出：`build_urgent_card`, `build_morning_report_html`, `build_evening_report_html`

### Batch B — 调度与配置（2 文件）

#### B1. `services/data/src/researcher/config.py` — MODIFY

改造点：**废弃原有四段 SEGMENTS，改为每工作小时调度**

```python
# 废弃原有 SEGMENTS dict
# 新调度：每工作小时整点
HOURLY_SCHEDULE = [
    {"hour": 8, "label": "08:00", "cron": "0 8 * * 1-5", "desc": "开盘前准备"},
    {"hour": 9, "label": "09:00", "cron": "0 9 * * 1-5", "desc": "开盘首小时"},
    {"hour": 10, "label": "10:00", "cron": "0 10 * * 1-5", "desc": ""},
    {"hour": 11, "label": "11:00", "cron": "0 11 * * 1-5", "desc": ""},
    {"hour": 13, "label": "13:00", "cron": "0 13 * * 1-5", "desc": "午盘开盘"},
    {"hour": 14, "label": "14:00", "cron": "0 14 * * 1-5", "desc": ""},
    {"hour": 15, "label": "15:00", "cron": "0 15 * * 1-5", "desc": "收盘"},
    {"hour": 16, "label": "16:00", "cron": "0 16 * * 1-5", "desc": "盘后总结"},
    {"hour": 21, "label": "21:00", "cron": "0 21 * * 1-5", "desc": "夜盘开盘"},
    {"hour": 22, "label": "22:00", "cron": "0 22 * * 1-5", "desc": ""},
    {"hour": 23, "label": "23:00", "cron": "0 23 * * 1-5", "desc": "夜盘收盘"},
]

# 邮件日报配置
EMAIL_MORNING_TRIGGER_HOUR = 16   # 16:00 研究完成后发早报
EMAIL_EVENING_TRIGGER_HOUR = 23   # 23:00 研究完成后发晚报
EMAIL_MORNING_HOURS = [8, 9, 10, 11, 13, 14, 15, 16]  # 早报汇总这些整点
EMAIL_EVENING_HOURS = [21, 22, 23]                      # 晚报汇总这些整点

# Mini data API 推送（研究报告推送到 Mini 供决策端消费）
DATA_API_PUSH_URL = os.getenv("DATA_API_URL", "http://192.168.31.76:8105") + "/api/v1/researcher/reports"

# 突发关键词（中文 + 英文）
URGENT_KEYWORDS = [
    "紧急通知", "暂停交易", "重大政策", "黑天鹅",
    "强制平仓", "交易所公告", "政策调整", "突发事件",
    "halt", "suspend", "emergency", "breaking",
]
```

保留原有 `SEGMENTS` dict 但标记为 `LEGACY`（向后兼容，避免已有测试断掉）。

#### B2. `services/data/src/researcher/scheduler.py` — MODIFY

**重大改造**：

1. **调度改为每小时**：
   - 废弃 `execute_segment(segment)` 的四段参数
   - 改为 `execute_hourly(hour: int)` — 参数是整点小时（8, 9, 10, ...）
   - `hour` 对应的 label 用 `f"{hour:02d}:00"` 格式
   - APScheduler 注册 11 个 cron job

2. **飞书推送（每次执行完立即推）**：
   - 调用 `notifier.notify_report_done(report)` 推精炼飞书卡片
   - 卡片标题用 `📈 [JBT 数据研究员-{HH}:00] {date}`

3. **邮件日报钩子**：
   - `hour == 16` 执行完后 → 生成早报 → 发早报邮件
   - `hour == 23` 执行完后 → 生成晚报 → 发晚报邮件

4. **突发检测**：
   - 爬虫采集阶段检查 `URGENT_KEYWORDS` 匹配
   - 命中 → 立即 `notifier.notify_urgent()` 单推 red 卡片

5. **数据推送 Mini**：
   - 每次研究完成后，`POST` 报告 JSON 到 `DATA_API_PUSH_URL`
   - 使用 `httpx.AsyncClient`，超时 10s
   - 失败只记日志，不影响飞书推送
   ```python
   async def _push_to_data_api(self, report: ResearchReport):
       """推送报告到 Mini data API，供决策端消费"""
       try:
           async with httpx.AsyncClient() as client:
               resp = await client.post(
                   ResearcherConfig.DATA_API_PUSH_URL,
                   json=report.dict(),
                   timeout=10.0
               )
               # 记录推送结果
       except Exception:
           pass  # 推送失败不影响主流程
   ```

### Batch C — 国际采集源（3 文件）

#### C1. `services/data/configs/researcher_sources.yaml` — MODIFY

在现有 6 个国内源之后追加 7 个国际源（见上表）。

#### C2. `services/data/src/researcher/crawler/parsers/international.py` — NEW

新建文件，实现 7 个解析器函数：
- `parse_cme_advisory(tree, url)`
- `parse_kitco_gold(tree, url)`
- `parse_oilprice_com(tree, url)`
- `parse_mining_com(tree, url)`
- `parse_investing_commodities(tree, url)`
- `parse_fed_releases(tree, url)`
- `parse_reuters_commodities(tree, url)`

每个函数：
1. `try/except` 包裹全部逻辑
2. 失败返回 `{"title": "XX解析失败", "content": "", "published_at": None}`
3. 使用 lxml xpath 提取
4. 国际源可能有不同的 HTML 结构，做多路选择器（类似 `futures.py` 的写法）

#### C3. `services/data/src/researcher/crawler/parsers/__init__.py` — MODIFY

在 `PARSER_REGISTRY` 中注册 7 个国际解析器：
```python
from .international import (
    parse_cme_advisory,
    parse_kitco_gold,
    parse_oilprice_com,
    parse_mining_com,
    parse_investing_commodities,
    parse_fed_releases,
    parse_reuters_commodities,
)

# 追加到 PARSER_REGISTRY
"cme_advisory": parse_cme_advisory,
"kitco_gold": parse_kitco_gold,
"oilprice_com": parse_oilprice_com,
"mining_com": parse_mining_com,
"investing_commodities": parse_investing_commodities,
"fed_releases": parse_fed_releases,
"reuters_commodities": parse_reuters_commodities,
```

### Batch D — 测试（3 文件）

#### D1. `services/data/tests/test_researcher_international.py` — NEW

测试 7 个国际解析器：
- 每个解析器用**模拟 HTML 片段**测试（不做真实网络请求）
- 验证返回格式正确（包含 title, content, published_at）
- 验证异常输入时不抛异常

#### D2. `services/data/tests/test_researcher_daily_mail.py` — NEW

测试早报/晚报：
- `test_morning_digest_covers_two_segments` — 早报只汇总盘前+午间
- `test_evening_digest_covers_two_segments` — 晚报只汇总盘后+夜盘
- `test_morning_html_is_chinese` — 早报 HTML 全中文
- `test_evening_html_is_chinese` — 晚报 HTML 全中文
- `test_morning_html_contains_sections` — 早报包含完整四个板块

#### D3. `services/data/tests/test_researcher_card_blue.py` — NEW

测试卡片三类分流：
- `test_report_card_is_blue` — 研究报告卡片用 blue 模板
- `test_report_card_icon_is_info` — 图标是 📈 不是 📊
- `test_failure_card_is_orange` — 失败卡片用 orange
- `test_urgent_card_is_red` — 突发卡片用 red
- `test_all_cards_have_footer` — 所有卡片都有 note footer
- `test_urgent_card_has_headline` — 突发卡片包含 headline + source + url

---

## 八、验收标准

1. `cd /Users/jayshao/JBT && python3 -m pytest services/data/tests/test_researcher_international.py services/data/tests/test_researcher_daily_mail.py services/data/tests/test_researcher_card_blue.py -v` **全部通过**
2. 已有测试不回归：`python3 -m pytest services/data/tests/test_researcher_*.py -v` **全部通过**
3. 飞书卡片用 `blue` 模板发资讯、`orange` 发报警、`red` 发突发
4. 飞书卡片精炼：有研判、有要闻、有结论，不冗长
5. 邮件 HTML 详尽、全中文、**必须包含信息来源表和重大策略建议**
6. 国际源解析器 try/except 包裹，不影响主流程
7. `parsers/__init__.py` 中 `PARSER_REGISTRY` 包含全部 13 个解析器（6国内+7国际）
8. `researcher_sources.yaml` 包含 6+7=13 个源
9. `config.py` 包含 11 个整点调度定义
10. `scheduler.py` 每次执行完后 POST 报告到 Mini data API

---

## 九、约束

1. **全中文**：所有卡片标题、邮件内容、日报内容均为中文
2. **不改模型层**：`summarizer.py`、`reporter.py`、`models.py` 不做修改
3. **不改爬虫引擎**：`engine.py`、`anti_detect.py`、`source_registry.py` 不做修改
4. **不改暂存区**：`staging.py` 不做修改
5. **不跨服务**：所有修改限于 `services/data/`
6. 国际源解析器全部放在 `parsers/international.py` 一个文件中（与 `futures.py` 平行）
7. 邮件只在早报/晚报时刻发送（16:00 后 + 23:00 后），不逐次发送
8. 突发紧急飞书推送不等整点结束，立即发送
9. 飞书推送每整点一次，精炼不冗长
10. Mini data API 推送失败只记日志，不阻塞飞书推送
