"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, TrendingDown } from "lucide-react"

interface PerformanceKpiProps {
  data: {
    total_return: number
    sharpe_ratio: number
    max_drawdown: number
    win_rate: number
    total_trades: number
  } | null
}

export function PerformanceKpi({ data }: PerformanceKpiProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>绩效指标</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">暂无数据</p>
        </CardContent>
      </Card>
    )
  }

  const metrics = [
    { label: "总收益", value: `${(data.total_return * 100).toFixed(2)}%`, trend: data.total_return >= 0 },
    { label: "夏普比率", value: data.sharpe_ratio.toFixed(2), trend: data.sharpe_ratio >= 1 },
    { label: "最大回撤", value: `${(data.max_drawdown * 100).toFixed(2)}%`, trend: data.max_drawdown <= 0.1 },
    { label: "胜率", value: `${(data.win_rate * 100).toFixed(1)}%`, trend: data.win_rate >= 0.5 },
    { label: "交易次数", value: data.total_trades.toString(), trend: true },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>绩效指标</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
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
