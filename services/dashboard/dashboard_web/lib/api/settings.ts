import { apiFetch } from "./fetcher"

const SIM_TRADING_BASE = "/api/sim-trading/api/v1"
const DATA_BASE = "/api/data/api/v1"
const DASHBOARD_BASE = "/api/dashboard/api/v1"

// 系统设置类型定义
export interface SystemSettings {
  account: AccountSettings
  trading: TradingSettings
  notifications: NotificationSettings
  services: ServiceStatus[]
}

export interface AccountSettings {
  username: string
  email: string
}

export interface TradingSettings {
  auto_trading_enabled: boolean
  pre_market_enabled: boolean
  post_market_enabled: boolean
  pre_market_minutes: number
  timezone: string
}

export interface TradingSession {
  id: number
  name: string
  label: string
  enabled: boolean
  start_time: string
  end_time: string
  sort_order: number
}

export type CalendarEntryType = "holiday" | "workday" | "early_close"

export interface CalendarEntry {
  id: number
  date: string
  type: CalendarEntryType
  label: string
  note: string
  trading_enabled: boolean
  created_at: string
}

export interface NotificationSettings {
  feishu_webhook: string
  smtp_server: string
  alert_enabled: boolean
}

export interface ServiceStatus {
  name: string
  status: "running" | "stopped" | "error"
  uptime?: number
}

export const settingsApi = {
  // 获取完整系统设置
  getSettings: async (): Promise<SystemSettings> => {
    // 并行获取各服务的配置
    const [simTradingState, dataHealth, dataNotifications, decisionHealth, backtestHealth] =
      await Promise.all([
        apiFetch<{
          trading_enabled: boolean
          active_preset: string
          paused_reason: string | null
        }>(`${SIM_TRADING_BASE}/system/state`).catch(() => null),
        apiFetch<{ status: string }>(`${DATA_BASE}/health`).catch(() => null),
        apiFetch<{
          feishu_webhook: string
          smtp_server: string
          smtp_port: number
          smtp_username: string
          alert_enabled: boolean
        }>(`${DATA_BASE}/settings/notifications`).catch(() => null),
        apiFetch<{ status: string }>("/api/decision/api/health").catch(() => null),
        apiFetch<{ status: string }>("/api/backtest/api/v1/health").catch(() => null),
      ])

    return {
      account: {
        username: "admin",
        email: "admin@jbt.com",
      },
      trading: {
        auto_trading_enabled: simTradingState?.trading_enabled ?? false,
        pre_market_enabled: true,
        post_market_enabled: true,
        pre_market_minutes: 30,
        timezone: "Asia/Shanghai",
      },
      notifications: {
        feishu_webhook: dataNotifications?.feishu_webhook ?? "",
        smtp_server: dataNotifications?.smtp_server ?? "",
        alert_enabled: dataNotifications?.alert_enabled ?? true,
      },
      services: [
        {
          name: "模拟交易",
          status: simTradingState ? "running" : "error",
        },
        {
          name: "回测系统",
          status: backtestHealth?.status === "ok" ? "running" : "error",
        },
        {
          name: "决策引擎",
          status: decisionHealth?.status === "ok" ? "running" : "error",
        },
        {
          name: "数据服务",
          status: dataHealth?.status === "ok" ? "running" : "error",
        },
      ],
    }
  },

  // 更新账户设置
  updateAccount: async (data: AccountSettings): Promise<{ success: boolean }> => {
    // Dashboard 只读，暂不实现写入
    console.log("Account update:", data)
    return { success: true }
  },

  // 更新交易设置
  updateTrading: async (data: Partial<TradingSettings>): Promise<{ success: boolean }> => {
    if (data.auto_trading_enabled !== undefined) {
      if (data.auto_trading_enabled) {
        await apiFetch<{ result: string }>(`${SIM_TRADING_BASE}/system/resume`, {
          method: "POST",
        })
      } else {
        await apiFetch<{ result: string }>(`${SIM_TRADING_BASE}/system/pause`, {
          method: "POST",
          body: JSON.stringify({ reason: "用户手动暂停" }),
        })
      }
    }
    return { success: true }
  },

  // 更新通知设置
  updateNotifications: async (data: NotificationSettings): Promise<{ success: boolean }> => {
    await apiFetch<{ success: boolean }>(`${DATA_BASE}/settings/notifications`, {
      method: "POST",
      body: JSON.stringify({
        feishu_webhook: data.feishu_webhook,
        smtp_server: data.smtp_server,
        smtp_port: 465,
        smtp_username: "",
        smtp_password: "",
        alert_enabled: data.alert_enabled,
      }),
    })
    return { success: true }
  },

  // 重启服务
  restartService: async (serviceName: string): Promise<{ success: boolean }> => {
    // Dashboard 只读，暂不实现服务重启
    console.log("Restart service:", serviceName)
    return { success: true }
  },
}

