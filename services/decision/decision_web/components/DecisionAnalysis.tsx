"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart3, Calendar, TrendingUp } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

interface DecisionAnalysisProps {
  decisions: any[]
}

export function DecisionAnalysis({ decisions }: DecisionAnalysisProps) {
  // 月度信号热力图数据
  const monthlyData = decisions.reduce((acc: any, d) => {
    const month = d.created_at?.substring(0, 7) || "未知"
    if (!acc[month]) {
      acc[month] = { month, count: 0, avgReturn: 0, totalReturn: 0 }
    }
    acc[month].count++
    acc[month].totalReturn += d.return || 0
    return acc
  }, {})

  const monthlyChartData = Object.values(monthlyData).map((m: any) => ({
    month: m.month,
    count: m.count,
    avgReturn: (m.totalReturn / m.count).toFixed(2),
  }))

  // 年度收益对比
  const yearlyData = decisions.reduce((acc: any, d) => {
    const year = d.created_at?.substring(0, 4) || "未知"
    if (!acc[year]) {
      acc[year] = { year, totalReturn: 0, count: 0 }
    }
    acc[year].totalReturn += d.return || 0
    acc[year].count++
    return acc
  }, {})

  const yearlyChartData = Object.values(yearlyData).map((y: any) => ({
    year: y.year,
    totalReturn: (y.totalReturn * 100).toFixed(2),
    avgReturn: ((y.totalReturn / y.count) * 100).toFixed(2),
  }))

  return (
    <div className="space-y-6">
      <Card className="bg-neutral-800 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-500" />
            月度信号热力图
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={monthlyChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="month" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151" }}
                labelStyle={{ color: "#fff" }}
              />
              <Bar dataKey="count" fill="#3b82f6" name="信号数量" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="bg-neutral-800 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-500" />
            年度收益对比
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={yearlyChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="year" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151" }}
                labelStyle={{ color: "#fff" }}
              />
              <Bar dataKey="totalReturn" fill="#22c55e" name="总收益率 (%)" />
              <Bar dataKey="avgReturn" fill="#f59e0b" name="平均收益率 (%)" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
