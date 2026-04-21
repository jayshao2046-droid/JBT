"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Database,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Cpu,
  MemoryStick,
  HardDrive,
  Activity,
  FileText,
  AlertCircle,
} from "lucide-react"
import { collectorDisplayName } from "@/lib/collector-labels"
import { dataApi, CollectorSummary, CollectorItem, ResourceCpu, ResourceMem, ResourceDisk, LogEntry } from "@/lib/api/data"

const STATUS_DOT: Record<string, string> = {
  success: "bg-green-500",
  failed: "bg-red-500",
  delayed: "bg-yellow-500",
  idle: "bg-neutral-500",
}
const STATUS_BG: Record<string, string> = {
  success: "bg-green-500/10 border-green-500/20",
  failed: "bg-red-500/10 border-red-500/20",
  delayed: "bg-yellow-500/10 border-yellow-500/20",
  idle: "bg-neutral-500/10 border-neutral-500/20",
}

export default function OverviewPage() {
  const [isLoading, setIsLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)
  const [summary, setSummary] = useState<CollectorSummary>({ total: 0, success: 0, failed: 0, delayed: 0, idle: 0 })
  const [items, setItems] = useState<CollectorItem[]>([])
  const [cpu, setCpu] = useState<ResourceCpu | null>(null)
  const [mem, setMem] = useState<ResourceMem | null>(null)
  const [disk, setDisk] = useState<ResourceDisk | null>(null)
  const [logs, setLogs] = useState<LogEntry[]>([])

  const fetchData = useCallback(async () => {
    try {
      const [cR, sR] = await Promise.all([dataApi.getCollectors(), dataApi.getSystem()])
      setSummary(cR.summary)
      setItems(cR.collectors ?? [])
      setCpu(sR.resources?.cpu ?? null)
      setMem(sR.resources?.memory ?? null)
      setDisk(sR.resources?.disk ?? null)
      setLogs((sR.logs ?? []).slice(-12))
      setFetchError(false)
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
    const t = setInterval(fetchData, 30000)
    return () => clearInterval(t)
  }, [fetchData])

  if (isLoading)
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-12 w-64" />
        <div className="grid grid-cols-3 lg:grid-cols-7 gap-3">
          {[1, 2, 3, 4, 5, 6, 7].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    )

  if (fetchError)
    return (
      <div className="flex flex-col items-center justify-center h-full py-24 text-neutral-500">
        <AlertCircle className="w-10 h-10 mb-3 text-red-500/60" />
        <p className="text-sm mb-4">数据加载失败</p>
        <Button variant="outline" size="sm" onClick={fetchData}>
          重新加载
        </Button>
      </div>
    )

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">数据端概览</h1>
        <p className="text-sm text-muted-foreground mt-1">JBT 数据服务实时总览</p>
      </div>

      <div className="grid grid-cols-3 lg:grid-cols-7 gap-3">
        {[
          { icon: Database, label: "采集源", value: `${summary.success}/${summary.total}`, color: "text-foreground", bg: "bg-blue-500/10", ic: "text-blue-500" },
          { icon: CheckCircle, label: "正常", value: summary.success, color: "text-green-400", bg: "bg-green-500/10", ic: "text-green-500" },
          { icon: XCircle, label: "失败", value: summary.failed, color: "text-red-400", bg: "bg-red-500/10", ic: "text-red-500" },
          { icon: AlertTriangle, label: "延迟", value: summary.delayed, color: "text-yellow-400", bg: "bg-yellow-500/10", ic: "text-yellow-500" },
          { icon: Cpu, label: "CPU", value: cpu ? `${cpu.usage_percent}%` : "—", color: "text-blue-500", bg: "bg-blue-500/10", ic: "text-blue-500" },
          { icon: MemoryStick, label: "内存", value: mem ? `${mem.used_percent}%` : "—", color: "text-purple-500", bg: "bg-purple-500/10", ic: "text-purple-500" },
          { icon: HardDrive, label: "磁盘", value: disk ? `${disk.used_percent}%` : "—", color: "text-orange-500", bg: "bg-orange-500/10", ic: "text-orange-500" },
        ].map((kpi) => (
          <Card key={kpi.label}>
            <CardContent className="p-3 flex flex-col items-center text-center">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-2 ${kpi.bg}`}>
                <kpi.icon className={`w-4 h-4 ${kpi.ic}`} />
              </div>
              <p className="text-[10px] text-muted-foreground">{kpi.label}</p>
              <p className={`text-lg font-bold font-mono ${kpi.color}`}>{kpi.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-foreground flex items-center gap-2">
                <Activity className="w-4 h-4 text-orange-500" />
                采集源状态矩阵
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {items.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">无采集源</p>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {items.map((c, i) => (
                  <div
                    key={`${c.id}-${i}`}
                    className={`p-3 rounded-lg border cursor-pointer hover:opacity-90 transition-opacity ${STATUS_BG[c.status] ?? STATUS_BG.idle}`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`w-2 h-2 rounded-full ${STATUS_DOT[c.status] ?? STATUS_DOT.idle}`} />
                      <p className="text-xs font-bold text-orange-400 font-mono tracking-wider truncate">{collectorDisplayName(c.id)}</p>
                    </div>
                    <p className="text-[10px] text-muted-foreground truncate">
                      {c.name} · {c.category}
                    </p>
                    <p className="text-[10px] text-muted-foreground mt-0.5">{c.age_str || "—"}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-foreground flex items-center gap-2">
                <FileText className="w-4 h-4 text-orange-500" />
                近期日志
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {logs.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">暂无日志</p>
            ) : (
              <div className="space-y-2">
                {logs
                  .slice()
                  .reverse()
                  .map((l, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <span className="text-[10px] text-muted-foreground font-mono whitespace-nowrap mt-0.5">{l.timestamp ? l.timestamp.slice(11, 19) : ""}</span>
                      <Badge
                        variant="outline"
                        className={`text-[10px] px-1 py-0 flex-shrink-0 ${
                          l.level === "ERROR" ? "border-red-500/50 text-red-400" : l.level === "WARNING" ? "border-yellow-500/50 text-yellow-400" : "border-blue-500/50 text-blue-400"
                        }`}
                      >
                        {l.level}
                      </Badge>
                      <span className="text-xs text-muted-foreground break-all">
                        {l.message.replace(/^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[,.]\d+\s+-\s+\S+\s+-\s+\w+\s+-\s+/, "")}
                      </span>
                    </div>
                  ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: "CPU", pct: cpu?.usage_percent, sub: cpu ? `${cpu.logical_cores} 核` : "" },
          { label: "内存", pct: mem?.used_percent, sub: mem ? `${(mem.used_mb / 1024).toFixed(1)}G / ${(mem.total_mb / 1024).toFixed(1)}G` : "" },
          { label: "磁盘", pct: disk?.used_percent, sub: disk ? `剩余 ${(disk.free_bytes / 1073741824).toFixed(1)} GB` : "" },
        ].map((r) => (
          <Card key={r.label}>
            <CardContent className="p-4 cursor-pointer hover:bg-muted/40 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-muted-foreground">{r.label}</span>
                <span className="text-sm font-bold text-foreground font-mono">{r.pct != null ? `${r.pct}%` : "—"}</span>
              </div>
              {r.pct != null && <Progress value={r.pct} className="h-2" />}
              <p className="text-[10px] text-muted-foreground mt-1">{r.sub}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
