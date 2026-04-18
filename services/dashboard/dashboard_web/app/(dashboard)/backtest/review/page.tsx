"use client"

import { ReviewPanel } from "@/components/backtest/review-panel"
import { useBacktest } from "@/hooks/use-backtest"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "sonner"

export default function ReviewPage() {
  const { strategies, loading } = useBacktest()

  const handleApprove = async (strategyId: string) => {
    toast.success(`策略 ${strategyId} 已批准`)
  }

  const handleReject = async (strategyId: string) => {
    toast.error(`策略 ${strategyId} 已拒绝`)
  }

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <ReviewPanel
        strategies={strategies}
        onApprove={handleApprove}
        onReject={handleReject}
      />
    </div>
  )
}
