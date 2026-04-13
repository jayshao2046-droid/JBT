"use client"

import { useState } from "react"
import { ParameterOptimizer } from "@/components/ParameterOptimizer"
import { DecisionAnalysis } from "@/components/DecisionAnalysis"
import { DecisionConfigEditor } from "@/components/DecisionConfigEditor"
import { DecisionQueue } from "@/components/DecisionQueue"
import { DecisionTemplates } from "@/components/DecisionTemplates"
import { Settings } from "lucide-react"

export default function OptimizerPage() {
  const [mockTasks] = useState([
    {
      task_id: "task_001",
      strategy_id: "strategy_001",
      params: { stop_loss: 0.03 },
      priority: 5,
      status: "pending",
      created_at: "2026-04-13T10:00:00Z",
    },
    {
      task_id: "task_002",
      strategy_id: "strategy_002",
      params: { stop_loss: 0.05 },
      priority: 3,
      status: "running",
      created_at: "2026-04-13T10:05:00Z",
    },
  ])

  const [mockDecisions] = useState([
    { created_at: "2026-03-15T10:00:00Z", return: 0.05, signal: 1 },
    { created_at: "2026-03-20T10:00:00Z", return: -0.02, signal: -1 },
    { created_at: "2026-04-10T10:00:00Z", return: 0.03, signal: 1 },
  ])

  return (
    <div className="min-h-screen bg-neutral-950 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white flex items-center gap-2">
            <Settings className="w-8 h-8 text-purple-500" />
            参数优化与配置
          </h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ParameterOptimizer />
          <DecisionConfigEditor />
        </div>

        <DecisionTemplates />

        <DecisionQueue tasks={mockTasks} />

        <DecisionAnalysis decisions={mockDecisions} />
      </div>
    </div>
  )
}
