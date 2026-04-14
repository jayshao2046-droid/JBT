"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  ChevronRight,
  Home,
  TrendingUp,
  LineChart,
  Brain,
  Database,
  Settings,
  LogOut,
  ChevronDown,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface NavItem {
  id: string
  label: string
  icon: React.ElementType
  href?: string
  children?: { id: string; label: string; href: string }[]
  color?: string
}

const navItems: NavItem[] = [
  {
    id: "home",
    label: "总控台",
    icon: Home,
    href: "/",
  },
  {
    id: "sim-trading",
    label: "模拟交易",
    icon: TrendingUp,
    color: "text-orange-500",
    children: [
      { id: "sim-intelligence", label: "风控监控", href: "/sim-trading" },
      { id: "sim-operations", label: "交易终端", href: "/sim-trading/operations" },
      { id: "sim-market", label: "行情报价", href: "/sim-trading/market" },
      { id: "sim-risk", label: "品种风控", href: "/sim-trading/risk-presets" },
      { id: "sim-ctp", label: "CTP 配置", href: "/sim-trading/ctp-config" },
    ],
  },
  {
    id: "backtest",
    label: "策略回测",
    icon: LineChart,
    color: "text-blue-500",
    children: [
      { id: "bt-agents", label: "策略管理", href: "/backtest" },
      { id: "bt-operations", label: "回测详情", href: "/backtest/operations" },
      { id: "bt-results", label: "回测结果", href: "/backtest/results" },
      { id: "bt-review", label: "策略审查", href: "/backtest/review" },
      { id: "bt-optimizer", label: "参数优化", href: "/backtest/optimizer" },
    ],
  },
  {
    id: "decision",
    label: "智能决策",
    icon: Brain,
    color: "text-purple-500",
    children: [
      { id: "dc-overview", label: "总览", href: "/decision" },
      { id: "dc-signal", label: "信号审查", href: "/decision/signal" },
      { id: "dc-models", label: "模型与因子", href: "/decision/models" },
      { id: "dc-repository", label: "策略仓库", href: "/decision/repository" },
      { id: "dc-research", label: "研究中心", href: "/decision/research" },
      { id: "dc-reports", label: "通知与日报", href: "/decision/reports" },
    ],
  },
  {
    id: "data",
    label: "数据采集",
    icon: Database,
    color: "text-cyan-500",
    children: [
      { id: "data-overview", label: "总览", href: "/data" },
      { id: "data-collectors", label: "采集器管理", href: "/data/collectors" },
      { id: "data-explorer", label: "数据浏览", href: "/data/explorer" },
      { id: "data-news", label: "新闻资讯", href: "/data/news" },
      { id: "data-system", label: "硬件系统", href: "/data/system" },
    ],
  },
  {
    id: "settings",
    label: "系统设置",
    icon: Settings,
    href: "/settings",
  },
]

interface AppSidebarProps {
  collapsed: boolean
  onToggle: () => void
}

export function AppSidebar({ collapsed, onToggle }: AppSidebarProps) {
  const pathname = usePathname()
  const [expandedItems, setExpandedItems] = useState<string[]>(["sim-trading"])

  const toggleExpand = (id: string) => {
    setExpandedItems((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/"
    return pathname === href || pathname.startsWith(href + "/")
  }

  const isParentActive = (item: NavItem) => {
    if (item.href) return isActive(item.href)
    return item.children?.some((child) => isActive(child.href))
  }

  return (
    <div
      className={cn(
        "h-full bg-card border-r border-border flex flex-col transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className={cn("p-4 border-b border-border", collapsed && "px-2")}>
        <div className="flex items-center justify-between">
          {!collapsed && (
            <Link href="/" className="flex items-center gap-2">
              <h1 className="text-lg font-extrabold text-orange-500 tracking-wide">
                JBT 量化研究室
              </h1>
            </Link>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className="text-muted-foreground hover:text-orange-500 hover:bg-accent shrink-0"
          >
            <ChevronRight
              className={cn(
                "w-4 h-4 transition-transform",
                !collapsed && "rotate-180"
              )}
            />
          </Button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-2 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const active = isParentActive(item)

          if (item.children) {
            const isExpanded = expandedItems.includes(item.id)
            const showChildren = isExpanded && !collapsed

            return (
              <div key={item.id}>
                <button
                  onClick={() => toggleExpand(item.id)}
                  className={cn(
                    "w-full flex items-center gap-3 p-3 rounded-lg transition-colors",
                    active
                      ? "bg-accent text-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent",
                    collapsed && "justify-center"
                  )}
                >
                  <Icon className={cn("w-5 h-5 shrink-0", item.color)} />
                  {!collapsed && (
                    <>
                      <span className="flex-1 text-left text-sm font-medium">
                        {item.label}
                      </span>
                      <ChevronDown
                        className={cn(
                          "w-4 h-4 transition-transform duration-200",
                          isExpanded && "rotate-180"
                        )}
                      />
                    </>
                  )}
                </button>
                {showChildren && (
                  <div className="ml-4 pl-4 mt-1 space-y-1 border-l border-border">
                    {item.children.map((child) => (
                      <Link
                        key={child.id}
                        href={child.href}
                        className={cn(
                          "block px-3 py-2 text-sm rounded-lg transition-colors",
                          isActive(child.href)
                            ? "bg-orange-500/10 text-orange-500 font-medium"
                            : "text-muted-foreground hover:text-foreground hover:bg-accent"
                        )}
                      >
                        {child.label}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            )
          }

          return (
            <Link
              key={item.id}
              href={item.href!}
              className={cn(
                "flex items-center gap-3 p-3 rounded-lg transition-colors",
                active
                  ? "bg-orange-500/10 text-orange-500 border border-orange-500/30"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent",
                collapsed && "justify-center"
              )}
            >
              <Icon className="w-5 h-5 shrink-0" />
              {!collapsed && (
                <span className="text-sm font-medium">{item.label}</span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Bottom Section */}
      {!collapsed && (
        <div className="p-4 border-t border-border space-y-3">
          {/* System Status */}
          <div className="p-3 bg-accent/50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-xs text-green-500 font-medium">系统运行中</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="text-muted-foreground">
                CPU: <span className="text-foreground font-mono">12%</span>
              </div>
              <div className="text-muted-foreground">
                内存: <span className="text-foreground font-mono">45%</span>
              </div>
            </div>
          </div>

          {/* User Info */}
          <div className="flex items-center gap-3 p-2">
            <div className="w-8 h-8 bg-accent rounded-full flex items-center justify-center text-sm text-foreground font-medium">
              A
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-foreground truncate">admin</p>
              <p className="text-xs text-muted-foreground">管理员</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="text-muted-foreground hover:text-foreground hover:bg-accent"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
