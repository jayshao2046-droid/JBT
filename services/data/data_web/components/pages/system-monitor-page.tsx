"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
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
} from "lucide-react"

interface ResourceCpu {
  usage_percent: number
  logical_cores: number
}
interface ResourceMemory {
  used_percent: number
  total_mb: number
  used_mb: number
}
interface ResourceDisk {
  used_percent: number
  total_bytes: number
  used_bytes: number
  free_bytes: number
}
interface Resources {
  cpu: ResourceCpu
  memory: ResourceMemory
  disk: ResourceDisk
}

interface ProcessEntry {
  id: string
  name: string
  status: "running" | "warning" | "stopped"
  pid: number | null
  uptime: string | null
  cpu_usage: number
  mem_usage: number
  last_heartbeat: string | null
  is_single_instance: boolean
}

interface NotificationChannel {
  id: string
  name: string
  type: "feishu" | "email"
  configured: boolean
  last_send_time: string | null
  last_status: "success" | "failed"
}

interface SourceItem {
  name: string
  label: string
  ok: boolean
  age_h: number
  age_str: string
  threshold_h: number
  skipped: boolean
}

interface LogEntry {
  timestamp: string | null
  level: "INFO" | "WARNING" | "ERROR"
  source: string
  message: string
}

interface SystemApiResponse {
  generated_at: string
  resources: Resources
  processes: ProcessEntry[]
  notifications: NotificationChannel[]
  sources: SourceItem[]
  logs: LogEntry[]
}

