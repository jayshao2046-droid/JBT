"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import {
  Cpu,
  HardDrive,
  MemoryStick,
  Activity,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  RefreshCw,
  Send,
  Mail,
  Server,
  Zap,
  Database,
  FileText,
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
} from "recharts"

type ProcessStatus = "running" | "warning" | "error" | "stopped"

interface JBTProcess {
  id: string
  name: string
  status: ProcessStatus
  pid: number | null
  uptime: string
  cpuUsage: number
  memUsage: number
  lastHeartbeat: string
  isSingleInstance: boolean
}

interface NotificationChannel {
  id: string
  name: string
  type: "feishu" | "email"
  lastSendTime: string
  lastStatus: "success" | "failed"
  errorMessage?: string
}

interface DataSourceFreshness {
  name: string
  lastUpdate: string
  age: string
  status: "fresh" | "stale" | "expired"
}

// 资源使用历史数据
const cpuHistory = [
  { time: "10:00", value: 32 },
  { time: "10:05", value: 38 },
  { time: "10:10", value: 45 },
  { time: "10:15", value: 42 },
  { time: "10:20", value: 48 },
  { time: "10:25", value: 35 },
  { time: "10:30", value: 40 },
  { time: "10:35", value: 38 },
  { time: "10:40", value: 32 },
  { time: "10:42", value: 35 },
]

const memoryHistory = [
  { time: "10:00", value: 62 },
  { time: "10:05", value: 64 },
  { time: "10:10", value: 68 },
  { time: "10:15", value: 66 },
  { time: "10:20", value: 70 },
  { time: "10:25", value: 68 },
  { time: "10:30", value: 72 },
  { time: "10:35", value: 70 },
  { time: "10:40", value: 68 },
  { time: "10:42", value: 68 },
]

// JBT 关键进程
const jbtProcesses: JBTProcess[] = [
  {
    id: "scheduler",
    name: "JBT 数据调度器",
    status: "running",
    pid: 12847,
    uptime: "168:42:15",
    cpuUsage: 8.5,
    memUsage: 245,
    lastHeartbeat: "10:42:30",
    isSingleInstance: true,
  },
  {
    id: "api",
    name: "数据 API",
    status: "running",
    pid: 12892,
    uptime: "168:42:10",
    cpuUsage: 3.2,
    memUsage: 128,
    lastHeartbeat: "10:42:28",
    isSingleInstance: true,
  },
]

// 通知渠道状态
const notificationChannels: NotificationChannel[] = [
  {
    id: "feishu-alert",
    name: "飞书告警通道",
    type: "feishu",
    lastSendTime: "10:40:00",
    lastStatus: "success",
  },
  {
    id: "feishu-news",
    name: "飞书新闻通道",
    type: "feishu",
    lastSendTime: "10:42:15",
    lastStatus: "success",
  },
  {
    id: "feishu-trade",
    name: "飞书交易通道",
    type: "feishu",
    lastSendTime: "10:30:00",
    lastStatus: "success",
  },
  {
    id: "email-morning",
    name: "邮件晨报",
    type: "email",
    lastSendTime: "07:32:15",
    lastStatus: "success",
  },
  {
    id: "email-noon",
    name: "邮件午报",
    type: "email",
    lastSendTime: "昨日 12:33",
    lastStatus: "success",
  },
]

// 数据源新鲜度
const dataSourceFreshness: DataSourceFreshness[] = [
  { name: "新闻 API", lastUpdate: "10:42:15", age: "30s", status: "fresh" },
  { name: "情绪指数", lastUpdate: "10:42:30", age: "15s", status: "fresh" },
  { name: "外盘分钟", lastUpdate: "10:40:00", age: "2m 45s", status: "fresh" },
  { name: "RSS 聚合", lastUpdate: "10:40:18", age: "2m 27s", status: "fresh" },
  { name: "期权行情", lastUpdate: "10:30:22", age: "12m 23s", status: "stale" },
  { name: "宏观数据", lastUpdate: "08:00:12", age: "2h 42m", status: "fresh" },
  { name: "持仓日报", lastUpdate: "昨日 16:35", age: "18h 8m", status: "fresh" },
  { name: "CFTC 持仓", lastUpdate: "上周六", age: "4d 2h", status: "fresh" },
]

