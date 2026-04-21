"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Folder,
  FolderOpen,
  FileText,
  ChevronRight,
  ChevronDown,
  Search,
  Database,
  RefreshCw,
  AlertCircle,
  HardDrive,
  FileStack,
  Globe2,
  TrendingUp,
  BarChart3,
  Ship,
  Landmark,
} from "lucide-react"
import { dataApi, StorageTotals, DirectoryEntry, TreeNode, MacroRecord, VolatilityRecord, ForexRecord, ShippingRecord, CftcRecord } from "@/lib/api/data"

// ── 通用表格组件 ─────────────────────────────────────────────
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function DataTable<T extends Record<string, any>>({
  records,
  columns,
  isLoading,
}: {
  records: T[]
  columns: { key: string; label: string; render?: (v: unknown, row: T) => React.ReactNode }[]
  isLoading: boolean
}) {
  if (isLoading) return <div className="p-6 space-y-2">{[1,2,3,4,5].map(i => <Skeleton key={i} className="h-8" />)}</div>
  if (records.length === 0) return (
    <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
      <Database className="w-10 h-10 mb-3 opacity-30" />
      <p className="text-sm">暂无数据</p>
    </div>
  )
  return (
    <div className="overflow-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-border bg-muted/30 sticky top-0">
            {columns.map(col => (
              <th key={col.key} className="px-3 py-2 text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider whitespace-nowrap">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border/50">
          {records.map((row, idx) => (
            <tr key={idx} className="hover:bg-muted/20 transition-colors">
              {columns.map(col => (
                <td key={col.key} className="px-3 py-1.5 text-foreground whitespace-nowrap font-mono text-[11px]">
                  {col.render ? col.render(row[col.key], row) : String(row[col.key] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function fmtNum(v: unknown): string {
  if (v == null) return "—"
  const n = Number(v)
  if (isNaN(n)) return String(v)
  return n.toLocaleString(undefined, { maximumFractionDigits: 4 })
}

function fmtDate(v: unknown): string {
  if (!v) return "—"
  const s = String(v)
  return s.length > 10 ? s.slice(0, 10) : s
}

export default function DataExplorer() {
  const [activeTab, setActiveTab] = useState("storage")
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set())
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [fileTypeFilter, setFileTypeFilter] = useState("all")
  const [sortBy, setSortBy] = useState<"name" | "size">("name")
  const [isLoading, setIsLoading] = useState(true)
  const [fetchError, setFetchError] = useState(false)
  const [totals, setTotals] = useState<StorageTotals | null>(null)
  const [directories, setDirectories] = useState<DirectoryEntry[]>([])
  const [tree, setTree] = useState<TreeNode[]>([])

  // Context data
  const [macroRecords, setMacroRecords] = useState<MacroRecord[]>([])
  const [volRecords, setVolRecords] = useState<VolatilityRecord[]>([])
  const [forexRecords, setForexRecords] = useState<ForexRecord[]>([])
  const [shippingRecords, setShippingRecords] = useState<ShippingRecord[]>([])
  const [cftcRecords, setCftcRecords] = useState<CftcRecord[]>([])
  const [contextLoading, setContextLoading] = useState(false)

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setFetchError(false)
    try {
      const data = await dataApi.getStorage(2, 20)
      setTotals(data.totals)
      setDirectories(data.directories ?? [])
      setTree(data.tree ?? [])
    } catch {
      setFetchError(true)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const fetchContextData = useCallback(async () => {
    setContextLoading(true)
    try {
      const [macro, vol, forex, shipping, cftc] = await Promise.all([
        dataApi.getMacroContext().catch(() => ({ records: [] as MacroRecord[], count: 0, data_type: "" })),
        dataApi.getVolatilityContext().catch(() => ({ records: [] as VolatilityRecord[], count: 0, data_type: "" })),
        dataApi.getForexContext().catch(() => ({ records: [] as ForexRecord[], count: 0, data_type: "" })),
        dataApi.getShippingContext().catch(() => ({ records: [] as ShippingRecord[], count: 0, data_type: "" })),
        dataApi.getCftcContext().catch(() => ({ records: [] as CftcRecord[], count: 0, data_type: "" })),
      ])
      setMacroRecords(macro.records)
      setVolRecords(vol.records)
      setForexRecords(forex.records)
      setShippingRecords(shipping.records)
      setCftcRecords(cftc.records)
    } finally {
      setContextLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    fetchContextData()
  }, [fetchData, fetchContextData])

  const toggleFolder = (path: string) => {
    const next = new Set(expandedPaths)
    if (next.has(path)) next.delete(path)
    else next.add(path)
    setExpandedPaths(next)
  }

  const getFileExtension = (name: string) => {
    const parts = name.split(".")
    return parts.length > 1 ? parts[parts.length - 1] : ""
  }

  const matchesFilter = (node: TreeNode): boolean => {
    if (node.type === "folder") return true
    if (fileTypeFilter === "all") return true
    const ext = getFileExtension(node.name)
    if (fileTypeFilter === "csv" && ext === "csv") return true
    if (fileTypeFilter === "parquet" && ext === "parquet") return true
    if (fileTypeFilter === "json" && ext === "json") return true
    if (fileTypeFilter === "other" && !["csv", "parquet", "json"].includes(ext)) return true
    return false
  }

  const renderNode = (node: TreeNode, depth = 0): React.ReactElement | null => {
    const isExpanded = expandedPaths.has(node.path)
    const isSelected = selectedNode?.path === node.path
    const searchLower = searchTerm.toLowerCase()
    const matchesSearch = !searchTerm || node.name.toLowerCase().includes(searchLower) || node.path.toLowerCase().includes(searchLower)

    if (!matchesSearch || !matchesFilter(node)) {
      return null
    }
    return (
      <div key={node.path}>
        <div
          className={`flex items-center gap-2 py-1.5 px-2 rounded cursor-pointer transition-colors ${
            isSelected ? "bg-orange-500/20 text-orange-400" : "text-foreground hover:bg-muted"
          }`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => {
            if (node.type === "folder") toggleFolder(node.path)
            setSelectedNode(node)
          }}
        >
          {node.type === "folder" ? (
            <>
              {node.children && node.children.length > 0 ? (
                isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                )
              ) : (
                <span className="w-4 flex-shrink-0" />
              )}
              {isExpanded ? <FolderOpen className="w-4 h-4 text-orange-400 flex-shrink-0" /> : <Folder className="w-4 h-4 text-muted-foreground flex-shrink-0" />}
            </>
          ) : (
            <>
              <span className="w-4 flex-shrink-0" />
              <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
            </>
          )}
          <span className="text-sm truncate flex-1">{node.name}</span>
          {node.size_human && <span className="text-xs text-muted-foreground ml-auto flex-shrink-0">{node.size_human}</span>}
        </div>
        {node.type === "folder" && isExpanded && node.children && node.children.length > 0 && <div>{node.children.map((child) => renderNode(child, depth + 1))}</div>}
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-12 w-64" />
        <div className="flex gap-4 h-[600px]">
          <Skeleton className="w-72" />
          <Skeleton className="flex-1" />
        </div>
      </div>
    )
  }

  if (fetchError) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-24 text-muted-foreground">
        <AlertCircle className="w-10 h-10 mb-3 text-red-500/60" />
        <p className="text-sm mb-4">数据加载失败，请稍后重试</p>
        <Button variant="outline" size="sm" onClick={fetchData}>
          重新加载
        </Button>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col">
      {/* ── 顶部 Tab 栏 ──────────────────────────────────────── */}
      <div className="px-5 py-2 border-b border-border bg-card/50 flex items-center justify-between gap-4">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
          <TabsList className="h-8 bg-muted/50">
            <TabsTrigger value="storage" className="h-6 text-xs gap-1">
              <HardDrive className="w-3 h-3" />存储目录
            </TabsTrigger>
            <TabsTrigger value="macro" className="h-6 text-xs gap-1">
              <Globe2 className="w-3 h-3" />宏观指标 ({macroRecords.length})
            </TabsTrigger>
            <TabsTrigger value="volatility" className="h-6 text-xs gap-1">
              <TrendingUp className="w-3 h-3" />波动率 ({volRecords.length})
            </TabsTrigger>
            <TabsTrigger value="forex" className="h-6 text-xs gap-1">
              <BarChart3 className="w-3 h-3" />外汇 ({forexRecords.length})
            </TabsTrigger>
            <TabsTrigger value="shipping" className="h-6 text-xs gap-1">
              <Ship className="w-3 h-3" />航运 ({shippingRecords.length})
            </TabsTrigger>
            <TabsTrigger value="cftc" className="h-6 text-xs gap-1">
              <Landmark className="w-3 h-3" />CFTC ({cftcRecords.length})
            </TabsTrigger>
          </TabsList>
        </Tabs>
        <Button variant="outline" size="sm" className="h-7 text-xs gap-1 flex-shrink-0" onClick={() => { fetchData(); fetchContextData() }}>
          <RefreshCw className="w-3 h-3" />刷新
        </Button>
      </div>

      {/* ── 存储目录 ─────────────────────────────────────────── */}
      {activeTab === "storage" && (
        <>
          {isLoading ? (
            <div className="p-6 space-y-4">
              <div className="flex gap-4 h-[600px]"><Skeleton className="w-72" /><Skeleton className="flex-1" /></div>
            </div>
          ) : fetchError ? (
            <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
              <AlertCircle className="w-10 h-10 mb-3 text-red-500/60" />
              <p className="text-sm mb-3">加载失败</p>
              <Button variant="outline" size="sm" onClick={fetchData}>重新加载</Button>
            </div>
          ) : (
            <>
              {totals && (
                <div className="flex items-center gap-5 px-5 py-2 border-b border-border bg-card/30 text-xs">
                  <span className="flex items-center gap-1.5 text-muted-foreground">
                    <HardDrive className="w-3.5 h-3.5 text-orange-400" />用量
                    <strong className="text-foreground ml-0.5">{totals.size_human}</strong>
                  </span>
                  <span className="flex items-center gap-1.5 text-muted-foreground">
                    <FileStack className="w-3.5 h-3.5 text-blue-400" />文件
                    <strong className="text-foreground ml-0.5">{totals.files.toLocaleString()}</strong>
                  </span>
                  <span className="flex items-center gap-1.5 text-muted-foreground">
                    <Folder className="w-3.5 h-3.5" />目录
                    <strong className="text-foreground ml-0.5">{totals.directories}</strong>
                  </span>
                  {totals.last_modified && (
                    <span className="text-muted-foreground ml-auto">最近更新: {totals.last_modified}</span>
                  )}
                </div>
              )}
              <div className="flex-1 flex overflow-hidden">
                {/* 左侧树 */}
                <div className="w-72 border-r border-border flex flex-col bg-card/50 flex-shrink-0">
                  <div className="p-3 border-b border-border space-y-2">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input placeholder="搜索文件/路径..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-9 h-8 text-sm" />
                    </div>
                    <div className="flex items-center gap-2">
                      <select value={fileTypeFilter} onChange={(e) => setFileTypeFilter(e.target.value)} className="flex-1 h-8 px-2 text-xs bg-background border border-input text-foreground rounded-md">
                        <option value="all">全部类型</option>
                        <option value="csv">CSV</option>
                        <option value="parquet">Parquet</option>
                        <option value="json">JSON</option>
                        <option value="other">其他</option>
                      </select>
                      <select value={sortBy} onChange={(e) => setSortBy(e.target.value as "name" | "size")} className="flex-1 h-8 px-2 text-xs bg-background border border-input text-foreground rounded-md">
                        <option value="name">按名称</option>
                        <option value="size">按大小</option>
                      </select>
                    </div>
                  </div>
                  <ScrollArea className="flex-1 p-2">
                    <div className="text-xs text-muted-foreground uppercase tracking-wider px-2 py-1.5 mb-1">数据存储目录</div>
                    {tree.length === 0 ? <p className="text-xs text-muted-foreground px-2 py-4">目录为空或配置未就绪</p> : tree.map((node) => renderNode(node))}
                  </ScrollArea>
                </div>

                {/* 中间详情 */}
                <div className="flex-1 flex flex-col min-w-0">
                  {selectedNode ? (
                    <>
                      <div className="p-4 border-b border-border bg-card/30">
                        <div className="flex items-start gap-3">
                          {selectedNode.type === "folder" ? <FolderOpen className="w-6 h-6 text-orange-400 flex-shrink-0 mt-0.5" /> : <FileText className="w-6 h-6 text-muted-foreground flex-shrink-0 mt-0.5" />}
                          <div className="flex-1 min-w-0">
                            <h2 className="text-base font-semibold text-foreground truncate">{selectedNode.name}</h2>
                            <p className="text-xs text-muted-foreground font-mono mt-0.5 truncate">{selectedNode.path}</p>
                          </div>
                          {selectedNode.suffix && <Badge variant="outline" className="text-xs flex-shrink-0">{selectedNode.suffix}</Badge>}
                        </div>
                        <div className="grid grid-cols-4 gap-3 mt-3">
                          {[
                            { label: "大小", value: selectedNode.size_human || "—" },
                            { label: "文件数", value: selectedNode.file_count },
                            { label: "子目录", value: selectedNode.dir_count },
                            { label: "最近更新", value: selectedNode.last_modified || "—" },
                          ].map(kpi => (
                            <div key={kpi.label} className="bg-muted/50 rounded-lg p-2.5">
                              <p className="text-[10px] text-muted-foreground mb-1">{kpi.label}</p>
                              <p className="text-sm font-bold text-foreground font-mono">{String(kpi.value)}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="flex-1 flex items-center justify-center">
                        <div className="text-center max-w-xs">
                          <Database className="w-10 h-10 text-neutral-700 mx-auto mb-3" />
                          <p className="text-sm text-muted-foreground">暂无行情预览 — 仅展示目录结构</p>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="flex-1 flex items-center justify-center">
                      <div className="text-center">
                        <Database className="w-14 h-14 text-neutral-700 mx-auto mb-3" />
                        <p className="text-base font-medium text-muted-foreground mb-1">选择文件或目录</p>
                        <p className="text-xs text-muted-foreground">从左侧目录树选择节点查看存储信息</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* 右侧统计 */}
                <div className="w-56 border-l border-border bg-card/50 flex flex-col flex-shrink-0">
                  <div className="p-3 border-b border-border">
                    <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">顶层目录</p>
                  </div>
                  <ScrollArea className="flex-1 p-2.5">
                    {directories.length === 0 ? (
                      <p className="text-xs text-muted-foreground py-4 text-center">暂无数据</p>
                    ) : (
                      <div className="space-y-2">
                        {directories.map((dir) => (
                          <div key={dir.path} className="p-2.5 bg-muted/50 rounded-lg hover:bg-muted transition-colors">
                            <div className="flex items-center gap-1.5 mb-1.5">
                              <Folder className="w-3 h-3 text-neutral-400 flex-shrink-0" />
                              <span className="text-xs font-medium text-foreground truncate">{dir.name}</span>
                            </div>
                            <div className="space-y-0.5 text-[10px]">
                              <div className="flex justify-between"><span className="text-muted-foreground">大小</span><span className="font-mono">{dir.size_human}</span></div>
                              <div className="flex justify-between"><span className="text-muted-foreground">文件</span><span className="font-mono">{dir.file_count}</span></div>
                              {dir.last_modified && <div className="flex justify-between"><span className="text-muted-foreground">更新</span><span className="font-mono text-muted-foreground">{dir.last_modified.split(" ")[0]}</span></div>}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </ScrollArea>
                </div>
              </div>
            </>
          )}
        </>
      )}

      {/* ── 宏观指标 ─────────────────────────────────────────── */}
      {activeTab === "macro" && (
        <ScrollArea className="flex-1">
          <div className="p-4">
            <p className="text-xs text-muted-foreground mb-3">全球宏观经济指标 · {macroRecords.length} 条</p>
            <DataTable
              records={macroRecords}
              isLoading={contextLoading}
              columns={[
                { key: "indicator", label: "指标" },
                { key: "country", label: "国家/地区" },
                { key: "timestamp", label: "日期", render: fmtDate },
                { key: "value", label: "实际值", render: fmtNum },
                { key: "forecast", label: "预期", render: fmtNum },
                { key: "previous", label: "前值", render: fmtNum },
                { key: "mode", label: "模式", render: v => <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${v === "mock" ? "border-yellow-500/40 text-yellow-500" : "border-green-500/40 text-green-500"}`}>{String(v)}</Badge> },
              ]}
            />
          </div>
        </ScrollArea>
      )}

      {/* ── 波动率 ───────────────────────────────────────────── */}
      {activeTab === "volatility" && (
        <ScrollArea className="flex-1">
          <div className="p-4">
            <p className="text-xs text-muted-foreground mb-3">市场波动率指标（VIX / QVIX 等）· {volRecords.length} 条</p>
            <DataTable
              records={volRecords}
              isLoading={contextLoading}
              columns={[
                { key: "indicator", label: "指标" },
                { key: "timestamp", label: "日期", render: fmtDate },
                { key: "close", label: "收盘", render: fmtNum },
                { key: "open", label: "开盘", render: fmtNum },
                { key: "high", label: "最高", render: fmtNum },
                { key: "low", label: "最低", render: fmtNum },
                { key: "volume", label: "成交量", render: fmtNum },
                { key: "mode", label: "模式", render: v => <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${v === "mock" ? "border-yellow-500/40 text-yellow-500" : "border-green-500/40 text-green-500"}`}>{String(v)}</Badge> },
              ]}
            />
          </div>
        </ScrollArea>
      )}

      {/* ── 外汇 ─────────────────────────────────────────────── */}
      {activeTab === "forex" && (
        <ScrollArea className="flex-1">
          <div className="p-4">
            <p className="text-xs text-muted-foreground mb-3">外汇汇率数据 · {forexRecords.length} 条</p>
            <DataTable
              records={forexRecords}
              isLoading={contextLoading}
              columns={[
                { key: "indicator", label: "指标" },
                { key: "pair", label: "货币对" },
                { key: "timestamp", label: "日期", render: fmtDate },
                { key: "bid_close", label: "买入收盘价", render: fmtNum },
                { key: "mode", label: "模式", render: v => <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${v === "mock" ? "border-yellow-500/40 text-yellow-500" : "border-green-500/40 text-green-500"}`}>{String(v)}</Badge> },
              ]}
            />
          </div>
        </ScrollArea>
      )}

      {/* ── 航运指数 ─────────────────────────────────────────── */}
      {activeTab === "shipping" && (
        <ScrollArea className="flex-1">
          <div className="p-4">
            <p className="text-xs text-muted-foreground mb-3">全球航运指数（波罗的海干散货等）· {shippingRecords.length} 条</p>
            <DataTable
              records={shippingRecords}
              isLoading={contextLoading}
              columns={[
                { key: "indicator", label: "指标" },
                { key: "timestamp", label: "日期", render: fmtDate },
                { key: "value", label: "指数值", render: fmtNum },
                { key: "change_pct", label: "变化%", render: (v) => {
                  const n = Number(v)
                  if (isNaN(n)) return "—"
                  return <span className={n >= 0 ? "text-green-400" : "text-red-400"}>{n >= 0 ? "+" : ""}{n.toFixed(2)}%</span>
                }},
                { key: "mode", label: "模式", render: v => <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${v === "mock" ? "border-yellow-500/40 text-yellow-500" : "border-green-500/40 text-green-500"}`}>{String(v)}</Badge> },
              ]}
            />
          </div>
        </ScrollArea>
      )}

      {/* ── CFTC 持仓报告 ────────────────────────────────────── */}
      {activeTab === "cftc" && (
        <ScrollArea className="flex-1">
          <div className="p-4">
            <p className="text-xs text-muted-foreground mb-3">CFTC COT 持仓报告 · {cftcRecords.length} 条</p>
            <DataTable
              records={cftcRecords}
              isLoading={contextLoading}
              columns={[
                { key: "indicator", label: "品种" },
                { key: "timestamp", label: "报告日", render: fmtDate },
                { key: "report_type", label: "报告类型" },
                { key: "net", label: "净多头持仓", render: (v) => {
                  const n = Number(v)
                  if (isNaN(n)) return "—"
                  return <span className={n >= 0 ? "text-green-400" : "text-red-400"}>{n >= 0 ? "+" : ""}{n.toLocaleString()}</span>
                }},
                { key: "mode", label: "模式", render: v => <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${v === "mock" ? "border-yellow-500/40 text-yellow-500" : "border-green-500/40 text-green-500"}`}>{String(v)}</Badge> },
              ]}
            />
          </div>
        </ScrollArea>
      )}
    </div>
  )
}
