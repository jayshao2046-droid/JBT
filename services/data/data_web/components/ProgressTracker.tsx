'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { dataAPI, ProgressUpdate } from '@/lib/data-api'

interface ProgressTrackerProps {
  collectionId: string
  onComplete?: () => void
}

export function ProgressTracker({ collectionId, onComplete }: ProgressTrackerProps) {
  const [progress, setProgress] = useState<ProgressUpdate | null>(null)

  useEffect(() => {
    const cleanup = dataAPI.streamProgress(collectionId, (update) => {
      setProgress(update)
      if (update.status === 'completed' && onComplete) {
        onComplete()
      }
    })

    return cleanup
  }, [collectionId, onComplete])

  if (!progress) {
    return <div>加载中...</div>
  }

  const estimatedTime = progress.estimated_completion
    ? new Date(progress.estimated_completion * 1000).toLocaleTimeString()
    : '计算中...'

  return (
    <Card>
      <CardHeader>
        <CardTitle>采集进度</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span>{progress.current_stage}</span>
            <span>{progress.progress_percent.toFixed(1)}%</span>
          </div>
          <Progress value={progress.progress_percent} />
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-muted-foreground">已完成</div>
            <div className="font-medium">{progress.completed_items} / {progress.total_items}</div>
          </div>
          <div>
            <div className="text-muted-foreground">预计完成</div>
            <div className="font-medium">{estimatedTime}</div>
          </div>
        </div>

        <div className="text-sm">
          <span className="text-muted-foreground">状态: </span>
          <span className={`font-medium ${
            progress.status === 'completed' ? 'text-green-600' :
            progress.status === 'failed' ? 'text-red-600' :
            'text-blue-600'
          }`}>
            {progress.status === 'completed' ? '已完成' :
             progress.status === 'failed' ? '失败' :
             '进行中'}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
