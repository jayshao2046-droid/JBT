"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { simApi, type PerformanceStats } from "@/lib/sim-api"
import { TrendingUp, TrendingDown, Activity, Target } from "lucide-react"

export function PerformanceKPI() {
  const [stats, setStats] = useState<PerformanceStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await simApi.performanceStats()
        setStats(data.performance)
      } catch (err) {
        console.error("获取绩效统计失败:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 10000) // 每 10 秒刷新
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return <div className="text-sm text-muted-foreground">加载中...</div>
  }

  if (!stats) {
    return <div className="text-sm text-muted-foreground">暂无数据</div>
  }

  const kpis = [
    {
      label: "胜率",
      value: `${stats.win_rate.toFixed(1)}%`,
      icon: Target,
      color: stats.win_rate >= 50 ? "text-red-600" : "text-green-600",
    },
    {
      label: "盈亏比",
      value: stats.profit_loss_ratio.toFixed(2),
      icon: Activity,
      color: stats.profit_loss_ratio >= 1 ? "text-red-600" : "text-green-600",
    },
    {
      label: "最大回撤",
      value: `${stats.max_drawdown.toFixed(2)}%`,
      icon: TrendingDown,
      color: "text-green-600",
    },
    {
      label: "夏普比率",
      value: stats.sharpe_ratio.toFixed(2),
      icon: TrendingUp,
      color: stats.sharpe_ratio >= 1 ? "text-red-600" : "text-muted-foreground",
    },
    {
      label: "今日盈亏",
      value: `¥${stats.today_pnl.toFixed(2)}`,
      icon: Activity,
      color: stats.today_pnl >= 0 ? "text-red-600" : "text-green-600",
    },
    {
      label: "本周盈亏",
      value: `¥${stats.week_pnl.toFixed(2)}`,
      icon: Activity,
      color: stats.week_pnl >= 0 ? "text-red-600" : "text-green-600",
    },
    {
      label: "本月盈亏",
      value: `¥${stats.month_pnl.toFixed(2)}`,
      icon: Activity,
      color: stats.month_pnl >= 0 ? "text-red-600" : "text-green-600",
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">交易绩效 KPI</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-4">
          {kpis.map((kpi) => {
            const Icon = kpi.icon
            return (
              <div key={kpi.label} className="flex flex-col space-y-1">
                <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                  <Icon className="h-3 w-3" />
                  <span>{kpi.label}</span>
                </div>
                <div className={`text-lg font-semibold ${kpi.color}`}>{kpi.value}</div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
