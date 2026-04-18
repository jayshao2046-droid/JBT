"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import { billingApi, type BillingRecord } from "@/lib/api/billing"

export function CostTrendChart() {
  const [data, setData] = useState<BillingRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await billingApi.getRecords(50)
        setData(res.records || [])
      } catch (err) {
        console.error("Failed to fetch records:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>成本趋势</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[400px] flex items-center justify-center text-muted-foreground">
            加载中...
          </div>
        </CardContent>
      </Card>
    )
  }

  const chartData = data.map((record) => ({
    time: new Date(record.timestamp).toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
    }),
    input_cost: record.input_cost,
    output_cost: record.output_cost,
    total_cost: record.total_cost,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>成本趋势（最近 50 次调用）</CardTitle>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="h-[400px] flex items-center justify-center text-muted-foreground">
            暂无数据
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip formatter={(value: number) => `¥${value.toFixed(4)}`} />
              <Legend />
              <Bar dataKey="input_cost" fill="#8884d8" name="输入成本" />
              <Bar dataKey="output_cost" fill="#82ca9d" name="输出成本" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