// 系统日志
const systemLogs = [
  { time: "10:42:30", level: "INFO", source: "scheduler", message: "情绪指数采集完成，写入 1440 条记录" },
  { time: "10:42:15", level: "INFO", source: "scheduler", message: "新闻 API 采集完成，获取 58 条新闻" },
  { time: "10:42:00", level: "ERROR", source: "scheduler", message: "新闻采集失败: 财联社连接超时 (timeout=30s)" },
  { time: "10:41:45", level: "WARNING", source: "scheduler", message: "期权行情采集延迟 +3s，建议检查网络" },
  { time: "10:40:18", level: "INFO", source: "scheduler", message: "RSS 聚合完成，解析 12 个源，获取 45 条" },
  { time: "10:40:00", level: "INFO", source: "api", message: "飞书心跳发送成功" },
  { time: "10:40:00", level: "INFO", source: "scheduler", message: "外盘分钟采集完成，更新 85 个品种" },
  { time: "10:35:22", level: "INFO", source: "scheduler", message: "Mini 设备 CPU: 32%, 内存: 68%, 磁盘: 42%" },
  { time: "10:30:22", level: "WARNING", source: "scheduler", message: "期权行情采集耗时 9.1s，超过预期阈值 6s" },
  { time: "10:05:30", level: "INFO", source: "scheduler", message: "Parquet 同步完成，处理 2.4GB 数据" },
  { time: "09:03:15", level: "INFO", source: "scheduler", message: "航运数据采集完成，BDI 指数更新" },
  { time: "07:32:15", level: "INFO", source: "api", message: "邮件晨报发送成功，收件人: 3" },
]

