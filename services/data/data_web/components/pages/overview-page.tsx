"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Database,
  CheckCircle,
  AlertTriangle,
  XCircle,
  RefreshCw,
  ArrowRight,
  FileText,
  SkipForward,
  AlertCircle,
} from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface CollectorItem {
  name: string
  label: string
  ok: boolean
  age_h: number
  age_str: string
  threshold_h: number
  trading_only: boolean
  skipped: boolean
  schedule_expr?: string
  schedule_type?: string
  data_source?: string
  output_dir?: string
}

interface CollectorSummary {
  total: number
  ok: number
  warning: number
  failed: number
  skipped: number
}

interface LogEntry {
  timestamp: string | null
  level: "INFO" | "WARNING" | "ERROR"
  source: string
  message: string
}

type LogFilter = "all" | "INFO" | "WARNING" | "ERROR"

function getItemStatus(c: CollectorItem): "success" | "skipped" | "warning" | "failed" {
  if (c.skipped) return "skipped"
  if (c.ok) return "success"
  if (c.age_h > 0 && c.age_h <= c.threshold_h * 2) return "warning"
  return "failed"
}

function statusDot(c: CollectorItem) {
  const s = getItemStatus(c)
  const map = {
    success: "bg-green-500",
    warning: "bg-yellow-500",
    failed: "bg-red-500",
    skipped: "bg-neutral-500",
  }
  return map[s]
}

function statusBorder(c: CollectorItem) {
  const s = getItemStatus(c)
  const map = {
    success: "border-green-500/30 hover:border-green-500/50",
    warning: "border-yellow-500/30 hover:border-yellow-500/50",
    failed: "border-red-500/30 hover:border-red-500/50",
    skipped: "border-neutral-600 hover:border-neutral-500",
  }
  return map[s]
}

