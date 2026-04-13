"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { simApi, type ExecutionStats } from "@/lib/sim-api"
import { Zap, XCircle, Clock, Ban, AlertTriangle } from "lucide-react"

export function ExecutionQualityKPI() {
  const [stats, setStats] = useState<ExecutionStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await simApi.executionStats()
        setStats(data.execution)
      } catch (err) {
        console.error("获取执行质量统计失败:", err)
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
      label: "平均滑点",
      value: stats.avg_slippage.toFixed(4),
      icon: Zap,
      color: stats.avg_slippage < 0.01 ? "text-green-600" : "text-orange-600",
    },
    {
      label: "拒绝率",
      value: `${stats.rejection_rate.toFixed(1)}%`,
      icon: XCircle,
      color: stats.rejection_rate < 5 ? "text-green-600" : "text-red-600",
    },
    {
      label: "平均延迟",
      value: `${stats.avg_latency_ms.toFixed(0)}ms`,
      icon: Clock,
      color: stats.avg_latency_ms < 100 ? "text-green-600" : "text-orange-600",
    },
    {
      label: "撤单率",
      value: `${stats.cancel_rate.toFixed(1)}%`,
      icon: Ban,
      color: stats.cancel_rate < 10 ? "text-green-600" : "text-orange-600",
    },
    {
      label: "部分成交率",
      value: `${stats.partial_fill_rate.toFixed(1)}%`,
      icon: AlertTriangle,
      color: stats.partial_fill_rate < 5 ? "text-green-600" : "text-orange-600",
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">执行质量 KPI</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-5 gap-4">
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
