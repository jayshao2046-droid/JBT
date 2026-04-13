"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Checkbox } from "@/components/ui/checkbox"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Play,
  Eye,
  RotateCcw,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  Search,
  AlertTriangle,
  FileText,
  Calendar,
  Settings2,
} from "lucide-react"

type CollectorStatus = "running" | "success" | "failed" | "idle" | "delayed"

interface CollectorTask {
  id: string
  name: string
  taskId: string
  scheduleType: "cron" | "interval"
  scheduleExpr: string
  lastRunTime: string
  lastDuration: string
  lastResult: CollectorStatus
  todaySuccess: number
  todayFailed: number
  category: string
  description: string
  dataSource: string
  outputDir: string
  history: { time: string; status: CollectorStatus; duration: string; records: number }[]
  errors: { time: string; message: string }[]
}

// 采集器任务数据
const collectorTasks: CollectorTask[] = [
  // 行情类
  {
    id: "futures-minute",
    name: "期货分钟 K 线",
    taskId: "TASK-001",
    scheduleType: "cron",
    scheduleExpr: "*/1 * * * *",
    lastRunTime: "10:42:00",
    lastDuration: "3.2s",
    lastResult: "success",
    todaySuccess: 642,
    todayFailed: 0,
    category: "行情类",
    description: "采集国内期货品种的分钟级 K 线数据，包含开高低收量额持仓",
    dataSource: "CTP",
    outputDir: "/data/futures_minute/",
    history: [
      { time: "10:42:00", status: "success", duration: "3.2s", records: 85 },
      { time: "10:41:00", status: "success", duration: "2.8s", records: 85 },
      { time: "10:40:00", status: "success", duration: "3.1s", records: 85 },
    ],
    errors: [],
  },
  {
    id: "overseas-minute",
    name: "外盘分钟 K 线",
    taskId: "TASK-002",
    scheduleType: "cron",
    scheduleExpr: "*/5 * * * *",
    lastRunTime: "10:40:00",
    lastDuration: "8.5s",
    lastResult: "success",
    todaySuccess: 128,
    todayFailed: 0,
    category: "行情类",
    description: "采集外盘品种分钟 K 线数据，包括 LME、COMEX、NYMEX 等",
    dataSource: "yfinance",
    outputDir: "/data/overseas_kline/",
    history: [
      { time: "10:40:00", status: "success", duration: "8.5s", records: 120 },
      { time: "10:35:00", status: "success", duration: "7.9s", records: 120 },
    ],
    errors: [],
  },
  {
    id: "stock-minute",
    name: "股票分钟 K 线",
    taskId: "TASK-003",
    scheduleType: "cron",
    scheduleExpr: "*/1 9-15 * * 1-5",
    lastRunTime: "10:42:00",
    lastDuration: "5.1s",
    lastResult: "success",
    todaySuccess: 162,
    todayFailed: 0,
    category: "行情类",
    description: "采集 A 股分钟级 K 线数据",
    dataSource: "Tushare",
    outputDir: "/data/stock_minute/",
    history: [],
    errors: [],
  },
  {
    id: "option-quote",
    name: "期权行情",
    taskId: "TASK-004",
    scheduleType: "cron",
    scheduleExpr: "*/15 9-15 * * 1-5",
    lastRunTime: "10:30:22",
    lastDuration: "9.1s",
    lastResult: "delayed",
    todaySuccess: 41,
    todayFailed: 1,
    category: "行情类",
    description: "采集商品期权和股指期权实时行情",
    dataSource: "CTP",
    outputDir: "/data/option/",
    history: [
      { time: "10:30:22", status: "delayed", duration: "9.1s", records: 450 },
      { time: "10:15:00", status: "success", duration: "5.8s", records: 450 },
    ],
    errors: [{ time: "10:30:22", message: "执行超时 +3s，超过预期阈值 6s" }],
  },

  // 宏观类
  {
    id: "macro-global",
    name: "宏观数据",
    taskId: "TASK-010",
    scheduleType: "cron",
    scheduleExpr: "0 */4 * * *",
    lastRunTime: "08:00:12",
    lastDuration: "12.3s",
    lastResult: "success",
    todaySuccess: 3,
    todayFailed: 0,
    category: "宏观类",
    description: "采集全球宏观经济指标，包括 GDP、CPI、PMI 等",
    dataSource: "AkShare",
    outputDir: "/data/macro_global/",
    history: [],
    errors: [],
  },
  {
    id: "forex-daily",
    name: "外汇日线",
    taskId: "TASK-011",
    scheduleType: "cron",
    scheduleExpr: "0 6 * * *",
    lastRunTime: "06:02:15",
    lastDuration: "5.8s",
    lastResult: "success",
    todaySuccess: 1,
    todayFailed: 0,
    category: "宏观类",
    description: "采集主要货币对日线数据",
    dataSource: "yfinance",
    outputDir: "/data/forex/",
    history: [],
    errors: [],
  },

  // 新闻资讯类
  {
    id: "news-api",
    name: "新闻 API",
    taskId: "TASK-020",
    scheduleType: "cron",
    scheduleExpr: "*/1 * * * *",
    lastRunTime: "10:42:15",
    lastDuration: "2.3s",
    lastResult: "success",
    todaySuccess: 642,
    todayFailed: 0,
    category: "新闻资讯类",
    description: "调用财联社、东方财富等新闻 API 获取实时资讯",
    dataSource: "API",
    outputDir: "/data/news_api/",
    history: [],
    errors: [],
  },
  {
    id: "news-collected",
    name: "新闻采集",
    taskId: "TASK-021",
    scheduleType: "cron",
    scheduleExpr: "*/2 * * * *",
    lastRunTime: "10:42:00",
    lastDuration: "5.8s",
    lastResult: "failed",
    todaySuccess: 318,
    todayFailed: 2,
    category: "新闻资讯类",
    description: "爬虫采集各大财经网站新闻",
    dataSource: "爬虫",
    outputDir: "/data/news_collected/",
    history: [
      { time: "10:42:00", status: "failed", duration: "5.8s", records: 0 },
      { time: "10:40:00", status: "success", duration: "4.2s", records: 28 },
    ],
    errors: [
      { time: "10:42:00", message: "连接超时: 财联社 (timeout=30s)" },
      { time: "09:22:00", message: "解析失败: 东方财富页面结构变更" },
    ],
  },
  {
    id: "rss-aggregate",
    name: "RSS 聚合",
    taskId: "TASK-022",
    scheduleType: "cron",
    scheduleExpr: "*/10 * * * *",
    lastRunTime: "10:40:18",
    lastDuration: "4.2s",
    lastResult: "success",
    todaySuccess: 64,
    todayFailed: 0,
    category: "新闻资讯类",
    description: "聚合财经 RSS 源，包括彭博、路透等",
    dataSource: "RSS",
    outputDir: "/data/news_collected/",
    history: [],
    errors: [],
  },

  // 情绪类
  {
    id: "sentiment-index",
    name: "情绪指数",
    taskId: "TASK-030",
    scheduleType: "cron",
    scheduleExpr: "*/1 * * * *",
    lastRunTime: "10:42:30",
    lastDuration: "1.8s",
    lastResult: "success",
    todaySuccess: 642,
    todayFailed: 0,
    category: "情绪类",
    description: "采集恐慌贪婪指数、社交热度等情绪指标",
    dataSource: "API",
    outputDir: "/data/sentiment/",
    history: [],
    errors: [],
  },

  // 仓单持仓类
  {
    id: "position-daily",
    name: "持仓日报",
    taskId: "TASK-040",
    scheduleType: "cron",
    scheduleExpr: "30 16 * * 1-5",
    lastRunTime: "昨日 16:35",
    lastDuration: "28.7s",
    lastResult: "success",
    todaySuccess: 0,
    todayFailed: 0,
    category: "仓单持仓类",
    description: "采集各交易所持仓排名数据",
    dataSource: "交易所",
    outputDir: "/data/position/",
    history: [],
    errors: [],
  },
  {
    id: "cftc-position",
    name: "CFTC 持仓",
    taskId: "TASK-041",
    scheduleType: "cron",
    scheduleExpr: "0 8 * * 6",
    lastRunTime: "上周六 08:05",
    lastDuration: "15.3s",
    lastResult: "success",
    todaySuccess: 0,
    todayFailed: 0,
    category: "仓单持仓类",
    description: "采集 CFTC 持仓报告",
    dataSource: "CFTC",
    outputDir: "/data/cftc/",
    history: [],
    errors: [],
  },
  {
    id: "shipping-data",
    name: "航运数据",
    taskId: "TASK-042",
    scheduleType: "cron",
    scheduleExpr: "0 9 * * *",
    lastRunTime: "09:03:15",
    lastDuration: "22.1s",
    lastResult: "success",
    todaySuccess: 1,
    todayFailed: 0,
    category: "仓单持仓类",
    description: "采集 BDI 指数、船舶运力等航运数据",
    dataSource: "AkShare",
    outputDir: "/data/shipping/",
    history: [],
    errors: [],
  },

  // 波动率类
  {
    id: "volatility-index",
    name: "波动率指数",
    taskId: "TASK-050",
    scheduleType: "cron",
    scheduleExpr: "0 * * * *",
    lastRunTime: "10:00:45",
    lastDuration: "3.2s",
    lastResult: "success",
    todaySuccess: 11,
    todayFailed: 0,
    category: "波动率类",
    description: "采集 VIX、iVX 等波动率指数",
    dataSource: "yfinance",
    outputDir: "/data/volatility_index/",
    history: [],
    errors: [],
  },

  // 系统通知类
  {
    id: "feishu-heartbeat",
    name: "飞书心跳",
    taskId: "TASK-060",
    scheduleType: "cron",
    scheduleExpr: "*/5 * * * *",
    lastRunTime: "10:40:00",
    lastDuration: "0.8s",
    lastResult: "success",
    todaySuccess: 128,
    todayFailed: 0,
    category: "系统通知类",
    description: "向飞书发送系统心跳，确保通知链路正常",
    dataSource: "webhook",
    outputDir: "飞书告警通道",
    history: [],
    errors: [],
  },
  {
    id: "email-morning",
    name: "邮件晨报",
    taskId: "TASK-061",
    scheduleType: "cron",
    scheduleExpr: "30 7 * * *",
    lastRunTime: "07:32:15",
    lastDuration: "18.5s",
    lastResult: "success",
    todaySuccess: 1,
    todayFailed: 0,
    category: "系统通知类",
    description: "发送每日晨报邮件",
    dataSource: "SMTP",
    outputDir: "邮件",
    history: [],
    errors: [],
  },
  {
    id: "email-noon",
    name: "邮件午报",
    taskId: "TASK-062",
    scheduleType: "cron",
    scheduleExpr: "30 12 * * *",
    lastRunTime: "昨日 12:33",
    lastDuration: "15.2s",
    lastResult: "success",
    todaySuccess: 0,
    todayFailed: 0,
    category: "系统通知类",
    description: "发送每日午报邮件",
    dataSource: "SMTP",
    outputDir: "邮件",
    history: [],
    errors: [],
  },

  // Tushare 五合一
  {
    id: "tushare-futures",
    name: "Tushare 期货五合一",
    taskId: "TASK-070",
    scheduleType: "cron",
    scheduleExpr: "30 15 * * 1-5",
    lastRunTime: "昨日 15:32",
    lastDuration: "45.2s",
    lastResult: "success",
    todaySuccess: 0,
    todayFailed: 0,
    category: "行情类",
    description: "Tushare 期货日线、持仓、仓单、基差、结算价五合一采集",
    dataSource: "Tushare",
    outputDir: "/data/tushare/",
    history: [],
    errors: [],
  },
]

