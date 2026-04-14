"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useSignals } from "@/hooks/use-signals"
import { useEffect, useState } from "react"

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ChartComponents = Record<string, any>

export function SignalDistributionChart() {
  const { overview, loading, error } = useSignals()
  const [Chart, setChart] = useState<ChartComponents | null>(null)

  useEffect(() => {
    import("recharts").then((mod) => {
      setChart({
        BarChart: mod.BarChart,
        Bar: mod.Bar,
        XAxis: mod.XAxis,
        YAxis: mod.YAxis,
        CartesianGrid: mod.CartesianGrid,
        Tooltip: mod.Tooltip,
        ResponsiveContainer: mod.ResponsiveContainer,
      })
    })
  }, [])

  if (loading) {
    return <div className="text-muted-foreground">加载中...</div>
  }

  if (error) {
    return <div className="text-destructive">错误: {error}</div>
  }

  if (!overview || !overview.stage_counts || overview.stage_counts.length === 0) {
    return <div className="text-muted-foreground">暂无数据</div>
  }

  const chartData = overview.stage_counts.map((item) => ({
    name: item.label,
    count: item.count,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>信号分布</CardTitle>
      </CardHeader>
      <CardContent>
        {Chart ? (
          <Chart.ResponsiveContainer width="100%" height={300}>
            <Chart.BarChart data={chartData}>
              <Chart.CartesianGrid strokeDasharray="3 3" />
              <Chart.XAxis dataKey="name" />
              <Chart.YAxis />
              <Chart.Tooltip />
              <Chart.Bar dataKey="count" fill="hsl(var(--primary))" />
            </Chart.BarChart>
          </Chart.ResponsiveContainer>
        ) : (
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            加载图表中...
          </div>
        )}

        <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
          {overview.stage_counts.map((item) => (
            <div key={item.key} className="flex justify-between">
              <span className="text-muted-foreground">{item.label}:</span>
              <span className="font-medium">{item.count}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
