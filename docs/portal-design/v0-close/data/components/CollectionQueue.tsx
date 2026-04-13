'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface QueueTask {
  task_id: string
  task_type: string
  status: string
  priority: number
  created_at: number
}

interface CollectionQueueProps {
  tasks: QueueTask[]
  onCancel?: (taskId: string) => void
  onRetry?: (taskId: string) => void
  onUpdatePriority?: (taskId: string, priority: number) => void
}

export function CollectionQueue({ tasks, onCancel, onRetry, onUpdatePriority }: CollectionQueueProps) {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <Badge variant="secondary">待执行</Badge>
      case 'running':
        return <Badge variant="default">执行中</Badge>
      case 'completed':
        return <Badge variant="outline" className="bg-green-500">已完成</Badge>
      case 'failed':
        return <Badge variant="destructive">失败</Badge>
      default:
        return <Badge>{status}</Badge>
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>任务队列</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {tasks.map((task) => (
            <div key={task.task_id} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{task.task_type}</span>
                  {getStatusBadge(task.status)}
                  <Badge variant="outline">优先级: {task.priority}</Badge>
                </div>
                <div className="flex gap-2">
                  {task.status === 'pending' && onCancel && (
                    <Button size="sm" variant="outline" onClick={() => onCancel(task.task_id)}>
                      取消
                    </Button>
                  )}
                  {task.status === 'failed' && onRetry && (
                    <Button size="sm" variant="outline" onClick={() => onRetry(task.task_id)}>
                      重试
                    </Button>
                  )}
                  {task.status === 'pending' && onUpdatePriority && (
                    <Button size="sm" variant="outline" onClick={() => onUpdatePriority(task.task_id, task.priority + 1)}>
                      提高优先级
                    </Button>
                  )}
                </div>
              </div>
              <div className="text-sm text-muted-foreground">
                创建时间: {new Date(task.created_at * 1000).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
