"use client"

import { useState, useEffect, useCallback } from "react"
import { simTradingApi } from "@/lib/api/sim-trading"
import type { AccountInfo, PerformanceStats, Position, Order } from "@/lib/api/types"

export function useSimTrading() {
  const [account, setAccount] = useState<AccountInfo | null>(null)
  const [performance, setPerformance] = useState<PerformanceStats | null>(null)
  const [positions, setPositions] = useState<Position[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      await Promise.allSettled([
        simTradingApi.getAccount().then(setAccount).catch((e) => {
          console.error("Failed to fetch account:", e)
          setAccount(null)
        }),
        simTradingApi.getPerformance().then(setPerformance).catch((e) => {
          console.error("Failed to fetch performance:", e)
          setPerformance(null)
        }),
        simTradingApi.getPositions().then(setPositions).catch((e) => {
          console.error("Failed to fetch positions:", e)
          setPositions([])
        }),
        simTradingApi.getOrders().then(setOrders).catch((e) => {
          console.error("Failed to fetch orders:", e)
          setOrders([])
        }),
      ])
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取数据失败")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 3000) // 3秒刷新
    return () => clearInterval(interval)
  }, [fetchData])

  return {
    account,
    performance,
    positions,
    orders,
    loading,
    error,
    refetch: fetchData,
  }
}
