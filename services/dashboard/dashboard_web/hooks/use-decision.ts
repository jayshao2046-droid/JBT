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
        const [strategies, runtime] = await Promise.allSettled([
          fetchStrategyOverview(),
          fetchRuntimeOverview(),
        ])

        if (strategies.status === "fulfilled") {
          setStrategyOverview(strategies.value)
        } else {
          setStrategyOverview(null)
        }

        if (runtime.status === "fulfilled") {
          setRuntimeOverview(runtime.value)
        } else {
          setRuntimeOverview(null)
        }

        if (strategies.status === "rejected" && runtime.status === "rejected") {
          const messages = [strategies.reason, runtime.reason]
            .map((reason) => reason instanceof Error ? reason.message : String(reason))
            .join(" | ")
          setError(messages || "Failed to load decision data")
        } else {
          setError(null)
        }
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
