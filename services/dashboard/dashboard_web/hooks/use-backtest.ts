"use client"

import { useState, useEffect, useCallback } from "react"
import { backtestApi, type Strategy, type BacktestJob, type SystemStatus } from "@/lib/api/backtest"

export function useBacktest() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [jobs, setJobs] = useState<BacktestJob[]>([])
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      await Promise.allSettled([
        backtestApi.getStrategies().then(setStrategies).catch((e) => {
          console.error("Failed to fetch strategies:", e)
          setStrategies([])
        }),
        backtestApi.getJobs().then(setJobs).catch((e) => {
          console.error("Failed to fetch jobs:", e)
          setJobs([])
        }),
        backtestApi.getSystemStatus().then(setSystemStatus).catch((e) => {
          console.error("Failed to fetch system status:", e)
          setSystemStatus(null)
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
    const interval = setInterval(fetchData, 5000) // 5秒刷新
    return () => clearInterval(interval)
  }, [fetchData])

  return {
    strategies,
    jobs,
    systemStatus,
    loading,
    error,
    refetch: fetchData,
  }
}
