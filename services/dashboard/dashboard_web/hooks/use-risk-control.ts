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
      const [l1Res, l2Res, alertsRes] = await Promise.all([
        simTradingApi.getRiskL1(),
        simTradingApi.getRiskL2(),
        simTradingApi.getRiskAlerts(),
      ])
      setL1Status(l1Res)
      setL2Status(l2Res.l2_status)
      setAlerts(alertsRes.alerts)
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
