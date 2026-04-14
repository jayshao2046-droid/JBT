"use client"

import { useEffect, useState } from "react"
import {
  fetchStrategyOverview,
  fetchRuntimeOverview,
  type StrategyOverviewResponse,
  type ModelRuntimeOverview,
} from "@/lib/api/decision"

export function useDecision() {
  const [strategyOverview, setStrategyOverview] = useState<StrategyOverviewResponse | null>(null)
  const [runtimeOverview, setRuntimeOverview] = useState<ModelRuntimeOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        const [strategies, runtime] = await Promise.all([
          fetchStrategyOverview(),
          fetchRuntimeOverview(),
        ])
        setStrategyOverview(strategies)
        setRuntimeOverview(runtime)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load decision data")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return {
    strategyOverview,
    runtimeOverview,
    loading,
    error,
  }
}