export default function OverviewPage({
  refreshNonce,
  onNavigate,
}: {
  refreshNonce?: number
  onNavigate?: (page: string) => void
}) {
  const [isLoading, setIsLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)
  const [summary, setSummary] = useState<CollectorSummary | null>(null)
  const [collectors, setCollectors] = useState<CollectorItem[]>([])
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [logFilter, setLogFilter] = useState<LogFilter>("all")

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setFetchError(false)
    try {
      const [cRes, sRes] = await Promise.all([
        fetch("/api/data/api/v1/dashboard/collectors"),
        fetch("/api/data/api/v1/dashboard/system"),
      ])
      if (!cRes.ok || !sRes.ok) throw new Error("fetch failed")
      const [cData, sData] = await Promise.all([cRes.json(), sRes.json()])
      setSummary(cData.summary)
      setCollectors(cData.collectors ?? [])
      setLogs(sData.logs ?? [])
    } catch {
      setFetchError(true)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [refreshNonce, fetchData])

  const filteredLogs = logFilter === "all" ? logs : logs.filter((l) => l.level === logFilter)

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-28 bg-neutral-800" />)}
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

  const lastLogTime = logs.length > 0 ? (logs[logs.length - 1].timestamp?.slice(11, 16) ?? "—") : "—"

  return (
    <div className="p-6 space-y-6">
      {/* 顶部操作栏 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">数据端总览</h1>
          <p className="text-sm text-neutral-400 mt-1">一屏看懂 JBT 数据采集系统全局健康状态</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="border-neutral-700 text-neutral-300 hover:bg-neutral-800" onClick={fetchData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新总览
          </Button>
          <Button className="bg-orange-500 hover:bg-orange-600 text-white" onClick={() => onNavigate?.("collectors")}>
            进入采集器管理
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </div>

      {/* 核心指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">采集器状态</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold text-white font-mono">{summary?.ok ?? "—"}</span>
                  <span className="text-lg text-neutral-500 font-mono">/ {summary?.total ?? "—"}</span>
                </div>
                <p className="text-xs text-neutral-400 mt-1">正常运行</p>
              </div>
              <div className="p-2 bg-green-500/10 rounded-lg">
                <Database className="w-6 h-6 text-green-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">警告 / 异常</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold text-yellow-400 font-mono">{summary?.warning ?? 0}</span>
                  <span className="text-lg text-neutral-500 font-mono">/ {summary?.failed ?? 0}</span>
                </div>
                <p className="text-xs text-neutral-400 mt-1">需关注</p>
              </div>
              <div className="p-2 bg-yellow-500/10 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-yellow-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">跳过采集器</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold text-neutral-400 font-mono">{summary?.skipped ?? "—"}</span>
                </div>
                <p className="text-xs text-neutral-400 mt-1">非交易日跳过</p>
              </div>
              <div className="p-2 bg-neutral-700/50 rounded-lg">
                <SkipForward className="w-6 h-6 text-neutral-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">最新日志</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold text-white font-mono">{lastLogTime}</span>
                </div>
                <p className="text-xs text-neutral-400 mt-1">最近一条时间</p>
              </div>
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <FileText className="w-6 h-6 text-blue-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 采集器运行状态矩阵 */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider">
              采集器运行状态矩阵
            </CardTitle>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-green-500" /><span className="text-neutral-400">正常</span></div>
              <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-yellow-500" /><span className="text-neutral-400">延迟</span></div>
              <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-red-500" /><span className="text-neutral-400">失败</span></div>
              <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-neutral-500" /><span className="text-neutral-400">跳过</span></div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {collectors.length === 0 ? (
            <p className="text-sm text-neutral-500 text-center py-8">暂无采集器数据</p>
          ) : (
            <TooltipProvider>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                {collectors.map((c) => (
                  <Tooltip key={c.name}>
                    <TooltipTrigger asChild>
                      <div className={`p-3 bg-neutral-800/50 border rounded-lg cursor-pointer transition-all ${statusBorder(c)}`}>
                        <div className="flex items-start justify-between mb-2">
                          <span className="text-sm font-medium text-white truncate pr-2">{c.label || c.name}</span>
                          <span className={`w-2 h-2 rounded-full flex-shrink-0 mt-1.5 ${statusDot(c)}`} />
                        </div>
                        <div className="space-y-1 text-xs">
                          {c.schedule_expr && (
                            <div className="flex justify-between text-neutral-500">
                              <span>调度</span>
                              <code className="text-neutral-300 font-mono text-xs truncate max-w-[80px]">{c.schedule_expr}</code>
                            </div>
                          )}
                          <div className="flex justify-between text-neutral-500">
                            <span>更新</span>
                            <span className="text-neutral-300 font-mono">{c.age_str || "—"}</span>
                          </div>
                          <div className="flex justify-between text-neutral-500">
                            <span>阈值</span>
                            <span className="text-neutral-300 font-mono">{c.threshold_h}h</span>
                          </div>
                        </div>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="bg-neutral-800 border-neutral-700 text-white p-3 max-w-xs">
                      <div className="space-y-1.5">
                        <p className="font-medium">{c.label || c.name}</p>
                        <p className="text-xs text-neutral-400 font-mono">{c.name}</p>
                        {c.data_source && <p className="text-xs text-neutral-400">数据源: <span className="text-white">{c.data_source}</span></p>}
                        {c.trading_only && <p className="text-xs text-blue-400">仅交易日有效</p>}
                        {c.skipped && <p className="text-xs text-neutral-400">当前已跳过（非交易日）</p>}
                      </div>
                    </TooltipContent>
                  </Tooltip>
                ))}
              </div>
            </TooltipProvider>
          )}
        </CardContent>
      </Card>

      {/* 最新运行日志 */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider">
              调度日志
            </CardTitle>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 bg-neutral-800 rounded-lg p-1">
                {(["all", "INFO", "WARNING", "ERROR"] as const).map((level) => (
                  <button
                    key={level}
                    onClick={() => setLogFilter(level)}
                    className={`px-2 py-1 text-xs rounded transition-colors ${
                      logFilter === level ? "bg-neutral-700 text-white" : "text-neutral-400 hover:text-white"
                    }`}
                  >
                    {level === "all" ? "全部" : level}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredLogs.length === 0 ? (
            <p className="text-sm text-neutral-500 text-center py-8">暂无日志记录</p>
          ) : (
            <div className="space-y-2 max-h-[280px] overflow-y-auto">
              {filteredLogs.slice().reverse().map((log, index) => (
                <div key={index} className="flex items-start gap-3 p-2 bg-neutral-800/30 rounded-lg hover:bg-neutral-800/50 transition-colors">
                  <span className="text-xs text-neutral-500 font-mono whitespace-nowrap mt-0.5">
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
                  <span className="text-sm text-neutral-300 flex-1 break-words">{log.message}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
