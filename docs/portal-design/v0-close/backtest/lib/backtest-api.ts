// backtest API 客户端
// 通过 next.config.mjs rewrite 代理到 localhost:8103

export interface HealthResponse {
  status: string
  service: string
}

export interface BacktestResult {
  id: string
  task_id: string
  name: string
  strategy: string
  status: string
  payload: {
    start: string
    end: string
    symbols: string[]
    contract: string
    params: Record<string, any>
    strategy: any
  }
  contracts: string[]
  submitted_at: number
  progress: number
  current_date: string
  trades: any[]
  equity_curve: any[]
  error_message: string | null
  totalReturn: number
  annualReturn: number
  maxDrawdown: number
  sharpeRatio: number
  winRate: number
  profitLossRatio: number
  totalTrades: number
  initialCapital: number
  finalCapital: number
}

export interface BacktestHistoryParams {
  start_date?: string
  end_date?: string
}

export interface PerformanceMetrics {
  annual_return: number
  max_drawdown: number
  sharpe_ratio: number
  calmar_ratio: number
  win_rate: number
  profit_loss_ratio: number
  total_trades: number
}

export interface QualityMetrics {
  out_of_sample_performance: number
  overfitting_score: number
  stability_score: number
  parameter_sensitivity: number
  data_quality_score: number
}

export interface BatchBacktestParams {
  strategy_id: string
  param_grid: Record<string, number[]>
  start: string
  end: string
  symbols: string[]
}

const BASE = "/api/backtest"

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" })
  if (!res.ok) throw new Error(`${path} → ${res.status}`)
  return res.json()
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  })
  if (!res.ok) throw new Error(`${path} → ${res.status}`)
  return res.json()
}

export const backtestApi = {
  // 健康检查
  health: () => get<HealthResponse>("/health"),

  // P0-1: 回测历史
  backtestHistory: (params?: BacktestHistoryParams) => {
    const query = new URLSearchParams()
    if (params?.start_date) query.append("start_date", params.start_date)
    if (params?.end_date) query.append("end_date", params.end_date)
    const queryString = query.toString() ? `?${query.toString()}` : ""
    return get<{ history: BacktestResult[]; count: number }>(`/history${queryString}`)
  },

  // P0-2: 策略参数验证
  validateParams: (params: { strategy_id: string; params: Record<string, any> }) =>
    post<{ valid: boolean; errors: string[] }>("/validate", params),

  // P0-3: 回测进度（SSE 在组件中直接使用 EventSource）
  progressUrl: (taskId: string) => `${BASE}/progress/${taskId}`,

  // P1-1: 绩效 KPI
  performanceKPI: (taskId: string) =>
    get<{ performance: PerformanceMetrics; timestamp: string }>(`/results/${taskId}/performance`),

  // P1-2: 质量 KPI
  qualityKPI: (taskId: string) =>
    get<{ quality: QualityMetrics; timestamp: string }>(`/results/${taskId}/quality`),

  // P1-3: 批量回测
  batchBacktest: (params: BatchBacktestParams) =>
    post<{ task_ids: string[]; total: number }>("/batch", params),

  // 现有 API（从 api.ts 迁移）
  summary: () => get<any>("/summary"),
  results: () => get<BacktestResult[]>("/results"),
  resultById: (taskId: string) => get<BacktestResult>(`/results/${taskId}`),
  equity: (taskId: string) => get<any[]>(`/results/${taskId}/equity`),
  trades: (taskId: string) => get<any[]>(`/results/${taskId}/trades`),
  progress: (taskId: string) => get<{ task_id: string; status: string; progress: number; current_date: string }>(`/progress/${taskId}`),
  cancel: (taskId: string) => post<{ task_id: string; status: string }>(`/cancel/${taskId}`, {}),

  // 运行回测
  run: (payload: any) => post<any>("/run", payload),

  // 调整回测
  adjust: (payload: any) => post<any>("/adjust", payload),
}
