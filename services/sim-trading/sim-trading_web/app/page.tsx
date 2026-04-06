"use client"

import { useState, useEffect } from "react"
import {
  ChevronRight, ShieldAlert, TrendingUp, Bell, RefreshCw,
  Shield, Settings, Calendar, PlugZap, BarChart2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import OperationsPage from "./operations/page"
import IntelligencePage from "./intelligence/page"
import RiskPresetsPage from "./risk-presets/page"
import CtpConfigPage from "./ctp-config/page"
import MarketPage from "./market/page"
import { simApi } from "@/lib/sim-api"
import { isTradingDay, getTodayHolidayName } from "@/lib/holidays-cn"

export default function TradingDashboard() {
  const [activeSection, setActiveSection] = useState("intelligence")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [tradingEnabled, setTradingEnabled] = useState(true)
  const [activePreset, setActivePreset] = useState("sim_50w")
  const [serviceStage, setServiceStage] = useState("--")
  const [serviceOnline, setServiceOnline] = useState(false)
  const [ctpMd, setCtpMd] = useState(false)
  const [ctpTd, setCtpTd] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [togglingSwitch, setTogglingSwitch] = useState(false)

  // 交易日历
  const todayIsTrading = isTradingDay()
  const holidayName = getTodayHolidayName()

  const fetchStatus = async () => {
    try {
      const [health, sysState] = await Promise.all([
        simApi.health(),
        simApi.systemState(),
      ])
      setServiceOnline(health.status === "ok")
      setTradingEnabled(sysState.trading_enabled)
      setActivePreset(sysState.active_preset)
      setCtpMd(sysState.ctp_md_connected)
      setCtpTd(sysState.ctp_td_connected)
      setServiceStage((sysState as any).stage ?? "skeleton")
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

  const handleToggleTrading = async () => {
    setTogglingSwitch(true)
    try {
      if (tradingEnabled) {
        await simApi.pauseTrading("手动暂停（看板操作）")
        setTradingEnabled(false)
        toast.warning("全局交易已暂停，所有新开仓被拒绝")
      } else {
        await simApi.resumeTrading()
        setTradingEnabled(true)
        toast.success("全局交易已恢复")
      }
    } catch {
      toast.error("操作失败，请检查后端连接")
    } finally {
      setTogglingSwitch(false)
    }
  }

  const sectionNames: Record<string, string> = {
    market: "行情报价",
    operations: "交易终端",
    intelligence: "风控监控",
    "risk-presets": "品种风控",
    "ctp-config": "CTP 配置",
  }

  return (
    <div className="flex h-screen bg-neutral-950">
      {/* 侧边栏 */}
      <div
        className={`${sidebarCollapsed ? "w-16" : "w-64"} bg-neutral-900 border-r border-neutral-700 transition-all duration-300 fixed left-0 top-0 h-full z-50 flex flex-col`}
      >
        <div className={`${sidebarCollapsed ? "p-2" : "p-4"} flex flex-col h-full`}>
          {/* Logo */}
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
              <ChevronRight className={`w-5 h-5 transition-transform ${sidebarCollapsed ? "" : "rotate-180"}`} />
            </Button>
          </div>

          {/* 导航菜单 */}
          <nav className="space-y-1 flex-1">
            {[
              { id: "market",        icon: BarChart2,   label: "行情报价" },
              { id: "intelligence",  icon: ShieldAlert, label: "风控监控" },
              { id: "operations",    icon: TrendingUp,  label: "交易终端" },
              { id: "risk-presets",  icon: Shield,      label: "品种风控" },
              { id: "ctp-config",    icon: PlugZap,     label: "CTP 配置" },
            ].map(item => (
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
                {!sidebarCollapsed && <span className="text-sm font-medium">{item.label}</span>}
              </button>
            ))}
          </nav>

          {/* 状态底栏 */}
          {!sidebarCollapsed && (
            <div className="space-y-2">
              {/* 交易日历提示 */}
              <div className={`p-2 rounded text-xs ${
                todayIsTrading
                  ? "bg-green-900/20 border border-green-800/50 text-green-400"
                  : "bg-red-900/20 border border-red-800/50 text-red-400"
              }`}>
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {todayIsTrading
                    ? "今日交易日 · 可开仓"
                    : holidayName
                      ? `今日 ${holidayName} · 禁止开仓`
                      : "今日休市 · 禁止开仓"
                  }
                </div>
              </div>

              {/* 系统状态卡 */}
              <div className="p-3 bg-neutral-800 border border-neutral-700 rounded space-y-2">
                <div className="text-xs text-neutral-400 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span>后端:</span>
                    <span className={serviceOnline ? "text-green-400 font-mono" : "text-red-400 font-mono"}>
                      {serviceOnline ? "● 在线" : "● 离线"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>行情:</span>
                    <span className={ctpMd ? "text-green-400 font-mono" : "text-neutral-500 font-mono"}>
                      {ctpMd ? "● 已连接" : "○ 未连"}
                    </span>
                    <span className="text-neutral-600 ml-1">交易:</span>
                    <span className={ctpTd ? "text-green-400 font-mono" : "text-neutral-500 font-mono"}>
                      {ctpTd ? "●" : "○"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>预设:</span>
                    <Badge className="bg-orange-900/30 text-orange-400 border-none text-xs px-1 py-0">
                      {activePreset}
                    </Badge>
                  </div>
                  {/* 全局交易开关 */}
                  <div className="flex items-center justify-between pt-1 border-t border-neutral-700">
                    <span className={tradingEnabled ? "text-green-400" : "text-red-400"}>
                      {tradingEnabled ? "交易 开" : "交易 停"}
                    </span>
                    <button
                      onClick={handleToggleTrading}
                      disabled={togglingSwitch}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors disabled:opacity-50 ${
                        tradingEnabled ? "bg-orange-500" : "bg-neutral-600"
                      }`}
                    >
                      <span
                        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                          tradingEnabled ? "translate-x-5" : "translate-x-0.5"
                        }`}
                      />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 主内容区 */}
      <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarCollapsed ? "ml-16" : "ml-64"}`}>
        {/* 顶部工具栏 */}
        <div className="h-16 bg-neutral-800 border-b border-neutral-700 flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center gap-4">
            <span className="text-sm text-neutral-400">
              JBotQuant / <span className="text-orange-500">{sectionNames[activeSection]}</span>
            </span>
            {!tradingEnabled && (
              <Badge className="bg-red-900/40 text-red-400 border border-red-700/50 text-xs animate-pulse">
                ⛔ 全局交易暂停
              </Badge>
            )}
            {!todayIsTrading && (
              <Badge variant="outline" className="border-neutral-600 text-neutral-500 text-xs">
                <Calendar className="w-3 h-3 mr-1" />
                {holidayName ?? "休市"}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs text-neutral-500">
              更新: {lastUpdate.toLocaleTimeString("zh-CN")}
            </span>
            <Button variant="ghost" size="icon" className="text-neutral-400 hover:text-orange-500 hover:bg-neutral-700">
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
          {activeSection === "market"       && <MarketPage />}
          {activeSection === "operations"   && <OperationsPage />}
          {activeSection === "intelligence" && <IntelligencePage />}
          {activeSection === "risk-presets" && <RiskPresetsPage />}
          {activeSection === "ctp-config"   && <CtpConfigPage />}
        </div>
      </div>
    </div>
  )
}
