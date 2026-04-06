// sim-trading API 客户端
// 通过 next.config.mjs rewrite 代理到 localhost:8101

export interface HealthResponse {
  status: string
  service: string
}

export interface StatusResponse {
  status: string
  stage: string
}

export interface Position {
  id?: string | number
  contract?: string
  direction?: string
  quantity?: number
  avgPrice?: number
  currentPrice?: number
  floatPnl?: number
  stopLoss?: number
  takeProfit?: number
}

export interface PositionsResponse {
  positions: Position[]
  note?: string
}

export interface Order {
  id?: string
  time?: string
  contract?: string
  action?: string
  price?: number
  quantity?: number
  status?: string
  reason?: string | null
}

export interface OrdersResponse {
  orders: Order[]
  note?: string
}

const BASE = "/api/sim"

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

export interface SystemState {
  trading_enabled: boolean
  active_preset: string
  paused_reason: string | null
  ctp_md_connected: boolean
  ctp_td_connected: boolean
  ctp_broker_id: string
  ctp_user_id: string
  ctp_md_front: string
  ctp_td_front: string
}

export interface RiskPreset {
  name: string
  max_lots: number
  max_position: number
  daily_loss_pct: number
  price_dev_pct: number
  enabled: boolean
}

export const simApi = {
  health: () => get<HealthResponse>("/health"),
  status: () => get<StatusResponse>("/api/v1/status"),
  positions: () => get<PositionsResponse>("/api/v1/positions"),
  orders: () => get<OrdersResponse>("/api/v1/orders"),
  // 系统状态
  systemState: () => get<SystemState>("/api/v1/system/state"),
  pauseTrading: (reason = "手动暂停") => post<{result: string}>("/api/v1/system/pause", { reason }),
  resumeTrading: () => post<{result: string}>("/api/v1/system/resume"),
  setPreset: (preset: string) => post<{result: string}>("/api/v1/system/preset", { preset }),
  // CTP
  ctpConfig: () => get<Partial<SystemState>>("/api/v1/ctp/config"),
  saveCtp: (cfg: {broker_id:string; user_id:string; password:string; md_front:string; td_front:string}) =>
    post<{result:string}>("/api/v1/ctp/config", cfg),
  ctpConnect: () => post<{result:string}>("/api/v1/ctp/connect"),
  ctpDisconnect: () => post<{result:string}>("/api/v1/ctp/disconnect"),
  // 风控预设
  riskPresets: () => get<{presets: Record<string, RiskPreset>}>("/api/v1/risk-presets"),
  updateRiskPreset: (data: {symbol:string} & RiskPreset) =>
    post<{result:string}>("/api/v1/risk-presets", data),
}
