"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { RefreshCw, X, Play, Pause } from "lucide-react"

interface BacktestTask {
  task_id: string
  strategy_id: string
  status: "pending" | "running" | "completed" | "failed" | "cancelled"
  priority: number
  created_at: string
  started_at?: string
  completed_at?: string
  progress: number
  result?: any
  error?: string
}

interface QueueStatus {
  total_tasks: number
  pending: number
  running: number
  completed: number
  failed: number
  cancelled: number
  max_concurrent: number
}

interface BacktestQueueProps {
  onRefresh: () => Promise<{ tasks: BacktestTask[]; status: QueueStatus }>
  onCancel: (taskId: string) => Promise<void>
  onRetry?: (taskId: string) => Promise<void>
}

const statusColors = {
  pending: "bg-yellow-500",
  running: "bg-blue-500",
  completed: "bg-green-500",
  failed: "bg-red-500",
  cancelled: "bg-gray-500",
}

const statusLabels = {
  pending: "待执行",
  running: "执行中",
  completed: "已完成",
  failed: "失败",
  cancelled: "已取消",
}

export function BacktestQueue({ onRefresh, onCancel, onRetry }: BacktestQueueProps) {
  const [tasks, setTasks] = useState<BacktestTask[]>([])
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const loadData = async () => {
    setIsRefreshing(true)
    try {
      const data = await onRefresh()
      setTasks(data.tasks)
      setQueueStatus(data.status)
    } catch (error) {
      console.error("Failed to load queue data:", error)
    } finally {
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      loadData()
    }, 3000)

    return () => clearInterval(interval)
  }, [autoRefresh])

  const handleCancel = async (taskId: string) => {
    try {
      await onCancel(taskId)
      await loadData()
    } catch (error) {
      console.error("Failed to cancel task:", error)
    }
  }

  const handleRetry = async (taskId: string) => {
    if (!onRetry) return
    try {
      await onRetry(taskId)
      await loadData()
    } catch (error) {
      console.error("Failed to retry task:", error)
    }
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "-"
    const date = new Date(dateStr)
    return date.toLocaleString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  const getDuration = (task: BacktestTask) => {
    if (!task.started_at) return "-"
    const start = new Date(task.started_at)
    const end = task.completed_at ? new Date(task.completed_at) : new Date()
    const seconds = Math.floor((end.getTime() - start.getTime()) / 1000)
    if (seconds < 60) return `${seconds}秒`
    const minutes = Math.floor(seconds / 60)
    return `${minutes}分${seconds % 60}秒`
  }

  return (
    <div className="space-y-4">
      {/* 队列状态概览 */}
      {queueStatus && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-base">队列状态</CardTitle>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setAutoRefresh(!autoRefresh)}
                >
                  {autoRefresh ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={loadData}
                  disabled={isRefreshing}
                >
                  <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-yellow-600">{queueStatus.pending}</div>
                <div className="text-xs text-muted-foreground">待执行</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-600">{queueStatus.running}</div>
                <div className="text-xs text-muted-foreground">执行中</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{queueStatus.completed}</div>
                <div className="text-xs text-muted-foreground">已完成</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-600">{queueStatus.failed}</div>
                <div className="text-xs text-muted-foreground">失败</div>
              </div>
            </div>
            <div className="mt-4 text-xs text-muted-foreground text-center">
              最大并发：{queueStatus.max_concurrent} | 总任务数：{queueStatus.total_tasks}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 任务列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">任务列表</CardTitle>
        </CardHeader>
        <CardContent>
          {tasks.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">暂无任务</p>
          ) : (
            <div className="space-y-3">
              {tasks.map((task) => (
                <div
                  key={task.task_id}
                  className="border rounded-lg p-4 space-y-3"
                >
                  {/* 任务头部 */}
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{task.strategy_id}</Badge>
                        <Badge className={statusColors[task.status]}>
                          {statusLabels[task.status]}
                        </Badge>
                        {task.priority > 0 && (
                          <Badge variant="secondary">优先级 {task.priority}</Badge>
                        )}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        任务ID: {task.task_id.substring(0, 8)}...
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {task.status === "failed" && onRetry && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleRetry(task.task_id)}
                        >
                          重试
                        </Button>
                      )}
                      {(task.status === "pending" || task.status === "running") && (
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleCancel(task.task_id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* 进度条 */}
                  {task.status === "running" && (
                    <div className="space-y-1">
                      <Progress value={task.progress * 100} />
                      <div className="text-xs text-muted-foreground text-right">
                        {(task.progress * 100).toFixed(0)}%
                      </div>
                    </div>
                  )}

                  {/* 任务信息 */}
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <span className="text-muted-foreground">创建时间：</span>
                      <span>{formatDate(task.created_at)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">开始时间：</span>
                      <span>{formatDate(task.started_at)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">耗时：</span>
                      <span>{getDuration(task)}</span>
                    </div>
                  </div>

                  {/* 结果或错误 */}
                  {task.status === "completed" && task.result && (
                    <div className="bg-green-50 dark:bg-green-950 rounded p-2 text-xs space-y-1">
                      <div className="font-medium text-green-700 dark:text-green-300">回测结果</div>
                      <div className="grid grid-cols-3 gap-2 text-green-600 dark:text-green-400">
                        {task.result.total_return !== undefined && (
                          <div>收益率: {(task.result.total_return * 100).toFixed(2)}%</div>
                        )}
                        {task.result.sharpe_ratio !== undefined && (
                          <div>夏普: {task.result.sharpe_ratio.toFixed(2)}</div>
                        )}
                        {task.result.max_drawdown !== undefined && (
                          <div>最大回撤: {(task.result.max_drawdown * 100).toFixed(2)}%</div>
                        )}
                      </div>
                    </div>
                  )}

                  {task.status === "failed" && task.error && (
                    <div className="bg-red-50 dark:bg-red-950 rounded p-2 text-xs">
                      <div className="font-medium text-red-700 dark:text-red-300 mb-1">错误信息</div>
                      <div className="text-red-600 dark:text-red-400">{task.error}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
