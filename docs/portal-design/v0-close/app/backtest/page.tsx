"use client"

import { useState, useEffect } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Input } from "@/components/ui/input"
import {
  LineChart as LineChartIcon,
  Play,
  Pause,
  Trash2,
  Plus,
  CheckCircle,
  Clock,
  AlertCircle,
  Search,
  Filter,
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
import { toast } from "sonner"
import { cn } from "@/lib/utils"

// 策略类型
interface Strategy {
  id: string
  name: string
  status: "running" | "completed" | "failed" | "pending"
  progress: number
  sharpe: number | null
  maxDrawdown: number | null
  winRate: number | null
  totalReturn: number | null
  createdAt: string
}

export default function BacktestPage() {
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")

  // 策略列表
  const [strategies, setStrategies] = useState<Strategy[]>([
    {
      id: "1",
      name: "双均线策略",
      status: "completed",
      progress: 100,
      sharpe: 1.85,
      maxDrawdown: 12.3,
      winRate: 58.5,
      totalReturn: 45.2,
      createdAt: "2024-01-15",
    },
    {
      id: "2",
      name: "动量突破策略",
      status: "running",
      progress: 67,
      sharpe: null,
      maxDrawdown: null,
      winRate: null,
      totalReturn: null,
      createdAt: "2024-01-16",
    },
    {
      id: "3",
      name: "波动率策略",
      status: "pending",
      progress: 0,
      sharpe: null,
      maxDrawdown: null,
      winRate: null,
      totalReturn: null,
      createdAt: "2024-01-16",
    },
    {
      id: "4",
      name: "趋势跟踪策略",
      status: "completed",
      progress: 100,
      sharpe: 2.12,
      maxDrawdown: 8.7,
      winRate: 62.3,
      totalReturn: 68.9,
      createdAt: "2024-01-14",
    },
    {
      id: "5",
      name: "反转策略",
      status: "failed",
      progress: 45,
      sharpe: null,
      maxDrawdown: null,
      winRate: null,
      totalReturn: null,
      createdAt: "2024-01-13",
    },
  ])

  // 权益曲线数据
  const [equityCurve] = useState([
    { date: "01-01", equity: 100000, benchmark: 100000 },
    { date: "01-05", equity: 102500, benchmark: 101000 },
    { date: "01-10", equity: 105800, benchmark: 102500 },
    { date: "01-15", equity: 103200, benchmark: 101800 },
    { date: "01-20", equity: 108500, benchmark: 103000 },
    { date: "01-25", equity: 112000, benchmark: 104500 },
    { date: "01-30", equity: 115800, benchmark: 105000 },
    { date: "02-05", equity: 118500, benchmark: 106200 },
    { date: "02-10", equity: 122000, benchmark: 107500 },
    { date: "02-15", equity: 125300, benchmark: 108000 },
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
      case "running":
        return (
          <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
            <div className="w-2 h-2 bg-blue-500 rounded-full mr-1.5 animate-pulse" />
            运行中
          </Badge>
        )
      case "completed":
        return (
          <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
            <CheckCircle className="w-3 h-3 mr-1" />
            已完成
          </Badge>
        )
      case "failed":
        return (
          <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
            <AlertCircle className="w-3 h-3 mr-1" />
            失败
          </Badge>
        )
      case "pending":
        return (
          <Badge className="bg-muted text-muted-foreground border-border">
            <Clock className="w-3 h-3 mr-1" />
            等待中
          </Badge>
        )
      default:
        return null
    }
  }

  const filteredStrategies = strategies.filter((s) =>
    s.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const runningCount = strategies.filter((s) => s.status === "running").length
  const completedCount = strategies.filter((s) => s.status === "completed").length

  return (
    <MainLayout
      title="策略回测"
      subtitle="策略管理"
      onRefresh={handleRefresh}
      isRefreshing={isRefreshing}
      lastUpdate={lastUpdate}
    >
      <div className="p-4 md:p-6 space-y-6">
        {/* 统计卡片 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-card border-border">
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground mb-1">策略总数</p>
              <p className="text-2xl font-bold text-foreground">{strategies.length}</p>
            </CardContent>
          </Card>
          <Card className="bg-card border-border">
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground mb-1">运行中</p>
              <p className="text-2xl font-bold text-blue-400">{runningCount}</p>
            </CardContent>
          </Card>
          <Card className="bg-card border-border">
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground mb-1">已完成</p>
              <p className="text-2xl font-bold text-green-400">{completedCount}</p>
            </CardContent>
          </Card>
          <Card className="bg-card border-border">
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground mb-1">平均夏普</p>
              <p className="text-2xl font-bold text-orange-400">1.98</p>
            </CardContent>
          </Card>
        </div>

        {/* 权益曲线 */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-base text-foreground flex items-center gap-2">
              <LineChartIcon className="w-4 h-4 text-orange-500" />
              最优策略权益曲线
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={equityCurve}>
                  <defs>
                    <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                    </linearGradient>
                  </defs>
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
                  <Area
                    type="monotone"
                    dataKey="equity"
                    stroke="#f97316"
                    fill="url(#equityGradient)"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="benchmark"
                    stroke="#6b7280"
                    strokeDasharray="4 4"
                    dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 策略列表 */}
        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base text-foreground">策略列表</CardTitle>
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="搜索策略..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 w-48 h-8 bg-accent border-border text-sm text-foreground"
                />
              </div>
              <Button className="bg-orange-500 hover:bg-orange-600 h-8">
                <Plus className="w-4 h-4 mr-1" />
                新建回测
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {filteredStrategies.map((strategy) => (
                <div
                  key={strategy.id}
                  className="flex items-center justify-between p-4 bg-accent/50 rounded-lg border border-border hover:border-border/80 transition-colors"
                >
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center shrink-0">
                      <LineChartIcon className="w-5 h-5 text-blue-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-sm font-medium text-foreground truncate">
                          {strategy.name}
                        </h3>
                        {getStatusBadge(strategy.status)}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        创建于 {strategy.createdAt}
                      </p>
                    </div>
                  </div>

                  {/* 进度或指标 */}
                  {strategy.status === "running" ? (
                    <div className="w-32 mr-6">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-muted-foreground">进度</span>
                        <span className="text-blue-400">{strategy.progress}%</span>
                      </div>
                      <Progress value={strategy.progress} className="h-1.5" />
                    </div>
                  ) : strategy.status === "completed" ? (
                    <div className="flex items-center gap-6 mr-6">
                      <div className="text-center">
                        <p className="text-xs text-muted-foreground mb-0.5">夏普比</p>
                        <p className="text-sm font-semibold text-foreground">
                          {strategy.sharpe?.toFixed(2)}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-muted-foreground mb-0.5">收益率</p>
                        <p
                          className={cn(
                            "text-sm font-semibold",
                            (strategy.totalReturn ?? 0) >= 0
                              ? "text-green-400"
                              : "text-red-400"
                          )}
                        >
                          {(strategy.totalReturn ?? 0) >= 0 ? "+" : ""}
                          {strategy.totalReturn?.toFixed(1)}%
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-muted-foreground mb-0.5">胜率</p>
                        <p className="text-sm font-semibold text-foreground">
                          {strategy.winRate?.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  ) : null}

                  {/* 操作按钮 */}
                  <div className="flex items-center gap-2">
                    {strategy.status === "running" ? (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-muted-foreground hover:text-yellow-500"
                      >
                        <Pause className="w-4 h-4" />
                      </Button>
                    ) : strategy.status === "pending" ? (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-muted-foreground hover:text-green-500"
                      >
                        <Play className="w-4 h-4" />
                      </Button>
                    ) : null}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-red-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
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
