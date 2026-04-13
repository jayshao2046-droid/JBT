"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Folder,
  FolderOpen,
  FileText,
  ChevronRight,
  ChevronDown,
  Search,
  Download,
  BarChart3,
  Table2,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  RefreshCw,
  Columns3,
  GitCompare,
  Calendar,
} from "lucide-react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
} from "recharts"

interface FileNode {
  id: string
  name: string
  type: "folder" | "file"
  children?: FileNode[]
  size?: string
  records?: number
  lastUpdate?: string
  columns?: string[]
  exchange?: string
  symbol?: string
  frequency?: string
}

// 模拟目录树结构
const fileTree: FileNode[] = [
  {
    id: "futures_minute",
    name: "futures_minute",
    type: "folder",
    children: [
      {
        id: "rb",
        name: "RB",
        type: "folder",
        children: [
          {
            id: "rb2510",
            name: "RB2510.parquet",
            type: "file",
            size: "128MB",
            records: 245680,
            lastUpdate: "2025-04-09 10:42",
            exchange: "SHFE",
            symbol: "RB2510",
            frequency: "1min",
            columns: ["datetime", "open", "high", "low", "close", "volume", "amount", "oi"],
          },
          {
            id: "rb2509",
            name: "RB2509.parquet",
            type: "file",
            size: "156MB",
            records: 312450,
            lastUpdate: "2025-04-09 10:42",
            exchange: "SHFE",
            symbol: "RB2509",
            frequency: "1min",
          },
        ],
      },
      {
        id: "cu",
        name: "CU",
        type: "folder",
        children: [
          {
            id: "cu2509",
            name: "CU2509.parquet",
            type: "file",
            size: "142MB",
            records: 286320,
            lastUpdate: "2025-04-09 10:42",
            exchange: "SHFE",
            symbol: "CU2509",
            frequency: "1min",
          },
        ],
      },
    ],
  },
  {
    id: "stock_minute",
    name: "stock_minute",
    type: "folder",
    children: [
      { id: "sh000001", name: "000001.SH.parquet", type: "file", size: "89MB", records: 178560 },
      { id: "sh000300", name: "000300.SH.parquet", type: "file", size: "92MB", records: 184230 },
    ],
  },
  {
    id: "overseas_kline",
    name: "overseas_kline",
    type: "folder",
    children: [
      { id: "gc", name: "GC=F.parquet", type: "file", size: "45MB", records: 89640, lastUpdate: "2025-04-09 06:00" },
      { id: "cl", name: "CL=F.parquet", type: "file", size: "48MB", records: 95280, lastUpdate: "2025-04-09 06:00" },
      { id: "hg", name: "HG=F.parquet", type: "file", size: "42MB", records: 84320, lastUpdate: "2025-04-09 06:00" },
    ],
  },
  {
    id: "parquet",
    name: "parquet",
    type: "folder",
    children: [
      { id: "continuous", name: "continuous", type: "folder", children: [] },
      { id: "main_contract", name: "main_contract", type: "folder", children: [] },
    ],
  },
  {
    id: "news_api",
    name: "news_api",
    type: "folder",
    children: [
      { id: "cls", name: "cls_20250409.json", type: "file", size: "2.3MB", records: 1842 },
      { id: "eastmoney", name: "eastmoney_20250409.json", type: "file", size: "1.8MB", records: 1256 },
    ],
  },
  {
    id: "news_collected",
    name: "news_collected",
    type: "folder",
    children: [],
  },
  {
    id: "sentiment",
    name: "sentiment",
    type: "folder",
    children: [
      { id: "fear_greed", name: "fear_greed.parquet", type: "file", size: "12MB", records: 24560 },
      { id: "social_heat", name: "social_heat.parquet", type: "file", size: "8MB", records: 16780 },
    ],
  },
  {
    id: "shipping",
    name: "shipping",
    type: "folder",
    children: [
      { id: "bdi", name: "bdi_index.parquet", type: "file", size: "5MB", records: 10240 },
    ],
  },
  {
    id: "position",
    name: "position",
    type: "folder",
    children: [],
  },
  {
    id: "tushare",
    name: "tushare",
    type: "folder",
    children: [],
  },
  {
    id: "macro_global",
    name: "macro_global",
    type: "folder",
    children: [
      { id: "gdp", name: "gdp.parquet", type: "file", size: "3MB", records: 5680 },
      { id: "cpi", name: "cpi.parquet", type: "file", size: "4MB", records: 7820 },
      { id: "pmi", name: "pmi.parquet", type: "file", size: "2MB", records: 4560 },
    ],
  },
  {
    id: "volatility_index",
    name: "volatility_index",
    type: "folder",
    children: [
      { id: "vix", name: "VIX.parquet", type: "file", size: "18MB", records: 36450 },
      { id: "ivx", name: "iVX.parquet", type: "file", size: "15MB", records: 30120 },
    ],
  },
  {
    id: "logs",
    name: "logs",
    type: "folder",
    children: [],
  },
]

