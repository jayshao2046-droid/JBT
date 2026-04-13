"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  ShieldAlert,
  AlertTriangle,
  TrendingDown,
  Activity,
  Zap,
  DollarSign,
  BarChart2,
  Bell,
  CheckCircle,
  XCircle,
  RefreshCw,
  Clock,
} from "lucide-react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

export default function RiskControlPage() {
  const [selectedAlert, setSelectedAlert] = useState(null)
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

  // 风险指标数据
  const riskMetrics = {
    totalRisk: 35,
    marginUsage: 42,
    dailyDrawdown: 2.3,
    weeklyDrawdown: 4.5,
    maxPositionRisk: 28,
    volatilityIndex: 18,
  }

  // 回撤历史数据
  const drawdownHistory = [
    { date: "06/01", value: -1.2 },
    { date: "06/05", value: -2.8 },
    { date: "06/10", value: -1.5 },
    { date: "06/15", value: -3.2 },
    { date: "06/20", value: -2.1 },
    { date: "06/25", value: -2.3 },
  ]

  // 策略风险评级
  const strategyRisks = [
    {
      id: "STR-001",
      name: "均线突破策略",
      grade: "A",
      score: 92,
      maxDrawdown: -8.2,
      sharpeRatio: 1.85,
    },
    {
      id: "STR-002",
      name: "布林带反转策略",
      grade: "C",
      score: 65,
      maxDrawdown: -12.5,
      sharpeRatio: -0.35,
    },
    {
      id: "STR-003",
      name: "MACD动量策略",
      grade: "A",
      score: 88,
      maxDrawdown: -6.8,
      sharpeRatio: 2.12,
    },
    {
      id: "STR-004",
      name: "RSI超卖策略",
      grade: "B",
      score: 78,
      maxDrawdown: -5.2,
      sharpeRatio: 1.65,
    },
  ]

  // 风控告警
  const alerts = [
    {
      id: 1,
      level: "严重",
      message: "布林带策略单日回撤超过10%，触发风控告警",
      time: "2025/06/25 14:32",
      status: "active",
    },
    {
      id: 2,
      level: "警告",
      message: "账户保证金使用率达到42%，建议关注后续行情",
      time: "2025/06/25 12:15",
      status: "active",
    },
    {
      id: 3,
      level: "提醒",
      message: "均线策略今日成交笔数过少，交易信号不足",
      time: "2025/06/25 10:30",
      status: "active",
    },
    {
      id: 4,
      level: "已解决",
      message: "RSI超卖策略回撤恢复到正常水平",
      time: "2025/06/25 09:45",
      status: "resolved",
    },
  ]

  const handleRefresh = () => {
    setIsLoading(true)
    setTimeout(() => {
      setLastUpdate(new Date())
      setIsLoading(false)
    }, 500)
  }

  const getAlertColor = (level: string) => {
    switch (level) {
      case "严重":
        return "bg-red-900/20 border-red-600/50 text-red-400"
      case "警告":
        return "bg-yellow-900/20 border-yellow-600/50 text-yellow-400"
      case "提醒":
        return "bg-blue-900/20 border-blue-600/50 text-blue-400"
      case "已解决":
        return "bg-green-900/20 border-green-600/50 text-green-400"
      default:
        return "bg-neutral-900/20 border-neutral-600/50 text-neutral-400"
    }
  }

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case "A":
        return "bg-green-500/20 text-green-400"
      case "B":
        return "bg-blue-500/20 text-blue-400"
      case "C":
        return "bg-red-500/20 text-red-400"
      default:
        return "bg-neutral-500/20 text-neutral-300"
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* 头部 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wider">风控监控</h1>
          <p className="text-sm text-neutral-400">实时风险指标、告警和策略评级</p>
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

      {/* 风险概览 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">综合风险度</p>
                <p className="text-2xl font-bold text-orange-500 font-mono">{riskMetrics.totalRisk}%</p>
              </div>
              <ShieldAlert className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">保证金使用率</p>
                <p className="text-2xl font-bold text-white font-mono">{riskMetrics.marginUsage}%</p>
              </div>
              <DollarSign className="w-8 h-8 text-white" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">日内回撤</p>
                <p className="text-2xl font-bold text-red-400 font-mono">-{riskMetrics.dailyDrawdown}%</p>
              </div>
              <TrendingDown className="w-8 h-8 text-red-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">周间回撤</p>
                <p className="text-2xl font-bold text-red-400 font-mono">-{riskMetrics.weeklyDrawdown}%</p>
              </div>
              <TrendingDown className="w-8 h-8 text-red-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">持仓风险</p>
                <p className="text-2xl font-bold text-yellow-500 font-mono">{riskMetrics.maxPositionRisk}%</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">波动率指数</p>
                <p className="text-2xl font-bold text-blue-400 font-mono">{riskMetrics.volatilityIndex}</p>
              </div>
              <Zap className="w-8 h-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 回撤历史 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">回撤历史</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={drawdownHistory}>
                <CartesianGrid stroke="transparent" />
                <XAxis dataKey="date" stroke="#737373" />
                <YAxis stroke="#737373" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #404040",
                    borderRadius: "4px",
                  }}
                  labelStyle={{ color: "#fff" }}
                />
                <Bar dataKey="value" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* 持仓风险分布和风控告警 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">持仓风险分布</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-neutral-400">高风险持仓</span>
                <span className="text-sm text-red-400 font-mono">28%</span>
              </div>
              <Progress value={28} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-neutral-400">中等风险持仓</span>
                <span className="text-sm text-yellow-400 font-mono">45%</span>
              </div>
              <Progress value={45} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-neutral-400">低风险持仓</span>
                <span className="text-sm text-green-400 font-mono">27%</span>
              </div>
              <Progress value={27} className="h-2" />
            </div>
          </CardContent>
        </Card>

        {/* 风控告警 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">风控告警</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 max-h-80 overflow-y-auto">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`border rounded p-3 cursor-pointer transition-colors ${getAlertColor(alert.level)}`}
                onClick={() => setSelectedAlert(alert)}
              >
                <div className="flex items-start gap-2">
                  {alert.status === "resolved" ? (
                    <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{alert.message}</p>
                    <p className="text-xs text-opacity-70 mt-1">{alert.time}</p>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* 策略风险评级 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">策略风险评级</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">策略ID</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">策略名称</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">评级</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">评分</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">最大回撤</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">夏普比率</th>
                </tr>
              </thead>
              <tbody>
                {strategyRisks.map((strategy, index) => (
                  <tr
                    key={strategy.id}
                    className={`border-b border-neutral-800 ${index % 2 === 0 ? "bg-neutral-900" : "bg-neutral-850"}`}
                  >
                    <td className="py-3 px-4 text-white font-mono">{strategy.id}</td>
                    <td className="py-3 px-4 text-white">{strategy.name}</td>
                    <td className="py-3 px-4">
                      <Badge className={getGradeColor(strategy.grade)}>{strategy.grade}级</Badge>
                    </td>
                    <td className="py-3 px-4 text-white font-mono">{strategy.score}</td>
                    <td className="py-3 px-4 text-red-400 font-mono">{strategy.maxDrawdown}%</td>
                    <td className="py-3 px-4 text-white font-mono">{strategy.sharpeRatio.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* 告警详情模态框 */}
      {selectedAlert && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedAlert(null)}
          onKeyDown={(e) => {
            if (e.key === "Escape") setSelectedAlert(null)
          }}
        >
          <Card className="bg-neutral-900 border-neutral-700 w-full max-w-md">
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle className="text-lg font-bold text-white">{selectedAlert.level}告警</CardTitle>
                <Button
                  variant="ghost"
                  onClick={() => setSelectedAlert(null)}
                  className="text-neutral-400 hover:text-white"
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-white">{selectedAlert.message}</p>
              <p className="text-sm text-neutral-400">{selectedAlert.time}</p>
              <Button className="bg-orange-500 hover:bg-orange-600 text-white w-full">
                查看详情
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
