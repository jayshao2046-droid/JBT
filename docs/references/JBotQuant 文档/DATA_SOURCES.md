# BotQuant 数据源与采集器明细

文档内容：按采集类别列出主要/备源、中文注释、常见字段/列名清单；列出所有相关环境变量（账号/Key）；并附上完整新闻 RSS / JSON 源名录（含 id/name/url/type）。

---

## 一、关键环境变量与账号（请在 `.env` 中配置）

- `TUSHARE_TOKEN`: Tushare Pro Token（期货/股票主数据、持仓/仓单等）。见 `.env.example`。
- `TQSDK_BROKER_ID`, `TQSDK_ACCOUNT_ID`, `TQSDK_PASSWORD`: TqSdk 模拟/实盘账号（用于实时 tick/行情/下单）；`TQSDK_ACCOUNT_TYPE` 配置为 `sim` 或 `live`。
- `FINNHUB_API_KEY`: Finnhub API Key（全球新闻与情绪，configs/news_sources.yaml 指定 env_var）。
- `NEWSAPI_KEY`: NewsAPI.org Key（新闻聚合，可选）。
- `ALPHA_VANTAGE_KEY`: Alpha Vantage Key（股票/外汇/情绪备源）。
- `FRED_API_KEY`: FRED 美联储数据 Key（宏观指标）。
- 飞书相关：`FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_VERIFICATION_TOKEN`, `FEISHU_ENCRYPT_KEY`，以及 `FEISHU_WEBHOOK_*`（用于告警/新闻推送）。
- AI/其他：`DEEPSEEK_API_KEY`, `QWEN_API_KEY`（本仓库 AI/决策相关）。

说明：参考文件 [/.env.example](.env.example) 包含以上示例条目与说明。

---

## 二、按分类的数据源总览（来自 `configs/data_sources.yaml`）

1) 内盘期货（domestic_futures）
   - primary: `tqsdk`（实时 minute）
   - backup: `tushare`, `akshare`（日线/分钟备源）
   - 注释：主力合约分钟优先用 TqSdk（需要 Sim/实盘账号），日线优先 Tushare；AkShare 作为免费/被动备源。
   - 常见字段（采集后记录 schema）：`symbol`, `timestamp`, `open`, `high`, `low`, `close`, `volume`, `oi`/`hold`, `amount`, `settle`。

2) 外盘期货（overseas_futures）
   - primary: `yfinance` / `tushare`（若覆盖）
   - backup: `twelvedata`, `alpha_vantage`, `akshare_foreign`
   - 注释：yfinance 对部分品种受限或限流；使用优先级自动切换。
   - 常见字段：`symbol`, `timestamp`, `open`, `high`, `low`, `close`, `volume`。

3) A 股（stock）
   - primary: `akshare`（eastmoney/新浪等），backup: `tushare`
   - 注释：全 A 股分钟数据多由 AkShare/EastMoney 提供，Tushare 作为备用。
   - 常见字段：`symbol`, `timestamp`/`trade_date`, `open`, `high`, `low`, `close`, `volume`, `amount`。

4) 宏观（macro / overseas_macro）
   - primary: `akshare`, backup: `tushare`, `wbgapi`, `fredapi`（视指标而定）
   - 注释：宏观指标字段常包含多种命名（中文/英文），在 `configs/data_sources.yaml` 中给出 `column_mapping`。
   - 常见字段：`date`/`日期`, `value`/`今值`, `forecast`/`预测值`, `previous`/`前值`。

5) 情绪数据（sentiment）
   - primary: `akshare`（margin、north_flow、qvix、market_activity），backup: `tushare`/`yfinance`
   - 注释：情绪因子覆盖融资融券、北向资金、QVIX 等；返回的 payload 多为指示器名与数值。
   - 常见字段（payload）：`indicator`, `margin_buy`, `margin_balance`, `short_sell`, `short_balance`, `total_balance`, `net_buy`, `flow_type`, `open/high/low/close`（QVIX）等。

