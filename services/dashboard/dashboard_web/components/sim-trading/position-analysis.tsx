"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

interface PositionAnalysisProps {
  positions: Array<{
    instrument_id: string
    direction: string
    volume: number
    avg_price: number
    current_price: number
    float_pnl: number
  }>
  onClose?: (position: { instrument_id: string; direction: string; volume: number; avg_price: number; current_price: number; float_pnl: number }) => void
}

export function PositionAnalysis({ positions, onClose }: PositionAnalysisProps) {
  const safePositions = Array.isArray(positions) ? positions : []
  const totalPnl = safePositions.reduce((sum, p) => sum + (p.float_pnl || 0), 0)
  const longCount = safePositions.filter(p => p.direction === "long").length
  const shortCount = safePositions.filter(p => p.direction === "short").length

  return (
    <Card>
      <CardHeader>
        <CardTitle>持仓分析 ({safePositions.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-2">
            <div className="p-2 border rounded text-center">
              <p className="text-xs text-muted-foreground">总浮盈</p>
              <p className={`text-lg font-bold ${totalPnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                {totalPnl >= 0 ? "+" : ""}¥{totalPnl.toFixed(2)}
              </p>
            </div>
            <div className="p-2 border rounded text-center">
              <p className="text-xs text-muted-foreground">多头</p>
              <p className="text-lg font-bold">{longCount}</p>
            </div>
            <div className="p-2 border rounded text-center">
              <p className="text-xs text-muted-foreground">空头</p>
              <p className="text-lg font-bold">{shortCount}</p>
            </div>
          </div>

          {safePositions.length === 0 ? (
            <p className="text-muted-foreground text-sm">暂无持仓</p>
          ) : (
            <div className="space-y-2">
              {safePositions.map((pos, idx) => (
                <div key={idx} className="p-3 border rounded">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{pos.instrument_id}</p>
                        <Badge variant={pos.direction === "long" ? "default" : "secondary"}>
                          {pos.direction === "long" ? "多" : "空"}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {pos.volume}手 @ ¥{pos.avg_price} → ¥{pos.current_price}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`font-medium ${pos.float_pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                        {pos.float_pnl >= 0 ? "+" : ""}¥{pos.float_pnl.toFixed(2)}
                      </p>
                      {onClose && (
                        <Button size="sm" variant="outline" className="mt-1" onClick={() => onClose(pos)}>
                          平仓
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
