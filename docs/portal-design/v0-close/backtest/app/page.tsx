"use client"

import { useState, useEffect } from "react"
import { ChevronRight, LineChart, Activity, Bell, RefreshCw } from "lucide-react"
import { toast } from 'sonner'
import { Button } from "@/components/ui/button"
import AgentNetworkPage from "./agent-network/page"
import OperationsPage from "./operations/page"
import { getSystemStatus } from "@/src/utils/api"
import api from "@/src/utils/api"

// 顶部工具栏组件（提取到文件顶层，避免在组件 return 之后定义）
function Toolbar({ sectionName, isRefreshing, globalLoading, onRefresh, lastUpdateTime }: {
  sectionName: string,
  isRefreshing: boolean,
  globalLoading: boolean,
  onRefresh: () => void,
  lastUpdateTime: string
}) {
  const [time, setTime] = useState<string>("")
  useEffect(() => {
    setTime(lastUpdateTime || new Date().toLocaleString('zh-CN'))
  }, [lastUpdateTime])
  useEffect(() => {
    setTime(new Date().toLocaleString('zh-CN'))
  }, [])
  return (
    <div className="h-16 bg-neutral-800 border-b border-neutral-700 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <div className="text-sm text-neutral-400">
          JBotQuant / <span className="text-orange-500">{sectionName}</span>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-xs text-neutral-500">最后更新: {time}</div>
        <Button variant="ghost" size="icon" className="text-neutral-400 hover:text-orange-500">
          <Bell className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="text-neutral-400 hover:text-orange-500"
          onClick={onRefresh}
          disabled={isRefreshing || globalLoading}
        >
          <RefreshCw className={`w-4 h-4 ${(globalLoading || isRefreshing) ? 'animate-spin' : ''}`} />
        </Button>
      </div>
    </div>
  )
}