6) 新闻（news）
   - API 主源：新浪/同花顺/华尔街见闻等 JSON API（见 `configs/news_sources.yaml` 与 `collectors/news_api_collector.py`）
   - RSS：公共 RSS 与 RSShub（见 `collectors/rss_collector.py` 与 `configs/rss_feeds.yaml`）
   - 常见字段（统一输出 record）：`source_type` (`news_api`/`rss_news`), `symbol_or_indicator`（源 id）, `timestamp`, `payload`（见下）
   - 新闻 payload 常见字段：`title`, `time`/`timestamp`, `url`/`link`, `content`/`summary`, `full_text`（RSS 抓取正文）, `uid`, `source`, `mode` (`live`/`mock`)。

7) 航运 / 其它行业指标（shipping / volatility）
   - primary: `akshare`（BDI/BCI 等）、备源 `httpx_scraper` 或 `yfinance`（部分指数）
   - 常见字段：`indicator`, `timestamp`, `value`/`level` 等

参考配置：`configs/data_sources.yaml`。

---

## 三、采集器到字段映射（从 `collectors/` 代码实测提取）

- `TushareDailyCollector` (`collectors/tushare_collector.py`)
  - 返回字段（每条记录为 dict）:
    - `symbol` (内部符号如 `SHFE.rb2405`)  
    - `timestamp` / `trade_date`  
    - `open`, `high`, `low`, `close`, `volume`（`vol`）, `oi`（持仓）, `amount`（成交额，可选）

- `AkshareBackupCollector` (`collectors/akshare_backup.py`)
  - minute (ak.futures_zh_minute_sina): `symbol`, `timestamp` (`datetime`/`date`), `open`, `high`, `low`, `close`, `volume`, `hold`（或 `position`）
  - daily (ak.futures_zh_daily_sina / ak.stock_zh_a_hist): `symbol`, `timestamp`/`date`, `open`, `high`, `low`, `close`, `volume`, `hold`/`settle`, `amount`

- `PositionCollector` (`collectors/position_collector.py`)
  - 返回结构：`source_type`: `position`, `symbol_or_indicator`（如 `RB.holding` 或 `warehouse_receipt`）, `timestamp`, `payload`=原始 `row` dict
  - 典型 payload 列（来自 Tushare `fut_holding` / `fut_wsr`）: `exchange`, `symbol`, `trade_date`/`date`, `long_vol`/`short_vol`/`position`、`warehouse`、`available` 等（字段随 Tushare 返回而异）。

- `SentimentCollector` (`collectors/sentiment_collector.py`)
  - 融资融券 (`margin_sh`/`margin_sz`) payload: `indicator`, `margin_buy`, `margin_balance`, `short_sell`, `short_balance`, `total_balance`。
  - 北向资金 (`north_flow`) payload: `indicator`, `flow_type`, `net_buy`, `balance`。
  - QVIX payload: `indicator`, `open`, `high`, `low`, `close`。

- `NewsAPICollector` (`collectors/news_api_collector.py`)
  - API sources 返回统一 record: `source_type`=`news_api`, `symbol_or_indicator`=源 id（如 `eastmoney`）, `timestamp`, `payload` 包含：`title`, `time`, `url`, `content`, `source`, `uid`, `mode`。

- `RSSCollector` (`collectors/rss_collector.py`)
  - `payload` 字段: `title`, `link`, `summary`, `full_text`（可选）, `feed`, `uid`, `mode`。

备注：某些采集器直接将 `dict(row)` 当作 `payload` 返回（如 `position_collector`），因此字段以源 API（Tushare/AkShare）为准；上表列出代码中显式转换或常见映射的字段。

---

## 四、完整新闻 RSS / JSON 源名录（来自 `configs/rss_feeds.yaml`）

注：下列按优先级分组（P0/P1/P2），列出 `id` / `name` / `url` / `type`。

P0 — 实时高优先（部分为 JSON API）

