'use client'

import { useState, useEffect } from "react"
import Link from "next/link"
import {
  TrendingUp,
  LineChart,
  Brain,
  Database,
  AlertTriangle,
  Activity,
  Zap,
  BarChart3,
  Calendar,
  RefreshCw,
  ChevronRight,
} from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import { KPICard } from "@/components/dashboard/kpi-card"
import { ChurnChart } from "@/components/dashboard/churn-chart"
import { CurrentPositions } from "@/components/dashboard/current-positions"
import { TodayTradingSummary } from "@/components/dashboard/today-trading-summary"
import { StrategySignals } from "@/components/dashboard/strategy-signals"
import { RealTimeRiskIndicators } from "@/components/dashboard/real-time-risk"
import { DataSourceStatusComponent } from "@/components/dashboard/data-source-status"
import { NewsList } from "@/components/dashboard/news-list"
import {
  mockKPIData,
  mockChurnData,
  mockPositions,
  mockSignals,
  mockDataSources,
  mockNews,
} from "@/lib/mock-data"

// 模块状态类型
interface ModuleStatus {
  id: string
  name: string
  icon: React.ElementType
  color: string
  bgColor: string
  borderColor: string
  status: "online" | "offline" | "warning"
  statusText: string
  stats: { label: string; value: string }[]
  href: string
}

// 系统指标
interface SystemMetrics {
  cpu: number
  memory: number
  disk: number
  network: "good" | "fair" | "poor"
  uptime: string
}

// 告警类型
interface Alert {
  id: string
  type: "error" | "warning" | "info"
  module: string
  message: string
  time: string
}

