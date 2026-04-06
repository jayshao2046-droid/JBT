"use client"

import { useState, useEffect } from "react"
import { ChevronRight, ShieldAlert, TrendingUp, Bell, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import OperationsPage from "./operations/page"
import IntelligencePage from "./intelligence/page"
import { simApi } from "@/lib/sim-api"

export default function TradingDashboard() {
  const [activeSection, setActiveSection] = useState("intelligence")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [globalSwitch, setGlobalSwitch] = useState(true)
  const [serviceStage, setServiceStage] = useState("--")
  const [serviceOnline, setServiceOnline] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  const fetchStatus = async () => {
    try {
      const [health, status] = await Promise.all([simApi.health(), simApi.status()])
      setServiceOnline(health.status === "ok")
      setServiceStage(status.stage ?? "--")
    } catch {
      setServiceOnline(false)
    }
    setLastUpdate(new Date())
  }

  useEffect(() => {
    fetchStatus()
    const t = setInterval(fetchStatus, 10000)
    return () => clearInterval(t)
  }, [])

  const sectionNames: Record<string, string> = {
    operations: "交易终端",
    intelligence: "风控监控",
  }

  return (
    <div className="flex h-screen bg-neutral-950">
      {/* 侧边栏 */}
      <div
        className={`${sidebarCollapsed ? "w-16" : "w-64"} bg-neutral-900 border-r border-neutral-700 transition-all duration-300 fixed left-0 top-0 h-full z-50 flex flex-col`}
      >
        <div className={`${sidebarCollapsed ? "p-2" : "p-4"} flex flex-col h-full`}>
          {/* Logo 区域 */}
          <div className={`flex items-center ${sidebarCollapsed ? "justify-center" : "justify-between"} mb-8`}>
            {!sidebarCollapsed && (
              <div>
                <h1 className="text-orange-500 font-bold text-xl tracking-wide">JBotQuant</h1>
                <p className="text-neutral-500 text-xs mt-1">v1.0.0 期货交易系统</p>
              </div>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="text-neutral-400 hover:text-orange-500 hover:bg-neutral-800 shrink-0"
            >
              <ChevronRight
                className={`w-5 h-5 transition-transform ${sidebarCollapsed ? "" : "rotate-180"}`}
              />
            </Button>
          </div>

          {/* 导航菜单 */}
          <nav className="space-y-2 flex-1">
            {[
              { id: "intelligence", icon: ShieldAlert, label: "风控监控" },
              { id: "operations", icon: TrendingUp, label: "交易终端" },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`w-full flex items-center ${sidebarCollapsed ? "justify-center" : ""} gap-3 p-3 rounded transition-colors ${
                  activeSection === item.id
                    ? "bg-orange-500 text-white"
                    : "text-neutral-400 hover:text-white hover:bg-neutral-800"
                }`}
              >
                <item.icon className="w-5 h-5 shrink-0" />
                {!sidebarCollapsed && (
                  <span className="text-sm font-medium">{item.label}</span>
                )}
              </button>
            ))}
          </nav>

          {/* 阶段和全局开关 */}
          {!sidebarCollapsed && (
            <div className="mt-4 p-3 bg-neutral-800 border border-neutral-700 rounded">
              <div className="text-xs text-neutral-400 space-y-2">
                <div className="flex items-center gap-2">
                  <span>后端:</span>
                  <span className={serviceOnline ? "text-green-400 font-mono" : "text-red-400 font-mono"}>
                    {serviceOnline ? "● 在线" : "● 离线"}
                  </span>
                </div>
                <div>阶段: <span className="text-green-400 font-mono">{serviceStage}</span></div>
                <div className="flex items-center gap-2">
                  <span>全局开关:</span>
                  <button
                    onClick={() => setGlobalSwitch(!globalSwitch)}
                    className={`relative inline-flex h-4 w-8 items-center rounded-full transition-colors ${
                      globalSwitch ? "bg-orange-500" : "bg-neutral-600"
                    }`}
                  >
                    <span
                      className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                        globalSwitch ? "translate-x-4" : "translate-x-0.5"
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 主内容区 */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${sidebarCollapsed ? "ml-16" : "ml-64"}`}
      >
        {/* 顶部工具栏 */}
        <div className="h-16 bg-neutral-800 border-b border-neutral-700 flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center gap-4">
            <span className="text-sm text-neutral-400">
              JBotQuant /{" "}
              <span className="text-orange-500">{sectionNames[activeSection]}</span>
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs text-neutral-500">
              最后更新: {lastUpdate.toLocaleString("zh-CN")}
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="text-neutral-400 hover:text-orange-500 hover:bg-neutral-700"
            >
              <Bell className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-neutral-400 hover:text-orange-500 hover:bg-neutral-700"
              onClick={fetchStatus}
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* 页面内容 */}
        <div className="flex-1 overflow-auto">
          {activeSection === "operations" && <OperationsPage />}
          {activeSection === "intelligence" && <IntelligencePage />}
        </div>
      </div>
    </div>
  )
}
