"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { simTradingApi, type ExecutionStats } from "@/lib/api/sim-trading"

export function ExecutionQualityCard() {
  const [stats, setStats] = useState<ExecutionStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await simTradingApi.getExecutionStats()
        setStats(res.execution)
      } catch (err) {
        console.error("Failed to fetch execution stats:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>执行质量</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground">加载中...</div>
        </CardContent>
      </Card>
    )
  }

  if (!stats) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>执行质量</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground">暂无数据</div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>执行质量统计</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span className="text-muted-foreground">平均滑点</span>
          <span className="font-medium">{stats.avg_slippage?.toFixed(2) || "N/A"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">拒单率</span>
          <span className="font-medium">{stats.rejection_rate ? `${(stats.rejection_rate * 100).toFixed(1)}%` : "N/A"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">平均延迟</span>
          <span className="font-medium">{stats.avg_latency_ms?.toFixed(0) || "N/A"} ms</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">撤单率</span>
          <span className="font-medium">{stats.cancel_rate ? `${(stats.cancel_rate * 100).toFixed(1)}%` : "N/A"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">部分成交率</span>
          <span className="font-medium">{stats.partial_fill_rate ? `${(stats.partial_fill_rate * 100).toFixed(1)}%` : "N/A"}</span>
        </div>
      </CardContent>
    </Card>
  )
}
