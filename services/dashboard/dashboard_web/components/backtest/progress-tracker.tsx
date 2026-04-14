"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface ProgressTrackerProps {
  progress: number
  status: string
}

export function ProgressTracker({ progress, status }: ProgressTrackerProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>回测进度</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm">{status}</span>
            <span className="text-sm font-medium">{progress}%</span>
          </div>
          <div className="w-full bg-secondary rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
