"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import { billingApi, type BillingRecord } from "@/lib/api/billing"

export function TokenUsageChart() {
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
          <CardTitle>Token 消费趋势</CardTitle>
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
    input: record.input_tokens,
    output: record.output_tokens,
    total: record.input_tokens + record.output_tokens,
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Token 消费趋势（最近 50 次调用）</CardTitle>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="h-[400px] flex items-center justify-center text-muted-foreground">
            暂无数据
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="input" stroke="#8884d8" name="输入 Token" />
              <Line type="monotone" dataKey="output" stroke="#82ca9d" name="输出 Token" />
              <Line type="monotone" dataKey="total" stroke="#ffc658" name="总计" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
