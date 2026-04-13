"use client"

import { useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, Activity } from "lucide-react"

interface Trade {
  instrument_id: string
  direction: string
  volume: number
  price: number
  timestamp: string
  pnl?: number
}

interface TradeHeatmapProps {
  trades: Trade[]
}

export function TradeHeatmap({ trades }: TradeHeatmapProps) {
  // 按小时统计交易活跃度
  const hourlyActivity = useMemo(() => {
    const activity: Record<number, { count: number; volume: number; pnl: number }> = {}

    for (let i = 0; i < 24; i++) {
      activity[i] = { count: 0, volume: 0, pnl: 0 }
    }

    trades.forEach(trade => {
      const hour = new Date(trade.timestamp).getHours()
      activity[hour].count += 1
      activity[hour].volume += trade.volume
      activity[hour].pnl += trade.pnl || 0
    })

    return activity
  }, [trades])

  // 按品种统计交易频率
  const symbolActivity = useMemo(() => {
    const activity: Record<string, { count: number; volume: number; pnl: number }> = {}

    trades.forEach(trade => {
      const symbol = trade.instrument_id.replace(/\d+/, "")
      if (!activity[symbol]) {
        activity[symbol] = { count: 0, volume: 0, pnl: 0 }
      }
      activity[symbol].count += 1
      activity[symbol].volume += trade.volume
      activity[symbol].pnl += trade.pnl || 0
    })

    return Object.entries(activity)
      .sort((a, b) => b[1].count - a[1].count)
      .slice(0, 10)
  }, [trades])

  const maxHourlyCount = Math.max(...Object.values(hourlyActivity).map(h => h.count), 1)

  const getHeatColor = (count: number) => {
    const intensity = count / maxHourlyCount
    if (intensity === 0) return "bg-secondary"
    if (intensity < 0.25) return "bg-blue-200 dark:bg-blue-900"
    if (intensity < 0.5) return "bg-blue-400 dark:bg-blue-700"
    if (intensity < 0.75) return "bg-blue-600 dark:bg-blue-500"
    return "bg-blue-800 dark:bg-blue-300"
  }

  return (
    <div className="space-y-4">
      {/* 时段热力图 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="h-4 w-4" />
            交易时段热力图
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-12 gap-1">
            {Object.entries(hourlyActivity).map(([hour, data]) => (
              <div
                key={hour}
                className={`aspect-square rounded flex flex-col items-center justify-center text-xs ${getHeatColor(
                  data.count
                )}`}
                title={`${hour}:00 - ${data.count} 笔交易, ${data.volume} 手, ${data.pnl.toFixed(
                  0
                )} 元`}
              >
                <div className="font-medium">{hour}</div>
                {data.count > 0 && <div className="text-[10px]">{data.count}</div>}
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between mt-4 text-xs text-muted-foreground">
            <span>活跃度</span>
            <div className="flex gap-1">
              <div className="w-4 h-4 bg-secondary rounded" />
              <span>低</span>
              <div className="w-4 h-4 bg-blue-400 dark:bg-blue-700 rounded" />
              <div className="w-4 h-4 bg-blue-600 dark:bg-blue-500 rounded" />
              <div className="w-4 h-4 bg-blue-800 dark:bg-blue-300 rounded" />
              <span>高</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 品种交易频率 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">品种交易频率 Top 10</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {symbolActivity.map(([symbol, data], index) => (
              <div key={symbol} className="flex items-center gap-3">
                <div className="w-6 text-sm text-muted-foreground">#{index + 1}</div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{symbol}</span>
                    <div className="flex items-center gap-2 text-sm">
                      <span>{data.count} 笔</span>
                      <Badge variant={data.pnl >= 0 ? "default" : "destructive"}>
                        {data.pnl >= 0 ? (
                          <TrendingUp className="h-3 w-3 mr-1" />
                        ) : (
                          <TrendingDown className="h-3 w-3 mr-1" />
                        )}
                        {data.pnl.toFixed(0)}
                      </Badge>
                    </div>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full"
                      style={{
                        width: `${(data.count / symbolActivity[0][1].count) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
