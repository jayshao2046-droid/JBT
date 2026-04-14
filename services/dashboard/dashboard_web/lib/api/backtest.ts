import { apiFetch } from "./fetcher"

// 代理规则：/api/backtest/:path* → http://localhost:8103/:path*（完整剥离前缀）
// backtest 后端实际路由分三组：
//   /api/backtest/*   → 回测运行/结果
//   /api/*            → 策略/系统管理
//   /api/v1/*         → 任务队列/审批
const PROXY = "/api/backtest"
const BASE = `${PROXY}/api/backtest`     // /api/backtest/* 路由组
const BASE_API = `${PROXY}/api`          // /api/strategies, /api/system/*, /api/health
const BASE_V1 = `${PROXY}/api/v1`        // /api/v1/jobs, /api/v1/strategy-queue/*

function asNumber(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0
}

function parseDurationToSeconds(value: unknown): number {
  if (typeof value !== "string" || value.length === 0) {
    return 0
  }

  const parts = value.split(":").map((part) => Number.parseInt(part, 10))
  if (parts.some((part) => Number.isNaN(part))) {
    return 0
  }

  if (parts.length === 3) {
    return parts[0] * 3600 + parts[1] * 60 + parts[2]
  }

  if (parts.length === 2) {
    return parts[0] * 60 + parts[1]
  }

  return parts.length === 1 ? parts[0] : 0
}

// 类型定义
export interface PerformanceMetrics {
  total_return: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  total_trades: number
}

export interface TradeRecord {
  timestamp: string
  symbol: string
  direction: string
  price: number
  volume: number
  pnl: number
}

export interface HistoryEntry {
  task_id: string
  strategy_name: string
  created_at: string
  status: string
  performance?: PerformanceMetrics
}

export interface Strategy {
  id?: string
  name: string
  description: string
  params: Record<string, unknown>
  status: string
}

interface RawStrategy extends Record<string, unknown> {
  id?: string
  name?: string
  description?: string
  params?: Record<string, unknown>
  status?: string
}

export interface BacktestJob {
  id: string
  strategy_name: string
  status: "pending" | "running" | "completed" | "failed"
  progress: number
  created_at: string
  completed_at?: string
  symbol?: string
}

interface RawBacktestJob {
  job_id: string
  strategy_template_id?: string
  strategy_yaml_filename?: string
  symbol?: string
  status: "pending" | "running" | "completed" | "failed"
  created_at: string
  updated_at?: string
}

interface RawBacktestJobList {
  total: number
  page: number
  limit: number
  items: RawBacktestJob[]
}

export interface BacktestResult {
  task_id: string
  strategy_name: string
  performance: PerformanceMetrics
  equity_curve: Array<{ timestamp: string; equity: number }>
  trades: TradeRecord[]
}

type RawBacktestResult = Record<string, unknown>

export interface SystemStatus {
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  latency_ms: number
  uptime: number
  active_jobs: number
  services: Array<{
    id: string
    name: string
    status: string
    uptime: string
    requests: number
    latency: number
  }>
}

interface RawSystemStatus {
  cpu?: number
  memory?: number
  disk?: number
  latency?: number
  services?: Array<Record<string, unknown>>
}

interface RawQueueStatus {
  total_count: number
  queued_count: number
  running_count: number
  completed_count: number
  failed_count: number
  items: Array<Record<string, unknown>>
}

function normalizeStrategy(raw: RawStrategy): Strategy {
  return {
    id: typeof raw.id === "string" ? raw.id : undefined,
    name: typeof raw.name === "string" && raw.name.length > 0
      ? raw.name
      : typeof raw.id === "string" && raw.id.length > 0
        ? raw.id
        : "unknown-strategy",
    description: typeof raw.description === "string"
      ? raw.description
      : typeof raw.id === "string"
        ? `策略标识: ${raw.id}`
        : "暂无描述",
    params: raw.params && typeof raw.params === "object" ? raw.params : {},
    status: typeof raw.status === "string" ? raw.status : "unknown",
  }
}

function normalizeJob(raw: RawBacktestJob): BacktestJob {
  return {
    id: raw.job_id,
    strategy_name: raw.strategy_yaml_filename || raw.strategy_template_id || raw.symbol || raw.job_id,
    status: raw.status,
    progress: raw.status === "completed" ? 100 : 0,
    created_at: raw.created_at,
    completed_at: raw.status === "completed" ? raw.updated_at : undefined,
    symbol: raw.symbol,
  }
}

function normalizeResult(raw: RawBacktestResult): BacktestResult {
  const performance = raw.performance && typeof raw.performance === "object"
    ? raw.performance as Record<string, unknown>
    : {}

  return {
    task_id: typeof raw.task_id === "string"
      ? raw.task_id
      : typeof raw.id === "string"
        ? raw.id
        : "unknown-task",
    strategy_name: typeof raw.strategy_name === "string"
      ? raw.strategy_name
      : typeof raw.strategy_id === "string"
        ? raw.strategy_id
        : typeof raw.name === "string"
          ? raw.name
          : "unknown-strategy",
    performance: {
      total_return: asNumber(performance.total_return),
      sharpe_ratio: asNumber(performance.sharpe_ratio),
      max_drawdown: asNumber(performance.max_drawdown),
      win_rate: asNumber(performance.win_rate),
      total_trades: asNumber(performance.total_trades),
    },
    equity_curve: Array.isArray(raw.equity_curve)
      ? raw.equity_curve as Array<{ timestamp: string; equity: number }>
      : [],
    trades: Array.isArray(raw.trades)
      ? raw.trades as TradeRecord[]
      : [],
  }
}

