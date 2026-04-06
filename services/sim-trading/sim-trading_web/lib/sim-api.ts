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

export const simApi = {
  health: () => get<HealthResponse>("/health"),
  status: () => get<StatusResponse>("/api/v1/status"),
  positions: () => get<PositionsResponse>("/api/v1/positions"),
  orders: () => get<OrdersResponse>("/api/v1/orders"),
}
