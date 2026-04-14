"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, TrendingDown } from "lucide-react"

interface PerformanceKpiProps {
  data: {
    win_rate: number
    profit_loss_ratio: number
    max_drawdown: number
    sharpe_ratio: number
    today_pnl: number
    week_pnl: number
    month_pnl: number
  } | null
}

export function PerformanceKpi({ data }: PerformanceKpiProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>绩效统计</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">暂无数据</p>
        </CardContent>
      </Card>
    )
  }

  const metrics = [
    { label: "胜率", value: `${(data.win_rate * 100).toFixed(1)}%`, trend: data.win_rate >= 0.5 },
    { label: "盈亏比", value: data.profit_loss_ratio.toFixed(2), trend: data.profit_loss_ratio >= 1 },
    { label: "最大回撤", value: `${(data.max_drawdown * 100).toFixed(2)}%`, trend: data.max_drawdown <= 0.1 },
    { label: "夏普比率", value: data.sharpe_ratio.toFixed(2), trend: data.sharpe_ratio >= 1 },
    { label: "今日盈亏", value: `¥${data.today_pnl.toFixed(2)}`, trend: data.today_pnl >= 0 },
    { label: "本周盈亏", value: `¥${data.week_pnl.toFixed(2)}`, trend: data.week_pnl >= 0 },
    { label: "本月盈亏", value: `¥${data.month_pnl.toFixed(2)}`, trend: data.month_pnl >= 0 },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>绩效统计</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {metrics.map((metric, idx) => (
            <div key={idx} className="p-3 border rounded">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">{metric.label}</p>
                {metric.trend ? (
                  <TrendingUp className="w-4 h-4 text-green-500" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-500" />
                )}
              </div>
              <p className={`text-lg font-bold mt-1 ${metric.trend ? "text-green-500" : "text-red-500"}`}>
                {metric.value}
              </p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
