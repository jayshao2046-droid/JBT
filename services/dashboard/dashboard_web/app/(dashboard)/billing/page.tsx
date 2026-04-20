"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { TokenUsageChart } from "@/components/billing/TokenUsageChart"
import { CostTrendChart } from "@/components/billing/CostTrendChart"
import { UsageBreakdown } from "@/components/billing/UsageBreakdown"
import { billingApi } from "@/lib/api/billing"

interface BillingSummary {
  hourly: {
    hour: string
    total_tokens: number
    total_cost: number
    by_model: Record<string, { tokens: number; cost: number }>
  }
  daily: {
    date: string
    total_tokens: number
    total_cost: number
    by_model: Record<string, { tokens: number; cost: number }>
    budget_progress?: number
  }
}

export default function BillingPage() {
  const [summary, setSummary] = useState<BillingSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [hourly, daily] = await Promise.all([
          billingApi.getHourlySummary(),
          billingApi.getDailySummary(),
        ])
        setSummary({ hourly, daily })
      } catch (err) {
        console.error("Failed to fetch billing data:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">LLM 计费统计</h1>
        <div className="text-muted-foreground">加载中...</div>
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">LLM 计费统计</h1>
        <div className="text-muted-foreground">暂无数据</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">LLM 计费统计</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>当前小时</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary.hourly.total_tokens.toLocaleString()} tokens
            </div>
            <div className="text-sm text-muted-foreground">
              ¥{summary.hourly.total_cost.toFixed(2)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>今日累计</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary.daily.total_tokens.toLocaleString()} tokens
            </div>
            <div className="text-sm text-muted-foreground">
              ¥{summary.daily.total_cost.toFixed(2)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>预算进度</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary.daily.budget_progress
                ? `${(summary.daily.budget_progress * 100).toFixed(1)}%`
                : "N/A"}
            </div>
            <div className="text-sm text-muted-foreground">今日预算使用</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="usage" className="space-y-4">
        <TabsList>
          <TabsTrigger value="usage">Token 消费</TabsTrigger>
          <TabsTrigger value="cost">成本趋势</TabsTrigger>
          <TabsTrigger value="breakdown">用量详情</TabsTrigger>
        </TabsList>

        <TabsContent value="usage" className="space-y-4">
          <TokenUsageChart />
        </TabsContent>

        <TabsContent value="cost" className="space-y-4">
          <CostTrendChart />
        </TabsContent>

        <TabsContent value="breakdown" className="space-y-4">
          <UsageBreakdown />
        </TabsContent>
      </Tabs>
    </div>
  )
}
