"use client"

import { Bell, RefreshCw, Search, Menu, Sun, Moon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useTheme } from "@/components/theme-provider"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface AppHeaderProps {
  title: string
  subtitle?: string
  onRefresh?: () => void
  isRefreshing?: boolean
  lastUpdate?: Date | null
  onMenuToggle?: () => void
  alerts?: { id: string; type: "error" | "warning" | "info"; message: string }[]
}

export function AppHeader({
  title,
  subtitle,
  onRefresh,
  isRefreshing,
  lastUpdate,
  onMenuToggle,
  alerts = [],
}: AppHeaderProps) {
  const { theme, toggleTheme } = useTheme()
  const unreadAlerts = alerts.length

  return (
    <header className="h-14 bg-card border-b border-border flex items-center justify-between px-4 md:px-6 shrink-0">
      {/* Left Section */}
      <div className="flex items-center gap-4">
        {/* Mobile Menu Toggle */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden text-muted-foreground hover:text-foreground"
          onClick={onMenuToggle}
        >
          <Menu className="w-5 h-5" />
        </Button>

        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm">
          <span className="text-orange-500 font-medium">{title}</span>
          {subtitle && (
            <>
              <span className="text-neutral-600">/</span>
              <span className="text-neutral-400">{subtitle}</span>
            </>
          )}
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-2 md:gap-4">
        {/* Search - Hidden on mobile */}
        <div className="hidden lg:block relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="搜索..."
            className="w-48 pl-9 h-8 bg-accent border-border text-sm text-foreground placeholder:text-muted-foreground focus:border-orange-500"
          />
        </div>

        {/* Last Update */}
        <div className="hidden md:block text-xs text-muted-foreground">
          {lastUpdate
            ? `更新: ${lastUpdate.toLocaleTimeString("zh-CN")}`
            : "更新: --:--:--"}
        </div>

        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          className="text-muted-foreground hover:text-orange-500 hover:bg-accent"
          aria-label={theme === "dark" ? "切换到日间模式" : "切换到夜间模式"}
          title={theme === "dark" ? "切换到日间模式" : "切换到夜间模式"}
        >
          {theme === "dark" ? (
            <Sun className="w-4 h-4" />
          ) : (
            <Moon className="w-4 h-4" />
          )}
        </Button>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="relative text-muted-foreground hover:text-orange-500 hover:bg-accent"
            >
              <Bell className="w-4 h-4" />
              {unreadAlerts > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full text-[10px] text-white flex items-center justify-center">
                  {unreadAlerts > 9 ? "9+" : unreadAlerts}
                </span>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            className="w-80 bg-card border-border"
          >
            <DropdownMenuLabel className="text-muted-foreground">
              系统通知
            </DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-neutral-800" />
            {alerts.length === 0 ? (
              <div className="p-4 text-center text-sm text-muted-foreground">
                暂无通知
              </div>
            ) : (
              alerts.slice(0, 5).map((alert) => (
                <DropdownMenuItem
                  key={alert.id}
                  className="flex items-start gap-3 p-3 focus:bg-accent"
                >
                  <div
                    className={`w-2 h-2 mt-1.5 rounded-full shrink-0 ${
                      alert.type === "error"
                        ? "bg-red-500"
                        : alert.type === "warning"
                          ? "bg-yellow-500"
                          : "bg-blue-500"
                    }`}
                  />
                  <span className="text-sm text-foreground">{alert.message}</span>
                </DropdownMenuItem>
              ))
            )}
            {alerts.length > 5 && (
              <>
                <DropdownMenuSeparator className="bg-border" />
                <DropdownMenuItem className="justify-center text-orange-500 focus:bg-accent focus:text-orange-400">
                  查看全部 ({alerts.length})
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Refresh Button */}
        {onRefresh && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onRefresh}
            disabled={isRefreshing}
            className="text-muted-foreground hover:text-orange-500 hover:bg-accent"
          >
            <RefreshCw
              className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`}
            />
          </Button>
        )}
      </div>
    </header>
  )
}
