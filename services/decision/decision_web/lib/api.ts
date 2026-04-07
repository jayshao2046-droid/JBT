/**
 * api.ts — JBT Decision Web API Client
 * 所有请求通过 /api/decision/ 代理到 decision 服务 (port 8104)
 */

const BASE = "/api/decision"

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" })
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`)
  return res.json()
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  })
  if (!res.ok) throw new Error(`API POST ${path} → ${res.status}`)
  return res.json()
}

// ── Health ────────────────────────────────────────────────────────────────────
export const fetchHealth = () => get<{ status: string; service: string; port: number }>("/health")
export const fetchReady = () => get<{ ready: boolean }>("/ready")

// ── Strategies ────────────────────────────────────────────────────────────────
export interface StrategyPackage {
  strategy_id: string
  strategy_name: string
  strategy_version: string
  template_id: string
  package_hash: string
  factor_version_hash: string
  factor_sync_status: "aligned" | "mismatch" | "unknown"
  research_snapshot_id: string
  backtest_certificate_id: string
  risk_profile_hash: string
  config_snapshot_ref: string
  lifecycle_status: string
  allowed_targets: string[]
  publish_target?: string
  live_visibility_mode: string
  reserved_at?: string
  published_at?: string
  retired_at?: string
  created_at: string
  updated_at: string
}

export const fetchStrategies = () => get<StrategyPackage[]>("/strategies")
export const fetchStrategy = (id: string) => get<StrategyPackage>(`/strategies/${id}`)

// ── Signals (Decision Records) ────────────────────────────────────────────────
export interface DecisionRecord {
  decision_id: string
  request_id: string
  trace_id: string
  strategy_id: string
  action: string
  confidence: number
  layer: string
  model_profile: {
    profile_id: string
    model_name: string
    deployment_class: string
    route_role: string
  }
  eligibility_status: string
  publish_target?: string | null
  publish_workflow_status: string
  reasoning_summary: string
  notification_event_id?: string | null
  generated_at: string
}

export const fetchSignals = () => get<DecisionRecord[]>("/signals")
export const fetchSignal = (id: string) => get<DecisionRecord>(`/signals/${id}`)

// ── Approvals ─────────────────────────────────────────────────────────────────
export interface ApprovalRecord {
  approval_id: string
  decision_id: string
  agent: string
  result?: string
  notes?: string
  submitted_at: string
  completed_at?: string
}

export const fetchApprovals = () => get<ApprovalRecord[]>("/approvals")
export const fetchApproval = (id: string) => get<ApprovalRecord>(`/approvals/${id}`)
export const submitApproval = (decision_id: string, agent: string, notes?: string) =>
  post<ApprovalRecord>("/approvals/submit", { decision_id, agent, notes })
export const completeApproval = (approval_id: string, result: "approved" | "rejected", notes?: string) =>
  post<ApprovalRecord>(`/approvals/${approval_id}/complete`, { result, notes })

// ── Models ────────────────────────────────────────────────────────────────────
export interface ModelStatus {
  model_router_require_backtest_cert: boolean
  model_router_require_research_snapshot: boolean
  execution_gate_enabled: boolean
  execution_gate_target: string
  live_trading_gate_locked: boolean
}

export const fetchModelStatus = () => get<ModelStatus>("/models/status")
export const routeModel = (strategy_id: string, context?: Record<string, unknown>) =>
  post<{ model: string; strategy_id: string }>("/models/route", { strategy_id, ...(context ?? {}) })

// ── Lifecycle ─────────────────────────────────────────────────────────────────
export const fetchStrategyLifecycle = (strategy_id: string) =>
  get<{ strategy_id: string; lifecycle_status: string; allowed_targets: string[] }>(
    `/strategies/${strategy_id}/lifecycle`
  )
