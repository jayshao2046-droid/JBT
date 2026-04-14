"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useSignals } from "@/hooks/use-signals"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

export function SignalDistributionChart() {
  const { overview, loading, error } = useSignals()

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
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="hsl(var(--primary))" />
          </BarChart>
        </ResponsiveContainer>

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