function humanBytes(bytes: number): string {
  if (bytes <= 0) return "0 B"
  const units = ["B","KB","MB","GB","TB"]
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

export default function SystemMonitorPage({ refreshNonce }: { refreshNonce?: number }) {
  const [activeLogType, setActiveLogType] = useState("all")
  const [isLoading, setIsLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)
  const [resources, setResources] = useState<Resources | null>(null)
  const [processes, setProcesses] = useState<ProcessEntry[]>([])
  const [notifications, setNotifications] = useState<NotificationChannel[]>([])
  const [sources, setSources] = useState<SourceItem[]>([])
  const [logs, setLogs] = useState<LogEntry[]>([])

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setFetchError(false)
    try {
      const res = await fetch("/api/data/api/v1/dashboard/system")
      if (!res.ok) throw new Error("fetch failed")
      const data: SystemApiResponse = await res.json()
      setResources(data.resources)
      setProcesses(data.processes ?? [])
      setNotifications(data.notifications ?? [])
      setSources(data.sources ?? [])
      setLogs(data.logs ?? [])
    } catch {
      setFetchError(true)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [refreshNonce, fetchData])

  const filteredLogs =
    activeLogType === "all"
      ? logs
      : logs.filter((l) =>
          activeLogType === "error"
            ? l.level === "ERROR"
            : activeLogType === "warning"
              ? l.level === "WARNING"
              : l.level === "INFO"
        )

  const getStatusIcon = (status: ProcessEntry["status"]) => {
    if (status === "running") return <CheckCircle className="w-4 h-4 text-green-500" />
    if (status === "warning") return <AlertTriangle className="w-4 h-4 text-yellow-500" />
    return <XCircle className="w-4 h-4 text-red-500" />
  }

  const getStatusBadge = (status: ProcessEntry["status"]) => {
    if (status === "running") return "bg-green-500/20 text-green-400 border-green-500/30"
    if (status === "warning") return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
    return "bg-red-500/20 text-red-400 border-red-500/30"
  }

  const cpuStatus = (pct: number) => pct < 70 ? "正常" : pct < 90 ? "偏高" : "过载"
  const cpuStatusCls = (pct: number) => pct < 70 ? "border-green-500/30 text-green-400" : pct < 90 ? "border-yellow-500/30 text-yellow-400" : "border-red-500/30 text-red-400"
  const memStatus = (pct: number) => pct < 75 ? "正常" : pct < 90 ? "偏高" : "告警"
  const memStatusCls = (pct: number) => pct < 75 ? "border-green-500/30 text-green-400" : pct < 90 ? "border-yellow-500/30 text-yellow-400" : "border-red-500/30 text-red-400"

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-12 w-64 bg-neutral-800" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-40 bg-neutral-800" />)}
        </div>
        <Skeleton className="h-96 bg-neutral-800" />
      </div>
    )
  }

  if (fetchError) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-24 text-neutral-500">
        <AlertCircle className="w-10 h-10 mb-3 text-red-500/60" />
        <p className="text-sm mb-4">数据加载失败，请稍后重试</p>
        <Button variant="outline" size="sm" onClick={fetchData} className="border-neutral-700 text-neutral-400">
          重新加载
        </Button>
      </div>
    )
  }

  const cpu = resources?.cpu
  const mem = resources?.memory
  const disk = resources?.disk

  return (
    <div className="p-6 space-y-6">
      {/* 页面头部 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">硬件与系统</h1>
          <p className="text-sm text-neutral-400 mt-1">监控 Mini 设备、JBT 调度器和通知链路健康状态</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData} className="border-neutral-700 text-neutral-300">
          <RefreshCw className="w-4 h-4 mr-2" />
          刷新
        </Button>
      </div>

      {/* 资源监控卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* CPU */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/10 rounded-lg">
                  <Cpu className="w-6 h-6 text-blue-500" />
                </div>
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider">CPU 使用率</p>
                  <p className="text-2xl font-bold text-white font-mono">
                    {cpu ? `${cpu.usage_percent}%` : "—"}
                  </p>
                </div>
              </div>
              {cpu && (
                <Badge variant="outline" className={cpuStatusCls(cpu.usage_percent)}>
                  {cpuStatus(cpu.usage_percent)}
                </Badge>
              )}
            </div>
            {cpu && <Progress value={cpu.usage_percent} className="h-3 bg-neutral-800" />}
            {cpu && (
              <p className="text-xs text-neutral-500 mt-2">{cpu.logical_cores} 逻辑核心</p>
            )}
          </CardContent>
        </Card>

        {/* 内存 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-500/10 rounded-lg">
                  <MemoryStick className="w-6 h-6 text-purple-500" />
                </div>
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider">内存使用率</p>
                  <p className="text-2xl font-bold text-white font-mono">
                    {mem ? `${mem.used_percent}%` : "—"}
                  </p>
                </div>
              </div>
              {mem && (
                <Badge variant="outline" className={memStatusCls(mem.used_percent)}>
                  {memStatus(mem.used_percent)}
                </Badge>
              )}
            </div>
            {mem && <Progress value={mem.used_percent} className="h-3 bg-neutral-800" />}
            {mem && (
              <p className="text-xs text-neutral-500 mt-2">
                已用 {(mem.used_mb / 1024).toFixed(1)} GB / 共 {(mem.total_mb / 1024).toFixed(1)} GB
              </p>
            )}
          </CardContent>
        </Card>

        {/* 磁盘 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-500/10 rounded-lg">
                  <HardDrive className="w-6 h-6 text-orange-500" />
                </div>
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider">磁盘使用率</p>
                  <p className="text-2xl font-bold text-white font-mono">
                    {disk ? `${disk.used_percent}%` : "—"}
                  </p>
                </div>
              </div>
              {disk && (
                <Badge variant="outline" className={disk.used_percent < 80 ? "border-green-500/30 text-green-400" : "border-yellow-500/30 text-yellow-400"}>
                  {disk.used_percent < 80 ? "正常" : "偏满"}
                </Badge>
              )}
            </div>
            {disk && <Progress value={disk.used_percent} className="h-3 bg-neutral-800" />}
            {disk && (
              <div className="mt-2 flex items-center justify-between text-xs text-neutral-500">
                <span>已用: {humanBytes(disk.used_bytes)}</span>
                <span>剩余: {humanBytes(disk.free_bytes)}</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* JBT 进程 + 通知状态 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 关键进程 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
              <Server className="w-4 h-4 text-orange-500" />
              JBT 关键进程状态
            </CardTitle>
          </CardHeader>
          <CardContent>
            {processes.length === 0 ? (
              <p className="text-sm text-neutral-500 text-center py-6">无进程数据</p>
            ) : (
              <div className="space-y-4">
                {processes.map((proc) => (
                  <div key={proc.id} className="p-4 bg-neutral-800/50 rounded-lg border border-neutral-800">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(proc.status)}
                        <span className="text-white font-medium">{proc.name}</span>
                      </div>
                      <Badge variant="outline" className={getStatusBadge(proc.status)}>
                        {proc.status === "running" ? "运行中" : proc.status === "warning" ? "警告" : "已停止"}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
                      <div>
                        <p className="text-xs text-neutral-500 mb-1">PID</p>
                        <p className="text-white font-mono">{proc.pid ?? "—"}</p>
                      </div>
                      <div>
                        <p className="text-xs text-neutral-500 mb-1">CPU</p>
                        <p className="text-white font-mono">{proc.cpu_usage.toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-xs text-neutral-500 mb-1">内存</p>
                        <p className="text-white font-mono">{proc.mem_usage.toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-xs text-neutral-500 mb-1">最近心跳</p>
                        <p className="text-green-400 font-mono text-xs">
                          {proc.last_heartbeat ? proc.last_heartbeat.slice(11, 19) : "—"}
                        </p>
                      </div>
                    </div>
                    {proc.is_single_instance && (
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

        {/* 通知状态 */}
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
                      {ch.type === "feishu"
                        ? <Zap className="w-4 h-4 text-blue-400" />
                        : <Mail className="w-4 h-4 text-purple-400" />}
                      <div>
                        <span className="text-sm text-white">{ch.name}</span>
                        {!ch.configured && (
                          <p className="text-xs text-neutral-500">未配置</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {ch.last_send_time && (
                        <span className="text-xs text-neutral-400 font-mono">
                          {ch.last_send_time.slice(11, 16)}
                        </span>
                      )}
                      {ch.configured
                        ? <CheckCircle className="w-4 h-4 text-green-500" />
                        : <XCircle className="w-4 h-4 text-neutral-500" />}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 日志查看器 + 采集源新鲜度 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="bg-neutral-900 border-neutral-800 lg:col-span-2">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
                <FileText className="w-4 h-4 text-orange-500" />
                调度日志
              </CardTitle>
              <Tabs value={activeLogType} onValueChange={setActiveLogType}>
                <TabsList className="bg-neutral-800 h-8">
                  <TabsTrigger value="all" className="text-xs px-3 py-1">全部</TabsTrigger>
                  <TabsTrigger value="info" className="text-xs px-3 py-1">INFO</TabsTrigger>
                  <TabsTrigger value="warning" className="text-xs px-3 py-1">WARN</TabsTrigger>
                  <TabsTrigger value="error" className="text-xs px-3 py-1">ERROR</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-80 bg-neutral-950 rounded-lg border border-neutral-800 p-4">
              {filteredLogs.length === 0 ? (
                <p className="text-xs text-neutral-500 text-center py-8">暂无日志记录</p>
              ) : (
                <div className="space-y-1 font-mono text-xs">
                  {filteredLogs.slice().reverse().map((log, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <span className="text-neutral-500 whitespace-nowrap">
                        {log.timestamp ? log.timestamp.slice(11, 19) : "—"}
                      </span>
                      <Badge
                        variant="outline"
                        className={`text-xs px-1.5 py-0 flex-shrink-0 ${
                          log.level === "ERROR"
                            ? "border-red-500/50 text-red-400"
                            : log.level === "WARNING"
                              ? "border-yellow-500/50 text-yellow-400"
                              : "border-blue-500/50 text-blue-400"
                        }`}
                      >
                        {log.level}
                      </Badge>
                      <span className="text-neutral-300 break-all">{log.message}</span>
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
                  {sources.map((src) => (
                    <div key={src.name} className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg">
                      <div>
                        <p className="text-sm text-white">{src.label || src.name}</p>
                        <p className="text-xs text-neutral-500">阈值 {src.threshold_h}h</p>
                      </div>
                      <span className={`text-sm font-mono ${
                        src.skipped ? "text-neutral-400" : src.ok ? "text-green-400" : "text-red-400"
                      }`}>
                        {src.age_str || "—"}
                      </span>
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