function normalizeSystemStatus(raw: RawSystemStatus): SystemStatus {
  const services = Array.isArray(raw.services)
    ? raw.services.map((service) => ({
        id: typeof service.id === "string" ? service.id : "unknown-service",
        name: typeof service.name === "string" ? service.name : "unknown-service",
        status: typeof service.status === "string" ? service.status : "unknown",
        uptime: typeof service.uptime === "string" ? service.uptime : "0:00:00",
        requests: asNumber(service.requests),
        latency: asNumber(service.latency),
      }))
    : []

  const uptime = services.reduce((maxSeconds, service) => {
    const seconds = parseDurationToSeconds(service.uptime)
    return seconds > maxSeconds ? seconds : maxSeconds
  }, 0)

  return {
    cpu_usage: asNumber(raw.cpu),
    memory_usage: asNumber(raw.memory),
    disk_usage: asNumber(raw.disk),
    latency_ms: asNumber(raw.latency),
    uptime,
    active_jobs: services.filter((service) => service.status === "running").length,
    services,
  }
}

export const backtestApi = {
  // 健康检查
  getHealth: () => apiFetch<{ status: string }>(`${BASE_API}/health`),

  // 系统状态
  getSystemStatus: async () => {
    const raw = await apiFetch<RawSystemStatus>(`${BASE_API}/system/status`)
    return normalizeSystemStatus(raw)
  },

  // 策略管理
  getStrategies: async () => {
    const raw = await apiFetch<RawStrategy[]>(`${BASE_API}/strategies`)
    return Array.isArray(raw) ? raw.map(normalizeStrategy) : []
  },
  getStrategy: async (name: string) => {
    const raw = await apiFetch<RawStrategy>(`${BASE_API}/strategy/${name}`)
    return normalizeStrategy(raw)
  },
  getStrategyParams: (name: string) => apiFetch<{ params: Record<string, unknown> }>(`${BASE_API}/strategy/${name}/params`),

  // 回测任务（/api/backtest/* 路由组）
  runBacktest: (params: { strategy_name: string; params: Record<string, unknown>; start_date: string; end_date: string }) =>
    apiFetch<{ task_id: string }>(`${BASE}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    }),
  getSummary: () => apiFetch<{ summary: unknown }>(`${BASE}/summary`),
  cancelBacktest: (taskId: string) => apiFetch<{ status: string }>(`${BASE}/cancel/${taskId}`, { method: "POST" }),
  getProgress: (taskId: string) => apiFetch<{ progress: number; status: string }>(`${BASE}/progress/${taskId}`),

  // 队列任务管理（/api/v1/* 路由组）
  enqueueBacktest: (params: { strategy_name: string; params: Record<string, unknown> }) =>
    apiFetch<{ job_id: string }>(`${BASE_V1}/strategy-queue/enqueue`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    }),
  getJobs: async () => {
    const raw = await apiFetch<RawBacktestJobList>(`${BASE_V1}/jobs`)
    return Array.isArray(raw.items) ? raw.items.map(normalizeJob) : []
  },
  getJob: async (jobId: string) => {
    const raw = await apiFetch<RawBacktestJob>(`${BASE_V1}/jobs/${jobId}`)
    return normalizeJob(raw)
  },
  getQueueStatus: async () => {
    const raw = await apiFetch<RawQueueStatus>(`${BASE_V1}/strategy-queue/status`)
    return {
      pending: raw.queued_count,
      running: raw.running_count,
      completed: raw.completed_count,
      failed: raw.failed_count,
      total: raw.total_count,
      items: Array.isArray(raw.items) ? raw.items : [],
    }
  },
  clearQueue: () => apiFetch<{ status: string }>(`${BASE_V1}/strategy-queue/clear`, { method: "POST" }),

  // 结果查询（/api/backtest/* 路由组）
  getResults: async () => {
    const raw = await apiFetch<RawBacktestResult[]>(`${BASE}/results`)
    return Array.isArray(raw) ? raw.map(normalizeResult) : []
  },
  getResult: async (taskId: string) => {
    const raw = await apiFetch<RawBacktestResult>(`${BASE}/results/${taskId}`)
    return normalizeResult(raw)
  },
  getEquityCurve: (taskId: string) => apiFetch<{ equity_curve: Array<{ timestamp: string; equity: number }> }>(`${BASE}/results/${taskId}/equity`),
  getTrades: (taskId: string) => apiFetch<{ trades: TradeRecord[] }>(`${BASE}/results/${taskId}/trades`),

  // 历史记录（按策略查询，需传 strategyId）
  getStrategyHistory: (strategyId: string) => apiFetch<{ history: HistoryEntry[] }>(`${BASE}/history/${strategyId}`),
}
