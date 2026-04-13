'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { PositionData } from '@/lib/mock-data'
import { cn } from '@/lib/utils'
import { X } from 'lucide-react'

interface CurrentPositionsProps {
  positions: PositionData[]
}

export function CurrentPositions({ positions }: CurrentPositionsProps) {
  const totalPositions = positions.length
  const totalFloatProfit = positions.reduce((sum, p) => sum + p.profitLoss, 0)
  const totalMargin = positions.length * 100000 // 示例值

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base text-foreground">当前持仓</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="overflow-x-auto">
          <div className="space-y-2 min-w-max md:min-w-full">
            {/* Header */}
            <div className="grid grid-cols-8 gap-2 px-3 py-2 bg-white/[0.05] rounded text-xs font-medium text-muted-foreground sticky top-0">
              <div>品种</div>
              <div>方向</div>
              <div className="text-right">数量</div>
              <div className="text-right">成本价</div>
              <div className="text-right">现价</div>
              <div className="text-right">盈亏</div>
              <div className="text-right">比例</div>
              <div className="text-center">操作</div>
            </div>

            {/* Rows */}
            {positions.map((position) => (
              <div
                key={position.id}
                className="grid grid-cols-8 gap-2 px-3 py-2 bg-white/[0.02] hover:bg-white/[0.05] rounded transition-colors text-sm"
              >
                <div className="font-mono font-semibold text-foreground">{position.symbol}</div>
                <div>
                  <Badge
                    variant="outline"
                    className={cn(
                      position.direction === 'long'
                        ? 'bg-red-500/20 text-red-400 border-red-500/30'
                        : 'bg-green-500/20 text-green-400 border-green-500/30'
                    )}
                  >
                    {position.direction === 'long' ? '多头' : '空头'}
                  </Badge>
                </div>
                <div className="text-right text-foreground">{position.quantity}</div>
                <div className="text-right text-muted-foreground font-mono">{position.costPrice.toFixed(2)}</div>
                <div className="text-right text-muted-foreground font-mono">{position.currentPrice.toFixed(2)}</div>
                <div
                  className={cn(
                    'text-right font-mono font-semibold',
                    position.profitLoss >= 0 ? 'text-red-400' : 'text-green-400'
                  )}
                >
                  {position.profitLoss >= 0 ? '+' : ''}{position.profitLoss.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </div>
                <div
                  className={cn(
                    'text-right font-mono',
                    position.profitLossPercent >= 0 ? 'text-red-400' : 'text-green-400'
                  )}
                >
                  {position.profitLossPercent >= 0 ? '+' : ''}{position.profitLossPercent.toFixed(2)}%
                </div>
                <div className="text-center">
                  <Button size="sm" variant="ghost" className="h-6 w-6 p-0 hover:bg-red-500/20 hover:text-red-400">
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Summary */}
        <div className="grid grid-cols-3 gap-3 pt-3 border-t border-border">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">总持仓数</p>
            <p className="text-lg font-semibold text-foreground">{totalPositions}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">总浮盈</p>
            <p className="text-lg font-semibold text-red-400">
              +¥{totalFloatProfit.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">保证金占用</p>
            <p className="text-lg font-semibold text-orange-400">
              ¥{(totalMargin / 10000).toFixed(0)}万
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
