"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CheckCircle2, XCircle, AlertCircle, Clock } from "lucide-react"
import type { Strategy } from "@/lib/api/backtest"

interface ReviewPanelProps {
  strategies: Strategy[]
  onApprove?: (strategyId: string) => void
  onReject?: (strategyId: string) => void
}

export function ReviewPanel({ strategies, onApprove, onReject }: ReviewPanelProps) {
  const pendingStrategies = strategies.filter(s => s.status === "pending" || s.status === "draft")

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "approved":
        return <Badge variant="default" className="bg-green-500"><CheckCircle2 className="w-3 h-3 mr-1" />已批准</Badge>
      case "rejected":
        return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" />已拒绝</Badge>
      case "pending":
        return <Badge variant="secondary"><Clock className="w-3 h-3 mr-1" />待审查</Badge>
      default:
        return <Badge variant="outline"><AlertCircle className="w-3 h-3 mr-1" />草稿</Badge>
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>策略审查 ({pendingStrategies.length} 待审)</CardTitle>
      </CardHeader>
      <CardContent>
        {strategies.length === 0 ? (
          <p className="text-muted-foreground text-sm">暂无策略</p>
        ) : (
          <div className="space-y-4">
            {strategies.map((strategy) => (
              <div key={strategy.id || strategy.name} className="p-4 border rounded space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium">{strategy.name}</h4>
                      {getStatusBadge(strategy.status)}
                    </div>
                    <p className="text-sm text-muted-foreground">{strategy.description}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  <div>
                    <p className="text-muted-foreground">参数数量</p>
                    <p className="font-medium">{Object.keys(strategy.params).length}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">策略ID</p>
                    <p className="font-medium text-xs">{strategy.id || "N/A"}</p>
                  </div>
                </div>

                {strategy.params && Object.keys(strategy.params).length > 0 && (
                  <div className="pt-2 border-t">
                    <p className="text-xs text-muted-foreground mb-2">参数配置</p>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                      {Object.entries(strategy.params).slice(0, 6).map(([key, value]) => (
                        <div key={key} className="p-2 bg-muted rounded">
                          <span className="text-muted-foreground">{key}:</span>{" "}
                          <span className="font-medium">{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {(strategy.status === "pending" || strategy.status === "draft") && (
                  <div className="flex gap-2 pt-2">
                    <Button
                      size="sm"
                      variant="default"
                      onClick={() => onApprove?.(strategy.id || strategy.name)}
                    >
                      <CheckCircle2 className="w-4 h-4 mr-1" />
                      批准
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => onReject?.(strategy.id || strategy.name)}
                    >
                      <XCircle className="w-4 h-4 mr-1" />
                      拒绝
                    </Button>
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
