"use client"

import { useState, useEffect, useCallback } from "react"
import { simTradingApi, type TickData, type MarketMover } from "@/lib/api/sim-trading"

export function useMarketData() {
  const [ticks, setTicks] = useState<TickData[]>([])
  const [movers, setMovers] = useState<{
    price_movers: MarketMover[]
    amplitude_movers: MarketMover[]
    volume_movers: MarketMover[]
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      await Promise.allSettled([
        simTradingApi.getTicks().then((res) => setTicks(res.ticks)).catch((e) => {
          console.error("Failed to fetch ticks:", e)
          setTicks([])
        }),
        simTradingApi.getMarketMovers(10).then((res) => setMovers(res.movers)).catch((e) => {
          console.error("Failed to fetch movers:", e)
          setMovers({ price_movers: [], amplitude_movers: [], volume_movers: [] })
        }),
      ])
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取行情数据失败")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 1000) // 1秒刷新
    return () => clearInterval(interval)
  }, [fetchData])

  return {
    ticks,
    movers,
    loading,
    error,
    refetch: fetchData,
  }
}
