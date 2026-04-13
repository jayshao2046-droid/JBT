// sim-trading API 客户端
// 通过 next.config.mjs rewrite 代理到 localhost:8101

export interface HealthResponse {
  status: string
  service: string
}

export interface StatusResponse {
  status: string
  stage: string
}

export interface Position {
  id?: string | number
  contract?: string
  direction?: string
  quantity?: number
  avgPrice?: number
  currentPrice?: number
  floatPnl?: number
  stopLoss?: number
  takeProfit?: number
}

export interface PositionsResponse {
  positions: Position[]
  note?: string
}

export interface Order {
  id?: string
  time?: string
  contract?: string
  action?: string
  price?: number
  quantity?: number
  status?: string
  reason?: string | null
  order_ref?: string
}

export interface OrdersResponse {
  orders: Order[]
  note?: string
}

// --- 下单/撤单/错误/合约 ---
export interface OrderRequest {
  instrument_id: string
  direction: "buy" | "sell"
  offset: "open" | "close" | "close_today"
  price: number
  volume: number
}

export interface OrderResult {
  rejected: boolean
  source: string
  error?: string
  code?: string
  order_ref?: string
  front_id?: number
  session_id?: number
}

export interface OrderError {
  timestamp?: string
  order_ref?: string
  error_id?: number
  error_msg?: string
  instrument_id?: string
  direction?: string
  offset?: string
  price?: number
  volume?: number
}

export interface InstrumentSpec {
  instrument_id?: string
  product_id?: string
  exchange_id?: string
  price_tick?: number
  volume_multiple?: number
  max_order_volume?: number
  long_margin_ratio?: number
  short_margin_ratio?: number
}

const BASE = "/api/sim"

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" })
  if (!res.ok) throw new Error(`${path} → ${res.status}`)
  return res.json()
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  })
  if (!res.ok) throw new Error(`${path} → ${res.status}`)
  return res.json()
}

async function patch<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  })
  if (!res.ok) throw new Error(`${path} → ${res.status}`)
  return res.json()
}

export interface SystemState {
  trading_enabled: boolean
  active_preset: string
  paused_reason: string | null
  ctp_md_connected: boolean
  ctp_td_connected: boolean
  ctp_broker_id: string
  ctp_user_id: string
  ctp_md_front: string
  ctp_td_front: string
}

export interface RiskPreset {
  name: string
  max_lots: number
  max_position: number
  daily_loss_pct: number
  price_dev_pct: number
  enabled: boolean
  commission: number
  slippage_ticks: number
}

// SIMWEB-01 新增接口类型
export interface EquityPoint {
  timestamp: string
  equity: number
}

export interface PerformanceStats {
  win_rate: number
  profit_loss_ratio: number
  max_drawdown: number
  sharpe_ratio: number
  today_pnl: number
  week_pnl: number
  month_pnl: number
}

export interface ExecutionStats {
  avg_slippage: number
  rejection_rate: number
  avg_latency_ms: number
  cancel_rate: number
  partial_fill_rate: number
}

export interface L1Status {
  trading_enabled: boolean
  ctp_connected: boolean
  reduce_only_mode: boolean
  disaster_stop_triggered: boolean
  max_position_check: boolean
  daily_loss_check: boolean
  price_deviation_check: boolean
  order_frequency_check: boolean
  margin_rate_check: boolean
  connection_quality_check: boolean
}

export interface L2Status {
  consecutive_losses: number
  margin_rate: number | null
  daily_trade_count: number
  daily_pnl: number
  position_count: number
}

export interface MarketMover {
  symbol: string
  name: string
  current_price?: number
  prev_close?: number
  change_rate?: number
  high?: number
  low?: number
  amplitude?: number
  current_volume?: number
  avg_volume?: number
  volume_ratio?: number
}

