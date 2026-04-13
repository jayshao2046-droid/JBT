"use client"

import { useState, useEffect, useRef } from "react"
import { Progress } from "@/components/ui/progress"
import { Card, CardContent } from "@/components/ui/card"
import { Clock, TrendingUp } from "lucide-react"

interface ProgressTrackerProps {
  taskId: string
  onComplete?: () => void
  onError?: (error: string) => void
}

export function ProgressTracker({ taskId, onComplete, onError }: ProgressTrackerProps) {
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState("pending")
  const [currentDate, setCurrentDate] = useState("")
  const [estimatedCompletion, setEstimatedCompletion] = useState<string | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    // 使用 SSE 接收实时进度
    const eventSource = new EventSource(`/api/backtest/progress/${taskId}/stream`)
    eventSourceRef.current = eventSource

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.error) {
          onError?.(data.error)
          eventSource.close()
          return
        }

        setProgress(data.progress || 0)
        setStatus(data.status || "pending")
        setCurrentDate(data.current_date || "")
        setEstimatedCompletion(data.estimated_completion)

        // 如果完成或失败，关闭连接
        if (data.status === "completed" || data.status === "failed" || data.status === "cancelled") {
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
  }, [taskId, onComplete, onError])

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
      case "submitted":
        return "已提交"
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
            <span className="text-sm font-medium text-white">回测进度</span>
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

        {currentDate && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-neutral-400 flex items-center gap-1">
              <Clock className="w-4 h-4" />
              当前日期
            </span>
            <span className="text-neutral-300 font-mono">{currentDate}</span>
          </div>
        )}

        {estimatedCompletion && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-neutral-400">预计完成</span>
            <span className="text-neutral-300 font-mono">{estimatedCompletion}</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

interface BatchProgressTrackerProps {
  taskIds: string[]
  onAllComplete?: () => void
}

export function BatchProgressTracker({ taskIds, onAllComplete }: BatchProgressTrackerProps) {
  const [progressMap, setProgressMap] = useState<Record<string, number>>({})
  const [completedCount, setCompletedCount] = useState(0)

  useEffect(() => {
    if (completedCount === taskIds.length && taskIds.length > 0) {
      onAllComplete?.()
    }
  }, [completedCount, taskIds.length, onAllComplete])

  const handleComplete = (taskId: string) => {
    setProgressMap((prev) => ({ ...prev, [taskId]: 100 }))
    setCompletedCount((prev) => prev + 1)
  }

  const totalProgress = taskIds.length > 0
    ? Math.round((completedCount / taskIds.length) * 100)
    : 0

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardContent className="pt-6 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-white">批量回测进度</span>
          <span className="text-sm text-neutral-400">
            {completedCount} / {taskIds.length}
          </span>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-neutral-400">总进度</span>
            <span className="text-white font-mono">{totalProgress}%</span>
          </div>
          <Progress value={totalProgress} className="h-2" />
        </div>

        <div className="space-y-2 max-h-60 overflow-y-auto">
          {taskIds.map((taskId) => (
            <div key={taskId} className="flex items-center justify-between text-xs">
              <span className="text-neutral-400 truncate max-w-[200px]">{taskId}</span>
              <ProgressTracker
                taskId={taskId}
                onComplete={() => handleComplete(taskId)}
              />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
