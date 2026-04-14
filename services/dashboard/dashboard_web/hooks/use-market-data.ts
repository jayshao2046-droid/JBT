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
      const [ticksRes, moversRes] = await Promise.all([
        simTradingApi.getTicks(),
        simTradingApi.getMarketMovers(10),
      ])
      setTicks(ticksRes.ticks)
      setMovers(moversRes.movers)
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
