"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useState, useEffect } from "react"

interface RotationPlan {
  plan_id: string
  generated_at: string
  target_date: string
  rotation_type: string
  candidates: Array<{
    symbol: string
    score: number
    rank: number
    factors: Record<string, number>
  }>
  execution_status: string
}

export function EveningRotationPlan() {
  const [plan, setPlan] = useState<RotationPlan | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        const res = await fetch("/api/decision/api/v1/evening-rotation/plan", {
          cache: "no-store",
        })
        if (!res.ok) throw new Error(`Failed: ${res.status}`)
        const data = await res.json()
        setPlan(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load plan")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return <div className="text-muted-foreground">加载中...</div>
  }

  if (error) {
    return <div className="text-destructive">错误: {error}</div>
  }

  if (!plan) {
    return <div className="text-muted-foreground">暂无换仓计划</div>
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>晚间换仓计划</CardTitle>
          <Badge variant="outline">{plan.execution_status}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-sm text-muted-foreground">
          <div>目标日期: {plan.target_date}</div>
          <div>生成时间: {new Date(plan.generated_at).toLocaleString("zh-CN")}</div>
          <div>轮换类型: {plan.rotation_type}</div>
        </div>

        <div>
          <div className="text-sm font-medium mb-2">候选标的 ({plan.candidates.length})</div>
          <div className="space-y-2">
            {plan.candidates.map((candidate) => (
              <div key={candidate.symbol} className="border-b pb-2 last:border-b-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">{candidate.symbol}</span>
                  <div className="flex gap-2">
                    <Badge variant="secondary">#{candidate.rank}</Badge>
                    <Badge variant="default">{candidate.score.toFixed(2)}</Badge>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(candidate.factors).map(([key, value]) => (
                    <span key={key} className="text-xs text-muted-foreground">
                      {key}: {typeof value === "number" ? value.toFixed(2) : value}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