// 模拟 K 线数据
const klineData = [
  { time: "09:00", open: 3852, high: 3865, low: 3848, close: 3860, volume: 12500 },
  { time: "09:15", open: 3860, high: 3872, low: 3858, close: 3868, volume: 15200 },
  { time: "09:30", open: 3868, high: 3875, low: 3862, close: 3870, volume: 18400 },
  { time: "09:45", open: 3870, high: 3878, low: 3865, close: 3875, volume: 14800 },
  { time: "10:00", open: 3875, high: 3882, low: 3870, close: 3878, volume: 16500 },
  { time: "10:15", open: 3878, high: 3885, low: 3875, close: 3880, volume: 13200 },
  { time: "10:30", open: 3880, high: 3888, low: 3878, close: 3885, volume: 17800 },
  { time: "10:45", open: 3885, high: 3890, low: 3882, close: 3888, volume: 15600 },
  { time: "11:00", open: 3888, high: 3895, low: 3885, close: 3892, volume: 19200 },
  { time: "11:15", open: 3892, high: 3898, low: 3890, close: 3895, volume: 14500 },
]

// 模拟表格数据
const tableData = [
  { datetime: "2025-04-09 09:00:00", open: 3852, high: 3865, low: 3848, close: 3860, volume: 12500, amount: 48125000, oi: 285640 },
  { datetime: "2025-04-09 09:01:00", open: 3860, high: 3862, low: 3858, close: 3861, volume: 8520, amount: 32892720, oi: 285680 },
  { datetime: "2025-04-09 09:02:00", open: 3861, high: 3865, low: 3860, close: 3864, volume: 9840, amount: 38022240, oi: 285720 },
  { datetime: "2025-04-09 09:03:00", open: 3864, high: 3868, low: 3862, close: 3866, volume: 7650, amount: 29583900, oi: 285750 },
  { datetime: "2025-04-09 09:04:00", open: 3866, high: 3870, low: 3865, close: 3868, volume: 8920, amount: 34502560, oi: 285780 },
]

// 数据质量检查结果
interface QualityCheck {
  item: string
  status: "pass" | "warning" | "error"
  value: string | number
  threshold?: string
}

const qualityChecks: QualityCheck[] = [
  { item: "缺失分钟数", status: "pass", value: 0, threshold: "< 5" },
  { item: "重复行数", status: "pass", value: 0, threshold: "= 0" },
  { item: "时间连续性", status: "pass", value: "连续", threshold: "连续" },
  { item: "字段完整性", status: "pass", value: "100%", threshold: ">= 99%" },
  { item: "数据延迟", status: "warning", value: "3min", threshold: "< 2min" },
  { item: "价格异常", status: "pass", value: "0 条", threshold: "= 0" },
]

