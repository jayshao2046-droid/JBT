"use client"

import { useState } from "react"
import {
  ChevronRight,
  LayoutDashboard,
  Settings,
  Database,
  Newspaper,
  Server,
  HardDrive,
  Bell,
  RefreshCw,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import OverviewPage from "@/components/pages/overview-page"
import CollectorsPage from "@/components/pages/collectors-page"
import DataExplorerPage from "@/components/pages/data-explorer-page"
import NewsFeedPage from "@/components/pages/news-feed-page"
import SystemMonitorPage from "@/components/pages/system-monitor-page"
import SettingsPage from "@/components/pages/settings-page"

export default function JBTDataDashboard() {
  const [activeSection, setActiveSection] = useState("overview")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [refreshNonce, setRefreshNonce] = useState(0)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [isRefreshing, setIsRefreshing] = useState(false)

  const sectionNames: Record<string, string> = {
    overview: "总览",
    collectors: "采集器管理",
    explorer: "数据浏览",
    news: "新闻资讯",
    system: "硬件系统",
    settings: "配置设置",
  }

  const navItems = [
    { id: "overview", icon: LayoutDashboard, label: "总览" },
    { id: "collectors", icon: Database, label: "采集器管理" },
    { id: "explorer", icon: HardDrive, label: "数据浏览" },
    { id: "news", icon: Newspaper, label: "新闻资讯" },
    { id: "system", icon: Server, label: "硬件系统" },
    { id: "settings", icon: Settings, label: "配置设置" },
  ]

  const handleRefresh = () => {
    setIsRefreshing(true)
    setLastUpdate(new Date())
    setRefreshNonce((n) => n + 1)
    setTimeout(() => setIsRefreshing(false), 600)
  }

  const formatTime = (date: Date) => {
    return date.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    })
  }

  return (
    <div className="flex h-screen bg-neutral-950">
      {/* 侧边栏 */}
      <div
        className={`${sidebarCollapsed ? "w-16" : "w-64"} bg-neutral-900 border-r border-neutral-800 transition-all duration-300 fixed md:relative z-50 h-full flex flex-col`}
      >
        <div className="p-4 flex-1">
          <div className="flex items-center justify-between mb-8">
            <div className={`${sidebarCollapsed ? "hidden" : "block"}`}>
              <h1 className="text-orange-500 font-bold text-xl tracking-wide">JBT Data</h1>
              <p className="text-neutral-500 text-xs mt-1">数据采集运维中控台</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="text-neutral-400 hover:text-orange-500 hover:bg-neutral-800"
            >
              <ChevronRight
                className={`w-4 h-4 transition-transform ${sidebarCollapsed ? "" : "rotate-180"}`}
              />
            </Button>
          </div>

          <nav className="space-y-1">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors ${
                  activeSection === item.id
                    ? "bg-orange-500/10 text-orange-500 border border-orange-500/30"
                    : "text-neutral-400 hover:text-white hover:bg-neutral-800"
                }`}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!sidebarCollapsed && <span className="text-sm font-medium">{item.label}</span>}
              </button>
            ))}
          </nav>
        </div>

        {/* 侧边栏底部状态指示 */}
        {!sidebarCollapsed && (
          <div className="p-4 border-t border-neutral-800">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-xs text-green-400 font-medium">系统运行中</span>
            </div>
          </div>
        )}
      </div>

      {/* 移动端遮罩 */}
      {!sidebarCollapsed && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setSidebarCollapsed(true)}
        />
      )}

      {/* 主内容区 */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* 顶部工具栏 */}
        <header className="h-14 bg-neutral-900 border-b border-neutral-800 flex items-center justify-between px-6 flex-shrink-0">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-neutral-500">JBT Data</span>
            <span className="text-neutral-600">/</span>
            <span className="text-orange-500 font-medium">{sectionNames[activeSection]}</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-xs text-neutral-500 hidden sm:block">
              最后更新: {formatTime(lastUpdate)}
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="text-neutral-400 hover:text-orange-500 hover:bg-neutral-800"
            >
              <Bell className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="text-neutral-400 hover:text-orange-500 hover:bg-neutral-800"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </header>

        {/* 页面内容 */}
        <main className="flex-1 overflow-auto bg-neutral-950">
          {activeSection === "overview" && <OverviewPage refreshNonce={refreshNonce} onNavigate={(page) => setActiveSection(page)} />}
          {activeSection === "collectors" && <CollectorsPage refreshNonce={refreshNonce} />}
          {activeSection === "explorer" && <DataExplorerPage refreshNonce={refreshNonce} />}
          {activeSection === "news" && <NewsFeedPage refreshNonce={refreshNonce} />}
          {activeSection === "system" && <SystemMonitorPage refreshNonce={refreshNonce} />}
          {activeSection === "settings" && <SettingsPage refreshNonce={refreshNonce} />}
        </main>
      </div>
    </div>
  )
}
