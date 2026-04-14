"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useSignals } from "@/hooks/use-signals"
import { reviewSignal } from "@/lib/api/decision"
import { useState } from "react"

export function SignalReview() {
  const { signals, loading, error } = useSignals()
  const [reviewing, setReviewing] = useState<string | null>(null)

  const handleReview = async (decisionId: string, action: "approve" | "reject") => {
    try {
      setReviewing(decisionId)
      await reviewSignal({ decision_id: decisionId, action })
      window.location.reload()
    } catch (err) {
      console.error("Review failed:", err)
    } finally {
      setReviewing(null)
    }
  }

  if (loading) {
    return <div className="text-muted-foreground">加载中...</div>
  }

  if (error) {
    return <div className="text-destructive">错误: {error}</div>
  }

  if (!signals || signals.length === 0) {
    return <div className="text-muted-foreground">暂无信号</div>
  }

  return (
    <div className="space-y-4">
      {signals.map((signal) => (
        <Card key={signal.decision_id}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">{signal.strategy_id}</CardTitle>
              <div className="flex gap-2">
                <Badge variant={signal.eligibility_status === "eligible" ? "default" : "secondary"}>
                  {signal.eligibility_status}
                </Badge>
                <Badge variant="outline">{signal.publish_workflow_status}</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">动作:</span>
                <span className="ml-2 font-medium">{signal.action}</span>
              </div>
              <div>
                <span className="text-muted-foreground">置信度:</span>
                <span className="ml-2 font-medium">{(signal.confidence * 100).toFixed(1)}%</span>
              </div>
              {signal.symbol && (
                <div>
                  <span className="text-muted-foreground">标的:</span>
                  <span className="ml-2 font-medium">{signal.symbol}</span>
                </div>
              )}
              <div>
                <span className="text-muted-foreground">层级:</span>
                <span className="ml-2 font-medium">{signal.layer}</span>
              </div>
              <div>
                <span className="text-muted-foreground">目标:</span>
                <span className="ml-2 font-medium">{signal.publish_target}</span>
              </div>
              <div>
                <span className="text-muted-foreground">生成时间:</span>
                <span className="ml-2 font-medium">
                  {new Date(signal.generated_at).toLocaleString("zh-CN")}
                </span>
              </div>
            </div>

            {signal.reasoning_summary && (
              <div className="text-sm">
                <span className="text-muted-foreground">推理摘要:</span>
                <p className="mt-1 text-foreground">{signal.reasoning_summary}</p>
              </div>
            )}

            {signal.gate_reasons && signal.gate_reasons.length > 0 && (
              <div className="text-sm">
                <span className="text-muted-foreground">门控原因:</span>
                <ul className="mt-1 list-disc list-inside">
                  {signal.gate_reasons.map((reason, idx) => (
                    <li key={idx} className="text-foreground">{reason}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <Button
                size="sm"
                onClick={() => handleReview(signal.decision_id, "approve")}
                disabled={reviewing === signal.decision_id}
              >
                批准
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleReview(signal.decision_id, "reject")}
                disabled={reviewing === signal.decision_id}
              >
                拒绝
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