- `sina_finance_api` — 新浪财经资讯 — https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=50&page=1&r=0.1&type=rss — type: json_api
- `tonghuashun` — 同花顺快讯 — https://news.10jqka.com.cn/tapp/news/push/stock/?page=1&tag=&track=website — type: json_api
- `wallstreetcn_api` — 华尔街见闻 — https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit=20 — type: json_api
- `yahoo_finance_news` — Yahoo Finance 新闻 — https://finance.yahoo.com/news/rssindex — type: rss
- `cnbc_business` — CNBC Business News — https://www.cnbc.com/id/100003114/device/rss/rss.html — type: rss
- `fxstreet` — FXStreet 外汇 — https://www.fxstreet.com/rss — type: rss
- `bloomberg_markets` — Bloomberg Markets RSS — https://feeds.bloomberg.com/markets/news.rss — type: rss
- `marketwatch_global` — MarketWatch 全球市场 — https://feeds.marketwatch.com/marketwatch/topstories/ — type: rss
- `chinanews_finance` — 中国新闻网财经 — https://www.chinanews.com.cn/rss/finance.xml — type: rss

P1 — 标准资讯 / HTML 抓取源

- `bbc_chinese_biz` — BBC 中文财经 — http://www.bbc.co.uk/zhongwen/simp/business/index.xml — type: rss
- `tradingview_feed` — TradingView 全球财经 Feed — https://www.tradingview.com/feed/ — type: rss
- `stcn_kuaixun` — 证券时报快讯 — https://kuaixun.stcn.com/ — type: html_scrape
- `qhrb` — 期货日报 — http://www.qhrb.com.cn/ — type: html_scrape
- `jin10` — 金十数据 — https://www.jin10.com/ — type: html_scrape
- `ifeng_finance` — 凤凰财经 — https://finance.ifeng.com/ — type: html_scrape
- `nbd` — 每日经济新闻 — https://www.nbd.com.cn/ — type: html_scrape
- `jingji_21` — 21世纪经济报道 — https://www.21jingji.com/ — type: html_scrape

P2 — 参考/交易所公告/统计局

- `shfe_notice` — 上期所公告 — https://www.shfe.com.cn/publicnotice/notice/ — type: html_scrape
- `csrc_notice` — 证监会公告 — https://www.csrc.gov.cn/csrc/c100028/common_xq_list.shtml — type: html_scrape
- `stats_gov_cn` — 国家统计局数据发布 — https://www.stats.gov.cn/sj/zxfb/ — type: html_scrape
- `mysteel` — 我的钢铁网 — https://www.mysteel.com/ — type: html_scrape (reference_only)
- `scicc99` — 卓创资讯 — https://www.sci99.com/list/3_1000001.html — type: html_scrape (reference_only)
- `sns_100ppi` — 生意社商品价格 — https://www.100ppi.com/price/ — type: html_scrape (reference_only)

受阻 / 需 AkShare 替代的公告源：

- `dce_notice` — 大商所公告 — blocked_by: WAF 412, 使用 `akshare.futures_notice_dce()` 作为替代
- `czce_notice` — 郑商所公告 — blocked_by: WAF 412, 使用 `akshare.futures_notice_czce()` 作为替代

（更多源与状态见 `configs/rss_feeds.yaml`）

---

## 五、其他参考文件 & 路径

- 采集器源码目录：`collectors/`（`tushare_collector.py`, `akshare_backup.py`, `news_api_collector.py`, `rss_collector.py`, `sentiment_collector.py`, `position_collector.py` 等）
- 源优先级与策略：`configs/data_sources.yaml`
- 新闻 API 列表：`configs/news_sources.yaml`
- RSS 源清单：`configs/rss_feeds.yaml`
- 环境变量样例：`.env.example`

---

如果需要：
- 我可以把每个采集器的字段名逐文件导出为 CSV 或 Markdown 表格（含示例记录），或
- 给出一键脚本用于在本地读取当前 `.env` 并验证第三方 Key 的连通性（需要你授权运行终端命令）。
