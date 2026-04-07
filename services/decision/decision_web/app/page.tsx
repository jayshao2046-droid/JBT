"use client"

import { useState } from "react"
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

const sectionNames: Record<string, string> = {
  overview: "总览",
  signal: "信号审查",
  models: "模型与因子",
  repository: "策略仓库",
  research: "研究中心",
  notifications: "通知与日报",
  config: "配置与运行",
}

export default function DecisionConsole() {
  const [activeSection, setActiveSection] = useState("overview")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <div className="flex h-screen bg-neutral-950">
      {/* 侧边栏 */}
      <Sidebar
        activeSection={activeSection}
        collapsed={sidebarCollapsed}
        onSectionChange={setActiveSection}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* 主内容区 */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${sidebarCollapsed ? "ml-16" : "ml-64"}`}
      >
        {/* 顶部状态条 */}
        <div className="h-14 bg-neutral-800 border-b border-neutral-700 flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center gap-6 text-sm">
            <span className="text-neutral-400">
              JBT / <span className="text-orange-500 font-medium">{sectionNames[activeSection]}</span>
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
