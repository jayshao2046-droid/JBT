"use client"

import { useCallback, useEffect, useState } from "react"
import { simTradingApi } from "@/lib/api/sim-trading"
import type { AccountInfo, PerformanceStats, RiskL1 } from "@/lib/api/types"

export function useDashboardKpis(intervalMs = 30000) {
  const [account, setAccount] = useState<AccountInfo | null>(null)
  const [performance, setPerformance] = useState<PerformanceStats | null>(null)
  const [risk, setRisk] = useState<RiskL1 | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  const fetchKpis = useCallback(async () => {
    const [accountResult, performanceResult, riskResult] = await Promise.allSettled([
      simTradingApi.getAccount(),
      simTradingApi.getPerformance(),
      simTradingApi.getRiskL1(),
    ])

    if (accountResult.status === "fulfilled") {
      setAccount(accountResult.value)
    }

    if (performanceResult.status === "fulfilled") {
      setPerformance(performanceResult.value)
    }

    if (riskResult.status === "fulfilled") {
      setRisk(riskResult.value)
    }

    if (
      accountResult.status === "fulfilled" ||
      performanceResult.status === "fulfilled" ||
      riskResult.status === "fulfilled"
    ) {
      setLastUpdate(new Date())
    }
  }, [])

  useEffect(() => {
    void fetchKpis()
    const timer = setInterval(() => {
      void fetchKpis()
    }, intervalMs)

    return () => clearInterval(timer)
  }, [fetchKpis, intervalMs])

  return {
    account,
    performance,
    risk,
    lastUpdate,
    refetch: fetchKpis,
  }
}