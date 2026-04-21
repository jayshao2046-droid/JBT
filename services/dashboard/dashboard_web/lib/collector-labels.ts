export const COLLECTOR_LABELS: Record<string, { display: string; zh: string }> = {
  // 行情类
  futures_minute: { display: "FUTURES_MIN", zh: "国内期货分钟" },
  futures_eod: { display: "FUTURES_EOD", zh: "国内期货日线" },
  overseas_minute: { display: "OVERSEAS_MIN", zh: "外盘期货分钟" },
  overseas_daily: { display: "OVERSEAS_EOD", zh: "外盘期货日线" },
  stock_minute: { display: "STOCK_MIN", zh: "A股分钟线" },
  stock_realtime: { display: "STOCK_RT", zh: "A股实时" },
  tushare: { display: "TUSHARE", zh: "Tushare日线" },
  options: { display: "OPTIONS", zh: "期权行情" },
  // 监控类
  watchlist: { display: "WATCHLIST", zh: "自选股" },
  health_log: { display: "HEALTH_LOG", zh: "健康日志" },
  // 宏观类
  macro_global: { display: "MACRO", zh: "宏观数据" },
  volatility_cboe: { display: "CBOE_VIX", zh: "CBOE波动率" },
  volatility_qvix: { display: "QVIX", zh: "QVIX波动率" },
  shipping: { display: "SHIPPING", zh: "航运指数" },
  weather: { display: "WEATHER", zh: "天气" },
  forex: { display: "FOREX", zh: "外汇日线" },
  cftc: { display: "CFTC", zh: "CFTC持仓" },
  // 持仓类
  position_daily: { display: "POS_DAILY", zh: "持仓日报" },
  position_weekly: { display: "POS_WEEKLY", zh: "持仓周报" },
  // 情绪类
  sentiment: { display: "SENTIMENT", zh: "情绪指数" },
  // 新闻资讯类
  news_rss: { display: "NEWS_RSS", zh: "新闻RSS" },
  news_api: { display: "NEWS_API", zh: "新闻API" },
  // 旧兼容条目
  akshare: { display: "AKSHARE", zh: "AkShare 财经" },
  macro: { display: "MACRO", zh: "宏观数据" },
  health: { display: "HEALTH", zh: "健康检查" },
  data_scheduler: { display: "SCHEDULER", zh: "数据调度器" },
  parquet: { display: "PARQUET", zh: "Parquet 存储" },
}

export function collectorDisplayName(name: string): string {
  return COLLECTOR_LABELS[name?.toLowerCase()]?.display ?? name.toUpperCase().replace(/[-]/g, "_")
}

export function collectorZhName(name: string, fallback?: string): string {
  return COLLECTOR_LABELS[name?.toLowerCase()]?.zh ?? (fallback || name)
}
