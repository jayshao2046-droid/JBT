import { apiFetch } from "./fetcher"

const BASE = "/api/decision"

export const decisionApi = {
  getSignals: async () => {
    const res = await apiFetch<Array<{
      strategy_id: string
      signal: string
      signal_strength: number
      timestamp: string
    }>>(`${BASE}/dashboard/signals`)

    // 适配前端期望的格式
    return res.map((item, idx) => ({
      id: `${item.strategy_id}-${idx}`,
      strategy_name: item.strategy_id,
      instrument_id: item.strategy_id.split('_')[0] || 'unknown',
      direction: (item.signal === 'long' ? 'long' : 'short') as 'long' | 'short',
      confidence: item.signal_strength,
      status: 'pending' as const,
      timestamp: item.timestamp,
    }))
  },
  getHealth: () => apiFetch<{ status: string }>(`${BASE}/health`),
  disableSignal: (signalId: string, reason: string) =>
    apiFetch(`${BASE}/signals/${signalId}/disable`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    }),
}
