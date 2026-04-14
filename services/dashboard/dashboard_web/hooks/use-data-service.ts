import { useState, useEffect, useCallback } from "react"
import { dataApi, SystemResponse, CollectorsResponse } from "@/lib/api/data"

export function useDataService(refreshNonce?: number) {
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [systemData, setSystemData] = useState<SystemResponse | null>(null)
  const [collectorsData, setCollectorsData] = useState<CollectorsResponse | null>(null)

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [system, collectors] = await Promise.all([
        dataApi.getSystem(),
        dataApi.getCollectors(),
      ])
      setSystemData(system)
      setCollectorsData(collectors)
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [refreshNonce, fetchData])

  return {
    isLoading,
    error,
    systemData,
    collectorsData,
    refetch: fetchData,
  }
}
