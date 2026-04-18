"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { simTradingApi } from "@/lib/api/sim-trading"
import type { DailyReport } from "@/lib/api/types"

export function DailyReportCard() {
  const [report, setReport] = useState<DailyReport | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const data = await simTradingApi.getDailyReport()
        setReport(data)
      } catch (err) {
        console.error("Failed to fetch daily report:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchReport()
    const interval = setInterval(fetchReport, 60000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>今日摘要</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground">加载中...</div>
        </CardContent>
      </Card>
    )
  }

  if (!report) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>今日摘要</CardTitle>
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
        <CardTitle>今日摘要</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex justify-between">
          <span className="text-muted-foreground">交易次数</span>
          <span className="font-medium">{report.trade_count || 0}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">今日盈亏</span>
          <span className={`font-medium ${(report.pnl || 0) >= 0 ? "text-green-600" : "text-red-600"}`}>
            ¥{report.pnl?.toFixed(2) || "0.00"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">日期</span>
          <span className="font-medium text-muted-foreground">{report.date}</span>
        </div>
      </CardContent>
    </Card>
  )
}
