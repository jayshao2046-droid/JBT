"use client"

import { useState, useEffect, useCallback } from "react"
import { backtestApi, type BacktestResult } from "@/lib/api/backtest"

export function useBacktestResults() {
  const [results, setResults] = useState<BacktestResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchResults = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await backtestApi.getResults()
      setResults(Array.isArray(res) ? res : [])
    } catch (err) {
      console.error("Failed to fetch backtest results:", err)
      setError(err instanceof Error ? err.message : "获取结果失败")
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchResults()
  }, [fetchResults])

  return {
    results,
    loading,
    error,
    refetch: fetchResults,
  }
}