const categories = [
  "全部",
  "行情类",
  "宏观类",
  "新闻资讯类",
  "情绪类",
  "仓单持仓类",
  "波动率类",
  "系统通知类",
]

export default function CollectorsPage() {
  const [activeCategory, setActiveCategory] = useState("全部")
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedTask, setSelectedTask] = useState<CollectorTask | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)
  const [executeDialogOpen, setExecuteDialogOpen] = useState(false)
  const [backfillDialogOpen, setBackfillDialogOpen] = useState(false)
  const [selectedTasks, setSelectedTasks] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)

  // 补采参数
  const [backfillParams, setBackfillParams] = useState({
    startDate: "",
    endDate: "",
    symbols: "",
    frequency: "daily",
    overwrite: false,
    notify: true,
  })

  const filteredTasks = collectorTasks.filter((task) => {
    const matchCategory = activeCategory === "全部" || task.category === activeCategory
    const matchSearch =
      task.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.taskId.toLowerCase().includes(searchTerm.toLowerCase())
    return matchCategory && matchSearch
  })

  const getStatusColor = (status: CollectorStatus) => {
    switch (status) {
      case "running":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30"
      case "success":
        return "bg-green-500/20 text-green-400 border-green-500/30"
      case "failed":
        return "bg-red-500/20 text-red-400 border-red-500/30"
      case "delayed":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
      case "idle":
        return "bg-neutral-500/20 text-neutral-400 border-neutral-500/30"
    }
  }

  const getStatusText = (status: CollectorStatus) => {
    switch (status) {
      case "running":
        return "运行中"
      case "success":
        return "成功"
      case "failed":
        return "失败"
      case "delayed":
        return "延迟"
      case "idle":
        return "待执行"
    }
  }

  const handleViewDetail = (task: CollectorTask) => {
    setSelectedTask(task)
    setDetailOpen(true)
  }

  const handleExecute = (task: CollectorTask) => {
    setSelectedTask(task)
    setExecuteDialogOpen(true)
  }

  const handleBackfill = (task: CollectorTask) => {
    setSelectedTask(task)
    setBackfillDialogOpen(true)
  }

  const confirmExecute = () => {
    setIsLoading(true)
    setTimeout(() => {
      setIsLoading(false)
      setExecuteDialogOpen(false)
    }, 1500)
  }

  const confirmBackfill = () => {
    setIsLoading(true)
    setTimeout(() => {
      setIsLoading(false)
      setBackfillDialogOpen(false)
    }, 1500)
  }

  const toggleTaskSelection = (taskId: string) => {
    setSelectedTasks((prev) =>
      prev.includes(taskId) ? prev.filter((id) => id !== taskId) : [...prev, taskId]
    )
  }

  const selectAllInCategory = () => {
    const categoryTaskIds = filteredTasks.map((t) => t.id)
    const allSelected = categoryTaskIds.every((id) => selectedTasks.includes(id))
    if (allSelected) {
      setSelectedTasks((prev) => prev.filter((id) => !categoryTaskIds.includes(id)))
    } else {
      setSelectedTasks((prev) => [...new Set([...prev, ...categoryTaskIds])])
    }
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-12 w-64 bg-neutral-800" />
        <Skeleton className="h-10 w-full bg-neutral-800" />
        <Skeleton className="h-96 bg-neutral-800" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* 页面头部 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">采集器管理</h1>
          <p className="text-sm text-neutral-400 mt-1">
            按分类管理所有采集任务，支持手动补采与立即执行
          </p>
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
          <Button
            variant="outline"
            className="border-neutral-700 text-neutral-300 hover:bg-neutral-800"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
        </div>
      </div>

      {/* 分类标签 */}
      <Tabs value={activeCategory} onValueChange={setActiveCategory}>
        <TabsList className="bg-neutral-800 border border-neutral-700 p-1 h-auto flex-wrap">
          {categories.map((cat) => (
            <TabsTrigger
              key={cat}
              value={cat}
              className="data-[state=active]:bg-orange-500 data-[state=active]:text-white text-neutral-400 px-4 py-2"
            >
              {cat}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={activeCategory} className="mt-6">
          {/* 采集器表格 */}
          <Card className="bg-neutral-900 border-neutral-800">
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-neutral-800">
                      <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider w-10">
                        <Checkbox
                          checked={
                            filteredTasks.length > 0 &&
                            filteredTasks.every((t) => selectedTasks.includes(t.id))
                          }
                          onCheckedChange={selectAllInCategory}
                          className="border-neutral-600"
                        />
                      </th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                        采集器名称
                      </th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                        任务 ID
                      </th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                        调度方式
                      </th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                        调度表达式
                      </th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                        最近执行
                      </th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                        耗时
                      </th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                        状态
                      </th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                        今日成功/失败
                      </th>
                      <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wider">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTasks.map((task, index) => (
                      <tr
                        key={task.id}
                        className={`border-b border-neutral-800/50 hover:bg-neutral-800/30 transition-colors ${
                          index % 2 === 0 ? "bg-neutral-900" : "bg-neutral-900/50"
                        }`}
                      >
                        <td className="py-3 px-4">
                          <Checkbox
                            checked={selectedTasks.includes(task.id)}
                            onCheckedChange={() => toggleTaskSelection(task.id)}
                            className="border-neutral-600"
                          />
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-white font-medium">{task.name}</span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-neutral-400 font-mono">{task.taskId}</span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-neutral-400">
                            {task.scheduleType === "cron" ? "Cron" : "Interval"}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <code className="text-xs bg-neutral-800 px-2 py-1 rounded text-neutral-300 font-mono">
                            {task.scheduleExpr}
                          </code>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-neutral-300 font-mono">{task.lastRunTime}</span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-neutral-300 font-mono">{task.lastDuration}</span>
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant="outline" className={getStatusColor(task.lastResult)}>
                            {getStatusText(task.lastResult)}
                          </Badge>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-green-400 font-mono">{task.todaySuccess}</span>
                            <span className="text-neutral-600">/</span>
                            <span className="text-sm text-red-400 font-mono">{task.todayFailed}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-neutral-400 hover:text-white hover:bg-neutral-700"
                              onClick={() => handleViewDetail(task)}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-neutral-400 hover:text-green-400 hover:bg-neutral-700"
                              onClick={() => handleExecute(task)}
                            >
                              <Play className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-neutral-400 hover:text-orange-400 hover:bg-neutral-700"
                              onClick={() => handleBackfill(task)}
                            >
                              <RotateCcw className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* 批量操作区 */}
          {selectedTasks.length > 0 && (
            <Card className="bg-neutral-800 border-orange-500/30 mt-4">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-neutral-300">
                      已选择 <span className="text-orange-500 font-bold">{selectedTasks.length}</span> 个采集器
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedTasks([])}
                      className="text-neutral-400 hover:text-white"
                    >
                      清除选择
                    </Button>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-green-500/50 text-green-400 hover:bg-green-500/10"
                    >
                      <Play className="w-4 h-4 mr-2" />
                      批量执行
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-orange-500/50 text-orange-400 hover:bg-orange-500/10"
                      onClick={() => setBackfillDialogOpen(true)}
                    >
                      <RotateCcw className="w-4 h-4 mr-2" />
                      批量补采
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* 详情抽屉 */}
      <Sheet open={detailOpen} onOpenChange={setDetailOpen}>
        <SheetContent className="bg-neutral-900 border-neutral-800 w-[500px] sm:max-w-[500px]">
          {selectedTask && (
            <>
              <SheetHeader>
                <SheetTitle className="text-white">{selectedTask.name}</SheetTitle>
                <SheetDescription className="text-neutral-400">
                  {selectedTask.taskId} | {selectedTask.category}
                </SheetDescription>
              </SheetHeader>
              <div className="mt-6 space-y-6">
                {/* 基本信息 */}
                <div>
                  <h4 className="text-sm font-medium text-neutral-300 mb-3">采集逻辑说明</h4>
                  <p className="text-sm text-neutral-400">{selectedTask.description}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-neutral-500 mb-1">数据源</p>
                    <p className="text-sm text-white">{selectedTask.dataSource}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-500 mb-1">输出目录</p>
                    <p className="text-sm text-white font-mono text-xs">{selectedTask.outputDir}</p>
                  </div>
                </div>

                {/* 执行历史 */}
                <div>
                  <h4 className="text-sm font-medium text-neutral-300 mb-3">最近执行历史</h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {selectedTask.history.length > 0 ? (
                      selectedTask.history.map((h, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-2 bg-neutral-800 rounded"
                        >
                          <span className="text-xs text-neutral-400 font-mono">{h.time}</span>
                          <Badge variant="outline" className={getStatusColor(h.status)}>
                            {getStatusText(h.status)}
                          </Badge>
                          <span className="text-xs text-neutral-300 font-mono">{h.duration}</span>
                          <span className="text-xs text-neutral-300">{h.records} 条</span>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-neutral-500">暂无历史记录</p>
                    )}
                  </div>
                </div>

                {/* 异常信息 */}
                {selectedTask.errors.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-red-400 mb-3 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      最近异常信息
                    </h4>
                    <div className="space-y-2">
                      {selectedTask.errors.map((e, i) => (
                        <div key={i} className="p-2 bg-red-500/10 border border-red-500/30 rounded">
                          <p className="text-xs text-neutral-400 font-mono mb-1">{e.time}</p>
                          <p className="text-sm text-red-400">{e.message}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 操作按钮 */}
                <div className="flex gap-2 pt-4">
                  <Button
                    className="flex-1 bg-green-600 hover:bg-green-700"
                    onClick={() => {
                      setDetailOpen(false)
                      handleExecute(selectedTask)
                    }}
                  >
                    <Play className="w-4 h-4 mr-2" />
                    立即执行
                  </Button>
                  <Button
                    variant="outline"
                    className="flex-1 border-orange-500/50 text-orange-400 hover:bg-orange-500/10"
                    onClick={() => {
                      setDetailOpen(false)
                      handleBackfill(selectedTask)
                    }}
                  >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    补采
                  </Button>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>

      {/* 立即执行确认弹窗 */}
      <Dialog open={executeDialogOpen} onOpenChange={setExecuteDialogOpen}>
        <DialogContent className="bg-neutral-900 border-neutral-800">
          <DialogHeader>
            <DialogTitle className="text-white">确认执行</DialogTitle>
            <DialogDescription className="text-neutral-400">
              确定要立即执行 <span className="text-orange-500">{selectedTask?.name}</span> 吗？
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setExecuteDialogOpen(false)}
              className="border-neutral-700 text-neutral-300"
            >
              取消
            </Button>
            <Button onClick={confirmExecute} className="bg-green-600 hover:bg-green-700">
              确认执行
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 补采弹窗 */}
      <Dialog open={backfillDialogOpen} onOpenChange={setBackfillDialogOpen}>
        <DialogContent className="bg-neutral-900 border-neutral-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">补采配置</DialogTitle>
            <DialogDescription className="text-neutral-400">
              配置补采参数，执行历史数据补全
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-neutral-400 mb-2 block">开始日期</label>
                <Input
                  type="date"
                  value={backfillParams.startDate}
                  onChange={(e) =>
                    setBackfillParams({ ...backfillParams, startDate: e.target.value })
                  }
                  className="bg-neutral-800 border-neutral-700 text-white"
                />
              </div>
              <div>
                <label className="text-xs text-neutral-400 mb-2 block">结束日期</label>
                <Input
                  type="date"
                  value={backfillParams.endDate}
                  onChange={(e) =>
                    setBackfillParams({ ...backfillParams, endDate: e.target.value })
                  }
                  className="bg-neutral-800 border-neutral-700 text-white"
                />
              </div>
            </div>
            <div>
              <label className="text-xs text-neutral-400 mb-2 block">标的（可选，逗号分隔）</label>
              <Input
                placeholder="如: RB2510,CU2509"
                value={backfillParams.symbols}
                onChange={(e) =>
                  setBackfillParams({ ...backfillParams, symbols: e.target.value })
                }
                className="bg-neutral-800 border-neutral-700 text-white placeholder:text-neutral-500"
              />
            </div>
            <div>
              <label className="text-xs text-neutral-400 mb-2 block">数据频率</label>
              <Select
                value={backfillParams.frequency}
                onValueChange={(v) => setBackfillParams({ ...backfillParams, frequency: v })}
              >
                <SelectTrigger className="bg-neutral-800 border-neutral-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-neutral-800 border-neutral-700">
                  <SelectItem value="minute">分钟</SelectItem>
                  <SelectItem value="hourly">小时</SelectItem>
                  <SelectItem value="daily">日线</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2 text-sm text-neutral-300 cursor-pointer">
                <Checkbox
                  checked={backfillParams.overwrite}
                  onCheckedChange={(c) =>
                    setBackfillParams({ ...backfillParams, overwrite: !!c })
                  }
                  className="border-neutral-600"
                />
                覆盖已有文件
              </label>
              <label className="flex items-center gap-2 text-sm text-neutral-300 cursor-pointer">
                <Checkbox
                  checked={backfillParams.notify}
                  onCheckedChange={(c) =>
                    setBackfillParams({ ...backfillParams, notify: !!c })
                  }
                  className="border-neutral-600"
                />
                完成后通知
              </label>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setBackfillDialogOpen(false)}
              className="border-neutral-700 text-neutral-300"
            >
              取消
            </Button>
            <Button onClick={confirmBackfill} className="bg-orange-500 hover:bg-orange-600">
              开始补采
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
