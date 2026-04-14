"use client"

import { ResearchCenter } from "@/components/decision/research-center"
import { EveningRotationPlan } from "@/components/decision/evening-rotation-plan"
import { PostMarketReport } from "@/components/decision/post-market-report"

export default function ResearchPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">研究中心</h1>
        <p className="text-muted-foreground mt-1">研究窗口与服务集成</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <EveningRotationPlan />
        <PostMarketReport />
      </div>

      <ResearchCenter />
    </div>
  )
}
