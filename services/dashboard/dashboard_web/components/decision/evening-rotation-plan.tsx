"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useState, useEffect } from "react"

interface RotationPlan {
  plan_id?: string | null
  rotated_at?: string | null
  top_n?: number
  selected?: Array<string | Record<string, unknown>>
  scores?: Array<Record<string, unknown>>
}

const ROTATION_PLAN_PATHS = [
  "/api/decision/api/v1/stock/rotation/plan",
]

export function EveningRotationPlan() {
  const [plan, setPlan] = useState<RotationPlan | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        let data: RotationPlan | null = null
        let lastError: Error | null = null

        for (const path of ROTATION_PLAN_PATHS) {
          try {
            const res = await fetch(path, { cache: "no-store" })
            if (!res.ok) {
              throw new Error(`Failed: ${res.status}`)
            }
            data = await res.json()
            break
          } catch (err) {
            lastError = err instanceof Error ? err : new Error("Failed to load plan")
          }
        }

        if (!data) {
          throw lastError ?? new Error("Failed to load plan")
        }

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

  const selected = Array.isArray(plan.selected) ? plan.selected : []
  const scores = Array.isArray(plan.scores) ? plan.scores : []
  const entries = selected.map((candidate, index) => {
    if (typeof candidate === "string") {
      return {
        key: candidate,
        label: candidate,
        rank: index + 1,
        score: null,
        details: [] as string[],
      }
    }

    const label = typeof candidate.symbol === "string"
      ? candidate.symbol
      : typeof candidate.code === "string"
        ? candidate.code
        : typeof candidate.name === "string"
          ? candidate.name
          : `candidate-${index + 1}`
    const numericScore = typeof candidate.score === "number"
      ? candidate.score
      : typeof candidate.total_score === "number"
        ? candidate.total_score
        : null
    const rank = typeof candidate.rank === "number" ? candidate.rank : index + 1
    const details = Object.entries(candidate)
      .filter(([key]) => !["symbol", "code", "name", "score", "total_score", "rank"].includes(key))
      .slice(0, 4)
      .map(([key, value]) => `${key}: ${typeof value === "number" ? value.toFixed(2) : String(value)}`)

    return {
      key: `${label}-${rank}`,
      label,
      rank,
      score: numericScore,
      details,
    }
  })

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>晚间换仓计划</CardTitle>
          <Badge variant="outline">最近计划</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-sm text-muted-foreground">
          <div>计划 ID: {plan.plan_id || "暂无"}</div>
          <div>
            最近生成: {plan.rotated_at ? new Date(plan.rotated_at).toLocaleString("zh-CN") : "暂无生成记录"}
          </div>
          <div>目标数量: {plan.top_n ?? entries.length}</div>
        </div>

        <div>
          <div className="text-sm font-medium mb-2">候选标的 ({entries.length})</div>
          {entries.length === 0 ? (
            <div className="text-sm text-muted-foreground">当前暂无换仓候选</div>
          ) : (
            <div className="space-y-2">
              {entries.map((candidate) => (
                <div key={candidate.key} className="border-b pb-2 last:border-b-0">
                  <div className="flex items-center justify-between mb-1 gap-2">
                    <span className="text-sm font-medium">{candidate.label}</span>
                    <div className="flex gap-2">
                      <Badge variant="secondary">#{candidate.rank}</Badge>
                      {candidate.score !== null && (
                        <Badge variant="default">{candidate.score.toFixed(2)}</Badge>
                      )}
                    </div>
                  </div>
                  {candidate.details.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {candidate.details.map((detail) => (
                        <span key={detail} className="text-xs text-muted-foreground">
                          {detail}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {scores.length > 0 && (
          <div>
            <div className="text-sm font-medium mb-2">评分快照 ({scores.length})</div>
            <div className="space-y-2">
              {scores.slice(0, 5).map((score, index) => (
                <div key={index} className="text-xs text-muted-foreground border-l-2 pl-2">
                  {JSON.stringify(score)}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