export interface KlinePoint {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export const simApi = {
  health: () => get<HealthResponse>("/health"),
  status: () => get<StatusResponse>("/api/v1/status"),
  positions: () => get<PositionsResponse>("/api/v1/positions"),
  orders: () => get<OrdersResponse>("/api/v1/orders"),
  // 系统状态
  systemState: () => get<SystemState>("/api/v1/system/state"),
  pauseTrading: (reason = "手动暂停") => post<{result: string}>("/api/v1/system/pause", { reason }),
  resumeTrading: () => post<{result: string}>("/api/v1/system/resume"),
  setPreset: (preset: string) => post<{result: string}>("/api/v1/system/preset", { preset }),
  // CTP
  ctpConfig: () => get<Partial<SystemState>>("/api/v1/ctp/config"),
  saveCtp: (cfg: {broker_id:string; user_id:string; password:string; md_front:string; td_front:string}) =>
    post<{result:string}>("/api/v1/ctp/config", cfg),
  ctpConnect: () => post<{result:string}>("/api/v1/ctp/connect"),
  ctpDisconnect: () => post<{result:string}>("/api/v1/ctp/disconnect"),
  // 风控预设
  riskPresets: () => get<{presets: Record<string, RiskPreset>}>("/api/v1/risk-presets"),
  updateRiskPreset: (data: {symbol:string} & RiskPreset) =>
    post<{result:string}>("/api/v1/risk-presets", data),
  // 报单/撤单
  createOrder: (req: OrderRequest) => post<OrderResult>("/api/v1/orders", req),
  cancelOrder: (orderRef: string) => post<{result:string}>("/api/v1/orders/cancel", { order_ref: orderRef }),
  // 订单错误
  orderErrors: () => get<{errors: OrderError[]}>("/api/v1/orders/errors"),
  // 合约规格
  instruments: (product?: string) =>
    get<{instruments: Record<string, InstrumentSpec>; count: number}>(
      `/api/v1/instruments${product ? `?product=${product}` : ""}`
    ),

  // SIMWEB-01 P0-1: 权益历史
  equityHistory: (start?: string, end?: string) => {
    const params = new URLSearchParams()
    if (start) params.append("start", start)
    if (end) params.append("end", end)
    const query = params.toString() ? `?${params.toString()}` : ""
    return get<{history: EquityPoint[]; count: number}>(`/api/v1/equity/history${query}`)
  },

  // SIMWEB-01 P0-2: L1/L2 风控状态
  riskL1Status: () => get<{l1_status: L1Status; timestamp: string}>("/api/v1/risk/l1"),
  riskL2Status: () => get<{l2_status: L2Status; timestamp: string}>("/api/v1/risk/l2"),

  // SIMWEB-01 P0-3: 止损修改
  updateStopLoss: (positionId: string, stopLoss: number) =>
    patch<{success: boolean; position_id: string; stop_loss: number; message: string}>(
      `/api/v1/positions/${positionId}/stop_loss`,
      { stop_loss: stopLoss }
    ),

  // SIMWEB-01 P1-1: 绩效统计
  performanceStats: () => get<{performance: PerformanceStats; timestamp: string}>("/api/v1/stats/performance"),

  // SIMWEB-01 P1-2: 执行质量统计
  executionStats: () => get<{execution: ExecutionStats; timestamp: string}>("/api/v1/stats/execution"),

  // SIMWEB-01 P1-3: 批量平仓
  batchClosePositions: (positionIds: string[]) =>
    post<{results: Array<{position_id: string; success: boolean; message?: string; error?: string}>; total: number; success: number; failed: number}>(
      "/api/v1/positions/batch_close",
      { position_ids: positionIds }
    ),

  // SIMWEB-01 P1-6: K线数据
  marketKline: (symbol: string, interval = "1m") =>
    get<{symbol: string; interval: string; klines: KlinePoint[]}>(`/api/v1/market/kline/${symbol}?interval=${interval}`),

  // SIMWEB-01 P1-7: 市场异动
  marketMovers: (topN = 10) =>
    get<{movers: {price_movers: MarketMover[]; amplitude_movers: MarketMover[]; volume_movers: MarketMover[]}; timestamp: string}>(
      `/api/v1/market/movers?top_n=${topN}`
    ),
}
