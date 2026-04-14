"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface MarketMoversProps {
  movers: Array<{
    symbol: string
    name: string
    current_price?: number
    change_rate?: number
  }>
}

export function MarketMovers({ movers }: MarketMoversProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>涨跌排行</CardTitle>
      </CardHeader>
      <CardContent>
        {movers.length === 0 ? (
          <p className="text-muted-foreground text-sm">暂无数据</p>
        ) : (
          <div className="space-y-2">
            {movers.map((mover, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 border rounded">
                <div>
                  <p className="font-medium">{mover.symbol}</p>
                  <p className="text-xs text-muted-foreground">{mover.name}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm">¥{mover.current_price?.toFixed(2)}</p>
                  <Badge variant={(mover.change_rate || 0) >= 0 ? "default" : "secondary"}>
                    {(mover.change_rate || 0) >= 0 ? "+" : ""}{((mover.change_rate || 0) * 100).toFixed(2)}%
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
