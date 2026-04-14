import { apiFetch } from "./fetcher"

const BASE = "/api/data"

export const dataApi = {
  getCollectors: async () => {
    const res = await apiFetch<{
      generated_at: string
      summary: { total: number; success: number; failed: number }
      collectors: Array<{
        id: string
        name: string
        status: string
        last_run_time: string
        data_source?: string
      }>
    }>(`${BASE}/api/v1/dashboard/collectors`)

    // 适配前端期望的格式
    return res.collectors.map(c => ({
      name: c.name,
      status: (c.status === 'success' ? 'running' : c.status === 'failed' ? 'error' : 'stopped') as 'running' | 'stopped' | 'error',
      last_update: c.last_run_time,
      data_count: 0,
    }))
  },
  getNews: async () => {
    const res = await apiFetch<{
      generated_at: string
      summary: { total_items: number }
      items: Array<{
        id?: string
        title: string
        source: string
        publish_time: string
        url?: string
        summary?: string
      }>
    }>(`${BASE}/api/v1/dashboard/news`)

    // 适配前端期望的格式
    return res.items.map((item, idx) => ({
      id: item.id || `news-${idx}`,
      title: item.title,
      source: item.source,
      timestamp: item.publish_time,
      url: item.url,
      summary: item.summary,
    }))
  },
  getHealth: () => apiFetch<{ status: string }>(`${BASE}/api/v1/health`),
}
