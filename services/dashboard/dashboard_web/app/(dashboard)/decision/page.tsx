"use client"

import { Overview } from "@/components/decision/overview"

export default function DecisionPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">智能决策</h1>
        <p className="text-muted-foreground mt-1">策略信号与决策系统</p>
      </div>

      <Overview />
    </div>
  )
}
