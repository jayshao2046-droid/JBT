"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useMarketData } from "@/hooks/use-market-data"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"

export default function MarketPage() {
  const { ticks, movers, loading } = useMarketData()

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 实时行情 */}
      <Card>
        <CardHeader>
          <CardTitle>实时行情 ({ticks.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {ticks.length === 0 ? (
            <p className="text-muted-foreground text-sm">暂无行情数据</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">合约</th>
                    <th className="text-right p-2">最新价</th>
                    <th className="text-right p-2">买价</th>
                    <th className="text-right p-2">卖价</th>
                    <th className="text-right p-2">成交量</th>
                    <th className="text-right p-2">持仓量</th>
                    <th className="text-right p-2">更新时间</th>
                  </tr>
                </thead>
                <tbody>
                  {ticks.map((tick, idx) => (
                    <tr key={idx} className="border-b hover:bg-muted/50">
                      <td className="p-2 font-medium">{tick.symbol}</td>
                      <td className="text-right p-2">{tick.last_price.toFixed(2)}</td>
                      <td className="text-right p-2 text-green-500">{tick.bid_price.toFixed(2)}</td>
                      <td className="text-right p-2 text-red-500">{tick.ask_price.toFixed(2)}</td>
                      <td className="text-right p-2">{tick.volume.toLocaleString()}</td>
                      <td className="text-right p-2">{tick.open_interest.toLocaleString()}</td>
                      <td className="text-right p-2 text-xs text-muted-foreground">{tick.update_time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 市场异动 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>价格异动</CardTitle>
          </CardHeader>
          <CardContent>
            {movers?.price_movers.length === 0 ? (
              <p className="text-muted-foreground text-sm">暂无数据</p>
            ) : (
              <div className="space-y-2">
                {movers?.price_movers.map((mover, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 border rounded">
                    <div>
                      <p className="font-medium">{mover.symbol}</p>
                      <p className="text-xs text-muted-foreground">{mover.name}</p>
                    </div>
                    <div className="text-right">
                      <p className={`font-medium ${(mover.change_rate || 0) >= 0 ? "text-green-500" : "text-red-500"}`}>
                        {(mover.change_rate || 0) >= 0 ? "+" : ""}{((mover.change_rate || 0) * 100).toFixed(2)}%
                      </p>
                      <p className="text-xs text-muted-foreground">¥{mover.current_price?.toFixed(2)}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>振幅异动</CardTitle>
          </CardHeader>
          <CardContent>
            {movers?.amplitude_movers.length === 0 ? (
              <p className="text-muted-foreground text-sm">暂无数据</p>
            ) : (
              <div className="space-y-2">
                {movers?.amplitude_movers.map((mover, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 border rounded">
                    <div>
                      <p className="font-medium">{mover.symbol}</p>
                      <p className="text-xs text-muted-foreground">{mover.name}</p>
                    </div>
                    <div className="text-right">
                      <Badge variant="outline">{((mover.amplitude || 0) * 100).toFixed(2)}%</Badge>
                      <p className="text-xs text-muted-foreground mt-1">
                        ¥{mover.high?.toFixed(2)} / ¥{mover.low?.toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>成交量异动</CardTitle>
          </CardHeader>
          <CardContent>
            {movers?.volume_movers.length === 0 ? (
              <p className="text-muted-foreground text-sm">暂无数据</p>
            ) : (
              <div className="space-y-2">
                {movers?.volume_movers.map((mover, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 border rounded">
                    <div>
                      <p className="font-medium">{mover.symbol}</p>
                      <p className="text-xs text-muted-foreground">{mover.name}</p>
                    </div>
                    <div className="text-right">
                      <Badge variant="secondary">{(mover.volume_ratio || 0).toFixed(2)}x</Badge>
                      <p className="text-xs text-muted-foreground mt-1">
                        {mover.current_volume?.toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
