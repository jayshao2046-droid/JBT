// sim-trading 接口
export interface AccountInfo {
  equity: number
  available: number
  margin: number
  float_pnl: number
}

export interface PerformanceStats {
  daily_pnl: number
  win_rate: number
  pnl_ratio: number
  total_trades: number
}

export interface RiskL1 {
  position_usage: number
  var_1d: number
  drawdown: number
  trading_enabled?: boolean
  ctp_connected?: boolean
  reduce_only_mode?: boolean
  disaster_stop_triggered?: boolean
  max_position_check?: boolean
  daily_loss_check?: boolean
  price_deviation_check?: boolean
  order_frequency_check?: boolean
  margin_rate_check?: boolean
  connection_quality_check?: boolean
}

export interface DailyReport {
  trade_count: number
  pnl: number
  date: string
}

export interface Position {
  instrument_id: string
  direction: "long" | "short"
  volume: number
  open_price: number
  avg_price?: number
  current_price: number
  float_pnl: number
  position_id?: string
}

export interface Order {
  order_id: string
  instrument_id: string
  direction: "buy" | "sell"
  volume: number
  price: number
  status: string
  timestamp: string
  insert_time?: string
  order_ref?: string
}

// decision 接口
export interface StrategySignal {
  id: string
  strategy_name: string
  instrument_id: string
  direction: "long" | "short"
  confidence: number
  status: "pending" | "approved" | "rejected" | "disabled"
  timestamp: string
}

// data 接口
export interface CollectorStatus {
  name: string
  status: "running" | "stopped" | "error"
  last_update: string
  data_count?: number
}

export interface NewsItem {
  id: string
  title: string
  source: string
  timestamp: string
  url?: string
  summary?: string
}

// 服务健康
export interface ServiceHealth {
  status: "ok" | "error" | "unknown"
  service: string
  timestamp?: string
}
