import { apiFetch } from "./fetcher"
import type { AccountInfo, PerformanceStats, RiskL1, DailyReport, Position, Order } from "./types"

const BASE = "/api/sim-trading"

export const simTradingApi = {
  getAccount: () => apiFetch<AccountInfo>(`${BASE}/account`),
  getPositions: () => apiFetch<Position[]>(`${BASE}/positions`),
  getPerformance: () => apiFetch<PerformanceStats>(`${BASE}/stats/performance`),
  getRiskL1: () => apiFetch<RiskL1>(`${BASE}/risk/l1`),
  getDailyReport: () => apiFetch<DailyReport>(`${BASE}/report/daily`),
  getOrders: () => apiFetch<Order[]>(`${BASE}/orders`),
  getStatus: () => apiFetch<{ status: string }>(`${BASE}/status`),
}
