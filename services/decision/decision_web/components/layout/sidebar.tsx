"use client"

import { ChevronRight, LayoutGrid, Eye, Package, Zap, Beaker, Bell, Settings } from "lucide-react"
import { Button } from "@/components/ui/button"

export const menuItems = [
  { id: "overview", icon: LayoutGrid, label: "总览" },
  { id: "signal", icon: Eye, label: "信号审查" },
  { id: "models", icon: Package, label: "模型与因子" },
  { id: "repository", icon: Zap, label: "策略仓库" },
  { id: "research", icon: Beaker, label: "研究中心" },
  { id: "notifications", icon: Bell, label: "通知与日报" },
  { id: "config", icon: Settings, label: "配置与运行" },
]

interface SidebarProps {
  activeSection: string
  collapsed: boolean
  onSectionChange: (section: string) => void
  onToggleCollapse: () => void
}

export default function Sidebar({
  activeSection,
  collapsed,
  onSectionChange,
  onToggleCollapse,
}: SidebarProps) {
  return (
    <div
      className={`${collapsed ? "w-16" : "w-64"} bg-neutral-900 border-r border-neutral-700 transition-all duration-300 fixed left-0 top-0 h-full z-50 flex flex-col`}
    >
      <div className={`${collapsed ? "p-2" : "p-4"} flex flex-col h-full`}>
        {/* Logo 区域 */}
        <div className={`flex items-center ${collapsed ? "justify-center" : "justify-between"} mb-8`}>
          {!collapsed && (
            <div>
              <h1 className="text-orange-500 font-bold text-xl tracking-wide">JBT</h1>
              <p className="text-neutral-500 text-xs mt-1">决策端控制台 v1.0</p>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleCollapse}
            className="text-neutral-400 hover:text-orange-500 hover:bg-neutral-800 shrink-0"
          >
            <ChevronRight
              className={`w-5 h-5 transition-transform ${collapsed ? "" : "rotate-180"}`}
            />
          </Button>
        </div>

        {/* 导航菜单 */}
        <nav className="space-y-2 flex-1">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onSectionChange(item.id)}
              className={`w-full flex items-center ${collapsed ? "justify-center" : ""} gap-3 p-3 rounded transition-colors ${
                activeSection === item.id
                  ? "bg-orange-500 text-white"
                  : "text-neutral-400 hover:text-white hover:bg-neutral-800"
              }`}
            >
              <item.icon className="w-5 h-5 shrink-0" />
              {!collapsed && (
                <span className="text-sm font-medium">{item.label}</span>
              )}
            </button>
          ))}
        </nav>

        {/* 状态指示 */}
        {!collapsed && (
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
  )
}