export default function DashboardPage() {
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    cpu: 23,
    memory: 45,
    disk: 62,
    network: "good",
    uptime: "12天 5小时",
  })

  const [alerts] = useState<Alert[]>([
    {
      id: "1",
      type: "warning",
      module: "模拟交易",
      message: "CTP 行情连接延迟较高 (>100ms)",
      time: "2分钟前",
    },
    {
      id: "2",
      type: "info",
      module: "策略回测",
      message: "回测任务 #1234 已完成",
      time: "15分钟前",
    },
    {
      id: "3",
      type: "error",
      module: "数据采集",
      message: "采集器 sina_quotes 连接失败",
      time: "1小时前",
    },
  ])

  const modules: ModuleStatus[] = [
    {
      id: "sim-trading",
      name: "模拟交易",
      icon: TrendingUp,
      color: "text-orange-500",
      bgColor: "bg-orange-500/10",
      borderColor: "border-orange-500/30",
      status: "online",
      statusText: "交易中",
      stats: [
        { label: "持仓品种", value: "5" },
        { label: "今日盈亏", value: "+¥12,580" },
        { label: "风控状态", value: "正常" },
      ],
      href: "/sim-trading",
    },
    {
      id: "backtest",
      name: "策略回测",
      icon: LineChart,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
      borderColor: "border-blue-500/30",
      status: "online",
      statusText: "空闲",
      stats: [
        { label: "策略数量", value: "12" },
        { label: "运行中", value: "0" },
        { label: "今日完成", value: "3" },
      ],
      href: "/backtest",
    },
    {
      id: "decision",
      name: "智能决策",
      icon: Brain,
      color: "text-purple-500",
      bgColor: "bg-purple-500/10",
      borderColor: "border-purple-500/30",
      status: "online",
      statusText: "就绪",
      stats: [
        { label: "本地模型", value: "3" },
        { label: "在线模型", value: "2" },
        { label: "今日信号", value: "18" },
      ],
      href: "/decision",
    },
    {
      id: "data",
      name: "数据采集",
      icon: Database,
      color: "text-cyan-500",
      bgColor: "bg-cyan-500/10",
      borderColor: "border-cyan-500/30",
      status: "warning",
      statusText: "部分异常",
      stats: [
        { label: "采集器", value: "8/10" },
        { label: "今日数据", value: "1.2GB" },
        { label: "队列积压", value: "0" },
      ],
      href: "/data",
    },
  ]

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => {
      setLastUpdate(new Date())
      setIsRefreshing(false)
    }, 1000)
  }

  useEffect(() => {
    setLastUpdate(new Date())
  }, [])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "online":
        return <div className="w-2 h-2 bg-green-500 rounded-full" />
      case "offline":
        return <div className="w-2 h-2 bg-red-500 rounded-full" />
      case "warning":
        return <div className="w-2 h-2 bg-yellow-500 rounded-full" />
      default:
        return null
    }
  }

  const getNetworkStatus = (status: string) => {
    switch (status) {
      case "good":
        return { color: "text-green-500", text: "良好" }
      case "fair":
        return { color: "text-yellow-500", text: "一般" }
      case "poor":
        return { color: "text-red-500", text: "较差" }
      default:
        return { color: "text-muted-foreground", text: "未知" }
    }
  }

  return (
    <MainLayout
      title="总控台"
      onRefresh={handleRefresh}
      isRefreshing={isRefreshing}
      lastUpdate={lastUpdate}
    >
      <div className="p-4 md:p-6 space-y-6">
        {/* 12 个核心 KPI 指标 */}
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-orange-500" />
            核心 KPI 指标
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {mockKPIData.map((kpi) => (
              <KPICard key={kpi.id} data={kpi} />
            ))}
          </div>
        </div>

        {/* 收益表 + 当前持仓 (60% + 40%) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ChurnChart data={mockChurnData} />
          </div>
          <div>
            <CurrentPositions positions={mockPositions.slice(0, 3)} />
          </div>
        </div>

        {/* 今日交易汇总 + 策略信号 (50% + 50%) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TodayTradingSummary />
          <StrategySignals signals={mockSignals} />
        </div>

        {/* 实时风险指标 + 数据源状态 (50% + 50%) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RealTimeRiskIndicators />
          <DataSourceStatusComponent dataSources={mockDataSources} />
        </div>

        {/* 新闻模块 (60% + 40%) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <NewsList news={mockNews.slice(0, 10)} title="重大新闻" />
          </div>
          <div>
            <NewsList news={mockNews.slice(5, 12)} title="全球新闻" />
          </div>
        </div>

        {/* ���端模块卡片 */}
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-orange-500" />
            核心模块
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {modules.map((module) => {
              const Icon = module.icon
              return (
                <Link key={module.id} href={module.href}>
                  <Card
                    className={cn(
                      "bg-card border transition-all duration-200 hover:scale-[1.02] cursor-pointer group",
                      module.borderColor
                    )}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={cn("p-2 rounded-lg", module.bgColor)}>
                            <Icon className={cn("w-5 h-5", module.color)} />
                          </div>
                          <CardTitle className="text-base text-foreground">
                            {module.name}
                          </CardTitle>
                        </div>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(module.status)}
                          <span
                            className={cn(
                              "text-xs font-medium",
                              module.status === "online"
                                ? "text-green-500"
                                : module.status === "warning"
                                  ? "text-yellow-500"
                                  : "text-red-500"
                            )}
                          >
                            {module.statusText}
                          </span>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-2">
                      <div className="grid grid-cols-3 gap-2">
                        {module.stats.map((stat, idx) => (
                          <div key={idx} className="text-center">
                            <p className="text-xs text-muted-foreground mb-0.5">
                              {stat.label}
                            </p>
                            <p
                              className={cn(
                                "text-sm font-semibold",
                                stat.value.startsWith("+")
                                  ? "text-red-500"
                                  : stat.value.startsWith("-")
                                    ? "text-green-500"
                                    : "text-foreground"
                              )}
                            >
                              {stat.value}
                            </p>
                          </div>
                        ))}
                      </div>
                      <div className="mt-4 flex items-center justify-end text-xs text-muted-foreground group-hover:text-orange-500 transition-colors">
                        进入模块
                        <ChevronRight className="w-4 h-4 ml-1" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              )
            })}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 系统资源监控 */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-base text-foreground flex items-center gap-2">
                <Zap className="w-4 h-4 text-orange-500" />
                系统资源
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-muted-foreground">CPU 使用率</span>
                  <span className="text-foreground font-mono">{systemMetrics.cpu}%</span>
                </div>
                <Progress value={systemMetrics.cpu} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-muted-foreground">内存使用率</span>
                  <span className="text-foreground font-mono">{systemMetrics.memory}%</span>
                </div>
                <Progress value={systemMetrics.memory} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-muted-foreground">磁盘使用率</span>
                  <span className="text-foreground font-mono">{systemMetrics.disk}%</span>
                </div>
                <Progress value={systemMetrics.disk} className="h-2" />
              </div>
            </CardContent>
          </Card>

          {/* 告警中心 */}
          <Card className="bg-card border-border lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base text-foreground flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-yellow-500" />
                告警中心
              </CardTitle>
              <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                查看全部
              </Button>
            </CardHeader>
            <CardContent>
              {alerts.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">暂无告警</div>
              ) : (
                <div className="space-y-3">
                  {alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="flex items-start gap-3 p-3 bg-accent/50 rounded-lg"
                    >
                      <div
                        className={cn(
                          "w-2 h-2 mt-1.5 rounded-full shrink-0",
                          alert.type === "error"
                            ? "bg-red-500"
                            : alert.type === "warning"
                              ? "bg-yellow-500"
                              : "bg-blue-500"
                        )}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-xs text-muted-foreground font-medium">{alert.module}</span>
                          <span className="text-xs text-muted-foreground">{alert.time}</span>
                        </div>
                        <p className="text-sm text-foreground">{alert.message}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* 快捷操作 */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-base text-foreground flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-orange-500" />
              快捷操作
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
              <Link href="/backtest">
                <Button
                  variant="outline"
                  className="w-full h-auto py-4 flex flex-col gap-2 bg-accent/50 border-border hover:bg-accent hover:border-orange-500/50 text-muted-foreground hover:text-foreground"
                >
                  <LineChart className="w-5 h-5 text-orange-500" />
                  <span className="text-xs">新建回测</span>
                </Button>
              </Link>
              <Link href="/sim-trading">
                <Button
                  variant="outline"
                  className="w-full h-auto py-4 flex flex-col gap-2 bg-accent/50 border-border hover:bg-accent hover:border-orange-500/50 text-muted-foreground hover:text-foreground"
                >
                  <TrendingUp className="w-5 h-5 text-orange-500" />
                  <span className="text-xs">查看持仓</span>
                </Button>
              </Link>
              <Link href="/decision/signal">
                <Button
                  variant="outline"
                  className="w-full h-auto py-4 flex flex-col gap-2 bg-accent/50 border-border hover:bg-accent hover:border-orange-500/50 text-muted-foreground hover:text-foreground"
                >
                  <Brain className="w-5 h-5 text-orange-500" />
                  <span className="text-xs">信号审查</span>
                </Button>
              </Link>
              <Link href="/data/explorer">
                <Button
                  variant="outline"
                  className="w-full h-auto py-4 flex flex-col gap-2 bg-accent/50 border-border hover:bg-accent hover:border-orange-500/50 text-muted-foreground hover:text-foreground"
                >
                  <Database className="w-5 h-5 text-orange-500" />
                  <span className="text-xs">数据浏览</span>
                </Button>
              </Link>
              <Link href="/settings">
                <Button
                  variant="outline"
                  className="w-full h-auto py-4 flex flex-col gap-2 bg-accent/50 border-border hover:bg-accent hover:border-orange-500/50 text-muted-foreground hover:text-foreground"
                >
                  <Calendar className="w-5 h-5 text-orange-500" />
                  <span className="text-xs">系统设置</span>
                </Button>
              </Link>
              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col gap-2 bg-accent/50 border-border hover:bg-accent hover:border-orange-500/50 text-muted-foreground hover:text-foreground"
                onClick={handleRefresh}
              >
                <RefreshCw className={cn("w-5 h-5 text-orange-500", isRefreshing && "animate-spin")} />
                <span className="text-xs">刷新数据</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
