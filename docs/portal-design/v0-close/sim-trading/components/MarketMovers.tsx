"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { simApi, type MarketMover } from "@/lib/sim-api"
import { TrendingUp, TrendingDown, Activity } from "lucide-react"

export function MarketMovers() {
  const [movers, setMovers] = useState<{
    price_movers: MarketMover[]
    amplitude_movers: MarketMover[]
    volume_movers: MarketMover[]
  } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchMovers = async () => {
      try {
        const data = await simApi.marketMovers(10)
        setMovers(data.movers)
      } catch (err) {
        console.error("获取市场异动失败:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchMovers()
    const interval = setInterval(fetchMovers, 30000) // 每 30 秒刷新
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return <div className="text-sm text-muted-foreground">加载中...</div>
  }

  if (!movers) {
    return <div className="text-sm text-muted-foreground">暂无数据</div>
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">市场异动监控</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="price">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="price">涨速</TabsTrigger>
            <TabsTrigger value="amplitude">振幅</TabsTrigger>
            <TabsTrigger value="volume">成交量</TabsTrigger>
          </TabsList>

          <TabsContent value="price" className="space-y-2">
            {movers.price_movers.map((mover, idx) => (
              <div
                key={mover.symbol}
                className="flex items-center justify-between p-2 rounded hover:bg-accent"
              >
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-muted-foreground w-4">{idx + 1}</span>
                  <div>
                    <div className="text-sm font-medium">{mover.symbol}</div>
                    <div className="text-xs text-muted-foreground">{mover.name}</div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm">¥{mover.current_price?.toFixed(2)}</span>
                  <div
                    className={`flex items-center ${
                      (mover.change_rate || 0) >= 0 ? "text-red-600" : "text-green-600"
                    }`}
                  >
                    {(mover.change_rate || 0) >= 0 ? (
                      <TrendingUp className="h-3 w-3 mr-1" />
                    ) : (
                      <TrendingDown className="h-3 w-3 mr-1" />
                    )}
                    <span className="text-sm font-semibold">
                      {Math.abs(mover.change_rate || 0).toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </TabsContent>

          <TabsContent value="amplitude" className="space-y-2">
            {movers.amplitude_movers.map((mover, idx) => (
              <div
                key={mover.symbol}
                className="flex items-center justify-between p-2 rounded hover:bg-accent"
              >
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-muted-foreground w-4">{idx + 1}</span>
                  <div>
                    <div className="text-sm font-medium">{mover.symbol}</div>
                    <div className="text-xs text-muted-foreground">{mover.name}</div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-muted-foreground">
                    {mover.low?.toFixed(2)} - {mover.high?.toFixed(2)}
                  </span>
                  <div className="flex items-center text-orange-600">
                    <Activity className="h-3 w-3 mr-1" />
                    <span className="text-sm font-semibold">{mover.amplitude?.toFixed(2)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </TabsContent>

          <TabsContent value="volume" className="space-y-2">
            {movers.volume_movers.map((mover, idx) => (
              <div
                key={mover.symbol}
                className="flex items-center justify-between p-2 rounded hover:bg-accent"
              >
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-muted-foreground w-4">{idx + 1}</span>
                  <div>
                    <div className="text-sm font-medium">{mover.symbol}</div>
                    <div className="text-xs text-muted-foreground">{mover.name}</div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-muted-foreground">
                    {mover.current_volume?.toLocaleString()}
                  </span>
                  <div className="flex items-center text-blue-600">
                    <TrendingUp className="h-3 w-3 mr-1" />
                    <span className="text-sm font-semibold">{mover.volume_ratio?.toFixed(2)}x</span>
                  </div>
                </div>
              </div>
            ))}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
