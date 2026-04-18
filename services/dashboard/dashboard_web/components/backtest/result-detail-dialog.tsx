"use client"

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { TrendingUp, TrendingDown, Activity, BarChart3 } from "lucide-react"
import type { BacktestResult } from "@/lib/api/backtest"

interface ResultDetailDialogProps {
  result: BacktestResult
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function ResultDetailDialog({ result, open, onOpenChange }: ResultDetailDialogProps) {
  const { performance, equity_curve, trades } = result

  const winTrades = trades.filter(t => t.pnl > 0).length
  const lossTrades = trades.filter(t => t.pnl < 0).length
  const avgWin = trades.filter(t => t.pnl > 0).reduce((sum, t) => sum + t.pnl, 0) / (winTrades || 1)
  const avgLoss = trades.filter(t => t.pnl < 0).reduce((sum, t) => sum + t.pnl, 0) / (lossTrades || 1)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            回测详情 - {result.strategy_name}
          </DialogTitle>
        </DialogHeader>

        <ScrollArea className="h-[70vh] pr-4">
          <div className="space-y-4">
            {/* 绩效指标 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="w-4 h-4" />
                  绩效指标
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="p-3 border rounded">
                    <p className="text-xs text-muted-foreground mb-1">总收益</p>
                    <p className={`text-lg font-bold ${performance.total_return >= 0 ? "text-green-500" : "text-red-500"}`}>
                      {(performance.total_return * 100).toFixed(2)}%
                    </p>
                  </div>
                  <div className="p-3 border rounded">
                    <p className="text-xs text-muted-foreground mb-1">夏普比率</p>
                    <p className="text-lg font-bold">{performance.sharpe_ratio.toFixed(2)}</p>
                  </div>
                  <div className="p-3 border rounded">
                    <p className="text-xs text-muted-foreground mb-1">最大回撤</p>
                    <p className="text-lg font-bold text-red-500">
                      {(performance.max_drawdown * 100).toFixed(2)}%
                    </p>
                  </div>
                  <div className="p-3 border rounded">
                    <p className="text-xs text-muted-foreground mb-1">胜率</p>
                    <p className="text-lg font-bold">{(performance.win_rate * 100).toFixed(1)}%</p>
                  </div>
                  <div className="p-3 border rounded">
                    <p className="text-xs text-muted-foreground mb-1">交易次数</p>
                    <p className="text-lg font-bold">{performance.total_trades}</p>
                  </div>
                  <div className="p-3 border rounded">
                    <p className="text-xs text-muted-foreground mb-1">盈亏比</p>
                    <p className="text-lg font-bold">
                      {avgLoss !== 0 ? (avgWin / Math.abs(avgLoss)).toFixed(2) : "N/A"}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 交易统计 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">交易统计</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-2 bg-green-50 rounded">
                      <span className="text-sm flex items-center gap-1">
                        <TrendingUp className="w-4 h-4 text-green-500" />
                        盈利交易
                      </span>
                      <Badge variant="default" className="bg-green-500">{winTrades}</Badge>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-red-50 rounded">
                      <span className="text-sm flex items-center gap-1">
                        <TrendingDown className="w-4 h-4 text-red-500" />
                        亏损交易
                      </span>
                      <Badge variant="destructive">{lossTrades}</Badge>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="p-2 border rounded">
                      <p className="text-xs text-muted-foreground">平均盈利</p>
                      <p className="text-sm font-medium text-green-500">
                        {avgWin.toFixed(2)}
                      </p>
                    </div>
                    <div className="p-2 border rounded">
                      <p className="text-xs text-muted-foreground">平均亏损</p>
                      <p className="text-sm font-medium text-red-500">
                        {avgLoss.toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 权益曲线 */}
            {equity_curve.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">权益曲线</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-48 flex items-end gap-1">
                    {equity_curve.slice(0, 50).map((point, index) => {
                      const height = ((point.equity - equity_curve[0].equity) / equity_curve[0].equity) * 100
                      return (
                        <div
                          key={index}
                          className="flex-1 bg-blue-500 rounded-t"
                          style={{
                            height: `${Math.max(5, 50 + height)}%`,
                            opacity: 0.7,
                          }}
                          title={`${point.timestamp}: ${point.equity.toFixed(2)}`}
                        />
                      )
                    })}
                  </div>
                  <p className="text-xs text-muted-foreground text-center mt-2">
                    显示前 50 个数据点
                  </p>
                </CardContent>
              </Card>
            )}

            {/* 交易记录 */}
            {trades.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">交易记录 (最近 20 笔)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {trades.slice(0, 20).map((trade, index) => (
                      <div key={index} className="flex items-center justify-between p-2 border rounded text-sm">
                        <div className="flex items-center gap-3">
                          <Badge variant={trade.direction === "buy" ? "default" : "secondary"}>
                            {trade.direction === "buy" ? "买入" : "卖出"}
                          </Badge>
                          <span className="font-medium">{trade.symbol}</span>
                          <span className="text-muted-foreground">
                            {new Date(trade.timestamp).toLocaleString("zh-CN")}
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span>¥{trade.price.toFixed(2)}</span>
                          <span className="text-muted-foreground">x{trade.volume}</span>
                          <span className={`font-medium ${trade.pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                            {trade.pnl >= 0 ? "+" : ""}{trade.pnl.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}
