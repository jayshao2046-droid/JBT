import { apiFetch } from "./fetcher"

const SIM_TRADING_BASE = "/api/sim-trading/api/v1"
const DATA_BASE = "/api/data/api/v1"

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
    const [simTradingState, dataHealth] = await Promise.all([
      apiFetch<{
        trading_enabled: boolean
        active_preset: string
        paused_reason: string | null
      }>(`${SIM_TRADING_BASE}/system/state`).catch(() => null),
      apiFetch<{ status: string }>(`${DATA_BASE}/health`).catch(() => null),
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
      },
      notifications: {
        feishu_webhook: "",
        smtp_server: "",
        alert_enabled: true,
      },
      services: [
        {
          name: "模拟交易",
          status: simTradingState ? "running" : "error",
        },
        {
          name: "回测系统",
          status: "running",
        },
        {
          name: "决策引擎",
          status: "running",
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
    // Dashboard 只读，暂不实现写入
    console.log("Notification update:", data)
    return { success: true }
  },

  // 重启服务
  restartService: async (serviceName: string): Promise<{ success: boolean }> => {
    // Dashboard 只读，暂不实现服务重启
    console.log("Restart service:", serviceName)
    return { success: true }
  },
}
