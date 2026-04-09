/**
 * api.ts — JBT Decision Web API Client
 * 所有请求通过 /api/decision/ 代理到 decision 服务 (port 8104)
 */

const API_BASE = process.env.NEXT_PUBLIC_DECISION_API_BASE ?? "/api/decision"

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  })

  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status}`)
  }

  return res.json()
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    throw new Error(`POST ${path} failed: ${res.status}`)
  }

  return res.json()
}

export interface HealthStatus {
  status: string
  service: string
  port: number
}

export interface ReadyStatus {
  ready: boolean
}

export interface StrategyApprovalSummary {
  approval_id: string
  strategy_id: string
  target: string
  requester: string
  justification: string
  approval_status: string
  result?: string | null
  submitted_at: string
  completed_at?: string | null
}

export interface StrategyPackage {
  strategy_id: string
  strategy_name: string
  lifecycle_status: string
  artifact_uri: string
  factor_ids: string[]
  factor_version_hash: string
  backtest_certificate_id?: string | null
  research_snapshot_id?: string | null
  model_id?: string | null
  publish_target?: string | null
  allowed_targets: string[]
  factor_sync_status: string
  imported_at: string
  updated_at: string
  created_at?: string
  template_id?: string
  strategy_version?: string
  backtest_cert_id?: string | null
  backtest_cert_status?: string
  backtest_cert_expires_at?: string | null
  research_snapshot_status?: string
  research_snapshot_valid_until?: string | null
  pending_approvals?: number
  latest_approval?: StrategyApprovalSummary | null
  publish_readiness?: {
    target: string
    eligible: boolean
    reasons: string[]
  }
}

export interface DecisionRecord {
  decision_id: string
  request_id: string
  trace_id: string
  strategy_id: string
  requested_target?: string
  symbol?: string
  requested_signal?: string
  requested_signal_strength?: number
  factor_count?: number
  factor_names?: string[]
  market_context?: Record<string, unknown>
  action: string
  confidence: number
  layer: string
  model_profile: Record<string, unknown>
  eligibility_status: string
  publish_target: string
  publish_gate_eligible?: boolean
  publish_workflow_status: string
  gate_reasons?: string[]
  decision_stage?: string
  reasoning_summary: string
  notification_event_id?: string | null
  generated_at: string
  latency_ms?: number
  eligibility_result?: Record<string, unknown>
}

export interface ApprovalRecord {
  approval_id: string
  strategy_id: string
  target: string
  requester: string
  justification: string
  approval_status: string
  result?: string | null
  submitted_at: string
  completed_at?: string | null
}

export interface ModelStatus {
  model_router_require_backtest_cert: boolean
  model_router_require_research_snapshot: boolean
  execution_gate_enabled: boolean
  execution_gate_target: string
  live_trading_gate_locked: boolean
}

export interface StrategyOverviewResponse {
  generated_at: string
  state_store: {
    path: string
    exists: boolean
  }
  runtime: {
    strategy_count: number
    approval_count: number
    execution_target: string
    live_trading_gate_locked: boolean
  }
  kpis: {
    total: number
    publish_ready: number
    published: number
    research_ready: number
    backtest_ready: number
    factor_aligned: number
    pending_approvals: number
  }
  lifecycle_counts: Array<{
    key: string
    label: string
    count: number
  }>
  pipeline: Array<{
    key: string
    label: string
    count: number
  }>
  blockers: Array<{
    key: string
    label: string
    count: number
    severity: string
  }>
  pending_actions: Array<{
    type: string
    strategy_id: string
    strategy_name: string
    lifecycle_status: string
    detail: string
    updated_at: string
  }>
  research_readiness: {
    research_ready: number
    research_missing: number
    backtest_ready: number
    backtest_missing: number
    factor_aligned: number
    factor_mismatch: number
    live_locked: number
  }
  strategies: StrategyPackage[]
}

export interface NotificationChannelStatus {
  channel: string
  status: string
  enabled: boolean
  configured: boolean
  attempts: number
  successes: number
  failures: number
  success_rate: number | null
  last_attempt_at?: string | null
  last_success_at?: string | null
  last_event_code?: string | null
  last_title?: string | null
  last_error?: string | null
}

export interface NotificationEventRecord {
  event_code: string
  event_type: string
  notify_level: string
  title: string
  strategy_id?: string | null
  model_id?: string | null
  signal_id?: string | null
  session_id?: string | null
  trace_id?: string | null
  dispatched_at: string
  dispatch_state: string
  channels: {
    feishu: boolean
    email: boolean
  }
  extra: Record<string, unknown>
}

export interface DailyReportSummary {
  report_date: string
  generated_at: string
  strategies_total: number
  strategies_active: number
  strategies_pending: number
  signals_generated: number
  signals_approved: number
  signals_rejected: number
  signals_pending: number
  research_sessions_total: number
  research_sessions_completed: number
  research_sessions_failed: number
  publishes_to_sim: number
  publishes_success: number
  publishes_failed: number
  research_summaries: Array<Record<string, unknown>>
  extra: Record<string, unknown>
}

export interface SignalOverviewResponse {
  generated_at: string
  kpis: {
    total: number
    approved: number
    hold: number
    blocked: number
    ready_for_publish: number
    locked_visible: number
  }
  stage_counts: Array<{
    key: string
    label: string
    count: number
  }>
  timeline: Array<{
    decision_id: string
    generated_at: string
    strategy_id: string
    symbol?: string
    action: string
    eligibility_status: string
    publish_workflow_status: string
    summary: string
  }>
  recent_signals: DecisionRecord[]
  notification_channels: NotificationChannelStatus[]
  recent_events: NotificationEventRecord[]
  dispatcher_state: string
  daily_report: {
    latest_report: DailyReportSummary
    last_sent_at?: string | null
    history: Array<{
      report_date: string
      generated_at: string
      dispatch_state: string
      summary: DailyReportSummary
    }>
    has_sent_history: boolean
  }
  empty_states: {
    signals: boolean
    events: boolean
    daily_history: boolean
  }
}

export interface ModelRuntimeOverview {
  generated_at: string
  runtime_status: {
    health: string
    state_store_path: string
    state_store_exists: boolean
    strategies_total: number
    approvals_total: number
    backtest_certs_total: number
    research_snapshots_total: number
    decision_records_total: number
    dispatcher_state: string
  }
  execution_gate: {
    enabled: boolean
    target: string
    live_trading_locked: boolean
    summary: string
  }
  model_router: {
    require_backtest_cert: boolean
    require_research_snapshot: boolean
    eligible_strategies: number
    blocked_strategies: number
  }
  local_models: Array<{
    profile_id: string
    model_name: string
    deployment_class: string
    route_role: string
    status: string
    source: string
  }>
  online_models: Array<{
    profile_id: string
    model_name: string
    deployment_class: string
    route_role: string
    status: string
    source: string
  }>
  factor_sync: {
    aligned: number
    mismatch: number
    unknown: number
    note: string
  }
  research_window: {
    timezone: string
    start: string
    end: string
    current_time: string
    is_open: boolean
    rule: string
  }
  service_integrations: Array<{
    name: string
    status: string
    url: string
    timeout_seconds: number | null
    note: string
  }>
}

// --- Request types ---

export interface StrategyCreateRequest {
  strategy_id: string
  strategy_name: string
  strategy_version: string
  template_id: string
  package_hash: string
  factor_version_hash: string
  factor_sync_status: string
  research_snapshot_id?: string | null
  backtest_certificate_id?: string | null
  risk_profile_hash?: string | null
  config_snapshot_ref?: string | null
  allowed_targets: string[]
  publish_target?: string | null
  live_visibility_mode?: string
}

export interface StrategyPublishRequest {
  target: "sim-trading" | "live-trading"
}

export interface StrategyPublishResponse {
  status: string
  message: string
  target: string
  strategy: StrategyPackage
  adapter_response?: Record<string, unknown>
}

export interface ApprovalSubmitRequest {
  strategy_id: string
  target: "sim-trading" | "live-trading"
  requester?: string
  notes?: string
}

export interface ApprovalCompleteRequest {
  result: "approve" | "reject"
  notes?: string
}

export interface StrategyLifecycle {
  strategy_id: string
  lifecycle_status: string
  updated_at: string
}

// --- Fetch functions ---

export function fetchHealth() {
  return get<HealthStatus>("/health")
}

export function fetchReady() {
  return get<ReadyStatus>("/ready")
}

export function fetchStrategies() {
  return get<StrategyPackage[]>("/strategies")
}

export function fetchStrategy(strategyId: string) {
  return get<StrategyPackage>(`/strategies/${strategyId}`)
}

export function fetchStrategyOverview() {
  return get<StrategyOverviewResponse>("/strategies/overview")
}

export function fetchStrategyLifecycle(strategyId: string) {
  return get<StrategyLifecycle>(`/strategies/${strategyId}/lifecycle`)
}

export function createStrategy(body: StrategyCreateRequest) {
  return post<StrategyPackage>("/strategies", body)
}

export function publishStrategy(strategyId: string, body: StrategyPublishRequest) {
  return post<StrategyPublishResponse>(`/strategies/${strategyId}/publish`, body)
}

export function fetchSignals() {
  return get<DecisionRecord[]>("/signals")
}

export function fetchSignal(decisionId: string) {
  return get<DecisionRecord>(`/signals/${decisionId}`)
}

export function fetchSignalOverview() {
  return get<SignalOverviewResponse>("/signals/overview")
}

export function fetchApprovals() {
  return get<ApprovalRecord[]>("/approvals")
}

export function submitApproval(body: ApprovalSubmitRequest) {
  return post<ApprovalRecord>("/approvals/submit", body)
}

export function completeApproval(approvalId: string, body: ApprovalCompleteRequest) {
  return post<ApprovalRecord>(`/approvals/${approvalId}/complete`, body)
}

export function fetchModelStatus() {
  return get<ModelStatus>("/models/status")
}

export function fetchRuntimeOverview() {
  return get<ModelRuntimeOverview>("/models/runtime")
}

export function reviewSignal(body: Record<string, unknown>) {
  return post<DecisionRecord>("/signals/review", body)
}

export function routeModel(body: Record<string, unknown>) {
  return post<{ allowed: boolean; reason: string }>("/models/route", body)
}
