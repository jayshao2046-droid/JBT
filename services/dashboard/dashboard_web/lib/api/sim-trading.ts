import { apiFetch } from "./fetcher"
import type { AccountInfo, PerformanceStats, RiskL1, DailyReport, Position, Order } from "./types"

const BASE = "/api/sim-trading/api/v1"

export const simTradingApi = {
  getAccount: () => apiFetch<AccountInfo>(`${BASE}/account`),
  getPositions: () => apiFetch<Position[]>(`${BASE}/positions`),
  getPerformance: () => apiFetch<PerformanceStats>(`${BASE}/stats/performance`),
  getRiskL1: () => apiFetch<RiskL1>(`${BASE}/risk/l1`),
  getDailyReport: () => apiFetch<DailyReport>(`${BASE}/report/daily`),
  getOrders: () => apiFetch<Order[]>(`${BASE}/orders`),
  getStatus: () => apiFetch<{ status: string }>(`${BASE}/status`),

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
}
