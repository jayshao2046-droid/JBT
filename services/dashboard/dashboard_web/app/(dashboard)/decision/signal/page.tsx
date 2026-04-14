"use client"

import { SignalReview } from "@/components/decision/signal-review"
import { SignalDistributionChart } from "@/components/decision/signal-distribution-chart"
import { IntradaySignal } from "@/components/decision/intraday-signal"

export default function SignalPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">信号审查</h1>
        <p className="text-muted-foreground mt-1">实时信号监控与审批</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SignalDistributionChart />
        <IntradaySignal />
      </div>

      <SignalReview />
    </div>
  )
}
