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
      const [accountRes, perfRes, posRes, ordersRes] = await Promise.all([
        simTradingApi.getAccount(),
        simTradingApi.getPerformance(),
        simTradingApi.getPositions(),
        simTradingApi.getOrders(),
      ])
      setAccount(accountRes)
      setPerformance(perfRes)
      setPositions(posRes)
      setOrders(ordersRes)
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
