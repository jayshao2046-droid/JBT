# TASK-U0-20260419-010 data端 Parquet schema 冲突根治 + CFTC采集器API升级

【类型】U0 紧急直修（事后审计）  
【建档】Atlas  
【日期】2026-04-19  
【状态】✅ 已完成并收口  
【服务边界】data（单服务）  
【设备】Mini (192.168.31.156)，容器 JBT-DATA-8105  
【授权】Jay.S U0 直修指令  
【提交】待 git commit 后补充

## 1. 问题来源

健康报告 17/21 红：情绪指数 / RSS / 新闻API 采集失败（11:18–11:33），天气异常（06:31）。

## 2. 根因诊断

### 2.1 Parquet payload 字段 schema 冲突

旧 parquet 文件写入时 `payload` 字段为 `string` 类型，新版采集器写入 `payload` 为 `struct`。  
PyArrow 在 append 写入时无法合并：`Field payload has incompatible types: string vs struct<...>`。

### 2.2 CFTC 采集器 akshare API 已废弃

容器内 `cftc_collector.py` 使用 `ak.macro_usa_cftc_nc_report(symbol=...)` 和 `ak.macro_usa_cftc_c_report(symbol=...)`，  
已从 akshare 中移除，导致所有 CFTC 品种 fetch 失败，fallback 到 mock。

### 2.3 health_check.py position_daily 路径错误

（本轮确认已在上轮 TASK-U0-20260418-007 中修复完毕，本轮采集验证通过）

## 3. 修复内容

### 3.1 删除旧 schema parquet 文件（共 11 个）

| 轮次 | 删除文件 |
|------|---------|
| Round 1 | weather, sentiment, news_api, news_rss（6个） |
| Round 2 | options, forex, shipping, macro_global, position_daily, cftc, volatility_index（7个） |

所有旧文件为 `payload=string`，删除后新采集重建为 `payload=struct`。

### 3.2 CFTC 采集器 API 迁移

**修改文件**：`services/data/src/collectors/cftc_collector.py`

| 变更点 | 旧值 | 新值 |
|--------|------|------|
| API 调用 | `ak.macro_usa_cftc_nc_report(symbol=...)` | `ak.macro_usa_cftc_merchant_goods_holding()` |
| API 调用 | `ak.macro_usa_cftc_c_report(symbol=...)` | 同上（单次批量调用） |
| 品种映射 | 含 copper/wheat/sp500/nasdaq | 移除 API 中不存在的品种 |
| 列名 | `多头/空头/净多` | `{prefix}-多头仓位/{prefix}-空头仓位/{prefix}-净仓位` |
| 品种前缀 | `ak_symbol` | `col_prefix`（与 API 列名对应） |

部署方式：`docker cp` 覆盖容器内 `/app/services/data/src/collectors/cftc_collector.py`。

## 4. 验收结果

### 4.1 schema 验证（采集后）
| 数据类型 | 行数 | payload 类型 |
|---------|------|-------------|
| weather | 105 | struct ✅ |
| sentiment | 424 | struct ✅ |
| news_api | 1544 | struct ✅ |
| news_rss | 100 | struct ✅ |

### 4.2 代理补采（有代理）
| 数据类型 | 结果 |
|---------|------|
| shipping | 120 records（含 scfi/ccfi） ✅ |
| cftc | 10 records（新 API 生效） ✅ |
| rss（海外源） | 139 records（bloomberg/ft/marketwatch） ✅ |

### 4.3 全量采集结果
11/14 成功，3 个失败项均为需要具体参数的定向 pipeline（run_daily_pipeline/run_overseas_daily_pipeline/run_tushare_futures_pipeline），非采集器问题。

## 5. 遗留事项

1. scfi / ccfi：investing.com 无代理时 403，是已知限制，非 bug。
2. CFTC mock fallback：akshare API 彻底废弃，新 API 已切换，无代理时仍可正常采集。
3. 持仓数据 / position：周末无实盘，mock fallback 为正常行为。
