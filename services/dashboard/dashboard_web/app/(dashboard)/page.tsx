"use client"

import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"
import { useDashboardData } from "@/hooks/use-dashboard-data"
import { KpiCard } from "@/components/dashboard/kpi-card"
import { CurrentPositions } from "@/components/dashboard/current-positions"
import { StrategySignals } from "@/components/dashboard/strategy-signals"
import { RealTimeRisk } from "@/components/dashboard/real-time-risk"
import { DataSourceStatus } from "@/components/dashboard/data-source-status"
import { NewsList } from "@/components/dashboard/news-list"
import { TrendingUp, DollarSign, Activity, AlertTriangle } from "lucide-react"

export default function DashboardPage() {
  const { account, performance, risk, positions, signals, collectors, news, loading, error } =
    useDashboardData()

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="p-6">
            <p className="text-red-400">{error}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const kpiData = [
    {
      title: "总权益",
      value: account?.equity || 0,
      icon: DollarSign,
      change: performance ? `${performance.daily_pnl >= 0 ? "+" : ""}${performance.daily_pnl}` : undefined,
      changeType: performance && performance.daily_pnl >= 0 ? ("positive" as const) : ("negative" as const),
      status: "success" as const,
    },
    {
      title: "可用资金",
      value: account?.available || 0,
      icon: TrendingUp,
      status: "default" as const,
    },
    {
      title: "浮动盈亏",
      value: account?.float_pnl || 0,
      icon: Activity,
      changeType: account && account.float_pnl >= 0 ? ("positive" as const) : ("negative" as const),
      status: account && account.float_pnl >= 0 ? ("success" as const) : ("danger" as const),
    },
    {
      title: "保证金占用",
      value: account?.margin || 0,
      icon: AlertTriangle,
      progress: risk ? risk.position_usage * 100 : 0,
      description: "占总权益",
      status: risk && risk.position_usage > 0.8 ? ("danger" as const) : ("warning" as const),
    },
  ]

  const riskMetrics = [
    {
      label: "保证金使用率",
      value: risk ? Math.round(risk.position_usage * 100) : 0,
      unit: "%",
      status: risk && risk.position_usage > 0.8 ? ("danger" as const) : ("normal" as const),
      description: "占总权益",
    },
    {
      label: "当日回撤",
      value: risk ? Math.abs(risk.drawdown) : 0,
      unit: "¥",
      status: "normal" as const,
      description: "最大回撤",
    },
    {
      label: "VaR风险值",
      value: risk ? Math.abs(risk.var_1d) : 0,
      unit: "¥",
      status: "normal" as const,
      description: "单日风险敞口",
    },
  ]

  return (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiData.map((kpi, idx) => (
          <KpiCard key={idx} {...kpi} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CurrentPositions positions={positions} />
        <StrategySignals signals={signals} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <RealTimeRisk metrics={riskMetrics} />
        <DataSourceStatus dataSources={collectors} />
        <NewsList news={news} />
      </div>
    </div>
  )
}
