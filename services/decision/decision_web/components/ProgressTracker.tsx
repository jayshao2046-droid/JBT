"use client"

import { useState, useEffect, useRef } from "react"
import { Progress } from "@/components/ui/progress"
import { Card, CardContent } from "@/components/ui/card"
import { Clock, TrendingUp } from "lucide-react"

interface ProgressTrackerProps {
  decisionId: string
  onComplete?: () => void
  onError?: (error: string) => void
}

export function ProgressTracker({ decisionId, onComplete, onError }: ProgressTrackerProps) {
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState("pending")
  const [currentStage, setCurrentStage] = useState("")
  const [estimatedCompletion, setEstimatedCompletion] = useState<string | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    const API_BASE = process.env.NEXT_PUBLIC_DECISION_API_URL || "http://localhost:8003"
    const eventSource = new EventSource(`${API_BASE}/api/v1/decision/progress/${decisionId}/stream`)
    eventSourceRef.current = eventSource

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.error) {
          onError?.(data.error)
          eventSource.close()
          return
        }

        setProgress(data.progress_percent || 0)
        setStatus(data.status || "pending")
        setCurrentStage(data.current_stage || "")
        setEstimatedCompletion(data.estimated_completion)

        if (data.status === "completed" || data.status === "failed") {
          eventSource.close()
          if (data.status === "completed") {
            onComplete?.()
          }
        }
      } catch (error) {
        console.error("Failed to parse SSE data:", error)
      }
    }

    eventSource.onerror = (error) => {
      console.error("SSE error:", error)
      eventSource.close()
      onError?.("连接失败")
    }

    return () => {
      eventSource.close()
    }
  }, [decisionId, onComplete, onError])

  const getStatusColor = () => {
    switch (status) {
      case "completed":
        return "text-green-400"
      case "failed":
        return "text-red-400"
      case "running":
        return "text-orange-400"
      default:
        return "text-neutral-400"
    }
  }

  const getStatusText = () => {
    switch (status) {
      case "completed":
        return "已完成"
      case "failed":
        return "失败"
      case "running":
        return "运行中"
      default:
        return "等待中"
    }
  }

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardContent className="pt-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-orange-500" />
            <span className="text-sm font-medium text-white">决策进度</span>
          </div>
          <span className={`text-sm font-medium ${getStatusColor()}`}>{getStatusText()}</span>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-neutral-400">进度</span>
            <span className="text-white font-mono">{progress}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {currentStage && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-neutral-400 flex items-center gap-1">
              <Clock className="w-4 h-4" />
              当前阶段
            </span>
            <span className="text-neutral-300 font-mono">{currentStage}</span>
          </div>
        )}

        {estimatedCompletion && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-neutral-400">预计完成</span>
            <span className="text-neutral-300 font-mono">
              {new Date(estimatedCompletion).toLocaleTimeString()}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
