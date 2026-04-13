import { apiFetch } from "./fetcher"
import type { StrategySignal } from "./types"

const BASE = "/api/decision"

export const decisionApi = {
  getSignals: () => apiFetch<StrategySignal[]>(`${BASE}/dashboard/signals`),
  getHealth: () => apiFetch<{ status: string }>(`${BASE}/health`),
  disableSignal: (signalId: string, reason: string) =>
    apiFetch(`${BASE}/signals/${signalId}/disable`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    }),
}
