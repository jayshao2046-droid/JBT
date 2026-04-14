import { apiFetch } from "./fetcher"

const BASE = "/api/backtest"

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
  name: string
  description: string
  params: Record<string, unknown>
  status: string
}

export interface BacktestJob {
  id: string
  strategy_name: string
  status: "pending" | "running" | "completed" | "failed"
  progress: number
  created_at: string
  completed_at?: string
}

export interface BacktestResult {
  task_id: string
  strategy_name: string
  performance: PerformanceMetrics
  equity_curve: Array<{ timestamp: string; equity: number }>
  trades: TradeRecord[]
}

export interface SystemStatus {
  cpu_usage: number
  memory_usage: number
  uptime: number
  active_jobs: number
}

export const backtestApi = {
  // 健康检查
  getHealth: () => apiFetch<{ status: string }>(`${BASE}/health`),

  // 系统状态
  getSystemStatus: () => apiFetch<SystemStatus>(`${BASE}/system/status`),

  // 策略管理
  getStrategies: () => apiFetch<{ strategies: Strategy[] }>(`${BASE}/strategies`),
  getStrategy: (name: string) => apiFetch<Strategy>(`${BASE}/strategy/${name}`),
  getStrategyParams: (name: string) => apiFetch<{ params: Record<string, unknown> }>(`${BASE}/strategy/${name}/params`),
  validateStrategy: (code: string) => apiFetch<{ valid: boolean; errors?: string[] }>(`${BASE}/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  }),

  // 回测任务
  runBacktest: (params: { strategy_name: string; params: Record<string, unknown>; start_date: string; end_date: string }) =>
    apiFetch<{ task_id: string }>(`${BASE}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    }),
  enqueueBacktest: (params: { strategy_name: string; params: Record<string, unknown> }) =>
    apiFetch<{ job_id: string }>(`${BASE}/enqueue`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    }),

  // 任务管理
  getJobs: () => apiFetch<{ jobs: BacktestJob[] }>(`${BASE}/jobs`),
  getJob: (jobId: string) => apiFetch<BacktestJob>(`${BASE}/jobs/${jobId}`),

  // 队列管理
  getQueueStatus: () => apiFetch<{ pending: number; running: number; completed: number }>(`${BASE}/queue/status`),

  // 结果查询
  getResults: () => apiFetch<{ results: BacktestResult[] }>(`${BASE}/results`),
  getResult: (taskId: string) => apiFetch<BacktestResult>(`${BASE}/results/${taskId}`),
  getEquityCurve: (taskId: string) => apiFetch<{ equity_curve: Array<{ timestamp: string; equity: number }> }>(`${BASE}/results/${taskId}/equity`),
  getTrades: (taskId: string) => apiFetch<{ trades: TradeRecord[] }>(`${BASE}/results/${taskId}/trades`),
  getPerformance: (taskId: string) => apiFetch<{ performance: PerformanceMetrics }>(`${BASE}/results/${taskId}/performance`),

  // 历史记录
  getHistory: () => apiFetch<{ history: HistoryEntry[] }>(`${BASE}/history`),
  getStrategyHistory: (strategyId: string) => apiFetch<{ history: HistoryEntry[] }>(`${BASE}/history/${strategyId}`),
}
