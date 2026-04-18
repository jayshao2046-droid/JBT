"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import {
  Cpu,
  HardDrive,
  MemoryStick,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Send,
  Mail,
  Server,
  Zap,
  Database,
  FileText,
  AlertCircle,
  Clock,
  Search,
  Play,
  Square,
} from "lucide-react"
import { collectorDisplayName, collectorZhName } from "@/lib/collector-labels"
import { dataApi, ResourceCpu, ResourceMem, ResourceDisk, ProcessEntry, NotifChannel, SourceItem, LogEntry } from "@/lib/api/data"

function humanBytes(b: number) {
  if (b <= 0) return "0 B"
  const u = ["B", "KB", "MB", "GB", "TB"]
  const i = Math.min(Math.floor(Math.log(b) / Math.log(1024)), u.length - 1)
  return (b / Math.pow(1024, i)).toFixed(1) + " " + u[i]
}

export default function SystemMonitor() {
  const [logFilter, setLogFilter] = useState("all")
  const [logSearch, setLogSearch] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastUpdate, setLastUpdate] = useState("")
  const [cpu, setCpu] = useState<ResourceCpu | null>(null)
  const [mem, setMem] = useState<ResourceMem | null>(null)
  const [disk, setDisk] = useState<ResourceDisk | null>(null)
  const [processes, setProcesses] = useState<ProcessEntry[]>([])
  const [notifications, setNotifications] = useState<NotifChannel[]>([])
  const [sources, setSources] = useState<SourceItem[]>([])
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [cpuHistory, setCpuHistory] = useState<number[]>([])
  const [memHistory, setMemHistory] = useState<number[]>([])

  const fetchData = useCallback(async () => {
    try {
      const d = await dataApi.getSystem()
      setCpu(d.resources?.cpu ?? null)
      setMem(d.resources?.memory ?? null)
      setDisk(d.resources?.disk ?? null)
      setProcesses(d.processes ?? [])
      setNotifications(d.notifications ?? [])
      setSources(d.sources ?? [])
      setLogs(d.logs ?? [])
      setLastUpdate(new Date().toLocaleTimeString("zh-CN"))
      setFetchError(false)

      // 更新历史数据（保留最近20个数据点）
      if (d.resources?.cpu?.usage_percent != null) {
        setCpuHistory((prev) => [...prev.slice(-19), d.resources.cpu.usage_percent])
      }
      if (d.resources?.memory?.used_percent != null) {
        setMemHistory((prev) => [...prev.slice(-19), d.resources.memory.used_percent])
      }
    } catch {
      setFetchError(true)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])
  useEffect(() => {
    if (!autoRefresh) return
    const t = setInterval(fetchData, 30000)
    return () => clearInterval(t)
  }, [autoRefresh, fetchData])

  const filteredLogs = logFilter === "all" ? logs : logs.filter((l) => l.level.toLowerCase() === logFilter)
  const searchedLogs = logSearch ? filteredLogs.filter((l) => l.message.toLowerCase().includes(logSearch.toLowerCase()) || l.source.toLowerCase().includes(logSearch.toLowerCase())) : filteredLogs

  if (isLoading)
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-12 w-64 bg-neutral-800" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-36 bg-neutral-800" />
          ))}
        </div>
        <Skeleton className="h-96 bg-neutral-800" />
      </div>
    )

  if (fetchError)
    return (
      <div className="flex flex-col items-center justify-center h-full py-24 text-neutral-500">
        <AlertCircle className="w-10 h-10 mb-3 text-red-500/60" />
        <p className="text-sm mb-4">数据加载失败</p>
        <Button variant="outline" size="sm" onClick={fetchData} className="border-neutral-700 text-neutral-400">
          重新加载
        </Button>
      </div>
    )

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">硬件与系统</h1>
          <p className="text-sm text-neutral-400 mt-1">Mini 设备、JBT 调度器和通知链路健康状态</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-neutral-500">自动刷新</span>
            <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} />
          </div>
          {lastUpdate && (
            <span className="text-xs text-neutral-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {lastUpdate}
            </span>
          )}
          <Button variant="outline" size="sm" onClick={fetchData} className="border-neutral-700 text-neutral-300">
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { icon: Cpu, label: "CPU 使用率", value: cpu?.usage_percent, sub: cpu ? `${cpu.logical_cores} 逻辑核心` : "", color: "blue" },
          { icon: MemoryStick, label: "内存使用率", value: mem?.used_percent, sub: mem ? `${(mem.used_mb / 1024).toFixed(1)} GB / ${(mem.total_mb / 1024).toFixed(1)} GB` : "", color: "purple" },
          { icon: HardDrive, label: "磁盘使用率", value: disk?.used_percent, sub: disk ? `已用 ${humanBytes(disk.used_bytes)} / 剩余 ${humanBytes(disk.free_bytes)}` : "", color: "orange" },
        ].map((r) => (
          <Card key={r.label} className="bg-neutral-900 border-neutral-800">
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`p-2 bg-${r.color}-500/10 rounded-lg`}>
                    <r.icon className={`w-6 h-6 text-${r.color}-500`} />
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500 uppercase tracking-wider">{r.label}</p>
                    <p className="text-2xl font-bold text-white font-mono">{r.value != null ? `${r.value}%` : "—"}</p>
                  </div>
                </div>
                {r.value != null && (
                  <Badge variant="outline" className={r.value < 75 ? "border-green-500/30 text-green-400" : r.value < 90 ? "border-yellow-500/30 text-yellow-400" : "border-red-500/30 text-red-400"}>
                    {r.value < 75 ? "正常" : r.value < 90 ? "偏高" : "告警"}
                  </Badge>
                )}
              </div>
              {r.value != null && <Progress value={r.value} className="h-3 bg-neutral-800" />}
              {r.sub && <p className="text-xs text-neutral-500 mt-2">{r.sub}</p>}
              {r.label === "CPU 使用率" && cpuHistory.length > 1 && (
                <div className="mt-3 flex items-end gap-0.5 h-8">
                  {cpuHistory.map((val, i) => (
                    <div key={i} className="flex-1 bg-blue-500/30 rounded-t" style={{ height: `${val}%` }} />
                  ))}
                </div>
              )}
              {r.label === "内存使用率" && memHistory.length > 1 && (
                <div className="mt-3 flex items-end gap-0.5 h-8">
                  {memHistory.map((val, i) => (
                    <div key={i} className="flex-1 bg-purple-500/30 rounded-t" style={{ height: `${val}%` }} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
              <Server className="w-4 h-4 text-orange-500" />
              JBT 关键进程
            </CardTitle>
          </CardHeader>
          <CardContent>
            {processes.length === 0 ? (
              <p className="text-sm text-neutral-500 text-center py-6">无进程数据</p>
            ) : (
              <div className="space-y-3">
                {processes.map((p) => (
                  <div key={p.id} className="p-4 bg-neutral-800/50 rounded-lg border border-neutral-800">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        {p.status === "running" ? <CheckCircle className="w-4 h-4 text-green-500" /> : p.status === "warning" ? <AlertTriangle className="w-4 h-4 text-yellow-500" /> : <XCircle className="w-4 h-4 text-red-500" />}
                        <span className="text-white font-medium">{p.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={p.status === "running" ? "bg-green-500/20 text-green-400 border-green-500/30" : p.status === "warning" ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" : "bg-red-500/20 text-red-400 border-red-500/30"}>
                          {p.status === "running" ? "运行中" : p.status === "warning" ? "警告" : "已停止"}
                        </Badge>
                        {p.status === "stopped" && (
                          <Button size="sm" variant="outline" className="h-7 px-2 border-green-500/30 text-green-400 hover:bg-green-500/10">
                            <Play className="w-3 h-3" />
                          </Button>
                        )}
                        {p.status === "running" && (
                          <Button size="sm" variant="outline" className="h-7 px-2 border-red-500/30 text-red-400 hover:bg-red-500/10">
                            <Square className="w-3 h-3" />
                          </Button>
                        )}
                      </div>
                    </div>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
                      <div>
                        <p className="text-xs text-neutral-500 mb-1">PID</p>
                        <p className="text-white font-mono">{p.pid ?? "—"}</p>
                      </div>
                      <div>
                        <p className="text-xs text-neutral-500 mb-1">CPU</p>
                        <p className="text-white font-mono">{p.cpu_usage.toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-xs text-neutral-500 mb-1">内存</p>
                        <p className="text-white font-mono">{p.mem_usage.toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-xs text-neutral-500 mb-1">最近心跳</p>
                        <p className="text-green-400 font-mono text-xs">{p.last_heartbeat ? p.last_heartbeat.slice(11, 19) : "—"}</p>
                      </div>
                    </div>
                    {p.is_single_instance && (
                      <div className="mt-2 flex items-center gap-1 text-xs text-neutral-500">
                        <CheckCircle className="w-3 h-3 text-green-500" />
                        单实例运行
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
              <Send className="w-4 h-4 text-orange-500" />
              通知状态面板
            </CardTitle>
          </CardHeader>
          <CardContent>
            {notifications.length === 0 ? (
              <p className="text-sm text-neutral-500 text-center py-6">无通知数据</p>
            ) : (
              <div className="space-y-3">
                {notifications.map((ch) => (
                  <div key={ch.id} className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg">
                    <div className="flex items-center gap-3">
                      {ch.type === "feishu" ? <Zap className="w-4 h-4 text-blue-400" /> : <Mail className="w-4 h-4 text-purple-400" />}
                      <div>
                        <span className="text-sm text-white">{ch.name}</span>
                        {!ch.configured && <p className="text-xs text-neutral-500">未配置</p>}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {ch.last_send_time && <span className="text-xs text-neutral-400 font-mono">{ch.last_send_time.slice(11, 16)}</span>}
                      {ch.configured ? <CheckCircle className="w-4 h-4 text-green-500" /> : <XCircle className="w-4 h-4 text-neutral-500" />}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="bg-neutral-900 border-neutral-800 lg:col-span-2">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
                <FileText className="w-4 h-4 text-orange-500" />
                调度日志
              </CardTitle>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-neutral-500" />
                  <Input
                    placeholder="搜索日志..."
                    value={logSearch}
                    onChange={(e) => setLogSearch(e.target.value)}
                    className="pl-7 w-40 h-7 text-xs bg-neutral-800 border-neutral-700 text-white placeholder:text-neutral-500"
                  />
                </div>
                <Tabs value={logFilter} onValueChange={setLogFilter}>
                  <TabsList className="bg-neutral-800 h-8">
                    <TabsTrigger value="all" className="text-xs px-3 py-1">
                      全部
                    </TabsTrigger>
                    <TabsTrigger value="info" className="text-xs px-3 py-1">
                      INFO
                    </TabsTrigger>
                    <TabsTrigger value="warning" className="text-xs px-3 py-1">
                      WARN
                    </TabsTrigger>
                    <TabsTrigger value="error" className="text-xs px-3 py-1">
                      ERROR
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-80 bg-neutral-950 rounded-lg border border-neutral-800 p-4">
              {searchedLogs.length === 0 ? (
                <p className="text-xs text-neutral-500 text-center py-8">暂无日志</p>
              ) : (
                <div className="space-y-1 font-mono text-xs">
                  {searchedLogs
                    .slice()
                    .reverse()
                    .map((l, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <span className="text-neutral-500 whitespace-nowrap">{l.timestamp ? l.timestamp.slice(11, 19) : "—"}</span>
                        <Badge variant="outline" className={`text-xs px-1.5 py-0 flex-shrink-0 ${l.level === "ERROR" ? "border-red-500/50 text-red-400" : l.level === "WARNING" ? "border-yellow-500/50 text-yellow-400" : "border-blue-500/50 text-blue-400"}`}>
                          {l.level}
                        </Badge>
                        <span className="text-neutral-300 break-all">{l.message}</span>
                      </div>
                    ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
              <Database className="w-4 h-4 text-orange-500" />
              采集源新鲜度
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-80">
              {sources.length === 0 ? (
                <p className="text-sm text-neutral-500 text-center py-8">无数据</p>
              ) : (
                <div className="space-y-2">
                  {sources.map((s, i) => (
                    <div key={`${s.name}-${i}`} className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg">
                      <div>
                        <p className="text-xs font-bold text-orange-400 font-mono tracking-wider">{collectorDisplayName(s.name)}</p>
                        <p className="text-[11px] text-neutral-500">
                          {collectorZhName(s.name, s.label)} · 阈值 {s.threshold_h}h
                        </p>
                      </div>
                      <span className={`text-sm font-mono ${s.skipped ? "text-neutral-400" : s.ok ? "text-green-400" : "text-red-400"}`}>{s.age_str || "—"}</span>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
