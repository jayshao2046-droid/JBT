"use client"

import { useEffect, useState } from "react"
import {
  fetchSignalOverview,
  fetchSignals,
  type SignalOverviewResponse,
  type DecisionRecord,
} from "@/lib/api/decision"

export function useSignals() {
  const [overview, setOverview] = useState<SignalOverviewResponse | null>(null)
  const [signals, setSignals] = useState<DecisionRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        const [overviewData, signalsData] = await Promise.all([
          fetchSignalOverview(),
          fetchSignals(),
        ])
        setOverview(overviewData)
        setSignals(signalsData)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load signals")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return {
    overview,
    signals,
    loading,
    error,
  }
}
