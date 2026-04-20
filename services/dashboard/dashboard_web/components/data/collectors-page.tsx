"use client"

import { useState, useEffect, useCallback, useMemo } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Database,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  RefreshCw,
  Search,
  Filter,
  AlertCircle,
  Loader2,
  Play,
} from "lucide-react"
import { collectorDisplayName, collectorZhName } from "@/lib/collector-labels"
import { dataApi, CollectorSummary, CollectorItem } from "@/lib/api/data"

const STATUS_CFG: Record<string, { dot: string; badge: string; label: string }> = {
  success: { dot: "bg-green-500", badge: "bg-green-500/15 text-green-400 border-green-500/30", label: "正常" },
  failed: { dot: "bg-red-500", badge: "bg-red-500/15 text-red-400 border-red-500/30", label: "失败" },
  delayed: { dot: "bg-yellow-500", badge: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30", label: "延迟" },
  idle: { dot: "bg-neutral-500", badge: "bg-neutral-500/15 text-neutral-400 border-neutral-500/30", label: "空闲" },
}

export default function CollectorsPage() {
  const [isLoading, setIsLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)
  const [summary, setSummary] = useState<CollectorSummary>({ total: 0, success: 0, failed: 0, delayed: 0, idle: 0 })
  const [collectors, setCollectors] = useState<CollectorItem[]>([])
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastUpdate, setLastUpdate] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("all")
  const [statusFilter, setStatusFilter] = useState("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [restartingIds, setRestartingIds] = useState<string[]>([])

  const fetchData = useCallback(async () => {
    try {
      const res = await dataApi.getCollectors()
      setSummary(res.summary)
      setCollectors(res.collectors ?? [])
      setLastUpdate(new Date().toLocaleTimeString("zh-CN"))
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
    if (!autoRefresh) return
    const t = setInterval(fetchData, 30000)
    return () => clearInterval(t)
  }, [autoRefresh, fetchData])

  const handleRestart = async (cid: string) => {
    setRestartingIds((p) => [...p, cid])
    try {
      await dataApi.restartCollector(cid)
    } catch {}
    setTimeout(() => {
      setRestartingIds((p) => p.filter((x) => x !== cid))
      fetchData()
    }, 2000)
  }

  const categories = useMemo(() => {
    const s = new Set(collectors.map((c) => c.category))
    return ["all", ...Array.from(s).sort()]
  }, [collectors])

  const filtered = useMemo(
    () =>
      collectors.filter((c) => {
        if (categoryFilter !== "all" && c.category !== categoryFilter) return false
        if (statusFilter !== "all" && c.status !== statusFilter) return false
        if (searchQuery) {
          const q = searchQuery.toLowerCase()
          if (!collectorDisplayName(c.name).toLowerCase().includes(q) && !collectorZhName(c.name).toLowerCase().includes(q) && !c.data_source.toLowerCase().includes(q)) return false
        }
        return true
      }),
    [collectors, categoryFilter, statusFilter, searchQuery]
  )

  if (isLoading)
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-12 w-72" />
        <div className="grid grid-cols-5 gap-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    )

  if (fetchError)
    return (
      <div className="flex flex-col items-center justify-center h-full py-24 text-neutral-500">
        <AlertCircle className="w-10 h-10 mb-3 text-red-500/60" />
        <p className="text-sm mb-4">数据加载失败，请稍后重试</p>
        <Button variant="outline" size="sm" onClick={fetchData}>
          重新加载
        </Button>
      </div>
    )

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">采集器管理</h1>
          <p className="text-sm text-muted-foreground mt-1">监控所有数据源的采集状态和运行健康度</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">自动刷新</span>
            <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} />
          </div>
          {lastUpdate && (
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {lastUpdate}
            </span>
          )}
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {[
          { icon: Database, label: "数据源总数", value: summary.total, color: "text-foreground", bg: "bg-blue-500/10", ic: "text-blue-500" },
          { icon: CheckCircle, label: "正常运行", value: summary.success, color: "text-green-400", bg: "bg-green-500/10", ic: "text-green-500" },
          { icon: XCircle, label: "采集失败", value: summary.failed, color: "text-red-400", bg: "bg-red-500/10", ic: "text-red-500" },
          { icon: AlertTriangle, label: "延迟告警", value: summary.delayed, color: "text-yellow-400", bg: "bg-yellow-500/10", ic: "text-yellow-500" },
          { icon: Clock, label: "空闲/停用", value: summary.idle, color: "text-muted-foreground", bg: "bg-neutral-500/10", ic: "text-muted-foreground" },
        ].map((kpi) => (
          <Card key={kpi.label}>
            <CardContent className="p-4 flex flex-col items-center text-center">
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-2 ${kpi.bg}`}>
                <kpi.icon className={`w-4 h-4 ${kpi.ic}`} />
              </div>
              <p className="text-[11px] text-muted-foreground mb-1">{kpi.label}</p>
              <p className={`text-xl font-bold font-mono ${kpi.color}`}>{kpi.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">筛选</span>
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-28 h-8 text-xs">
                <SelectValue placeholder="类别" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((cat) => (
                  <SelectItem key={cat} value={cat}>
                    {cat === "all" ? "全部类别" : cat}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-24 h-8 text-xs">
                <SelectValue placeholder="状态" />
              </SelectTrigger>
              <SelectContent>
                {[
                  { v: "all", l: "全部状态" },
                  { v: "success", l: "正常" },
                  { v: "failed", l: "失败" },
                  { v: "delayed", l: "延迟" },
                  { v: "idle", l: "空闲" },
                ].map((s) => (
                  <SelectItem key={s.v} value={s.v}>
                    {s.l}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="relative flex-1 min-w-[200px]">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" />
              <Input placeholder="搜索采集源..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9 h-8 text-xs" />
            </div>
            <span className="text-xs text-muted-foreground ml-auto">
              {filtered.length} / {collectors.length}
            </span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <ScrollArea className="max-h-[calc(100vh-420px)]">
            {filtered.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-12">无匹配的采集源</p>
            ) : (
              <div className="divide-y divide-border">
                {filtered.map((c, idx) => {
                  const sc = STATUS_CFG[c.status] ?? STATUS_CFG.idle
                  const restarting = restartingIds.includes(c.id)
                  return (
                    <div key={`${c.id}-${idx}`} className="p-4 hover:bg-muted/40 transition-colors">
                      <div className="flex items-center gap-4">
                        <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${sc.dot}`} />
                        <div className="min-w-[180px]">
                          <p className="text-sm font-bold text-orange-400 font-mono tracking-wider">{collectorDisplayName(c.name)}</p>
                          <p className="text-xs text-neutral-500">{collectorZhName(c.name, c.name)}</p>
                        </div>
                        <Badge variant="outline" className="text-xs flex-shrink-0">
                          {c.category}
                        </Badge>
                        <Badge variant="outline" className={`text-xs flex-shrink-0 ${sc.badge}`}>
                          {sc.label}
                        </Badge>
                        <div className="flex-shrink-0 text-xs text-muted-foreground min-w-[120px]">
                          <p className="font-mono">{c.schedule_expr || "—"}</p>
                          <p className="text-[10px]">{c.schedule_type}</p>
                        </div>
                        <div className="flex-shrink-0 min-w-[100px]">
                          <p className="text-xs text-muted-foreground">{c.age_str || "—"}</p>
                        </div>
                        <div className="flex-shrink-0 min-w-[80px]">
                          <p className="text-xs text-muted-foreground">{c.data_source}</p>
                        </div>
                        <div className="flex-1" />
                        {c.errors.length > 0 && (
                          <span className="text-xs text-red-400 flex items-center gap-1 flex-shrink-0">
                            <AlertTriangle className="w-3 h-3" />
                            {c.errors[0].message}
                          </span>
                        )}
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-neutral-500 hover:text-orange-400" onClick={() => handleRestart(c.id)} disabled={restarting}>
                          {restarting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                        </Button>
                      </div>
                      {c.description && (
                        <div className="ml-6 mt-2 flex items-center gap-4 text-[11px] text-muted-foreground">
                          <span>输出: {c.output_dir}</span>
                          {c.trading_only && (
                            <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-yellow-600/30 text-yellow-600">
                              仅交易时段
                            </Badge>
                          )}
                          {c.skipped && (
                            <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-neutral-600 text-neutral-500">
                              已跳过
                            </Badge>
                          )}
                          {c.last_run_time && <span>末次运行: {c.last_run_time}</span>}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}
