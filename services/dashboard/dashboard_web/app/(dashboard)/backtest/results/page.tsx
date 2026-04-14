"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useBacktestResults } from "@/hooks/use-backtest-results"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"

export default function ResultsPage() {
  const { results, loading } = useBacktestResults()

  const safeResults = Array.isArray(results) ? results : []

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>回测结果 ({safeResults.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {safeResults.length === 0 ? (
            <p className="text-muted-foreground text-sm">暂无结果</p>
          ) : (
            <div className="space-y-4">
              {safeResults.map((result) => (
                <div key={result.task_id} className="p-4 border rounded">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="font-medium">{result.strategy_name}</p>
                      <p className="text-xs text-muted-foreground">任务ID: {result.task_id}</p>
                    </div>
                    <Badge variant="default">已完成</Badge>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    <div>
                      <p className="text-xs text-muted-foreground">总收益</p>
                      <p className={`font-medium ${result.performance.total_return >= 0 ? "text-green-500" : "text-red-500"}`}>
                        {(result.performance.total_return * 100).toFixed(2)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">夏普比率</p>
                      <p className="font-medium">{result.performance.sharpe_ratio.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">最大回撤</p>
                      <p className="font-medium text-red-500">{(result.performance.max_drawdown * 100).toFixed(2)}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">胜率</p>
                      <p className="font-medium">{(result.performance.win_rate * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">交易次数</p>
                      <p className="font-medium">{result.performance.total_trades}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
