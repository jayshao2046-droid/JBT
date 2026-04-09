# TASK-0031 Review

## Review 信息

- 任务 ID：TASK-0031
- 审核角色：项目架构师
- 审核阶段：终审
- 审核时间：2026-04-09
- 审核结论：通过

---

## 一、本轮范围

1. 本轮只在 `services/data/**` 单服务 6 文件白名单内实施。
2. 本轮只收口三项：A 股分钟停采、`health_check` 对 stock/news 误报收口、新闻 / RSS 批量推送恢复。
3. 未扩展到 `pipeline.py`、`collectors/**`、`main.py`、任一 `.env` 与 `data_web`。

## 二、实现结论

1. `data_scheduler.py` 已停止注册 A 股分钟 APScheduler 任务，并从 fallback jobs 移除；`job_stock_minute` 本体也已按“暂停采集”直接返回。
2. `health_check.py` 已将 `stock_minute` / `stock_realtime` 转为“已暂停采集”跳过口径，并为 `news_rss` 增加多目录 freshness 检查。
3. `dispatcher.py` 已兼容以下双向环境变量口径：
   - `FEISHU_NEWS_WEBHOOK_URL` ↔ `FEISHU_INFO_WEBHOOK_URL`
   - `FEISHU_TRADING_WEBHOOK_URL` ↔ `FEISHU_TRADE_WEBHOOK_URL`
4. `news_pusher.py` 已将单源同步窗口提升为 5000，`job_news_push_batch` 也显式传入 5000，足以覆盖当前 Mini 上 30 分钟窗口内的 news_api / RSS 写盘量级。

## 三、自校验结果

1. token validate：通过。
2. 静态诊断：6 个白名单文件 `No errors found`。
3. 本地回归：`pytest services/data/tests/test_notify.py services/data/tests/test_scheduler.py -q -k 'not test_pipeline_importable'` → `19 passed, 1 deselected`。
4. 说明：被 deselect 的 `test_pipeline_importable` 依赖当前本地环境缺少 `polars`，属于既有环境依赖问题，不属于本轮改动回归。

## 四、Mini 运行态验证

1. 新实例启动日志已明确输出：`A股分钟K线任务当前已暂停，不注册 APScheduler 任务`。
2. Mini 运行态检查结果：
   - `stock_minute_enabled = False`
   - `news_sync_limit = 5000`
   - `NEWS/INFO/TRADE` webhook 解析结果均为 `True`
   - `stock_minute` / `stock_realtime` freshness 为 `已暂停采集`
   - `news_rss` freshness 正常
3. 旧残留调度器已清理，当前仅保留新实例 `PID 91101`。

## 五、终审结论

1. `TASK-0031` 本轮 6 文件改动边界合规。
2. A 股分钟停采、`health_check` 对 stock/news 误报收口、新闻批量推送与 webhook 兼容恢复均已闭环。
3. 终审通过，可按 `REVIEW-TASK-0031` 留痕并进入 lockback。

## 六、lockback 留痕字段

1. `review_id`：`REVIEW-TASK-0031`
2. `token_id`：`tok-01c2acc1-eec5-46ec-8cf0-f26e122feee1`
3. `result`：待 lockback 后回填为 `approved`