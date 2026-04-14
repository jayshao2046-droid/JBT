"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { PerformanceMetrics } from "@/lib/api/backtest"

interface BacktestAnalysisProps {
  result: {
    task_id: string
    strategy_name: string
    performance: PerformanceMetrics
  }
}

export function BacktestAnalysis({ result }: BacktestAnalysisProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>回测分析</CardTitle>
      </CardHeader>
      <CardContent>
        <div>
          <p className="font-medium">{result.strategy_name}</p>
          <p className="text-xs text-muted-foreground">任务ID: {result.task_id}</p>
        </div>
      </CardContent>
    </Card>
  )
}
