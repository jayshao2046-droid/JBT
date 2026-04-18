import { apiFetch } from "./fetcher"

const BASE = "/api/data/api/v1/researcher"

export interface FuturesSymbolData {
  [key: string]: unknown
}

export interface StockMover {
  [key: string]: unknown
}

export interface ResearchReport {
  report_id: string
  segment: string
  generated_at: string
  model: string
  futures_summary: {
    symbols_covered: number
    market_overview: string
    symbols: Record<string, FuturesSymbolData>
  }
  stocks_summary: {
    symbols_covered: number
    market_overview: string
    top_movers: StockMover[]
  }
}

export interface ReportListItem {
  segment: string
  report_id: string
  generated_at: string
}

export const researcherApi = {
  getLatestReport: () => apiFetch<ResearchReport>(`${BASE}/report/latest`),

  getReportsByDate: (date: string) =>
    apiFetch<{ date: string; segments: ReportListItem[] }>(`${BASE}/report/${date}`),

  getReportByDateSegment: (date: string, segment: string) =>
    apiFetch<ResearchReport>(`${BASE}/report/${date}/${segment}`),

  getStatus: () =>
    apiFetch<{
      status: string
      last_run: { report_id: string; segment: string; generated_at: string } | null
      next_schedule: Record<string, string>
      resource_status: { alienware_reachable: boolean; ollama_available: boolean }
    }>(`${BASE}/status`),

  triggerResearch: (segment: string) =>
    apiFetch<{ status: string; message: string }>(`${BASE}/trigger?segment=${encodeURIComponent(segment)}`, {
      method: "POST",
    }),
}
