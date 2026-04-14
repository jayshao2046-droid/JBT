"use client"

import { ModelsFactors } from "@/components/decision/models-factors"
import { FactorAnalysis } from "@/components/decision/factor-analysis"

export default function ModelsPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">模型与因子</h1>
        <p className="text-muted-foreground mt-1">模型状态与因子同步管理</p>
      </div>

      <FactorAnalysis />

      <ModelsFactors />
    </div>
  )
}
