const BASE_URL = "/api/data/api/v1"

export interface CollectorSummary {
  total: number
  success: number
  failed: number
  delayed: number
  idle: number
}

export interface CollectorItem {
  id: string
  name: string
  category: string
  status: "success" | "failed" | "delayed" | "idle"
  last_result: string
  age_str: string
  age_h: number
  threshold_h: number
  schedule_expr: string
  schedule_type: string
  last_run_time: string | null
  data_source: string
  output_dir: string
  trading_only: boolean
  skipped: boolean
  description: string
  errors: Array<{ message: string }>
}

export interface ResourceCpu {
  usage_percent: number
  logical_cores: number
}

export interface ResourceMem {
  used_percent: number
  total_mb: number
  used_mb: number
}

export interface ResourceDisk {
  used_percent: number
  total_bytes: number
  used_bytes: number
  free_bytes: number
}

export interface ProcessEntry {
  id: string
  name: string
  status: "running" | "warning" | "stopped"
  pid: number | null
  uptime: string | null
  cpu_usage: number
  mem_usage: number
  last_heartbeat: string | null
  is_single_instance: boolean
}

export interface NotifChannel {
  id: string
  name: string
  type: "feishu" | "email"
  configured: boolean
  last_send_time: string | null
  last_status: "success" | "failed"
}

export interface SourceItem {
  name: string
  label: string
  ok: boolean
  age_h: number
  age_str: string
  threshold_h: number
  skipped: boolean
}

export interface LogEntry {
  timestamp: string | null
  level: string
  source: string
  message: string
}

export interface CollectorsResponse {
  generated_at: string
  summary: CollectorSummary
  collectors: CollectorItem[]
}

export interface SystemResponse {
  generated_at: string
  resources: {
    cpu: ResourceCpu
    memory: ResourceMem
    disk: ResourceDisk
  }
  processes: ProcessEntry[]
  notifications: NotifChannel[]
  sources: SourceItem[]
  logs: LogEntry[]
}

export interface StorageTotals {
  size_bytes: number
  size_human: string
  files: number
  directories: number
  last_modified: string | null
}

export interface DirectoryEntry {
  name: string
  path: string
  type: string
  size_human: string
  file_count: number
  dir_count: number
  last_modified: string | null
}

export interface TreeNode {
  name: string
  path: string
  type: "folder" | "file"
  size_human: string
  file_count: number
  dir_count: number
  last_modified: string | null
  truncated: boolean
  suffix?: string
  children?: TreeNode[]
}

export interface StorageResponse {
  generated_at: string
  root_label: string
  exists: boolean
  totals: StorageTotals
  directories: DirectoryEntry[]
  tree: TreeNode[]
}

export interface NewsItem {
  id: string
  title: string
  source: string
  publish_time: string
  summary: string
  keywords: string[]
  sentiment: "positive" | "negative" | "neutral"
  is_important: boolean
  is_pushed: boolean
  file: string
}

export interface HotKeyword {
  word: string
  count: number
}

export interface PushRecord {
  title: string
  source: string
  time: string
}

export interface SentimentBucket {
  sentiment: string
  count: number
}

export interface NewsResponse {
  generated_at: string
  summary: {
    total_items: number
    important_count: number
    pushed_count: number
    source_count: number
  }
  items: NewsItem[]
  hot_keywords: HotKeyword[]
  source_breakdown: Array<{ source: string; count: number }>
  push_records: PushRecord[]
  sentiment_distribution: SentimentBucket[]
}

export const dataApi = {
  async getCollectors(): Promise<CollectorsResponse> {
    const res = await fetch(`${BASE_URL}/dashboard/collectors`)
    if (!res.ok) throw new Error("Failed to fetch collectors")
    return res.json()
  },

  async getSystem(): Promise<SystemResponse> {
    const res = await fetch(`${BASE_URL}/dashboard/system`)
    if (!res.ok) throw new Error("Failed to fetch system")
    return res.json()
  },

  async getStorage(maxDepth = 2, maxChildren = 20): Promise<StorageResponse> {
    const res = await fetch(
      `${BASE_URL}/dashboard/storage?max_depth=${maxDepth}&max_children=${maxChildren}`
    )
    if (!res.ok) throw new Error("Failed to fetch storage")
    return res.json()
  },

  async getNews(): Promise<NewsResponse> {
    const res = await fetch(`${BASE_URL}/dashboard/news`)
    if (!res.ok) throw new Error("Failed to fetch news")
    return res.json()
  },

  async restartCollector(collectorId: string): Promise<void> {
    const res = await fetch(
      `${BASE_URL}/ops/restart-collector?collector=${encodeURIComponent(collectorId)}`,
      { method: "POST" }
    )
    if (!res.ok) throw new Error("Failed to restart collector")
  },

  async autoRemediate(): Promise<void> {
    const res = await fetch(`${BASE_URL}/ops/auto-remediate`, { method: "POST" })
    if (!res.ok) throw new Error("Failed to auto-remediate")
  },

  async getHealth(): Promise<{ status: string }> {
    const res = await fetch("/api/data/api/v1/health")
    if (!res.ok) throw new Error("Failed to fetch health")
    return res.json()
  },
}
