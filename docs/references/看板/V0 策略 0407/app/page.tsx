"use client"

import { useState } from "react"
import { ChevronRight, LayoutGrid, Eye, Package, Zap, Beaker, Bell, Settings, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import DecisionOverview from "@/components/decision/overview"
import SignalReview from "@/components/decision/signal-review"
import ModelsFactors from "@/components/decision/models-factors"
import StrategyRepository from "@/components/decision/strategy-repository"
import ResearchCenter from "@/components/decision/research-center"
import NotificationsReport from "@/components/decision/notifications-report"
import ConfigRuntime from "@/components/decision/config-runtime"

export default function DecisionConsole() {
  const [activeSection, setActiveSection] = useState("overview")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const sectionNames: Record<string, string> = {
    overview: "总览",
    signal: "信号审查",
    models: "模型与因子",
    repository: "策略仓库",
    research: "研究中心",
    notifications: "通知与日报",
    config: "配置与运行",
  }

  const menuItems = [
    { id: "overview", icon: LayoutGrid, label: "总览" },
    { id: "signal", icon: Eye, label: "信号审查" },
    { id: "models", icon: Package, label: "模型与因子" },
    { id: "repository", icon: Zap, label: "策略仓库" },
    { id: "research", icon: Beaker, label: "研究中心" },
    { id: "notifications", icon: Bell, label: "通知与日报" },
    { id: "config", icon: Settings, label: "配置与运行" },
  ]

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
                <p className="text-neutral-500 text-xs mt-1">决策端控制台 v1.0</p>
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
            {menuItems.map((item) => (
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

          {/* 状态指示 */}
          {!sidebarCollapsed && (
            <div className="mt-4 p-3 bg-neutral-800 border border-neutral-700 rounded space-y-2 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-400"></div>
                <span className="text-neutral-300">系统: <span className="text-green-400">运行中</span></span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-orange-400"></div>
                <span className="text-neutral-300">研究: <span className="text-orange-400">活跃</span></span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 主内容区 */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${sidebarCollapsed ? "ml-16" : "ml-64"}`}
      >
        {/* 顶部状态条 */}
        <div className="h-14 bg-neutral-800 border-b border-neutral-700 flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center gap-6 text-sm">
            <span className="text-neutral-400">
              JBotQuant / <span className="text-orange-500 font-medium">{sectionNames[activeSection]}</span>
            </span>
            <div className="flex items-center gap-4 ml-4 border-l border-neutral-700 pl-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-400"></div>
                <span className="text-neutral-400 text-xs">本地模型: <span className="text-green-400">就绪</span></span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-blue-400"></div>
                <span className="text-neutral-400 text-xs">在线L3: <span className="text-blue-400">连接</span></span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-orange-400"></div>
                <span className="text-neutral-400 text-xs">研究窗: <span className="text-orange-400">开启</span></span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs text-neutral-500">
              {new Date().toLocaleString("zh-CN")}
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="text-neutral-400 hover:text-orange-500 hover:bg-neutral-700"
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* 页面内容 */}
        <div className="flex-1 overflow-auto bg-neutral-950">
          {activeSection === "overview" && <DecisionOverview />}
          {activeSection === "signal" && <SignalReview />}
          {activeSection === "models" && <ModelsFactors />}
          {activeSection === "repository" && <StrategyRepository />}
          {activeSection === "research" && <ResearchCenter />}
          {activeSection === "notifications" && <NotificationsReport />}
          {activeSection === "config" && <ConfigRuntime />}
        </div>
      </div>
    </div>
  )
}