export default function SystemMonitorPage() {
  const [activeLogType, setActiveLogType] = useState("all")
  const [isLoading, setIsLoading] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const filteredLogs =
    activeLogType === "all"
      ? systemLogs
      : systemLogs.filter((log) =>
          activeLogType === "error"
            ? log.level === "ERROR"
            : activeLogType === "warning"
              ? log.level === "WARNING"
              : log.level === "INFO"
        )

  const getLogColor = (level: string) => {
    switch (level) {
      case "ERROR":
        return "text-red-400"
      case "WARNING":
        return "text-yellow-400"
      default:
        return "text-blue-400"
    }
  }

  const getStatusIcon = (status: ProcessStatus) => {
    switch (status) {
      case "running":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case "error":
        return <XCircle className="w-4 h-4 text-red-500" />
      case "stopped":
        return <XCircle className="w-4 h-4 text-neutral-500" />
    }
  }

  const getStatusColor = (status: ProcessStatus) => {
    switch (status) {
      case "running":
        return "bg-green-500/20 text-green-400 border-green-500/30"
      case "warning":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
      case "error":
        return "bg-red-500/20 text-red-400 border-red-500/30"
      case "stopped":
        return "bg-neutral-500/20 text-neutral-400 border-neutral-500/30"
    }
  }

  const getFreshnessColor = (status: DataSourceFreshness["status"]) => {
    switch (status) {
      case "fresh":
        return "text-green-400"
      case "stale":
        return "text-yellow-400"
      case "expired":
        return "text-red-400"
    }
  }

  const handleRefresh = () => {
    setIsLoading(true)
    setTimeout(() => setIsLoading(false), 800)
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-12 w-64 bg-neutral-800" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-40 bg-neutral-800" />
          ))}
        </div>
        <Skeleton className="h-96 bg-neutral-800" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* 页面头部 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">硬件与系统</h1>
          <p className="text-sm text-neutral-400 mt-1">
            监控 Mini 设备、JBT 调度器和通知链路健康状态
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-neutral-400">自动刷新</span>
            <Badge
              variant="outline"
              className={
                autoRefresh
                  ? "border-green-500/30 text-green-400"
                  : "border-neutral-500/30 text-neutral-400"
              }
            >
              {autoRefresh ? "60s" : "关闭"}
            </Badge>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            className="border-neutral-700 text-neutral-300"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
        </div>
      </div>

      {/* 资源监控大卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* CPU */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/10 rounded-lg">
                  <Cpu className="w-6 h-6 text-blue-500" />
                </div>
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider">CPU 使用率</p>
                  <p className="text-2xl font-bold text-white font-mono">35%</p>
                </div>
              </div>
              <Badge
                variant="outline"
                className="border-green-500/30 text-green-400"
              >
                正常
              </Badge>
            </div>
            <Progress value={35} className="h-3 bg-neutral-800" />
            <div className="mt-3 h-20">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={cpuHistory}>
                  <defs>
                    <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#3b82f6"
                    fill="url(#cpuGradient)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 内存 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-500/10 rounded-lg">
                  <MemoryStick className="w-6 h-6 text-purple-500" />
                </div>
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider">内存使用率</p>
                  <p className="text-2xl font-bold text-white font-mono">68%</p>
                </div>
              </div>
              <Badge
                variant="outline"
                className="border-yellow-500/30 text-yellow-400"
              >
                偏高
              </Badge>
            </div>
            <Progress value={68} className="h-3 bg-neutral-800" />
            <div className="mt-3 h-20">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={memoryHistory}>
                  <defs>
                    <linearGradient id="memGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#a855f7"
                    fill="url(#memGradient)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 磁盘 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-500/10 rounded-lg">
                  <HardDrive className="w-6 h-6 text-orange-500" />
                </div>
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider">磁盘使用率</p>
                  <p className="text-2xl font-bold text-white font-mono">42%</p>
                </div>
              </div>
              <Badge
                variant="outline"
                className="border-green-500/30 text-green-400"
              >
                正常
              </Badge>
            </div>
            <Progress value={42} className="h-3 bg-neutral-800" />
            <div className="mt-3 flex items-center justify-between text-xs text-neutral-500">
              <span>已用: 128.5 GB</span>
              <span>总计: 512 GB</span>
            </div>
            <div className="mt-2 flex items-center justify-between text-xs">
              <span className="text-neutral-400">/data</span>
              <span className="text-white font-mono">98.2 GB</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-neutral-400">/logs</span>
              <span className="text-white font-mono">12.8 GB</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* JBT 进程和通知状态 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* JBT 关键进程状态 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
              <Server className="w-4 h-4 text-orange-500" />
              JBT 关键进程状态
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {jbtProcesses.map((process) => (
                <div
                  key={process.id}
                  className="p-4 bg-neutral-800/50 rounded-lg border border-neutral-800"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(process.status)}
                      <span className="text-white font-medium">{process.name}</span>
                    </div>
                    <Badge variant="outline" className={getStatusColor(process.status)}>
                      {process.status === "running" ? "运行中" : process.status}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-xs text-neutral-500 mb-1">PID</p>
                      <p className="text-white font-mono">{process.pid}</p>
                    </div>
                    <div>
                      <p className="text-xs text-neutral-500 mb-1">运行时长</p>
                      <p className="text-white font-mono">{process.uptime}</p>
                    </div>
                    <div>
                      <p className="text-xs text-neutral-500 mb-1">CPU / 内存</p>
                      <p className="text-white font-mono">
                        {process.cpuUsage}% / {process.memUsage}MB
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-neutral-500 mb-1">最近心跳</p>
                      <p className="text-green-400 font-mono">{process.lastHeartbeat}</p>
                    </div>
                  </div>
                  {process.isSingleInstance && (
                    <div className="mt-2 flex items-center gap-1 text-xs text-neutral-500">
                      <CheckCircle className="w-3 h-3 text-green-500" />
                      单实例运行
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 通知状态面板 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
              <Send className="w-4 h-4 text-orange-500" />
              通知状态面板
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {notificationChannels.map((channel) => (
                <div
                  key={channel.id}
                  className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {channel.type === "feishu" ? (
                      <Zap className="w-4 h-4 text-blue-400" />
                    ) : (
                      <Mail className="w-4 h-4 text-purple-400" />
                    )}
                    <span className="text-sm text-white">{channel.name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-neutral-400 font-mono">
                      {channel.lastSendTime}
                    </span>
                    {channel.lastStatus === "success" ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 日志查看器和数据源新鲜度 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 实时日志查看器 */}
        <Card className="bg-neutral-900 border-neutral-800 lg:col-span-2">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
                <FileText className="w-4 h-4 text-orange-500" />
                实时日志查看器
              </CardTitle>
              <Tabs value={activeLogType} onValueChange={setActiveLogType}>
                <TabsList className="bg-neutral-800 h-8">
                  <TabsTrigger value="all" className="text-xs px-3 py-1">
                    全部
                  </TabsTrigger>
                  <TabsTrigger value="info" className="text-xs px-3 py-1">
                    INFO
                  </TabsTrigger>
                  <TabsTrigger value="warning" className="text-xs px-3 py-1">
                    WARNING
                  </TabsTrigger>
                  <TabsTrigger value="error" className="text-xs px-3 py-1">
                    ERROR
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-80 bg-neutral-950 rounded-lg border border-neutral-800 p-4">
              <div className="space-y-1 font-mono text-xs">
                {filteredLogs.map((log, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <span className="text-neutral-500 whitespace-nowrap">{log.time}</span>
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
                    <span className="text-neutral-500">[{log.source}]</span>
                    <span className={getLogColor(log.level)}>{log.message}</span>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* 采集源新鲜度 */}
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-neutral-300 uppercase tracking-wider flex items-center gap-2">
              <Database className="w-4 h-4 text-orange-500" />
              采集源新鲜度
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-80">
              <div className="space-y-2">
                {dataSourceFreshness.map((source) => (
                  <div
                    key={source.name}
                    className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg"
                  >
                    <div>
                      <p className="text-sm text-white">{source.name}</p>
                      <p className="text-xs text-neutral-500">{source.lastUpdate}</p>
                    </div>
                    <span className={`text-sm font-mono ${getFreshnessColor(source.status)}`}>
                      {source.age}
                    </span>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
