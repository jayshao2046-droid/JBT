"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ListTodo, Play, X, RotateCcw } from "lucide-react"

interface Task {
  task_id: string
  strategy_id: string
  params: any
  priority: number
  status: string
  created_at: string
}

interface DecisionQueueProps {
  tasks: Task[]
  onCancel?: (taskId: string) => void
  onRetry?: (taskId: string) => void
  onUpdatePriority?: (taskId: string, priority: number) => void
}

export function DecisionQueue({ tasks, onCancel, onRetry, onUpdatePriority }: DecisionQueueProps) {
  const [filter, setFilter] = useState<"all" | "pending" | "running" | "completed">("all")

  const filteredTasks = filter === "all" ? tasks : tasks.filter((t) => t.status === filter)

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "text-green-400"
      case "failed":
        return "text-red-400"
      case "running":
        return "text-orange-400"
      case "cancelled":
        return "text-neutral-500"
      default:
        return "text-blue-400"
    }
  }

  const getStatusText = (status: string) => {
    const map: Record<string, string> = {
      pending: "待执行",
      running: "执行中",
      completed: "已完成",
      failed: "失败",
      cancelled: "已取消",
    }
    return map[status] || status
  }

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <ListTodo className="w-5 h-5 text-blue-500" />
          决策任务队列
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* 筛选器 */}
          <div className="flex gap-2">
            <Button size="sm" variant={filter === "all" ? "default" : "outline"} onClick={() => setFilter("all")}>
              全部 ({tasks.length})
            </Button>
            <Button
              size="sm"
              variant={filter === "pending" ? "default" : "outline"}
              onClick={() => setFilter("pending")}
            >
              待执行 ({tasks.filter((t) => t.status === "pending").length})
            </Button>
            <Button
              size="sm"
              variant={filter === "running" ? "default" : "outline"}
              onClick={() => setFilter("running")}
            >
              执行中 ({tasks.filter((t) => t.status === "running").length})
            </Button>
            <Button
              size="sm"
              variant={filter === "completed" ? "default" : "outline"}
              onClick={() => setFilter("completed")}
            >
              已完成 ({tasks.filter((t) => t.status === "completed").length})
            </Button>
          </div>

          {/* 任务列表 */}
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {filteredTasks.length === 0 ? (
              <div className="text-center text-neutral-500 py-8">暂无任务</div>
            ) : (
              filteredTasks.map((task) => (
                <div key={task.task_id} className="p-3 bg-neutral-900 rounded-lg border border-neutral-700">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white">{task.task_id.slice(0, 12)}</span>
                      <span className={`text-xs ${getStatusColor(task.status)}`}>{getStatusText(task.status)}</span>
                    </div>
                    <div className="flex gap-1">
                      {task.status === "pending" && onCancel && (
                        <Button size="sm" variant="ghost" onClick={() => onCancel(task.task_id)}>
                          <X className="w-3 h-3" />
                        </Button>
                      )}
                      {task.status === "failed" && onRetry && (
                        <Button size="sm" variant="ghost" onClick={() => onRetry(task.task_id)}>
                          <RotateCcw className="w-3 h-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-neutral-400">策略</span>
                      <div className="text-white">{task.strategy_id}</div>
                    </div>
                    <div>
                      <span className="text-neutral-400">优先级</span>
                      <div className="text-white">{task.priority}</div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
