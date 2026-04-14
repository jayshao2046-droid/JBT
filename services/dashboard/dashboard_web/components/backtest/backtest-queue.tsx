"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface BacktestQueueProps {
  jobs: Array<{
    id: string
    strategy_name: string
    status: string
    progress: number
    created_at: string
  }>
}

export function BacktestQueue({ jobs }: BacktestQueueProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>回测队列 ({jobs.length})</CardTitle>
      </CardHeader>
      <CardContent>
        {jobs.length === 0 ? (
          <p className="text-muted-foreground text-sm">队列为空</p>
        ) : (
          <div className="space-y-2">
            {jobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between p-2 border rounded">
                <div>
                  <p className="font-medium">{job.strategy_name}</p>
                  <p className="text-xs text-muted-foreground">{job.created_at}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={job.status === "running" ? "default" : "secondary"}>
                    {job.status}
                  </Badge>
                  {job.status === "running" && (
                    <span className="text-sm">{job.progress}%</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
