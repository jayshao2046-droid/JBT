import { apiFetch } from "./fetcher"
import type { StrategySignal } from "./types"

const BASE = "/api/decision"

export const decisionApi = {
  getSignals: () => apiFetch<StrategySignal[]>(`${BASE}/dashboard/signals`),
  getHealth: () => apiFetch<{ status: string }>(`${BASE}/api/health`),
}
