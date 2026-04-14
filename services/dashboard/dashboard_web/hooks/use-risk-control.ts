"use client"

import { useState, useEffect, useCallback } from "react"
import { simTradingApi, type L2Status } from "@/lib/api/sim-trading"
import type { RiskL1 } from "@/lib/api/types"

export function useRiskControl() {
  const [l1Status, setL1Status] = useState<RiskL1 | null>(null)
  const [l2Status, setL2Status] = useState<L2Status | null>(null)
  const [alerts, setAlerts] = useState<Array<{timestamp: string; level: string; message: string}>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      await Promise.allSettled([
        simTradingApi.getRiskL1().then(setL1Status).catch((e) => {
          console.error("Failed to fetch L1 risk:", e)
          setL1Status(null)
        }),
        simTradingApi.getRiskL2().then((res) => setL2Status(res.l2_status)).catch((e) => {
          console.error("Failed to fetch L2 risk:", e)
          setL2Status(null)
        }),
        simTradingApi.getRiskAlerts().then((res) => setAlerts(res.alerts)).catch((e) => {
          console.error("Failed to fetch alerts:", e)
          setAlerts([])
        }),
      ])
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取风控数据失败")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 2000) // 2秒刷新
    return () => clearInterval(interval)
  }, [fetchData])

  return {
    l1Status,
    l2Status,
    alerts,
    loading,
    error,
    refetch: fetchData,
  }
}
