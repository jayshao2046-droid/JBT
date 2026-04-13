"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface Signal {
  symbol: string
  signal_type: "breakout" | "volume_spike"
  price: number
  triggered_at: string
}

export function IntradaySignal({ refreshToken }: { refreshToken?: number }) {
  const [signals, setSignals] = useState<Signal[]>([])

  const fetchSignals = async () => {
    try {
      const res = await fetch("/api/decision/v1/stock/intraday/signals")
      const data = await res.json()
      setSignals(data)
    } catch (error) {
      console.error("Failed to fetch signals:", error)
    }
  }

  useEffect(() => {
    fetchSignals()
    const interval = setInterval(fetchSignals, 10000) // 每10秒刷新
    return () => clearInterval(interval)
  }, [refreshToken])

  const getSignalBadge = (type: string) => {
    if (type === "breakout") {
      return <Badge className="bg-green-600 text-white">突破</Badge>
    }
    return <Badge className="bg-orange-600 text-white">放量</Badge>
  }

  return (
    <Card className="bg-neutral-900 border-neutral-800">
      <CardHeader>
        <CardTitle className="text-white">盘中信号</CardTitle>
        <p className="text-sm text-neutral-400">
          实时监控 · 每10秒刷新 · {signals.length} 个信号
        </p>
      </CardHeader>
      <CardContent>
        {signals.length === 0 ? (
          <p className="text-neutral-500 text-center py-8">暂无信号</p>
        ) : (
          <div className="space-y-3">
            {signals.map((signal, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 bg-neutral-950 rounded border border-neutral-800"
              >
                <div className="flex items-center gap-3">
                  {getSignalBadge(signal.signal_type)}
                  <span className="text-white font-mono">{signal.symbol}</span>
                </div>
                <div className="text-right">
                  <div className="text-white font-semibold">
                    ¥{signal.price.toFixed(2)}
                  </div>
                  <div className="text-xs text-neutral-500">
                    {new Date(signal.triggered_at).toLocaleTimeString("zh-CN")}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
