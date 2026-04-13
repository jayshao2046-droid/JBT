"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Database,
  HardDrive,
  Clock,
  CheckCircle,
  AlertTriangle,
  XCircle,
  RefreshCw,
  ArrowRight,
  Activity,
  FileText,
  Send,
  Filter,
} from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

// 采集器状态类型
type CollectorStatus = "normal" | "delayed" | "failed" | "idle"

interface Collector {
  id: string
  name: string
  schedule: string
  lastSuccess: string
  lastDuration: string
  todayCount: number
  status: CollectorStatus
  nextRun?: string
  errorSummary?: string
  outputPath?: string
}

// 模拟采集器数据
const collectors: Collector[] = [
  {
    id: "news-api",
    name: "新闻 API",
    schedule: "每分钟",
    lastSuccess: "10:42:15",
    lastDuration: "2.3s",
    todayCount: 1842,
    status: "normal",
    nextRun: "10:43:00",
    outputPath: "/data/news_api/",
  },
  {
    id: "sentiment",
    name: "情绪指数",
    schedule: "每分钟",
    lastSuccess: "10:42:30",
    lastDuration: "1.8s",
    todayCount: 1440,
    status: "normal",
    nextRun: "10:43:30",
    outputPath: "/data/sentiment/",
  },
  {
    id: "overseas-minute",
    name: "外盘分钟",
    schedule: "每5分钟",
    lastSuccess: "10:40:00",
    lastDuration: "8.5s",
    todayCount: 288,
    status: "normal",
    nextRun: "10:45:00",
    outputPath: "/data/overseas_kline/",
  },
  {
    id: "tushare",
    name: "Tushare 期货",
    schedule: "每日 15:30",
    lastSuccess: "昨日 15:32",
    lastDuration: "45.2s",
    todayCount: 0,
    status: "idle",
    nextRun: "今日 15:30",
    outputPath: "/data/tushare/",
  },
  {
    id: "macro",
    name: "宏观数据",
    schedule: "每4小时",
    lastSuccess: "08:00:12",
    lastDuration: "12.3s",
    todayCount: 3,
    status: "normal",
    nextRun: "12:00:00",
    outputPath: "/data/macro_global/",
  },
  {
    id: "position",
    name: "持仓日报",
    schedule: "每日 16:30",
    lastSuccess: "昨日 16:35",
    lastDuration: "28.7s",
    todayCount: 0,
    status: "idle",
    nextRun: "今日 16:30",
    outputPath: "/data/position/",
  },
  {
    id: "volatility",
    name: "波动率指数",
    schedule: "每小时",
    lastSuccess: "10:00:45",
    lastDuration: "3.2s",
    todayCount: 11,
    status: "normal",
    nextRun: "11:00:00",
    outputPath: "/data/volatility_index/",
  },
  {
    id: "forex",
    name: "外汇日线",
    schedule: "每日 06:00",
    lastSuccess: "今日 06:02",
    lastDuration: "5.8s",
    todayCount: 1,
    status: "normal",
    nextRun: "明日 06:00",
    outputPath: "/data/forex/",
  },
  {
    id: "cftc",
    name: "CFTC 持仓",
    schedule: "每周六 08:00",
    lastSuccess: "上周六 08:05",
    lastDuration: "15.3s",
    todayCount: 0,
    status: "idle",
    nextRun: "本周六 08:00",
    outputPath: "/data/cftc/",
  },
  {
    id: "option",
    name: "期权行情",
    schedule: "每15分钟",
    lastSuccess: "10:30:22",
    lastDuration: "6.1s",
    todayCount: 42,
    status: "delayed",
    nextRun: "10:45:00",
    errorSummary: "上次执行超时 +3s",
    outputPath: "/data/option/",
  },
  {
    id: "rss",
    name: "RSS 聚合",
    schedule: "每10分钟",
    lastSuccess: "10:40:18",
    lastDuration: "4.2s",
    todayCount: 156,
    status: "normal",
    nextRun: "10:50:00",
    outputPath: "/data/news_collected/",
  },
  {
    id: "feishu-heartbeat",
    name: "飞书心跳",
    schedule: "每5分钟",
    lastSuccess: "10:40:00",
    lastDuration: "0.8s",
    todayCount: 288,
    status: "normal",
    nextRun: "10:45:00",
    outputPath: "webhook",
  },
  {
    id: "email-morning",
    name: "邮件晨报",
    schedule: "每日 07:30",
    lastSuccess: "今日 07:32",
    lastDuration: "18.5s",
    todayCount: 1,
    status: "normal",
    nextRun: "明日 07:30",
    outputPath: "smtp",
  },
  {
    id: "email-noon",
    name: "邮件午报",
    schedule: "每日 12:30",
    lastSuccess: "昨日 12:33",
    lastDuration: "15.2s",
    todayCount: 0,
    status: "idle",
    nextRun: "今日 12:30",
    outputPath: "smtp",
  },
  {
    id: "mini-device",
    name: "Mini 设备监控",
    schedule: "每分钟",
    lastSuccess: "10:42:00",
    lastDuration: "0.5s",
    todayCount: 642,
    status: "normal",
    nextRun: "10:43:00",
    outputPath: "/data/logs/",
  },
  {
    id: "data-scheduler",
    name: "数据调度器",
    schedule: "持续运行",
    lastSuccess: "运行中",
    lastDuration: "-",
    todayCount: 0,
    status: "normal",
    outputPath: "process",
  },
  {
    id: "data-api",
    name: "数据 API",
    schedule: "持续运行",
    lastSuccess: "运行中",
    lastDuration: "-",
    todayCount: 12458,
    status: "normal",
    outputPath: "http://localhost:8105",
  },
  {
    id: "shipping",
    name: "航运数据",
    schedule: "每日 09:00",
    lastSuccess: "今日 09:03",
    lastDuration: "22.1s",
    todayCount: 1,
    status: "normal",
    nextRun: "明日 09:00",
    outputPath: "/data/shipping/",
  },
  {
    id: "news-collected",
    name: "新闻采集",
    schedule: "每2分钟",
    lastSuccess: "10:42:00",
    lastDuration: "5.8s",
    todayCount: 720,
    status: "failed",
    errorSummary: "连接超时: 财联社",
    outputPath: "/data/news_collected/",
  },
  {
    id: "parquet-sync",
    name: "Parquet 同步",
    schedule: "每小时",
    lastSuccess: "10:05:30",
    lastDuration: "180.5s",
    todayCount: 11,
    status: "normal",
    nextRun: "11:00:00",
    outputPath: "/data/parquet/",
  },
]