export default function BacktestDashboard() {
  const [activeSection, setActiveSection] = useState("agents")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [globalLoading, setGlobalLoading] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdateTime, setLastUpdateTime] = useState<string>("")
  const [sysInfo, setSysInfo] = useState<{ cpu: number; memory: number; latency: number; uptime: string }>({ cpu: 0, memory: 0, latency: 0, uptime: '--:--:--' })
  const [runningBacktests, setRunningBacktests] = useState<any[]>([])
  const [progressMap, setProgressMap] = useState<Record<string, number>>({})

  useEffect(() => {
    const onLoading = (e: any) => setGlobalLoading(Boolean(e?.detail))
    window.addEventListener('backtest:loading', onLoading)
    return () => window.removeEventListener('backtest:loading', onLoading)
  }, [])

  // 每 5 秒拉取系统状态
  useEffect(() => {
    const fetchSys = async () => {
      try {
        const d = await getSystemStatus()
        const uptime = d?.services?.[0]?.uptime ?? '--:--:--'
        // CPU 使用最近 10 个历史均值，避免单次采样时恰好为 0 导致永远显示 0%
        const history: number[] = Array.isArray(d?.cpuHistory) ? d.cpuHistory : []
        const recentCpu = history.length > 0
          ? parseFloat((history.slice(-10).reduce((a: number, b: number) => a + b, 0) / Math.min(10, history.length)).toFixed(1))
          : (d?.cpu ?? 0)
        setSysInfo({ cpu: recentCpu, memory: d?.memory ?? 0, latency: d?.latency ?? 0, uptime })
      } catch {}
    }
    fetchSys()
    const t = setInterval(fetchSys, 5000)
    return () => clearInterval(t)
  }, [])

  // 每 3 秒拉取运行中的回测进度
  useEffect(() => {
    const fetchProgress = async () => {
      try {
        const results = await api.getResults()
        const running = (results || []).filter((r: any) => r.status === 'running' || r.status === 'submitted' || r.status === 'pending')
        setRunningBacktests(running)
        const updates: Record<string, number> = {}
        await Promise.allSettled(running.map(async (r: any) => {
          try {
            const p = await api.getProgress(r.id)
            updates[r.id] = p.progress ?? 0
          } catch {}
        }))
        setProgressMap(prev => ({ ...prev, ...updates }))
      } catch {}
    }
    fetchProgress()
    const t = setInterval(fetchProgress, 3000)
    return () => clearInterval(t)
  }, [])

  const sectionNames: Record<string, string> = {
    agents: "策略管理",
    operations: "回测详情",
  }

  return (
    <div className="flex h-screen">
      {/* 侧边栏 */}
      <div
        className={`${sidebarCollapsed ? "w-16" : "w-72"} bg-neutral-900 border-r border-neutral-700 transition-all duration-300 fixed md:relative z-50 md:z-auto h-full overflow-y-auto`}
      >
        <div className="p-4">
          <div className="flex items-center justify-between mb-8">
            <div className={`${sidebarCollapsed ? "hidden" : "block"}`}>
              <h1 className="text-orange-500 font-bold text-xl tracking-wide">JBotQuant</h1>
              <p className="text-neutral-500 text-xs mt-1">v1.0.0 期货回测系统</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="text-neutral-400 hover:text-orange-500"
            >
              <ChevronRight
                className={`w-4 h-4 sm:w-5 sm:h-5 transition-transform ${sidebarCollapsed ? "" : "rotate-180"}`}
              />
            </Button>
          </div>

          <nav className="space-y-2">
            {[
              { id: "agents", icon: LineChart, label: "策略管理" },
              { id: "operations", icon: Activity, label: "回测详情" },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`w-full flex items-center gap-3 p-3 rounded transition-colors ${
                  activeSection === item.id
                    ? "bg-orange-500 text-white"
                    : "text-neutral-400 hover:text-white hover:bg-neutral-800"
                }`}
              >
                <item.icon className="w-5 h-5 md:w-5 md:h-5 sm:w-6 sm:h-6" />
                {!sidebarCollapsed && <span className="text-sm font-medium">{item.label}</span>}
              </button>
            ))}
          </nav>

          {!sidebarCollapsed && (
            <div className="mt-8 p-3 bg-neutral-800 border border-neutral-700 rounded space-y-3">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-xs text-white font-medium">系统运行中</span>
              </div>
              {/* 系统指标 */}
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-xs mb-0.5">
                    <span className="text-neutral-400">CPU</span>
                    <span className="text-white font-mono">{sysInfo.cpu.toFixed(1)}%</span>
                  </div>
                  <div className="h-1 bg-neutral-700 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full transition-all duration-1000" style={{ width: `${Math.min(100, sysInfo.cpu)}%` }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-0.5">
                    <span className="text-neutral-400">内存</span>
                    <span className="text-white font-mono">{sysInfo.memory.toFixed(1)}%</span>
                  </div>
                  <div className="h-1 bg-neutral-700 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-1000 ${sysInfo.memory > 80 ? 'bg-red-500' : 'bg-green-500'}`} style={{ width: `${Math.min(100, sysInfo.memory)}%` }} />
                  </div>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-neutral-400">延迟</span>
                  <span className={`font-mono ${sysInfo.latency < 10 ? 'text-green-400' : sysInfo.latency < 50 ? 'text-yellow-400' : 'text-red-400'}`}>{sysInfo.latency.toFixed(0)} ms</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-neutral-400">运行时长</span>
                  <span className="text-neutral-300 font-mono">{sysInfo.uptime}</span>
                </div>
              </div>
              {/* 回测进度 */}
              {runningBacktests.length > 0 && (
                <div className="border-t border-neutral-700 pt-2 space-y-2">
                  <p className="text-xs text-orange-400">回测进度 ({runningBacktests.length})</p>
                  {runningBacktests.map((r: any) => (
                    <div key={r.id} className="space-y-0.5">
                      <div className="flex justify-between text-xs">
                        <span className="text-neutral-400 truncate max-w-[120px]">{r.name ?? r.id?.slice(0, 8)}</span>
                        <span className="text-orange-400 font-mono">{progressMap[r.id] ?? 0}%</span>
                      </div>
                      <div className="h-1 bg-neutral-700 rounded-full overflow-hidden">
                        <div className="h-full bg-orange-500 rounded-full transition-all duration-500" style={{ width: `${progressMap[r.id] ?? 0}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 移动端遮罩 */}
      {!sidebarCollapsed && (
        <div className="fixed inset-0 bg-black/50 z-40 md:hidden" onClick={() => setSidebarCollapsed(true)} />
      )}

      {/* 主内容区 */}
      <div className={`flex-1 flex flex-col min-w-0 ${sidebarCollapsed ? "ml-16" : "ml-72"} md:ml-0 transition-all duration-300`}>
        {/* 顶部工具栏 */}
        <Toolbar
          sectionName={sectionNames[activeSection]}
          isRefreshing={isRefreshing}
          globalLoading={globalLoading}
          onRefresh={() => {
            if (isRefreshing || globalLoading) return
            setIsRefreshing(true)
            setLastUpdateTime(new Date().toLocaleString('zh-CN'))
            window.dispatchEvent(new CustomEvent('backtest:refresh'))
            setTimeout(() => {
              setIsRefreshing(false)
              toast.success('数据已更新')
            }, 1000)
          }}
          lastUpdateTime={lastUpdateTime}
        />


        {/* 仪表板内容 */}
        <div className="flex-1 overflow-auto">
          {activeSection === "agents" && <AgentNetworkPage />}
          {activeSection === "operations" && <OperationsPage />}
        </div>
      </div>
    </div>
  )
}

// 监听全局更新时间事件，更新 window 上的缓存值供渲染使用
if (typeof window !== 'undefined') {
  window.addEventListener('backtest:lastUpdate', (e: any) => {
    try {
      const iso = e?.detail
      if (iso) {
        window.__backtest_last_update = new Date(iso).toLocaleString('zh-CN')
      }
    } catch (err) {
      // ignore
    }
  })
}
