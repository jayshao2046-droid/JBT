"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ChevronRight, FileText, Download, Upload, Play, Trash2, Lock } from "lucide-react"

const kpiData = [
  { label: "策略包总数", value: "42", status: "pass" },
  { label: "草稿数", value: "5", status: "pass" },
  { label: "已预约数", value: "8", status: "pass" },
  { label: "研究中", value: "6", status: "pass" },
  { label: "研究完成", value: "12", status: "pass" },
  { label: "待执行", value: "7", status: "pass" },
  { label: "生产中", value: "3", status: "pass" },
  { label: "已下架", value: "1", status: "pass" },
]

const strategyFolders = [
  { name: "全部策略", count: 42, icon: "📊" },
  { name: "市场风格", children: [
    { name: "趋势跟踪", count: 15 },
    { name: "均值回归", count: 10 },
    { name: "高频交易", count: 8 },
  ]},
  { name: "品种分类", children: [
    { name: "商品期货", count: 20 },
    { name: "金融期货", count: 15 },
    { name: "跨期套利", count: 7 },
  ]},
  { name: "状态筛选", children: [
    { name: "生产活跃", count: 3 },
    { name: "研究中", count: 6 },
    { name: "已下架", count: 1 },
  ]},
]

const strategies = [
  {
    id: 1,
    name: "MA交叉策略-期货",
    category: "趋势跟踪",
    status: "生产中",
    version: "v2.1.3",
    lastBacktest: "2024-04-05",
    backtestStatus: "有效",
    factors: ["MA5", "MA20", "RSI14"],
    factorsAllSynced: true,
    backTestAge: 2,
    description: "简单MA交叉，支持多品种",
  },
  {
    id: 2,
    name: "动量因子-多品种",
    category: "趋势跟踪",
    status: "待执行",
    version: "v1.8.2",
    lastBacktest: "2024-04-03",
    backtestStatus: "过期",
    factors: ["MACD", "KDJ"],
    factorsAllSynced: false,
    backTestAge: 4,
    description: "基于动量的多策略组合",
  },
  {
    id: 3,
    name: "均值回归-能源",
    category: "均值回归",
    status: "研究中",
    version: "v1.5.1",
    lastBacktest: "2024-04-02",
    backtestStatus: "进行中",
    factors: ["BOLL", "ATR20"],
    factorsAllSynced: false,
    backTestAge: 5,
    description: "能源品种专用均值回归",
  },
]

const getStatusBadgeColor = (status: string) => {
  switch (status) {
    case "生产中":
      return "bg-green-900 text-green-400"
    case "待执行":
      return "bg-blue-900 text-blue-400"
    case "研究中":
      return "bg-purple-900 text-purple-400"
    case "草稿":
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

export default function StrategyRepository() {
  const [selectedFolder, setSelectedFolder] = useState("全部策略")
  const [selectedStrategy, setSelectedStrategy] = useState(strategies[0])
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({})

  const toggleFolder = (name: string) => {
    setExpandedFolders({
      ...expandedFolders,
      [name]: !expandedFolders[name],
    })
  }

  const isExecutionDisabled = (strategy: typeof strategies[0]) => {
    return !strategy.factorsAllSynced || strategy.backtestStatus === "过期" || strategy.backtestStatus === "进行中"
  }

  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* KPI 卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
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

                <div className="space-y-2 pt-2">
                  <Button className="w-full bg-orange-600 hover:bg-orange-700 text-white text-xs h-8" disabled={isExecutionDisabled(selectedStrategy)}>
                    <Play className="w-3 h-3 mr-1" />
                    执行
                  </Button>
                  {isExecutionDisabled(selectedStrategy) && (
                    <p className="text-xs text-red-400 text-center">
                      {!selectedStrategy.factorsAllSynced ? "因子未同步" : "回测需更新"}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-2 pt-2">
                  <Button size="sm" variant="outline" className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 h-7 text-xs">
                    <Upload className="w-3 h-3" />
                  </Button>
                  <Button size="sm" variant="outline" className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 h-7 text-xs">
                    <Download className="w-3 h-3" />
                  </Button>
                  <Button size="sm" variant="outline" className="border-red-700 text-red-400 hover:bg-red-500/10 h-7 text-xs">
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

      {/* 生命周期时间线 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300">策略生命周期说明</CardTitle>
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
            策略必须完成研究和回测确认才能进入待执行状态。任何因子失配或回测过期都会禁用执行按钮。
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
