"use client"

import { useEffect, useState } from "react"
import { RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import Sidebar from "@/components/layout/sidebar"
import DecisionOverview from "@/components/decision/overview"
import SignalReview from "@/components/decision/signal-review"
import ModelsFactors from "@/components/decision/models-factors"
import StrategyRepository from "@/components/decision/strategy-repository"
import ResearchCenter from "@/components/decision/research-center"
import NotificationsReport from "@/components/decision/notifications-report"
import ConfigRuntime from "@/components/decision/config-runtime"
import { fetchHealth, fetchRuntimeOverview, type HealthStatus, type ModelRuntimeOverview } from "@/lib/api"

const sectionNames: Record<string, string> = {
  overview: "总览",
  signal: "信号审查",
  models: "模型与因子",
  repository: "策略仓库",
  research: "研究中心",
  notifications: "通知与日报",
  config: "配置与运行",
}

function formatStatusTime(raw?: string | null) {
  if (!raw) return new Date().toLocaleString("zh-CN")
  const date = new Date(raw)
  return Number.isNaN(date.getTime()) ? raw : date.toLocaleString("zh-CN")
}

function getDotClass(active: boolean, activeColor: string) {
  return `w-2 h-2 rounded-full ${active ? activeColor : "bg-neutral-600"}`
}

function getTextClass(active: boolean, activeColor: string, inactiveColor = "text-neutral-500") {
  return active ? activeColor : inactiveColor
}

export default function DecisionConsole() {
  const [activeSection, setActiveSection] = useState("overview")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [refreshToken, setRefreshToken] = useState(0)
  const [headerLoading, setHeaderLoading] = useState(true)
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [runtime, setRuntime] = useState<ModelRuntimeOverview | null>(null)
  const [lastRefreshAt, setLastRefreshAt] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadHeader() {
      setHeaderLoading(true)

      try {
        const [healthSnapshot, runtimeSnapshot] = await Promise.all([
          fetchHealth(),
          fetchRuntimeOverview(),
        ])

        if (cancelled) return
        setHealth(healthSnapshot)
        setRuntime(runtimeSnapshot)
        setLastRefreshAt(new Date().toISOString())
      } catch {
        if (cancelled) return
        setHealth(null)
        setRuntime(null)
      } finally {
        if (!cancelled) {
          setHeaderLoading(false)
        }
      }
    }

    void loadHeader()

    return () => {
      cancelled = true
    }
  }, [refreshToken])

  const renderContent = () => {
    const props = { refreshToken }

    switch (activeSection) {
      case "overview":
        return <DecisionOverview {...props} />
      case "signal":
        return <SignalReview {...props} />
      case "models":
        return <ModelsFactors {...props} />
      case "repository":
        return <StrategyRepository {...props} />
      case "research":
        return <ResearchCenter {...props} />
      case "notifications":
        return <NotificationsReport {...props} />
      case "config":
        return <ConfigRuntime {...props} />
      default:
        return <DecisionOverview {...props} />
    }
  }

  const localModelsReady = (runtime?.local_models.length ?? 0) > 0 && health?.status === "ok"
  const onlineModelsReady = (runtime?.online_models.length ?? 0) > 0
  const researchWindowOpen = runtime?.research_window?.is_open ?? false

  return (
    <div className="flex h-screen bg-neutral-950">
      <Sidebar
        activeSection={activeSection}
        collapsed={sidebarCollapsed}
        onSectionChange={setActiveSection}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${sidebarCollapsed ? "ml-16" : "ml-64"}`}
      >
        <div className="h-14 bg-neutral-800 border-b border-neutral-700 flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center gap-6 text-sm">
            <span className="text-neutral-400">
              JBT / <span className="text-orange-500 font-medium">{sectionNames[activeSection]}</span>
            </span>
            <div className="flex items-center gap-4 ml-4 border-l border-neutral-700 pl-4">
              <div className="flex items-center gap-2">
                <div className={getDotClass(localModelsReady, "bg-green-400")}></div>
                <span className="text-neutral-400 text-xs">
                  本地模型: <span className={getTextClass(localModelsReady, "text-green-400")}>{localModelsReady ? "就绪" : headerLoading ? "加载中" : "缺失"}</span>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className={getDotClass(onlineModelsReady, "bg-blue-400")}></div>
                <span className="text-neutral-400 text-xs">
                  在线L3: <span className={getTextClass(onlineModelsReady, "text-blue-400")}>{onlineModelsReady ? "连接" : headerLoading ? "加载中" : "未配置"}</span>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className={getDotClass(researchWindowOpen, "bg-orange-400")}></div>
                <span className="text-neutral-400 text-xs">
                  研究窗: <span className={getTextClass(researchWindowOpen, "text-orange-400")}>{researchWindowOpen ? "开启" : headerLoading ? "加载中" : "关闭"}</span>
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs text-neutral-500">
              {formatStatusTime(lastRefreshAt)}
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="text-neutral-400 hover:text-orange-500 hover:bg-neutral-700"
              onClick={() => setRefreshToken((value) => value + 1)}
            >
              <RefreshCw className={`w-4 h-4 ${headerLoading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-auto bg-neutral-950">
          {renderContent()}
        </div>
      </div>
    </div>
  )
}
