"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart3, TrendingUp } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from "recharts"

interface SignalDistributionChartProps {
  signals: any[]
}

export function SignalDistributionChart({ signals }: SignalDistributionChartProps) {
  // 按日期分组统计信号数量
  const timeDistribution = signals.reduce((acc: any, signal) => {
    const date = signal.created_at?.split("T")[0] || "未知"
    if (!acc[date]) {
      acc[date] = { date, buy: 0, sell: 0, hold: 0 }
    }
    if (signal.signal > 0) acc[date].buy++
    else if (signal.signal < 0) acc[date].sell++
    else acc[date].hold++
    return acc
  }, {})

  const timeData = Object.values(timeDistribution).slice(-30) // 最近30天

  // 按信号类型统计
  const typeDistribution = [
    { name: "买入", value: signals.filter((s) => s.signal > 0).length, fill: "#22c55e" },
    { name: "卖出", value: signals.filter((s) => s.signal < 0).length, fill: "#ef4444" },
    { name: "持有", value: signals.filter((s) => s.signal === 0).length, fill: "#6b7280" },
  ]

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-foreground flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-500" />
            信号时间分布
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timeData}>
              <CartesianGrid stroke="transparent" />
              <XAxis dataKey="date" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{ backgroundColor: "transparent", border: "none" }}
                labelStyle={{ color: "#fff" }}
              />
              <Legend />
              <Line type="monotone" dataKey="buy" stroke="#22c55e" name="买入" />
              <Line type="monotone" dataKey="sell" stroke="#ef4444" name="卖出" />
              <Line type="monotone" dataKey="hold" stroke="#6b7280" name="持有" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-foreground flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-500" />
            信号类型分布
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={typeDistribution}>
              <CartesianGrid stroke="transparent" />
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{ backgroundColor: "transparent", border: "none" }}
                labelStyle={{ color: "#fff" }}
              />
              <Bar dataKey="value" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
