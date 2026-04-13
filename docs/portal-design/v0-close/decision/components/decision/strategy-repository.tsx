"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ChevronRight, FileText, Download, Upload, Trash2, Loader2 } from "lucide-react"
import { fetchStrategies, publishStrategy, type StrategyPackage } from "@/lib/api"

// 8 状态机：导入→预约→研究中→研究完成→回测确认→待执行→生产中→已下架
const LIFECYCLE_CN: Record<string, string> = {
  imported: "已导入",
  reserved: "已预约",
  in_research: "研究中",
  research_done: "研究完成",
  backtest_confirmed: "回测确认",
  pending_execution: "待执行",
  in_production: "生产中",
  retired: "已下架",
}

interface Strategy {
  id: string
  name: string
  category: string
  status: string
  version: string
  lastBacktest: string
  backtestStatus: string
  factors: string[]
  factorsAllSynced: boolean
  backTestAge: number
  description: string
}

function mapStrategy(pkg: StrategyPackage): Strategy {
  const dayAge = Math.floor((Date.now() - new Date(pkg.updated_at || pkg.created_at).getTime()) / 86_400_000)
  return {
    id: pkg.strategy_id,
    name: pkg.strategy_name,
    category: pkg.template_id ?? "—",
    status: LIFECYCLE_CN[pkg.lifecycle_status] ?? pkg.lifecycle_status,
    version: pkg.strategy_version,
    lastBacktest: (pkg.updated_at || pkg.created_at).slice(0, 10),
    backtestStatus: pkg.backtest_certificate_id ? "有效" : "进行中",
    factors: [],
    factorsAllSynced: pkg.factor_sync_status === "aligned",
    backTestAge: dayAge,
    description: pkg.research_snapshot_id ?? "",
  }
}

const getStatusBadgeColor = (status: string) => {
  switch (status) {
    case "生产中":
      return "bg-green-900 text-green-400"
    case "待执行":
      return "bg-blue-900 text-blue-400"
    case "回测确认":
      return "bg-cyan-900 text-cyan-400"
    case "研究完成":
      return "bg-purple-900 text-purple-400"
    case "研究中":
      return "bg-indigo-900 text-indigo-400"
    case "已预约":
      return "bg-yellow-900 text-yellow-400"
    case "已导入":
      return "bg-neutral-700 text-neutral-300"
    case "已下架":
      return "bg-red-900 text-red-400"
    default:
      return "bg-neutral-700 text-neutral-300"
  }
}

const getBacktestStatusColor = (status: string) => {
  switch (status) {
    case "有效":
      return "bg-green-900 text-green-400"
    case "过期":
      return "bg-red-900 text-red-400"
    case "进行中":
      return "bg-yellow-900 text-yellow-400"
    default:
      return "bg-neutral-700 text-neutral-300"
  }
}

// "执行"按钮只在"待执行"状态可用，映射到"进入发布流转"
const canEnterPublish = (strategy: Strategy) => {
  return strategy.status === "待执行"
}