// 24小时时间线数据
const timelineData = [
  { hour: "00", collectors: ["macro", "forex"] },
  { hour: "01", collectors: [] },
  { hour: "02", collectors: [] },
  { hour: "03", collectors: [] },
  { hour: "04", collectors: [] },
  { hour: "05", collectors: [] },
  { hour: "06", collectors: ["forex", "macro"] },
  { hour: "07", collectors: ["email-morning"] },
  { hour: "08", collectors: ["macro", "cftc"] },
  { hour: "09", collectors: ["shipping", "volatility"] },
  { hour: "10", collectors: ["volatility", "parquet-sync"] },
  { hour: "11", collectors: ["volatility"] },
  { hour: "12", collectors: ["email-noon", "macro", "volatility"] },
  { hour: "13", collectors: ["volatility"] },
  { hour: "14", collectors: ["volatility"] },
  { hour: "15", collectors: ["tushare", "volatility"] },
  { hour: "16", collectors: ["position", "macro", "volatility"] },
  { hour: "17", collectors: ["volatility"] },
  { hour: "18", collectors: ["volatility"] },
  { hour: "19", collectors: ["volatility"] },
  { hour: "20", collectors: ["macro", "volatility"] },
  { hour: "21", collectors: ["volatility"] },
  { hour: "22", collectors: ["volatility"] },
  { hour: "23", collectors: ["volatility"] },
]

// 运行日志
const logs = [
  { time: "10:42:30", level: "INFO", message: "情绪指数采集完成，写入 1440 条记录" },
  { time: "10:42:15", level: "INFO", message: "新闻 API 采集完成，获取 58 条新闻" },
  { time: "10:42:00", level: "ERROR", message: "新闻采集失败: 财联社连接超时 (timeout=30s)" },
  { time: "10:41:45", level: "WARNING", message: "期权行情采集延迟 +3s，建议检查网络" },
  { time: "10:40:18", level: "INFO", message: "RSS 聚合完成，解析 12 个源，获取 45 条" },
  { time: "10:40:00", level: "INFO", message: "飞书心跳发送成功" },
  { time: "10:40:00", level: "INFO", message: "外盘分钟采集完成，更新 85 个品种" },
  { time: "10:35:22", level: "INFO", message: "Mini 设备 CPU: 32%, 内存: 68%, 磁盘: 42%" },
  { time: "10:30:22", level: "WARNING", message: "期权行情采集耗时 9.1s，超过预期阈值 6s" },
  { time: "10:05:30", level: "INFO", message: "Parquet 同步完成，处理 2.4GB 数据" },
]

