import { apiFetch } from "./fetcher"
import type { CollectorStatus, NewsItem } from "./types"

const BASE = "/api/data"

export const dataApi = {
  getCollectors: () => apiFetch<CollectorStatus[]>(`${BASE}/api/v1/dashboard/collectors`),
  getNews: () => apiFetch<NewsItem[]>(`${BASE}/api/v1/dashboard/news`),
  getHealth: () => apiFetch<{ status: string }>(`${BASE}/api/v1/health`),
}
