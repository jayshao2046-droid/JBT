"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Database,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Cpu,
  Activity,
  AlertCircle,
  Clock,
  ArrowUpCircle,
  ArrowDownCircle,
} from "lucide-react"
import { collectorDisplayName } from "@/lib/collector-labels"
import { dataApi, CollectorSummary, CollectorItem, ResourceCpu, ResourceMem, ResourceDisk, ResourceNetwork, CollectorResultsResponse } from "@/lib/api/data"
import { LogsViewer } from "./logs-viewer"

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
  const [net, setNet] = useState<ResourceNetwork | null>(null)
  const [collectorResults, setCollectorResults] = useState<CollectorResultsResponse | null>(null)

  const fetchData = useCallback(async () => {
    try {
      const [cR, sR, crR] = await Promise.all([
        dataApi.getCollectors(), 
        dataApi.getSystem(),
        dataApi.getCollectorResults(),
      ])
      setSummary(cR.summary)
      setItems(cR.collectors ?? [])
      setCpu(sR.resources?.cpu ?? null)
      setMem(sR.resources?.memory ?? null)
      setDisk(sR.resources?.disk ?? null)
      setNet(sR.resources?.network ?? null)
      setCollectorResults(crR)
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
        <div className="grid grid-cols-4 gap-3">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
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

      {/* 第1排：采集器状态 */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { icon: Database, label: "采集源",   value: `${summary.success}/${summary.total}`, color: "text-blue-400",    bg: "bg-blue-500/10",    ic: "text-blue-500" },
          { icon: CheckCircle, label: "正常",  value: String(summary.success),               color: "text-green-400",  bg: "bg-green-500/10",  ic: "text-green-500" },
          { icon: AlertTriangle, label: "延迟",value: String(summary.delayed),               color: "text-yellow-400", bg: "bg-yellow-500/10", ic: "text-yellow-500" },
          { icon: XCircle, label: "失败",      value: String(summary.failed),                color: "text-red-400",    bg: "bg-red-500/10",    ic: "text-red-500" },
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

      {/* 第2排：系统规格（静态参数 + 网络速率）*/}
      <div className="grid grid-cols-4 gap-3">
        {[
          { icon: Clock,          label: "空闲采集",  value: String(summary.idle),                                              color: "text-neutral-400",  bg: "bg-neutral-500/10",  ic: "text-neutral-400" },
          { icon: Cpu,            label: "CPU 核数",  value: cpu  ? `${cpu.logical_cores} 核`                      : "—",       color: "text-blue-400",     bg: "bg-blue-500/10",     ic: "text-blue-500" },
          { icon: ArrowUpCircle,  label: "网络上行",  value: net  ? `${net.send_kbps.toFixed(1)} KB/s`            : "—",       color: "text-cyan-400",     bg: "bg-cyan-500/10",     ic: "text-cyan-500" },
          { icon: ArrowDownCircle,label: "网络下行",  value: net  ? `${net.recv_kbps.toFixed(1)} KB/s`            : "—",       color: "text-teal-400",     bg: "bg-teal-500/10",     ic: "text-teal-500" },
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

      {/* 第3排：最新采集结果（实时数据，不是 mock）*/}
      <div className="grid grid-cols-4 gap-3">
        {collectorResults && Object.values(collectorResults.collectors).slice(0, 4).map((collector) => (
          <Card key={collector.name}>
            <CardContent className="p-3 flex flex-col items-center text-center">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-2 ${collector.status === "success" ? "bg-green-500/10" : "bg-red-500/10"}`}>
                {collector.status === "success" ? (
                  <CheckCircle className={`w-4 h-4 ${collector.status === "success" ? "text-green-500" : "text-red-500"}`} />
                ) : (
                  <XCircle className="w-4 h-4 text-red-500" />
                )}
              </div>
              <p className="text-[10px] text-muted-foreground truncate">{collector.name}</p>
              <p className={`text-lg font-bold font-mono ${collector.status === "success" ? "text-green-400" : "text-red-400"}`}>
                {collector.count > 0 ? `${collector.count}` : "—"}
              </p>
              {collector.duration && (
                <p className="text-[9px] text-muted-foreground mt-0.5">{collector.duration.toFixed(2)}s</p>
              )}
            </CardContent>
          </Card>
        ))}
        {/* 如果采集结果少于4个，补充空白卡片 */}
        {collectorResults && Object.values(collectorResults.collectors).length < 4 && 
          Array(4 - Object.values(collectorResults.collectors).length).fill(null).map((_, idx) => (
            <Card key={`empty-${idx}`}>
              <CardContent className="p-3 flex flex-col items-center text-center justify-center h-24">
                <p className="text-xs text-muted-foreground">暂无数据</p>
              </CardContent>
            </Card>
          ))
        }
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-[500px]">
        <Card className="lg:col-span-2 flex flex-col">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-foreground flex items-center gap-2">
                <Activity className="w-4 h-4 text-orange-500" />
                采集源状态矩阵
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="flex-1 overflow-auto">
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

        {/* 采集日志窗口 - 右侧空缺位置，填满整个高度 */}
        <div className="flex flex-col">
          <LogsViewer />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: "CPU 使用率",  pct: cpu?.usage_percent,  sub: cpu  ? `${cpu.usage_percent}% · ${cpu.logical_cores} 核`                                                    : "" },
          { label: "内存使用率",  pct: mem?.used_percent,   sub: mem  ? `${(mem.used_mb/1024).toFixed(1)} GB / ${(mem.total_mb/1024).toFixed(1)} GB 已用`                   : "" },
          { label: "磁盘使用率",  pct: disk?.used_percent,  sub: disk ? `${(disk.used_bytes/1073741824).toFixed(0)} GB / ${(disk.total_bytes/1073741824).toFixed(0)} GB 已用` : "" },
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