// ── 交易时段 & 日历 API ──────────────────────────────────────
function getDashboardHeaders(): HeadersInit {
  const token = typeof window !== "undefined" ? localStorage.getItem("jbt_token") : null
  const h: Record<string, string> = { "Content-Type": "application/json" }
  if (token) h["Authorization"] = `Bearer ${token}`
  return h
}

async function dashFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${DASHBOARD_BASE}${path}`, {
    ...init,
    headers: { ...getDashboardHeaders(), ...(init?.headers ?? {}) },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error((err as { detail?: string }).detail ?? "Request failed")
  }
  return res.json() as Promise<T>
}

export const tradingSessionsApi = {
  list: () => dashFetch<TradingSession[]>("/trading/sessions"),

  update: (id: number, data: Partial<Pick<TradingSession, "label" | "enabled" | "start_time" | "end_time">>) =>
    dashFetch<{ success: boolean }>(`/trading/sessions/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
}

export const tradingConfigApi = {
  get: () => dashFetch<Record<string, string>>("/trading/config"),

  update: (data: Record<string, string | boolean | number>) =>
    dashFetch<{ success: boolean }>("/trading/config", {
      method: "PUT",
      body: JSON.stringify(data),
    }),
}

export const calendarApi = {
  list: (year?: number) =>
    dashFetch<CalendarEntry[]>(`/trading/calendar${year ? `?year=${year}` : ""}`),

  add: (entry: Omit<CalendarEntry, "id" | "created_at">) =>
    dashFetch<CalendarEntry>("/trading/calendar", {
      method: "POST",
      body: JSON.stringify(entry),
    }),

  update: (id: number, entry: Omit<CalendarEntry, "id" | "created_at">) =>
    dashFetch<{ success: boolean }>(`/trading/calendar/${id}`, {
      method: "PUT",
      body: JSON.stringify(entry),
    }),

  remove: (id: number) =>
    dashFetch<{ success: boolean }>(`/trading/calendar/${id}`, { method: "DELETE" }),
}

// ── sim-trading 实时控制（经 Next.js server route 注入 X-API-Key）──────────
export const simControlApi = {
  getState: () => apiFetch<{
    trading_enabled: boolean
    active_preset: string
    paused_reason: string | null
    ctp_md_connected: boolean
    ctp_td_connected: boolean
  }>("/api/sim-trading/api/v1/system/state").catch(() => null),

  pause: (reason = "用户手动暂停") =>
    fetch("/api/sim-control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "pause", reason }),
    }).then(r => r.json()),

  resume: () =>
    fetch("/api/sim-control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "resume" }),
    }).then(r => r.json()),
}

// ── 通知配置 API ──────────────────────────────────────────
export interface ServiceNotifConfig {
  service: string
  display_name: string
  feishu_webhook: string
  feishu_enabled: boolean
  smtp_host: string
  smtp_port: number
  smtp_username: string
  smtp_password_set: boolean
  smtp_to_addrs: string
  smtp_enabled: boolean
  updated_at: string
}

export interface NotificationRule {
  id: number
  service: string
  name: string
  rule_type: "alarm_p0" | "alarm_p1" | "alarm_p2" | "trade" | "info" | "news" | "notify"
  color: "red" | "orange" | "yellow" | "grey" | "blue" | "wathet" | "turquoise"
  content_template: string
  enabled: boolean
  feishu_enabled: boolean
  smtp_enabled: boolean
  sort_order: number
  created_at: string
}

export const notificationApi = {
  listConfigs: () =>
    dashFetch<ServiceNotifConfig[]>("/notifications/configs"),

  updateConfig: (service: string, data: {
    feishu_webhook: string
    feishu_enabled: boolean
    smtp_host: string
    smtp_port: number
    smtp_username: string
    smtp_password: string
    smtp_to_addrs: string
    smtp_enabled: boolean
  }) =>
    dashFetch<{ success: boolean }>(`/notifications/configs/${service}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  testFeishu: (service: string) =>
    dashFetch<{ success: boolean; result?: unknown }>(`/notifications/configs/${service}/test-feishu`, {
      method: "POST",
    }),

  listRules: (service?: string) =>
    dashFetch<NotificationRule[]>(`/notifications/rules${service ? `?service=${service}` : ""}`),

  createRule: (data: Omit<NotificationRule, "id" | "sort_order" | "created_at">) =>
    dashFetch<{ id: number; success: boolean }>("/notifications/rules", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateRule: (id: number, data: Omit<NotificationRule, "id" | "sort_order" | "created_at">) =>
    dashFetch<{ success: boolean }>(`/notifications/rules/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteRule: (id: number) =>
    dashFetch<{ success: boolean }>(`/notifications/rules/${id}`, { method: "DELETE" }),
}
