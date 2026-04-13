"use client"

import { useState, useEffect } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Brain,
  Cpu,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Activity,
  Zap,
  Eye,
  BarChart3,
} from "lucide-react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from "recharts"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

// 信号类型
interface Signal {
  id: string
  symbol: string
  direction: "long" | "short"
  confidence: number
  model: string
  time: string
  status: "pending" | "executed" | "rejected"
}

export default function DecisionPage() {
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // 模型状态
  const [localModelsReady] = useState(true)
  const [onlineModelsReady] = useState(true)
  const [researchWindowOpen] = useState(false)

  // 信号列表
  const [signals] = useState<Signal[]>([
    { id: "1", symbol: "RB2405", direction: "long", confidence: 85, model: "TrendL1", time: "14:32:15", status: "executed" },
    { id: "2", symbol: "IF2403", direction: "short", confidence: 72, model: "MomentumL2", time: "14:28:45", status: "pending" },
    { id: "3", symbol: "AU2406", direction: "long", confidence: 68, model: "TrendL1", time: "14:25:30", status: "rejected" },
    { id: "4", symbol: "CU2405", direction: "short", confidence: 91, model: "VolatilityL3", time: "14:20:00", status: "executed" },
    { id: "5", symbol: "AG2406", direction: "long", confidence: 78, model: "TrendL1", time: "14:15:20", status: "pending" },
  ])

  // 模型性能数据
  const [modelPerformance] = useState([
    { name: "TrendL1", accuracy: 72, signals: 45 },
    { name: "MomentumL2", accuracy: 68, signals: 32 },
    { name: "VolatilityL3", accuracy: 81, signals: 28 },
    { name: "PatternL1", accuracy: 65, signals: 21 },
    { name: "HybridL2", accuracy: 75, signals: 18 },
  ])

  // 信号分布数据
  const [signalDistribution] = useState([
    { hour: "09:00", long: 5, short: 3 },
    { hour: "10:00", long: 8, short: 6 },
    { hour: "11:00", long: 4, short: 7 },
    { hour: "13:30", long: 6, short: 4 },
    { hour: "14:00", long: 9, short: 5 },
    { hour: "14:30", long: 7, short: 8 },
  ])

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => {
      setLastUpdate(new Date())
      setIsRefreshing(false)
      toast.success("数据已刷新")
    }, 1000)
  }

  useEffect(() => {
    setLastUpdate(new Date())
  }, [])

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "executed":
        return (
          <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
            已执行
          </Badge>
        )
      case "pending":
        return (
          <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
            待处理
          </Badge>
        )
      case "rejected":
        return (
          <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
            已拒绝
          </Badge>
        )
      default:
        return null
    }
  }

  const todaySignals = signals.length
  const executedSignals = signals.filter((s) => s.status === "executed").length
  const avgConfidence = Math.round(
    signals.reduce((sum, s) => sum + s.confidence, 0) / signals.length
  )

  return (
    <MainLayout
      title="智能决策"
      subtitle="总览"
      onRefresh={handleRefresh}
      isRefreshing={isRefreshing}
      lastUpdate={lastUpdate}
    >
      <div className="p-4 md:p-6 space-y-6">
        {/* 模型状态卡片 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-card border-border">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">本地模型</p>
                  <p
                    className={cn(
                      "text-lg font-semibold",
                      localModelsReady ? "text-green-400" : "text-red-400"
                    )}
                  >
                    {localModelsReady ? "就绪" : "离线"}
                  </p>
                </div>
                <div
                  className={cn(
                    "w-3 h-3 rounded-full",
                    localModelsReady ? "bg-green-500" : "bg-red-500"
                  )}
                />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">在线模型</p>
                  <p
                    className={cn(
                      "text-lg font-semibold",
                      onlineModelsReady ? "text-blue-400" : "text-muted-foreground"
                    )}
                  >
                    {onlineModelsReady ? "连接" : "未配置"}
                  </p>
                </div>
                <div
                  className={cn(
                    "w-3 h-3 rounded-full",
                    onlineModelsReady ? "bg-blue-500" : "bg-muted-foreground"
                  )}
                />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">研究窗口</p>
                  <p
                    className={cn(
                      "text-lg font-semibold",
                      researchWindowOpen ? "text-orange-400" : "text-muted-foreground"
                    )}
                  >
                    {researchWindowOpen ? "开启" : "关闭"}
                  </p>
                </div>
                <div
                  className={cn(
                    "w-3 h-3 rounded-full",
                    researchWindowOpen ? "bg-orange-500" : "bg-muted-foreground"
                  )}
                />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">今日信号</p>
                  <p className="text-lg font-semibold text-foreground">{todaySignals}</p>
                </div>
                <Activity className="w-6 h-6 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 统计指标 */}
        <div className="grid grid-cols-3 gap-4">
          <Card className="bg-card border-border">
            <CardContent className="p-4 text-center">
              <Zap className="w-6 h-6 text-orange-500 mx-auto mb-2" />
              <p className="text-2xl font-bold text-foreground">{todaySignals}</p>
              <p className="text-xs text-muted-foreground">今日信号总数</p>
            </CardContent>
          </Card>
          <Card className="bg-card border-border">
            <CardContent className="p-4 text-center">
              <CheckCircle className="w-6 h-6 text-green-500 mx-auto mb-2" />
              <p className="text-2xl font-bold text-green-400">{executedSignals}</p>
              <p className="text-xs text-muted-foreground">已执行信号</p>
            </CardContent>
          </Card>
          <Card className="bg-card border-border">
            <CardContent className="p-4 text-center">
              <Brain className="w-6 h-6 text-purple-500 mx-auto mb-2" />
              <p className="text-2xl font-bold text-purple-400">{avgConfidence}%</p>
              <p className="text-xs text-muted-foreground">平均置信度</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 模型性能 */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-base text-foreground flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-purple-500" />
                模型准确率
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={modelPerformance} layout="vertical">
                    <CartesianGrid stroke="transparent" />
                    <XAxis type="number" domain={[0, 100]} stroke="#737373" />
                    <YAxis dataKey="name" type="category" stroke="#737373" width={100} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f2937",
                        border: "1px solid #404040",
                        borderRadius: "4px",
                      }}
                      labelStyle={{ color: "#fff" }}
                    />
                    <Bar dataKey="accuracy" radius={[0, 4, 4, 0]}>
                      {modelPerformance.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.accuracy >= 75 ? "#22c55e" : entry.accuracy >= 65 ? "#eab308" : "#ef4444"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* 信号分布 */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-base text-foreground flex items-center gap-2">
                <Activity className="w-4 h-4 text-purple-500" />
                信号时间分布
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={signalDistribution}>
                    <CartesianGrid stroke="transparent" />
                    <XAxis dataKey="hour" stroke="#737373" />
                    <YAxis stroke="#737373" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f2937",
                        border: "1px solid #404040",
                        borderRadius: "4px",
                      }}
                      labelStyle={{ color: "#fff" }}
                    />
                    <Bar dataKey="long" fill="#22c55e" name="做多" />
                    <Bar dataKey="short" fill="#ef4444" name="做空" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 最新信号列表 */}
        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base text-foreground flex items-center gap-2">
              <Zap className="w-4 h-4 text-purple-500" />
              最新信号
            </CardTitle>
            <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
              <Eye className="w-4 h-4 mr-1" />
              查看全部
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {signals.map((signal) => (
                <div
                  key={signal.id}
                  className="flex items-center justify-between p-3 bg-accent/50 rounded-lg border border-border"
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={cn(
                        "w-10 h-10 rounded-lg flex items-center justify-center",
                        signal.direction === "long"
                          ? "bg-green-500/10"
                          : "bg-red-500/10"
                      )}
                    >
                      {signal.direction === "long" ? (
                        <TrendingUp className="w-5 h-5 text-green-500" />
                      ) : (
                        <TrendingDown className="w-5 h-5 text-red-500" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-foreground font-medium">{signal.symbol}</span>
                        <Badge
                          variant="outline"
                          className={cn(
                            "text-xs",
                            signal.direction === "long"
                              ? "border-green-500/50 text-green-400"
                              : "border-red-500/50 text-red-400"
                          )}
                        >
                          {signal.direction === "long" ? "做多" : "做空"}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {signal.model} | {signal.time}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-xs text-muted-foreground">置信度</p>
                      <p
                        className={cn(
                          "text-sm font-semibold",
                          signal.confidence >= 80
                            ? "text-green-400"
                            : signal.confidence >= 60
                              ? "text-yellow-400"
                              : "text-red-400"
                        )}
                      >
                        {signal.confidence}%
                      </p>
                    </div>
                    {getStatusBadge(signal.status)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
