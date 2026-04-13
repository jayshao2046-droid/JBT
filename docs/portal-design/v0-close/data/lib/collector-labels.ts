/* 采集源 UPPERCASE + 中文名称映射 */
export const COLLECTOR_LABELS: Record<string, { display: string; zh: string }> = {
  tushare:          { display: "TUSHARE",          zh: "A股行情" },
  akshare:          { display: "AKSHARE",          zh: "AkShare 财经" },
  news_api:         { display: "NEWS_API",         zh: "新闻 API" },
  news_rss:         { display: "NEWS_RSS",         zh: "RSS 新闻" },
  futures_minute:   { display: "FUTURES_MINUTE",   zh: "期货分钟线" },
  futures_eod:      { display: "FUTURES_EOD",      zh: "期货日线" },
  overseas_minute:  { display: "OVERSEAS_MINUTE",  zh: "外盘分钟线" },
  overseas_daily:   { display: "OVERSEAS_DAILY",   zh: "外盘日线" },
  macro:            { display: "MACRO",            zh: "宏观数据" },
  sentiment:        { display: "SENTIMENT",        zh: "情绪指数" },
  shipping:         { display: "SHIPPING",         zh: "航运指数" },
  stock_minute:     { display: "STOCK_MINUTE",     zh: "A股分钟线" },
  volatility_cboe:  { display: "VOLATILITY_CBOE",  zh: "VIX 波动率" },
  health:           { display: "HEALTH",           zh: "健康检查" },
  data_scheduler:   { display: "DATA_SCHEDULER",   zh: "数据调度器" },
  parquet:          { display: "PARQUET",          zh: "Parquet 存储" },
}

export function collectorDisplayName(name: string): string {
  return COLLECTOR_LABELS[name?.toLowerCase()]?.display ?? name.toUpperCase().replace(/[-]/g, "_")
}

export function collectorZhName(name: string, fallback?: string): string {
  return COLLECTOR_LABELS[name?.toLowerCase()]?.zh ?? (fallback || name)
}
