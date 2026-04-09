# TASK-0031 data端非夜盘热修与新闻推送恢复

## 文档信息

- 任务 ID：TASK-0031
- 文档类型：单服务 P1 热修任务建档
- 签名：Atlas
- 建档时间：2026-04-09
- 设备：MacBook

---

## 一、任务目标

在 `services/data/**` 单服务范围内完成以下三项最小热修：

1. 暂停 A 股分钟全量采集，避免继续在现有设计下重复堆积与误报。
2. 收口 `health_check.py` 对 stock/news 的 legacy 目录误判，避免已冻结停采和现网 parquet 结构继续被判红。
3. 恢复新闻 / RSS 批量推送链路，使 Mini 现网不再依赖运行态 webhook 别名注入，并确保 30 分钟窗口内真实新增新闻可以被同步和推送。

---

## 二、根因冻结

### 1. A 股分钟全量采集

1. `job_stock_minute` 当前每 2 分钟触发。
2. `run_stock_minute_pipeline()` 每轮会全量抓取 5000+ A 股代码，并带分批休眠。
3. 该设计在当前频率下天然跑不完；Jay.S 已明确要求本轮先停采，不做全量优化恢复。

### 2. health_check 误报

1. `services/data/src/health/health_check.py` 仍按 legacy `stock_minute`、`news_collected` 等目录做 freshness 判定。
2. 当前 data 服务真实写盘已切到 parquet 结构，继续沿用 legacy 目录会制造 stock/news 假红灯。

### 3. 新闻 / RSS 今日无送达

1. Mini 运行态已确认：`news_api` 与 `RSS` 任务都在真实持续运行，且都有非 0 产出。
2. `job_news_push_batch()` 走的是 `NewsPusher.sync_from_storage() + flush()`，不是采集后直接推送。
3. 当前 `sync_from_storage(limit_per_source=120)` 小于单窗口真实产量，存在只读到尾部小窗口后被 dedup 误判“无新内容”的风险。
4. 当前 `dispatcher.py` 仍优先读取 `FEISHU_INFO_WEBHOOK_URL` / `FEISHU_TRADE_WEBHOOK_URL`；Mini 现网主要保留 `FEISHU_NEWS_WEBHOOK_URL` / `FEISHU_TRADING_WEBHOOK_URL`，现阶段只能靠运行态别名注入维持，必须根修到代码层。

---

## 三、任务边界

### 本轮允许处理

1. A 股分钟停采。
2. `health_check` 对 stock/news 的误报收口。
3. 新闻 / RSS 批量推送恢复。
4. 与上述三项直接相关的最小测试补充。

### 本轮明确排除

1. 夜盘国内期货真实采集闭环。
2. 外盘分钟 `Alpha Vantage` / `Twelve Data` key 与 fallback 根因。
3. `services/data/src/collectors/**` 本体实现修改。
4. `services/data/src/scheduler/pipeline.py`。
5. `services/data/src/main.py`。
6. 任一 `.env.example`、任一真实 `.env`。
7. `services/data/data_web/**`。
8. 任一跨服务文件、`shared/**`、部署文件。

---

## 四、待签发白名单

当前状态：`pending_token`

仅允许后续申请以下 6 文件最小 P1 Token：

1. `services/data/src/scheduler/data_scheduler.py`
2. `services/data/src/health/health_check.py`
3. `services/data/src/notify/dispatcher.py`
4. `services/data/src/notify/news_pusher.py`
5. `services/data/tests/test_scheduler.py`
6. `services/data/tests/test_notify.py`

---

## 五、验收标准

1. A 股分钟任务在调度主链路内停止执行，且不再通过 fallback 继续触发。
2. `health_check` 不再因为 A 股分钟停采和 news parquet 目录差异而继续给出假红灯。
3. NEWS 通知发送不再依赖运行态临时 webhook 别名注入。
4. `job_news_push_batch` 能看到覆盖 30 分钟窗口的真实新增新闻，不再稳定输出“无新内容”。
5. 新增或更新的测试能覆盖：
   - A 股分钟停采口径；
   - 新闻批量推送同步窗口；
   - webhook 兼容回退口径。

---

## 六、当前结论

1. `TASK-0031` 为 data 单服务 P1 热修，符合按最小白名单进入标准流程。
2. 本轮不允许顺手处理外盘、夜盘或 `data_web`。
3. 待 Jay.S 为上述 6 文件签发有效 Token 后，方可进入代码修改。