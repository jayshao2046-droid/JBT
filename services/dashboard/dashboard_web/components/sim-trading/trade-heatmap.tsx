"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface TradeHeatmapProps {
  data: Array<{
    hour: number
    count: number
    pnl: number
  }>
}

export function TradeHeatmap({ data }: TradeHeatmapProps) {
  const maxCount = Math.max(...data.map(d => d.count), 1)

  return (
    <Card>
      <CardHeader>
        <CardTitle>交易热力图</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <p className="text-muted-foreground text-sm">暂无数据</p>
        ) : (
          <div className="grid grid-cols-12 gap-1">
            {data.map((item, idx) => (
              <div
                key={idx}
                className="aspect-square rounded flex items-center justify-center text-xs"
                style={{
                  backgroundColor: `rgba(59, 130, 246, ${item.count / maxCount})`,
                  color: item.count / maxCount > 0.5 ? "white" : "inherit",
                }}
                title={`${item.hour}:00 - ${item.count}笔 - ¥${item.pnl.toFixed(2)}`}
              >
                {item.hour}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