export default function DataExplorerPage() {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(["futures_minute", "rb"]))
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart")
  const [timeRange, setTimeRange] = useState("1d")
  const [compareMode, setCompareMode] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const toggleFolder = (folderId: string) => {
    const newExpanded = new Set(expandedFolders)
    if (newExpanded.has(folderId)) {
      newExpanded.delete(folderId)
    } else {
      newExpanded.add(folderId)
    }
    setExpandedFolders(newExpanded)
  }

  const selectFile = (file: FileNode) => {
    if (file.type === "file") {
      setIsLoading(true)
      setTimeout(() => {
        setSelectedFile(file)
        setIsLoading(false)
      }, 300)
    }
  }

  const renderTreeNode = (node: FileNode, depth: number = 0) => {
    const isExpanded = expandedFolders.has(node.id)
    const isSelected = selectedFile?.id === node.id
    const matchesSearch = node.name.toLowerCase().includes(searchTerm.toLowerCase())

    if (searchTerm && !matchesSearch && node.type === "file") {
      return null
    }

    return (
      <div key={node.id}>
        <div
          className={`flex items-center gap-2 py-1.5 px-2 rounded cursor-pointer transition-colors ${
            isSelected
              ? "bg-orange-500/20 text-orange-400"
              : "text-neutral-300 hover:bg-neutral-800"
          }`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => (node.type === "folder" ? toggleFolder(node.id) : selectFile(node))}
        >
          {node.type === "folder" ? (
            <>
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-neutral-500" />
              ) : (
                <ChevronRight className="w-4 h-4 text-neutral-500" />
              )}
              {isExpanded ? (
                <FolderOpen className="w-4 h-4 text-orange-400" />
              ) : (
                <Folder className="w-4 h-4 text-neutral-400" />
              )}
            </>
          ) : (
            <>
              <span className="w-4" />
              <FileText className="w-4 h-4 text-neutral-500" />
            </>
          )}
          <span className="text-sm truncate">{node.name}</span>
          {node.type === "file" && node.size && (
            <span className="text-xs text-neutral-500 ml-auto">{node.size}</span>
          )}
        </div>
        {node.type === "folder" && isExpanded && node.children && (
          <div>
            {node.children.map((child) => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  const getQualityStatusIcon = (status: QualityCheck["status"]) => {
    switch (status) {
      case "pass":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case "error":
        return <AlertTriangle className="w-4 h-4 text-red-500" />
    }
  }

  const getQualityStatusColor = (status: QualityCheck["status"]) => {
    switch (status) {
      case "pass":
        return "text-green-400"
      case "warning":
        return "text-yellow-400"
      case "error":
        return "text-red-400"
    }
  }

  return (
    <div className="h-[calc(100vh-3.5rem)] flex">
      {/* 左侧目录树 */}
      <div className="w-72 border-r border-neutral-800 flex flex-col bg-neutral-900/50">
        <div className="p-4 border-b border-neutral-800">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
            <Input
              placeholder="搜索文件..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-neutral-800 border-neutral-700 text-white placeholder:text-neutral-500 h-9"
            />
          </div>
        </div>
        <ScrollArea className="flex-1 p-2">
          <div className="text-xs text-neutral-500 uppercase tracking-wider px-2 py-2 mb-1">
            JBT 数据目录
          </div>
          {fileTree.map((node) => renderTreeNode(node))}
        </ScrollArea>
      </div>

      {/* 中间主内容区 */}
      <div className="flex-1 flex flex-col min-w-0">
        {selectedFile ? (
          <>
            {/* 文件信息头部 */}
            <div className="p-4 border-b border-neutral-800 bg-neutral-900/30">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <Database className="w-5 h-5 text-orange-500" />
                  <div>
                    <h2 className="text-lg font-semibold text-white">{selectedFile.name}</h2>
                    <p className="text-xs text-neutral-400">
                      {selectedFile.exchange && `${selectedFile.exchange} | `}
                      {selectedFile.symbol && `${selectedFile.symbol} | `}
                      {selectedFile.frequency && `${selectedFile.frequency}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Select value={timeRange} onValueChange={setTimeRange}>
                    <SelectTrigger className="w-24 h-8 bg-neutral-800 border-neutral-700 text-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-neutral-800 border-neutral-700">
                      <SelectItem value="1d">1 天</SelectItem>
                      <SelectItem value="1w">1 周</SelectItem>
                      <SelectItem value="1m">1 月</SelectItem>
                      <SelectItem value="all">全部</SelectItem>
                    </SelectContent>
                  </Select>
                  <div className="flex items-center bg-neutral-800 rounded-lg p-1">
                    <button
                      onClick={() => setViewMode("chart")}
                      className={`px-3 py-1 text-sm rounded transition-colors ${
                        viewMode === "chart"
                          ? "bg-neutral-700 text-white"
                          : "text-neutral-400 hover:text-white"
                      }`}
                    >
                      <BarChart3 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setViewMode("table")}
                      className={`px-3 py-1 text-sm rounded transition-colors ${
                        viewMode === "table"
                          ? "bg-neutral-700 text-white"
                          : "text-neutral-400 hover:text-white"
                      }`}
                    >
                      <Table2 className="w-4 h-4" />
                    </button>
                  </div>
                  <Button
                    variant={compareMode ? "default" : "outline"}
                    size="sm"
                    onClick={() => setCompareMode(!compareMode)}
                    className={
                      compareMode
                        ? "bg-orange-500 hover:bg-orange-600"
                        : "border-neutral-700 text-neutral-300"
                    }
                  >
                    <GitCompare className="w-4 h-4 mr-1" />
                    对比
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-neutral-700 text-neutral-300"
                  >
                    <Download className="w-4 h-4 mr-1" />
                    导出
                  </Button>
                </div>
              </div>

              {/* 数据概览 */}
              <div className="grid grid-cols-5 gap-4">
                <div className="bg-neutral-800/50 rounded-lg p-3">
                  <p className="text-xs text-neutral-500 mb-1">记录数</p>
                  <p className="text-lg font-bold text-white font-mono">
                    {selectedFile.records?.toLocaleString() || "-"}
                  </p>
                </div>
                <div className="bg-neutral-800/50 rounded-lg p-3">
                  <p className="text-xs text-neutral-500 mb-1">文件大小</p>
                  <p className="text-lg font-bold text-white font-mono">{selectedFile.size || "-"}</p>
                </div>
                <div className="bg-neutral-800/50 rounded-lg p-3">
                  <p className="text-xs text-neutral-500 mb-1">最新时间</p>
                  <p className="text-lg font-bold text-white font-mono">
                    {selectedFile.lastUpdate?.split(" ")[1] || "10:42"}
                  </p>
                </div>
                <div className="bg-neutral-800/50 rounded-lg p-3">
                  <p className="text-xs text-neutral-500 mb-1">最旧时间</p>
                  <p className="text-lg font-bold text-white font-mono">09:00</p>
                </div>
                <div className="bg-neutral-800/50 rounded-lg p-3">
                  <p className="text-xs text-neutral-500 mb-1">缺失率</p>
                  <p className="text-lg font-bold text-green-400 font-mono">0%</p>
                </div>
              </div>
            </div>

            {/* 数据展示区 */}
            <div className="flex-1 p-4 overflow-auto">
              {isLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-64 bg-neutral-800" />
                  <Skeleton className="h-32 bg-neutral-800" />
                </div>
              ) : viewMode === "chart" ? (
                <div className="space-y-4">
                  {/* K线/折线图 */}
                  <Card className="bg-neutral-900 border-neutral-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-neutral-300">
                        价格走势
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={klineData}>
                            <defs>
                              <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                            <XAxis dataKey="time" stroke="#666" tick={{ fill: "#888", fontSize: 12 }} />
                            <YAxis stroke="#666" tick={{ fill: "#888", fontSize: 12 }} domain={["dataMin - 10", "dataMax + 10"]} />
                            <Tooltip
                              contentStyle={{
                                backgroundColor: "#1a1a1a",
                                border: "1px solid #333",
                                borderRadius: "8px",
                              }}
                              labelStyle={{ color: "#fff" }}
                            />
                            <Area
                              type="monotone"
                              dataKey="close"
                              stroke="#f97316"
                              fill="url(#priceGradient)"
                              strokeWidth={2}
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>

                  {/* 成交量图 */}
                  <Card className="bg-neutral-900 border-neutral-800">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium text-neutral-300">
                        成交量
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-32">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={klineData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                            <XAxis dataKey="time" stroke="#666" tick={{ fill: "#888", fontSize: 12 }} />
                            <YAxis stroke="#666" tick={{ fill: "#888", fontSize: 12 }} />
                            <Tooltip
                              contentStyle={{
                                backgroundColor: "#1a1a1a",
                                border: "1px solid #333",
                                borderRadius: "8px",
                              }}
                            />
                            <Bar dataKey="volume" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              ) : (
                /* 表格视图 */
                <Card className="bg-neutral-900 border-neutral-800">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm font-medium text-neutral-300">
                        数据预览（前 100 行）
                      </CardTitle>
                      <div className="flex items-center gap-2 text-xs text-neutral-500">
                        <Columns3 className="w-4 h-4" />
                        <span>8 列</span>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-neutral-800">
                            {["datetime", "open", "high", "low", "close", "volume", "amount", "oi"].map(
                              (col) => (
                                <th
                                  key={col}
                                  className="text-left py-2 px-3 text-xs font-medium text-neutral-500 uppercase tracking-wider"
                                >
                                  {col}
                                </th>
                              )
                            )}
                          </tr>
                        </thead>
                        <tbody>
                          {tableData.map((row, i) => (
                            <tr
                              key={i}
                              className="border-b border-neutral-800/50 hover:bg-neutral-800/30"
                            >
                              <td className="py-2 px-3 text-neutral-300 font-mono text-xs">
                                {row.datetime}
                              </td>
                              <td className="py-2 px-3 text-white font-mono">{row.open}</td>
                              <td className="py-2 px-3 text-red-400 font-mono">{row.high}</td>
                              <td className="py-2 px-3 text-green-400 font-mono">{row.low}</td>
                              <td className="py-2 px-3 text-white font-mono">{row.close}</td>
                              <td className="py-2 px-3 text-neutral-300 font-mono">
                                {row.volume.toLocaleString()}
                              </td>
                              <td className="py-2 px-3 text-neutral-300 font-mono">
                                {row.amount.toLocaleString()}
                              </td>
                              <td className="py-2 px-3 text-neutral-300 font-mono">
                                {row.oi.toLocaleString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </>
        ) : (
          /* 未选择文件时的空状态 */
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Database className="w-16 h-16 text-neutral-700 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-neutral-400 mb-2">选择文件查看数据</h3>
              <p className="text-sm text-neutral-500">从左侧目录树中选择一个数据文件</p>
            </div>
          </div>
        )}
      </div>

      {/* 右侧数据质量区 */}
      <div className="w-72 border-l border-neutral-800 bg-neutral-900/50 flex flex-col">
        <div className="p-4 border-b border-neutral-800">
          <h3 className="text-sm font-medium text-neutral-300 uppercase tracking-wider">
            数据质量检查
          </h3>
        </div>
        <ScrollArea className="flex-1 p-4">
          {selectedFile ? (
            <div className="space-y-3">
              {qualityChecks.map((check, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg"
                >
                  <div className="flex items-center gap-2">
                    {getQualityStatusIcon(check.status)}
                    <span className="text-sm text-neutral-300">{check.item}</span>
                  </div>
                  <span className={`text-sm font-mono ${getQualityStatusColor(check.status)}`}>
                    {check.value}
                  </span>
                </div>
              ))}

              <div className="mt-6 pt-4 border-t border-neutral-800">
                <h4 className="text-xs text-neutral-500 uppercase tracking-wider mb-3">
                  列信息
                </h4>
                <div className="space-y-2">
                  {["datetime", "open", "high", "low", "close", "volume", "amount", "oi"].map(
                    (col) => (
                      <div
                        key={col}
                        className="flex items-center justify-between text-sm"
                      >
                        <span className="text-neutral-400">{col}</span>
                        <Badge
                          variant="outline"
                          className="text-xs border-neutral-700 text-neutral-400"
                        >
                          {col === "datetime" ? "datetime64" : "float64"}
                        </Badge>
                      </div>
                    )
                  )}
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-neutral-800">
                <h4 className="text-xs text-neutral-500 uppercase tracking-wider mb-3">
                  统计信息
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-neutral-400">最高价</span>
                    <span className="text-red-400 font-mono">3,898</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">最低价</span>
                    <span className="text-green-400 font-mono">3,848</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">平均价</span>
                    <span className="text-white font-mono">3,872</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-400">总成交量</span>
                    <span className="text-white font-mono">156,200</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <AlertTriangle className="w-8 h-8 text-neutral-600 mx-auto mb-2" />
              <p className="text-sm text-neutral-500">选择文件后显示质量检查</p>
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  )
}
