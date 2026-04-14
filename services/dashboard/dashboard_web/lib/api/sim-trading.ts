import { apiFetch } from "./fetcher"
import type { PerformanceStats, RiskL1, DailyReport, Position, Order } from "./types"

const BASE = "/api/sim-trading/api/v1"

// 扩展类型定义
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

export interface ExecutionStats {
  avg_slippage: number
  rejection_rate: number
  avg_latency_ms: number
  cancel_rate: number
  partial_fill_rate: number
}

export interface L2Status {
  consecutive_losses: number
  margin_rate: number | null
  daily_trade_count: number
  daily_pnl: number
  position_count: number
}

export interface TickData {
  symbol: string
  last_price: number
  bid_price: number
  ask_price: number
  volume: number
  open_interest: number
  update_time: string
}

export interface KlinePoint {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
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

export const simTradingApi = {
  // 基础状态
  getAccount: async () => {
    const res = await apiFetch<{
      connected: boolean
      local_virtual: { principal: number }
      ctp_snapshot: {
        balance: number | null
        available: number | null
        margin: number | null
        floating_pnl: number | null
      }
    }>(`${BASE}/account`)

    // 适配前端期望的格式
    const snapshot = res.ctp_snapshot
    return {
      equity: snapshot.balance || res.local_virtual.principal,
      available: snapshot.available || res.local_virtual.principal,
      margin: snapshot.margin || 0,
      float_pnl: snapshot.floating_pnl || 0,
    }
  },
  getPositions: async () => {
    const res = await apiFetch<{positions: Position[]; note?: string}>(`${BASE}/positions`)
    return Array.isArray(res.positions) ? res.positions : []
  },
  getPerformance: async () => {
    const res = await apiFetch<{performance: PerformanceStats; timestamp: string}>(`${BASE}/stats/performance`)
    return res.performance
  },
  getRiskL1: async () => {
    const res = await apiFetch<{l1_status: RiskL1; timestamp: string}>(`${BASE}/risk/l1`)
    return res.l1_status
  },
  getDailyReport: () => apiFetch<DailyReport>(`${BASE}/report/daily`),
  getOrders: async () => {
    const res = await apiFetch<{orders: Record<string, Order> | Order[]; note?: string}>(`${BASE}/orders`)
    if (Array.isArray(res.orders)) return res.orders
    return Object.values(res.orders || {})
  },
  getStatus: () => apiFetch<{ status: string }>(`${BASE}/status`),

  // 系统状态
  getSystemState: () => apiFetch<SystemState>(`${BASE}/system/state`),
  pauseTrading: (reason = "手动暂停") =>
    apiFetch<{result: string}>(`${BASE}/system/pause`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    }),
  resumeTrading: () =>
    apiFetch<{result: string}>(`${BASE}/system/resume`, { method: "POST" }),

  // CTP 配置
  getCtpConfig: () => apiFetch<Partial<SystemState>>(`${BASE}/ctp/config`),
  saveCtpConfig: (cfg: {broker_id:string; user_id:string; password:string; md_front:string; td_front:string}) =>
    apiFetch<{result:string}>(`${BASE}/ctp/config`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cfg),
    }),
  ctpConnect: () => apiFetch<{result:string}>(`${BASE}/ctp/connect`, { method: "POST" }),
  ctpDisconnect: () => apiFetch<{result:string}>(`${BASE}/ctp/disconnect`, { method: "POST" }),
  getCtpStatus: () => apiFetch<{md_connected: boolean; td_connected: boolean; timestamp: string}>(`${BASE}/ctp/status`),

  // 风控预设
  getRiskPresets: () => apiFetch<{presets: Record<string, RiskPreset>}>(`${BASE}/risk-presets`),
  updateRiskPreset: (data: {symbol:string} & RiskPreset) =>
    apiFetch<{result:string}>(`${BASE}/risk-presets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  // L2 风控
  getRiskL2: () => apiFetch<{l2_status: L2Status; timestamp: string}>(`${BASE}/risk/l2`),
  getRiskAlerts: () => apiFetch<{alerts: Array<{timestamp: string; level: string; message: string}>}>(`${BASE}/risk/alerts`),

  // 执行质量
  getExecutionStats: () => apiFetch<{execution: ExecutionStats; timestamp: string}>(`${BASE}/stats/execution`),

  // 行情数据
  getTicks: () => apiFetch<{ticks: TickData[]; timestamp: string}>(`${BASE}/ticks`),
  getMarketKline: (symbol: string, interval = "1m") =>
    apiFetch<{symbol: string; interval: string; klines: KlinePoint[]}>(`${BASE}/market/kline/${symbol}?interval=${interval}`),
  getMarketMovers: (topN = 10) =>
    apiFetch<{movers: {price_movers: MarketMover[]; amplitude_movers: MarketMover[]; volume_movers: MarketMover[]}; timestamp: string}>(
      `${BASE}/market/movers?top_n=${topN}`
    ),

  // 日志
  getLogs: (lines = 200, level?: string) => {
    const params = new URLSearchParams({ lines: lines.toString() })
    if (level) params.append("level", level)
    return apiFetch<{logs: Array<{timestamp: string; level: string; message: string}>}>(`${BASE}/logs/tail?${params.toString()}`)
  },

  // 报单/撤单
  placeOrder: (params: {
    instrument_id: string
    direction: "long" | "short"
    volume: number
    price?: number
    order_type?: "limit" | "market"
  }) =>
    apiFetch<Order>(`${BASE}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    }),

  cancelOrder: (orderRef: string) =>
    apiFetch<{result: string}>(`${BASE}/orders/cancel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_ref: orderRef }),
    }),

  closePosition: (params: {
    instrument_id: string
    direction: "long" | "short"
    volume: number
    price?: number
    order_type?: "limit" | "market"
  }) =>
    apiFetch<Order>(`${BASE}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    }),

  // 批量平仓
  batchClosePositions: (positionIds: string[]) =>
    apiFetch<{results: Array<{position_id: string; success: boolean; message?: string; error?: string}>; total: number; success: number; failed: number}>(
      `${BASE}/positions/batch_close`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ position_ids: positionIds }),
      }
    ),
}