export default function StrategyRepository({ refreshToken }: { refreshToken?: number }) {
  const [rawStrategies, setRawStrategies] = useState<StrategyPackage[]>([])
  const [loading, setLoading] = useState(true)
  const [publishing, setPublishing] = useState(false)
  const [publishResult, setPublishResult] = useState<{ ok: boolean; msg: string } | null>(null)
  const [selectedFolder, setSelectedFolder] = useState("全部策略")
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null)
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({})

  const reload = () => {
    setLoading(true)
    fetchStrategies()
      .then(data => {
        setRawStrategies(data)
        if (data.length > 0 && !selectedStrategy) setSelectedStrategy(mapStrategy(data[0]))
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [refreshToken])

  const strategies = rawStrategies.map(mapStrategy)

  /* 发布策略到模拟交易 */
  const handlePublish = async (strategy: Strategy) => {
    setPublishing(true)
    setPublishResult(null)
    try {
      const res = await publishStrategy(strategy.id, { target: "sim-trading" })
      setPublishResult({ ok: true, msg: res.message ?? "发布成功" })
      reload()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "发布失败"
      setPublishResult({ ok: false, msg })
    } finally {
      setPublishing(false)
    }
  }

  /* 导出策略 JSON */
  const handleExport = (strategy: Strategy) => {
    const pkg = rawStrategies.find(s => s.strategy_id === strategy.id)
    if (!pkg) return
    const blob = new Blob([JSON.stringify(pkg, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${pkg.strategy_id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  /* 导入策略 JSON — 调用 POST /strategies */
  const handleImport = () => {
    const input = document.createElement("input")
    input.type = "file"
    input.accept = ".json"
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return
      try {
        const text = await file.text()
        const body = JSON.parse(text)
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_DECISION_API_BASE ?? "/api/decision"}/strategies`,
          { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
        )
        if (!res.ok) throw new Error(`Import failed: ${res.status}`)
        setPublishResult({ ok: true, msg: "策略导入成功" })
        reload()
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "导入失败"
        setPublishResult({ ok: false, msg })
      }
    }
    input.click()
  }

  const kpiData = [
    { label: "策略包总数", value: String(strategies.length) },
    { label: "已导入数", value: String(strategies.filter(s => s.status === "已导入").length) },
    { label: "已预约数", value: String(strategies.filter(s => s.status === "已预约").length) },
    { label: "研究中", value: String(strategies.filter(s => s.status === "研究中").length) },
    { label: "研究完成", value: String(strategies.filter(s => s.status === "研究完成").length) },
    { label: "回测确认", value: String(strategies.filter(s => s.status === "回测确认").length) },
    { label: "待执行", value: String(strategies.filter(s => s.status === "待执行").length) },
    { label: "生产中", value: String(strategies.filter(s => s.status === "生产中").length) },
    { label: "已下架", value: String(strategies.filter(s => s.status === "已下架").length) },
  ]

  const strategyFolders = [
    { name: "全部策略", count: strategies.length },
    { name: "状态筛选", children: [
      { name: "生产活跃", count: strategies.filter(s => s.status === "生产中").length },
      { name: "研究中", count: strategies.filter(s => s.status === "研究中").length },
      { name: "已下架", count: strategies.filter(s => s.status === "已下架").length },
    ]},
  ]

  const toggleFolder = (name: string) => {
    setExpandedFolders({
      ...expandedFolders,
      [name]: !expandedFolders[name],
    })
  }

  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* KPI 卡片 — 8状态 + 总数 */}
      <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-9 gap-3">
        {kpiData.map((kpi, idx) => (
          <Card key={idx} className="bg-neutral-900 border-neutral-700">
            <CardContent className="p-2">
              <p className="text-xs text-neutral-400 mb-1 truncate">{kpi.label}</p>
              <p className="text-lg font-bold text-white">{kpi.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 文件夹树 + 列表 + 详情 */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 文件夹树 */}
        <Card className="bg-neutral-900 border-neutral-700 lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">策略分类</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            {strategyFolders.map((folder, idx) => (
              <div key={idx}>
                <button
                  onClick={() => {
                    if (folder.children) toggleFolder(folder.name)
                    setSelectedFolder(folder.name)
                  }}
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded text-sm transition-colors ${
                    selectedFolder === folder.name
                      ? "bg-orange-500 text-white"
                      : "text-neutral-300 hover:bg-neutral-800"
                  }`}
                >
                  {folder.children && (
                    <ChevronRight
                      className={`w-4 h-4 transition-transform ${
                        expandedFolders[folder.name] ? "rotate-90" : ""
                      }`}
                    />
                  )}
                  {!folder.children && <FileText className="w-4 h-4" />}
                  <span className="flex-1 text-left truncate">{folder.name}</span>
                  <span className="text-xs opacity-70">({folder.count})</span>
                </button>
                {folder.children && expandedFolders[folder.name] && (
                  <div className="ml-2 space-y-1">
                    {folder.children.map((child, childIdx) => (
                      <button
                        key={childIdx}
                        className="w-full flex items-center gap-2 px-3 py-1.5 rounded text-xs transition-colors text-neutral-400 hover:bg-neutral-800"
                      >
                        <span className="flex-1 text-left truncate">{child.name}</span>
                        <span className="opacity-70">({child.count})</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>

        {/* 策略列表 */}
        <Card className="bg-neutral-900 border-neutral-700 lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">策略包列表</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-96 overflow-y-auto">
            {strategies.map((strategy) => (
              <button
                key={strategy.id}
                onClick={() => setSelectedStrategy(strategy)}
                className={`w-full text-left p-3 rounded border transition-colors ${
                  selectedStrategy?.id === strategy.id
                    ? "bg-orange-500/10 border-orange-500"
                    : "border-neutral-700 hover:bg-neutral-800/50"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{strategy.name}</p>
                    <p className="text-xs text-neutral-400 mt-1">{strategy.description}</p>
                  </div>
                  <Badge className={getStatusBadgeColor(strategy.status)} style={{ height: "20px" }}>
                    {strategy.status}
                  </Badge>
                </div>
              </button>
            ))}
          </CardContent>
        </Card>

        {/* 详情面板 */}
        <Card className="bg-neutral-900 border-neutral-700 lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">策略详情</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {selectedStrategy ? (
              <>
                <div className="space-y-1 border-b border-neutral-700 pb-3">
                  <p className="text-xs text-neutral-400">策略名称</p>
                  <p className="text-sm font-medium text-white">{selectedStrategy.name}</p>
                </div>

                <div className="space-y-1 border-b border-neutral-700 pb-3">
                  <p className="text-xs text-neutral-400">状态</p>
                  <Badge className={getStatusBadgeColor(selectedStrategy.status)}>
                    {selectedStrategy.status}
                  </Badge>
                </div>

                <div className="space-y-1 border-b border-neutral-700 pb-3">
                  <p className="text-xs text-neutral-400">版本</p>
                  <p className="text-sm text-neutral-200">{selectedStrategy.version}</p>
                </div>

                <div className="space-y-1 border-b border-neutral-700 pb-3">
                  <p className="text-xs text-neutral-400">回测状态</p>
                  <Badge className={getBacktestStatusColor(selectedStrategy.backtestStatus)}>
                    {selectedStrategy.backtestStatus}
                  </Badge>
                  <p className="text-xs text-neutral-500 mt-1">
                    {selectedStrategy.lastBacktest}（{selectedStrategy.backTestAge}天前）
                  </p>
                </div>

                <div className="space-y-1 border-b border-neutral-700 pb-3">
                  <p className="text-xs text-neutral-400">因子对齐状态</p>
                  <div className="space-y-1">
                    {selectedStrategy.factors.map((factor, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-xs">
                        {selectedStrategy.factorsAllSynced ? (
                          <span className="text-green-400">✓</span>
                        ) : (
                          <span className="text-red-400">✕</span>
                        )}
                        <span className="text-neutral-300">{factor}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* "进入发布流转"按钮：仅"待执行"状态可用 */}
                <div className="space-y-2 pt-2">
                  <Button
                    className="w-full bg-orange-600 hover:bg-orange-700 text-white text-xs h-8"
                    disabled={!canEnterPublish(selectedStrategy) || publishing}
                    onClick={() => handlePublish(selectedStrategy)}
                  >
                    {publishing ? (
                      <><Loader2 className="w-3 h-3 mr-1 animate-spin" />发布中…</>
                    ) : (
                      "进入发布流转 → 模拟交易"
                    )}
                  </Button>
                  {publishResult && (
                    <p className={`text-xs text-center ${publishResult.ok ? "text-green-400" : "text-red-400"}`}>
                      {publishResult.msg}
                    </p>
                  )}
                  {!canEnterPublish(selectedStrategy) && !publishResult && (
                    <p className="text-xs text-neutral-500 text-center">
                      {selectedStrategy.status === "待执行"
                        ? ""
                        : `当前状态「${selectedStrategy.status}」不可发布`}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-2 pt-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 h-7 text-xs"
                    onClick={handleImport}
                    title="导入策略 JSON"
                  >
                    <Upload className="w-3 h-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 h-7 text-xs"
                    onClick={() => handleExport(selectedStrategy)}
                    title="导出策略 JSON"
                  >
                    <Download className="w-3 h-3" />
                  </Button>
                  <Button size="sm" variant="outline" className="border-red-700 text-red-400 hover:bg-red-500/10 h-7 text-xs" disabled title="下架（未来）">
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </>
            ) : (
              <p className="text-center text-neutral-500 py-8">选择策略查看详情</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 生命周期时间线（严格8状态） */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300">策略生命周期 — 8状态流转</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {["已导入", "已预约", "研究中", "研究完成", "回测确认", "待执行", "生产中", "已下架"].map((stage, idx) => (
              <div key={idx} className="flex items-center gap-2 flex-shrink-0">
                <div className="w-8 h-8 rounded-full bg-orange-500/20 border border-orange-500 flex items-center justify-center text-xs text-orange-400 font-medium">
                  {idx + 1}
                </div>
                <span className="text-xs text-neutral-400 whitespace-nowrap">{stage}</span>
                {idx < 7 && <span className="text-orange-500 text-lg">→</span>}
              </div>
            ))}
          </div>
          <p className="text-xs text-neutral-500 mt-4">
            策略必须完成研究和回测确认才能进入待执行状态。只有「待执行」状态可触发「进入发布流转」，发布目标为模拟交易；实盘入口可见但已锁定。
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
