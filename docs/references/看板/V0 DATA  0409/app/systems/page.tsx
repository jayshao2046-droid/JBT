"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Server,
  HardDrive,
  Cpu,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  MemoryStick,
  Network,
  RefreshCw,
} from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

export default function SystemStatusPage() {
  const [selectedSystem, setSelectedSystem] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  // 自动刷新机制（60秒）
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      handleRefresh()
    }, 60000)

    return () => clearInterval(interval)
  }, [autoRefresh])

  // CPU 使用率历史
  const cpuHistory = [
    { time: "10:00", value: 32 },
    { time: "10:05", value: 45 },
    { time: "10:10", value: 38 },
    { time: "10:15", value: 52 },
    { time: "10:20", value: 48 },
    { time: "10:25", value: 55 },
    { time: "10:30", value: 42 },
  ]

  // 内存使用率历史
  const memoryHistory = [
    { time: "10:00", value: 62 },
    { time: "10:05", value: 65 },
    { time: "10:10", value: 68 },
    { time: "10:15", value: 64 },
    { time: "10:20", value: 67 },
    { time: "10:25", value: 70 },
    { time: "10:30", value: 68 },
  ]

  // 服务状态
  const services = [
    {
      id: 1,
      name: "CTP行情接口",
      status: "running",
      uptime: "72:14:33",
      requests: 1250000,
      latency: 12,
    },
    {
      id: 2,
      name: "CTP交易接口",
      status: "running",
      uptime: "72:14:30",
      requests: 45000,
      latency: 25,
    },
    {
      id: 3,
      name: "策略引擎",
      status: "running",
      uptime: "168:45:12",
      requests: 2100000,
      latency: 8,
    },
    {
      id: 4,
      name: "回测引擎",
      status: "running",
      uptime: "48:22:15",
      requests: 890000,
      latency: 45,
    },
    {
      id: 5,
      name: "数据库服务",
      status: "running",
      uptime: "720:15:48",
      requests: 5200000,
      latency: 5,
    },
    {
      id: 6,
      name: "风控服务",
      status: "warning",
      uptime: "24:08:30",
      requests: 320000,
      latency: 85,
    },
  ]

  // 系统日志
  const systemLogs = [
    "2025-06-25 14:32:15 [INFO] 回测任务 BT-2025-048 已完成",
    "2025-06-25 14:15:42 [INFO] CTP 行情连接成功，已接收 1.2M 条数据",
    "2025-06-25 13:58:20 [WARNING] 策略引擎内存使用率达到 85%，监控中",
    "2025-06-25 13:45:30 [INFO] 风控告警系统已启用，阈值: 20%",
    "2025-06-25 13:30:15 [ERROR] 回测任务 BT-2025-046 执行失败: 参数错误",
    "2025-06-25 13:15:42 [INFO] 数据同步完成，已更新 850 条记录",
    "2025-06-25 13:00:08 [INFO] 策略 STR-001 日内交易 156 笔，收益 +2.3%",
    "2025-06-25 12:45:33 [WARNING] 网络延迟升高至 45ms，正在优化路由",
  ]

  const handleRefresh = () => {
    setIsLoading(true)
    setTimeout(() => {
      setLastUpdate(new Date())
      setIsLoading(false)
    }, 500)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-green-500/20 text-green-400"
      case "warning":
        return "bg-yellow-500/20 text-yellow-400"
      case "error":
        return "bg-red-500/20 text-red-400"
      default:
        return "bg-neutral-500/20 text-neutral-300"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "running":
        return <CheckCircle className="w-4 h-4" />
      case "warning":
        return <AlertTriangle className="w-4 h-4" />
      case "error":
        return <AlertTriangle className="w-4 h-4" />
      default:
        return <Activity className="w-4 h-4" />
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* 头部 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wider">系统状态</h1>
          <p className="text-sm text-neutral-400">监控本地资源使用情况和服务状态</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? "bg-green-600 hover:bg-green-700" : "bg-neutral-700 hover:bg-neutral-600"}
            variant={autoRefresh ? "default" : "outline"}
          >
            <Clock className="w-4 h-4 mr-2" />
            {autoRefresh ? "自动刷新中" : "自动刷新关闭"}
          </Button>
          <Button
            onClick={handleRefresh}
            variant="outline"
            className="border-neutral-700 text-neutral-400 hover:bg-neutral-800"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* 更新时间戳 */}
      <div className="text-xs text-neutral-500 text-right">
        最后更新: {lastUpdate.toLocaleString("zh-CN")}
      </div>

      {/* 资源概览 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-neutral-400 tracking-wider">CPU 使用率</p>
              <Cpu className="w-4 h-4 text-white" />
            </div>
            <p className="text-2xl font-bold text-white font-mono mb-2">45%</p>
            <Progress value={45} className="h-2 bg-neutral-800" />
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-neutral-400 tracking-wider">内存使用率</p>
              <MemoryStick className="w-4 h-4 text-white" />
            </div>
            <p className="text-2xl font-bold text-white font-mono mb-2">68%</p>
            <Progress value={68} className="h-2 bg-neutral-800" />
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-neutral-400 tracking-wider">磁盘使用率</p>
              <HardDrive className="w-4 h-4 text-white" />
            </div>
            <p className="text-2xl font-bold text-white font-mono mb-2">42%</p>
            <Progress value={42} className="h-2 bg-neutral-800" />
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-neutral-400 tracking-wider">网络延迟</p>
              <Network className="w-4 h-4 text-white" />
            </div>
            <p className="text-2xl font-bold text-white font-mono mb-2">12ms</p>
            <p className="text-xs text-green-400">正常</p>
          </CardContent>
        </Card>
      </div>

      {/* CPU 和内存趋势 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">CPU 使用率趋势</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={cpuHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                  <XAxis dataKey="time" stroke="#737373" />
                  <YAxis stroke="#737373" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1f2937",
                      border: "1px solid #404040",
                      borderRadius: "4px",
                    }}
                    labelStyle={{ color: "#fff" }}
                  />
                  <Line type="monotone" dataKey="value" stroke="#f97316" dot={false} isAnimationActive={true} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">内存使用率趋势</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={memoryHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                  <XAxis dataKey="time" stroke="#737373" />
                  <YAxis stroke="#737373" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1f2937",
                      border: "1px solid #404040",
                      borderRadius: "4px",
                    }}
                    labelStyle={{ color: "#fff" }}
                  />
                  <Line type="monotone" dataKey="value" stroke="#3b82f6" dot={false} isAnimationActive={true} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 服务状态 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">服务状态</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">服务名称</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">状态</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">运行时长</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">请求数</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">延迟 (ms)</th>
                </tr>
              </thead>
              <tbody>
                {services.map((service, index) => (
                  <tr
                    key={service.id}
                    className={`border-b border-neutral-800 hover:bg-neutral-800 transition-colors cursor-pointer ${
                      index % 2 === 0 ? "bg-neutral-900" : "bg-neutral-850"
                    }`}
                    onClick={() => setSelectedSystem(service)}
                  >
                    <td className="py-3 px-4 text-white">{service.name}</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className={getStatusColor(service.status)}>
                          {getStatusIcon(service.status)}
                        </div>
                        <Badge className={getStatusColor(service.status)}>
                          {service.status === "running" ? "运行中" : service.status === "warning" ? "警告" : "错误"}
                        </Badge>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-neutral-300 font-mono">{service.uptime}</td>
                    <td className="py-3 px-4 text-white font-mono">{service.requests.toLocaleString()}</td>
                    <td className={`py-3 px-4 font-mono ${service.latency > 50 ? "text-red-400" : "text-green-400"}`}>
                      {service.latency}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* 系统日志 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">系统日志</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-black rounded border border-neutral-800 p-4 h-64 overflow-y-auto font-mono text-xs space-y-1">
            {systemLogs.map((log, index) => {
              const isError = log.includes("[ERROR]")
              const isWarning = log.includes("[WARNING]")
              const color = isError ? "text-red-400" : isWarning ? "text-yellow-400" : "text-green-400"

              return (
                <div key={index} className={color}>
                  {log}
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* 服务详情模态框 */}
      {selectedSystem && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedSystem(null)}
          onKeyDown={(e) => {
            if (e.key === "Escape") setSelectedSystem(null)
          }}
        >
          <Card className="bg-neutral-900 border-neutral-700 w-full max-w-md">
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle className="text-lg font-bold text-white">{selectedSystem.name}</CardTitle>
                <Button
                  variant="ghost"
                  onClick={() => setSelectedSystem(null)}
                  className="text-neutral-400 hover:text-white"
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-xs text-neutral-500 mb-1">服务状态</p>
                <Badge className={getStatusColor(selectedSystem.status)}>
                  {selectedSystem.status === "running" ? "运行中" : selectedSystem.status === "warning" ? "警告" : "错误"}
                </Badge>
              </div>
              <div>
                <p className="text-xs text-neutral-500 mb-1">运行时长</p>
                <p className="text-sm text-white font-mono">{selectedSystem.uptime}</p>
              </div>
              <div>
                <p className="text-xs text-neutral-500 mb-1">请求数</p>
                <p className="text-sm text-white font-mono">{selectedSystem.requests.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs text-neutral-500 mb-1">平均延迟</p>
                <p className={`text-sm font-mono ${selectedSystem.latency > 50 ? "text-red-400" : "text-green-400"}`}>
                  {selectedSystem.latency}ms
                </p>
              </div>
              <Button className="bg-orange-500 hover:bg-orange-600 text-white w-full">
                查看详细日志
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
