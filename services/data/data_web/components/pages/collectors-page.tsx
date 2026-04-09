"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  Eye,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  Search,
  AlertCircle,
  Database,
  Calendar,
  SkipForward,
} from "lucide-react"

interface CollectorItem {
  name: string
  label: string
  ok: boolean
  age_h: number
  age_str: string
  threshold_h: number
  trading_only: boolean
  skipped: boolean
  data_source?: string
  output_dir?: string
  schedule_expr?: string
  schedule_type?: string
}

interface CollectorSummary {
  total: number
  ok: number
  warning: number
  failed: number
  skipped: number
}

interface ApiResponse {
  ts: string
  summary: CollectorSummary
  collectors: CollectorItem[]
}

type StatusFilter = "全部" | "正常" | "异常" | "跳过"

function getItemStatus(c: CollectorItem): "success" | "failed" | "skipped" | "warning" {
  if (c.skipped) return "skipped"
  if (c.ok) return "success"
  if (c.age_h > 0 && c.age_h <= c.threshold_h * 2) return "warning"
  return "failed"
}

function StatusBadge({ collector }: { collector: CollectorItem }) {
  const status = getItemStatus(collector)
  const map = {
    success: { cls: "bg-green-500/20 text-green-400 border-green-500/30", label: "正常" },
    failed: { cls: "bg-red-500/20 text-red-400 border-red-500/30", label: "异常" },
    warning: { cls: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30", label: "延迟" },
    skipped: { cls: "bg-neutral-500/20 text-neutral-400 border-neutral-500/30", label: "跳过" },
  } as const
  const { cls, label } = map[status]
  return (
    <Badge variant="outline" className={cls}>
      {label}
    </Badge>
  )
}

export default function CollectorsPage({ refreshNonce }: { refreshNonce?: number }) {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("全部")
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedItem, setSelectedItem] = useState<CollectorItem | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)
  const [summary, setSummary] = useState<CollectorSummary | null>(null)
  const [collectors, setCollectors] = useState<CollectorItem[]>([])

  const fetchData = async () => {
    setIsLoading(true)
    setFetchError(false)
    try {
      const res = await fetch("/api/data/api/v1/dashboard/collectors")
      if (!res.ok) throw new Error("fetch failed")
      const data: ApiResponse = await res.json()
      setSummary(data.summary)
      setCollectors(data.collectors ?? [])
    } catch {
      setFetchError(true)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [refreshNonce])

  const filteredCollectors = collectors.filter((c) => {
    const matchStatus =
      statusFilter === "全部" ||
      (statusFilter === "正常" && c.ok && !c.skipped) ||
      (statusFilter === "异常" && !c.ok && !c.skipped) ||
      (statusFilter === "跳过" && c.skipped)
    const matchSearch =
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.label ?? "").toLowerCase().includes(searchTerm.toLowerCase())
    return matchStatus && matchSearch
  })

  const statusFilters: StatusFilter[] = ["全部", "正常", "异常", "跳过"]

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-12 w-64 bg-neutral-800" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24 bg-neutral-800" />
          ))}
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

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">采集器管理</h1>
          <p className="text-sm text-neutral-400 mt-1">查看所有数据采集任务状态与鲜度信息</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
            <Input
              placeholder="搜索采集器..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-64 bg-neutral-800 border-neutral-700 text-white placeholder:text-neutral-500"
            />
          </div>
          <Button variant="outline" className="border-neutral-700 text-neutral-300 hover:bg-neutral-800" onClick={fetchData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
        </div>
      </div>

      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          <Card className="bg-neutral-900 border-neutral-800">
            <CardContent className="p-4 flex items-center gap-3">
              <Database className="w-5 h-5 text-neutral-400" />
              <div><p className="text-xs text-neutral-500">总计</p><p className="text-2xl font-bold text-white">{summary.total}</p></div>
            </CardContent>
          </Card>
          <Card className="bg-neutral-900 border-neutral-800">
            <CardContent className="p-4 flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <div><p className="text-xs text-neutral-500">正常</p><p className="text-2xl font-bold text-green-400">{summary.ok}</p></div>
            </CardContent>
          </Card>
          <Card className="bg-neutral-900 border-neutral-800">
            <CardContent className="p-4 flex items-center gap-3">
              <Clock className="w-5 h-5 text-yellow-400" />
              <div><p className="text-xs text-neutral-500">警告</p><p className="text-2xl font-bold text-yellow-400">{summary.warning}</p></div>
            </CardContent>
          </Card>
          <Card className="bg-neutral-900 border-neutral-800">
            <CardContent className="p-4 flex items-center gap-3">
              <XCircle className="w-5 h-5 text-red-400" />
              <div><p className="text-xs text-neutral-500">异常</p><p className="text-2xl font-bold text-red-400">{summary.failed}</p></div>
            </CardContent>
          </Card>
          <Card className="bg-neutral-900 border-neutral-800">
            <CardContent className="p-4 flex items-center gap-3">
              <SkipForward className="w-5 h-5 text-neutral-500" />
              <div><p className="text-xs text-neutral-500">跳过</p><p className="text-2xl font-bold text-neutral-400">{summary.skipped}</p></div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="flex items-center gap-2">
        {statusFilters.map((f) => (
          <button
            key={f}
            onClick={() => setStatusFilter(f)}
            className={`px-4 py-2 text-sm rounded-lg transition-colors ${
              statusFilter === f
                ? "bg-orange-500 text-white"
                : "bg-neutral-800 text-neutral-400 hover:text-white hover:bg-neutral-700"
            }`}
          >
            {f}
          </button>
        ))}
        <span className="ml-auto text-xs text-neutral-500">共 {filteredCollectors.length} 条</span>
      </div>

      <Card className="bg-neutral-900 border-neutral-800">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">采集器名称</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">调度方式</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">调度表达式</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">最近更新</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">鲜度阈值</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">仅交易日</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">状态</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredCollectors.length === 0 ? (
                  <tr><td colSpan={8} className="py-12 text-center text-neutral-500 text-sm">暂无数据</td></tr>
                ) : (
                  filteredCollectors.map((c, index) => (
                    <tr key={c.name} className={`border-b border-neutral-800/50 hover:bg-neutral-800/30 transition-colors ${index % 2 === 0 ? "bg-neutral-900" : "bg-neutral-900/50"}`}>
                      <td className="py-3 px-4">
                        <span className="text-sm text-white font-medium">{c.label || c.name}</span>
                        {c.label && c.label !== c.name && <p className="text-xs text-neutral-500 font-mono mt-0.5">{c.name}</p>}
                      </td>
                      <td className="py-3 px-4"><span className="text-sm text-neutral-400">{c.schedule_type || "—"}</span></td>
                      <td className="py-3 px-4">
                        {c.schedule_expr
                          ? <code className="text-xs bg-neutral-800 px-2 py-1 rounded text-neutral-300 font-mono">{c.schedule_expr}</code>
                          : <span className="text-neutral-600">—</span>}
                      </td>
                      <td className="py-3 px-4"><span className="text-sm text-neutral-300 font-mono">{c.age_str || "—"}</span></td>
                      <td className="py-3 px-4"><span className="text-sm text-neutral-400 font-mono">{c.threshold_h}h</span></td>
                      <td className="py-3 px-4">
                        {c.trading_only
                          ? <Badge variant="outline" className="text-xs border-blue-500/30 text-blue-400">是</Badge>
                          : <span className="text-xs text-neutral-600">否</span>}
                      </td>
                      <td className="py-3 px-4"><StatusBadge collector={c} /></td>
                      <td className="py-3 px-4">
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-neutral-400 hover:text-white hover:bg-neutral-700"
                          onClick={() => { setSelectedItem(c); setDetailOpen(true) }}>
                          <Eye className="w-4 h-4" />
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Sheet open={detailOpen} onOpenChange={setDetailOpen}>
        <SheetContent className="bg-neutral-900 border-neutral-800 w-[480px] sm:max-w-[480px]">
          {selectedItem && (
            <>
              <SheetHeader>
                <SheetTitle className="text-white">{selectedItem.label || selectedItem.name}</SheetTitle>
                <SheetDescription className="text-neutral-400 font-mono text-xs">{selectedItem.name}</SheetDescription>
              </SheetHeader>
              <div className="mt-6 space-y-5">
                <div className="grid grid-cols-2 gap-4">
                  <div><p className="text-xs text-neutral-500 mb-1">状态</p><StatusBadge collector={selectedItem} /></div>
                  <div><p className="text-xs text-neutral-500 mb-1">仅交易日</p><p className="text-sm text-white">{selectedItem.trading_only ? "是" : "否"}</p></div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div><p className="text-xs text-neutral-500 mb-1">调度类型</p><p className="text-sm text-white">{selectedItem.schedule_type || "—"}</p></div>
                  <div>
                    <p className="text-xs text-neutral-500 mb-1">调度表达式</p>
                    <code className="text-xs bg-neutral-800 px-2 py-1 rounded text-neutral-300 font-mono">{selectedItem.schedule_expr || "—"}</code>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div><p className="text-xs text-neutral-500 mb-1">最近更新</p><p className="text-sm text-white font-mono">{selectedItem.age_str || "—"}</p></div>
                  <div><p className="text-xs text-neutral-500 mb-1">鲜度阈值</p><p className="text-sm text-white font-mono">{selectedItem.threshold_h}h</p></div>
                </div>
                {selectedItem.data_source && (
                  <div><p className="text-xs text-neutral-500 mb-1">数据源</p><p className="text-sm text-white">{selectedItem.data_source}</p></div>
                )}
                {selectedItem.output_dir && (
                  <div>
                    <p className="text-xs text-neutral-500 mb-1">输出目录</p>
                    <p className="text-xs text-white font-mono bg-neutral-800 px-3 py-2 rounded break-all">{selectedItem.output_dir}</p>
                  </div>
                )}
                <div className="pt-2 border-t border-neutral-800">
                  <p className="text-xs text-neutral-600 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    此页面为只读展示，采集任务由后台服务自动调度执行
                  </p>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  )
}
