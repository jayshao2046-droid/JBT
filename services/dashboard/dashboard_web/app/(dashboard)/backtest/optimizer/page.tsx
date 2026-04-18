"use client"

import { ParameterOptimizer } from "@/components/backtest/parameter-optimizer"
import { useBacktest } from "@/hooks/use-backtest"
import { Skeleton } from "@/components/ui/skeleton"

export default function OptimizerPage() {
  const { strategies, loading } = useBacktest()

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <ParameterOptimizer strategies={strategies} />
    </div>
  )
}
