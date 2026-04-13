import { apiFetch } from "./fetcher"

const BASE = "/api/backtest"

export const backtestApi = {
  getHealth: () => apiFetch<{ status: string }>(`${BASE}/health`),
}
