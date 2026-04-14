import { useState, useEffect, useCallback } from "react"
import { dataApi, CollectorsResponse } from "@/lib/api/data"

export function useCollectors(refreshNonce?: number, autoRefresh = false) {
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [data, setData] = useState<CollectorsResponse | null>(null)

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await dataApi.getCollectors()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [refreshNonce, fetchData])

  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [autoRefresh, fetchData])

  return {
    isLoading,
    error,
    data,
    refetch: fetchData,
  }
}
