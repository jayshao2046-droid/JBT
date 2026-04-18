import { apiFetch } from "./fetcher"

const BASE = "/api/decision/api/v1/billing"

export interface BillingRecord {
  timestamp: string
  model: string
  component: string
  tier: string
  input_tokens: number
  output_tokens: number
  input_cost: number
  output_cost: number
  total_cost: number
  is_local: boolean
  fallback_from?: string
}

export interface HourlySummary {
  hour: string
  total_tokens: number
  total_cost: number
  by_model: Record<string, { tokens: number; cost: number }>
}

export interface DailySummary {
  date: string
  total_tokens: number
  total_cost: number
  by_model: Record<string, { tokens: number; cost: number }>
  budget_progress?: number
}

export const billingApi = {
  getHourlySummary: () => apiFetch<HourlySummary>(`${BASE}/hourly`),

  getDailySummary: () => apiFetch<DailySummary>(`${BASE}/daily`),

  getRecords: (limit = 100) =>
    apiFetch<{ records: BillingRecord[] }>(`${BASE}/records?limit=${limit}`),

  sendReport: () =>
    apiFetch<{ sent: boolean; error?: string }>(`${BASE}/report`, {
      method: "POST",
    }),
}