export default function OverviewPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [logFilter, setLogFilter] = useState<"all" | "INFO" | "WARNING" | "ERROR">("all")

  const handleRefresh = () => {
    setIsLoading(true)
    setTimeout(() => setIsLoading(false), 1000)
  }

  const getStatusColor = (status: CollectorStatus) => {
    switch (status) {
      case "normal":
        return "bg-green-500"
      case "delayed":
        return "bg-yellow-500"
      case "failed":
        return "bg-red-500"
      case "idle":
        return "bg-neutral-500"
    }
  }

  const getStatusBorder = (status: CollectorStatus) => {
    switch (status) {
      case "normal":
        return "border-green-500/30 hover:border-green-500/50"
      case "delayed":
        return "border-yellow-500/30 hover:border-yellow-500/50"
      case "failed":
        return "border-red-500/30 hover:border-red-500/50"
      case "idle":
        return "border-neutral-600 hover:border-neutral-500"
    }
  }

  const getLogColor = (level: string) => {
    switch (level) {
      case "INFO":
        return "text-blue-400"
      case "WARNING":
        return "text-yellow-400"
      case "ERROR":
        return "text-red-400"
      default:
        return "text-neutral-400"
    }
  }

  const normalCount = collectors.filter((c) => c.status === "normal").length
  const totalCount = collectors.length
  const todayTotal = collectors.reduce((sum, c) => sum + c.todayCount, 0)

  const filteredLogs = logFilter === "all" ? logs : logs.filter((l) => l.level === logFilter)

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-28 bg-neutral-800" />
          ))}
        </div>
        <Skeleton className="h-96 bg-neutral-800" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* 顶部操作栏 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">数据端总览</h1>
          <p className="text-sm text-neutral-400 mt-1">一屏看懂 JBT 数据采集系统全局健康状态</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleRefresh}
            variant="outline"
            className="border-neutral-700 text-neutral-300 hover:bg-neutral-800 hover:text-white"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新总览
          </Button>
          <Button className="bg-orange-500 hover:bg-orange-600 text-white">
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
                  <span className="text-3xl font-bold text-white font-mono">{normalCount}</span>
                  <span className="text-lg text-neutral-500 font-mono">/ {totalCount}</span>
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
                <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">今日采集</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold text-white font-mono">
                    {(todayTotal / 1000).toFixed(1)}
                  </span>
                  <span className="text-lg text-neutral-500">K</span>
                </div>
                <p className="text-xs text-neutral-400 mt-1">累计记录数</p>
              </div>
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <FileText className="w-6 h-6 text-blue-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">数据存储</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold text-white font-mono">128.5</span>
                  <span className="text-lg text-neutral-500">GB</span>
                </div>
                <p className="text-xs text-neutral-400 mt-1">当前体积</p>
              </div>
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <HardDrive className="w-6 h-6 text-purple-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">飞书心跳</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold text-white font-mono">10:40</span>
                </div>
                <p className="text-xs text-green-400 mt-1 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                  最近一次发送
                </p>
              </div>
              <div className="p-2 bg-orange-500/10 rounded-lg">
                <Send className="w-6 h-6 text-orange-500" />
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
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-neutral-400">正常</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-yellow-500" />
                <span className="text-neutral-400">延迟</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-neutral-400">失败</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-neutral-500" />
                <span className="text-neutral-400">未触发</span>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <TooltipProvider>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
              {collectors.map((collector) => (
                <Tooltip key={collector.id}>
                  <TooltipTrigger asChild>
                    <div
                      className={`p-3 bg-neutral-800/50 border rounded-lg cursor-pointer transition-all ${getStatusBorder(collector.status)}`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-sm font-medium text-white truncate pr-2">
                          {collector.name}
                        </span>
                        <span className={`w-2 h-2 rounded-full flex-shrink-0 mt-1.5 ${getStatusColor(collector.status)}`} />
                      </div>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between text-neutral-500">
                          <span>频率</span>
                          <span className="text-neutral-300">{collector.schedule}</span>
                        </div>
                        <div className="flex justify-between text-neutral-500">
                          <span>最近成功</span>
                          <span className="text-neutral-300 font-mono">{collector.lastSuccess}</span>
                        </div>
                        <div className="flex justify-between text-neutral-500">
                          <span>耗时</span>
                          <span className="text-neutral-300 font-mono">{collector.lastDuration}</span>
                        </div>
                        <div className="flex justify-between text-neutral-500">
                          <span>今日写入</span>
                          <span className="text-neutral-300 font-mono">{collector.todayCount.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent
                    side="bottom"
                    className="bg-neutral-800 border-neutral-700 text-white p-3 max-w-xs"
                  >
                    <div className="space-y-2">
                      <p className="font-medium">{collector.name}</p>
                      {collector.errorSummary && (
                        <p className="text-xs text-red-400">{collector.errorSummary}</p>
                      )}
                      {collector.nextRun && (
                        <p className="text-xs text-neutral-400">
                          下次运行: <span className="text-white">{collector.nextRun}</span>
                        </p>
                      )}
                      <p className="text-xs text-neutral-400">
                        输出路径: <span className="text-neutral-300 font-mono">{collector.outputPath}</span>
                      </p>
                    </div>
                  </TooltipContent>
                </Tooltip>
              ))}
            </div>
          </TooltipProvider>
        </CardContent>
      </Card>

      {/* 24小时运行时间线和最新日志 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 24小时运行时间线 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider">
              24 小时运行时间线
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative">
              {/* 时间轴 */}
              <div className="flex items-end gap-1 h-32 overflow-x-auto pb-6">
                {timelineData.map((item, index) => {
                  const currentHour = new Date().getHours()
                  const isCurrent = parseInt(item.hour) === currentHour
                  const isPast = parseInt(item.hour) < currentHour
                  const hasActivity = item.collectors.length > 0

                  return (
                    <div key={item.hour} className="flex flex-col items-center min-w-[28px]">
                      <div
                        className={`w-6 rounded-t transition-all ${
                          hasActivity
                            ? isPast
                              ? "bg-green-500/60"
                              : isCurrent
                                ? "bg-orange-500"
                                : "bg-neutral-700"
                            : "bg-neutral-800"
                        }`}
                        style={{ height: `${Math.max(20, item.collectors.length * 20)}px` }}
                      />
                      <span
                        className={`text-xs mt-2 font-mono ${
                          isCurrent ? "text-orange-500 font-bold" : "text-neutral-500"
                        }`}
                      >
                        {item.hour}
                      </span>
                    </div>
                  )
                })}
              </div>
              {/* 当前时间指示器 */}
              <div className="absolute bottom-0 left-0 w-full h-px bg-neutral-700" />
            </div>
            <div className="mt-4 flex items-center gap-4 text-xs text-neutral-500">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-green-500/60" />
                <span>已执行</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-orange-500" />
                <span>当前</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-neutral-700" />
                <span>待执行</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 最新运行日志 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider">
                最新运行日志
              </CardTitle>
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1 bg-neutral-800 rounded-lg p-1">
                  {(["all", "INFO", "WARNING", "ERROR"] as const).map((level) => (
                    <button
                      key={level}
                      onClick={() => setLogFilter(level)}
                      className={`px-2 py-1 text-xs rounded transition-colors ${
                        logFilter === level
                          ? "bg-neutral-700 text-white"
                          : "text-neutral-400 hover:text-white"
                      }`}
                    >
                      {level === "all" ? "全部" : level}
                    </button>
                  ))}
                </div>
                <Button variant="ghost" size="icon" className="h-8 w-8 text-neutral-400 hover:text-white">
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-[280px] overflow-y-auto">
              {filteredLogs.map((log, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-2 bg-neutral-800/30 rounded-lg hover:bg-neutral-800/50 transition-colors"
                >
                  <span className="text-xs text-neutral-500 font-mono whitespace-nowrap mt-0.5">
                    {log.time}
                  </span>
                  <Badge
                    variant="outline"
                    className={`text-xs px-1.5 py-0 ${
                      log.level === "ERROR"
                        ? "border-red-500/50 text-red-400"
                        : log.level === "WARNING"
                          ? "border-yellow-500/50 text-yellow-400"
                          : "border-blue-500/50 text-blue-400"
                    }`}
                  >
                    {log.level}
                  </Badge>
                  <span className="text-sm text-neutral-300 flex-1">{log.message}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
