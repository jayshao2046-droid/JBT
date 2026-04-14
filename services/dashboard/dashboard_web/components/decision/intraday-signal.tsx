"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useSignals } from "@/hooks/use-signals"

export function IntradaySignal() {
  const { signals, loading, error } = useSignals()

  if (loading) {
    return <div className="text-muted-foreground">加载中...</div>
  }

  if (error) {
    return <div className="text-destructive">错误: {error}</div>
  }

  const intradaySignals = signals.filter((s) => s.decision_stage === "intraday" || s.layer === "intraday")

  return (
    <Card>
      <CardHeader>
        <CardTitle>盘中信号 ({intradaySignals.length})</CardTitle>
      </CardHeader>
      <CardContent>
        {intradaySignals.length === 0 ? (
          <div className="text-sm text-muted-foreground">暂无盘中信号</div>
        ) : (
          <div className="space-y-3">
            {intradaySignals.map((signal) => (
              <div key={signal.decision_id} className="border-b pb-3 last:border-b-0">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">{signal.strategy_id}</span>
                  <Badge variant={signal.action === "long" ? "default" : "destructive"}>
                    {signal.action}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                  {signal.symbol && <div>标的: {signal.symbol}</div>}
                  <div>置信度: {(signal.confidence * 100).toFixed(1)}%</div>
                  <div>状态: {signal.eligibility_status}</div>
                  <div>时间: {new Date(signal.generated_at).toLocaleTimeString("zh-CN")}</div>
                </div>
                {signal.reasoning_summary && (
                  <div className="text-xs text-muted-foreground mt-2">
                    {signal.reasoning_summary}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
