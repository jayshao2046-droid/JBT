"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowUpDown, Filter } from "lucide-react"

interface TradeDetailAnalysisProps {
  trades: any[]
}

export function TradeDetailAnalysis({ trades }: TradeDetailAnalysisProps) {
  const [sortBy, setSortBy] = useState<"date" | "pnl" | "symbol">("date")
  const [filterDirection, setFilterDirection] = useState<"all" | "long" | "short">("all")

  // 筛选和排序
  let filteredTrades = trades.filter((trade) => {
    if (filterDirection === "all") return true
    const direction = trade.direction?.toLowerCase() || trade.side?.toLowerCase() || ""
    return direction === filterDirection
  })

  filteredTrades = [...filteredTrades].sort((a, b) => {
    if (sortBy === "date") {
      return (a.date || a.entry_time || "").localeCompare(b.date || b.entry_time || "")
    } else if (sortBy === "pnl") {
      return (b.pnl || b.profit || 0) - (a.pnl || a.profit || 0)
    } else {
      return (a.symbol || "").localeCompare(b.symbol || "")
    }
  })

  // 统计
  const winningTrades = trades.filter((t) => (t.pnl || t.profit || 0) > 0)
  const losingTrades = trades.filter((t) => (t.pnl || t.profit || 0) < 0)
  const winRate = trades.length > 0 ? (winningTrades.length / trades.length) * 100 : 0
  const avgWin = winningTrades.length > 0 ? winningTrades.reduce((sum, t) => sum + (t.pnl || t.profit || 0), 0) / winningTrades.length : 0
  const avgLoss = losingTrades.length > 0 ? Math.abs(losingTrades.reduce((sum, t) => sum + (t.pnl || t.profit || 0), 0) / losingTrades.length) : 0
  const profitLossRatio = avgLoss > 0 ? avgWin / avgLoss : 0

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white">交易明细分析</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-3 bg-neutral-900 rounded border border-neutral-700">
            <div className="text-xs text-neutral-400">总交易次数</div>
            <div className="text-xl font-bold text-white">{trades.length}</div>
          </div>
          <div className="p-3 bg-neutral-900 rounded border border-neutral-700">
            <div className="text-xs text-neutral-400">胜率</div>
            <div className="text-xl font-bold text-green-400">{winRate.toFixed(1)}%</div>
          </div>
          <div className="p-3 bg-neutral-900 rounded border border-neutral-700">
            <div className="text-xs text-neutral-400">盈亏比</div>
            <div className="text-xl font-bold text-blue-400">{profitLossRatio.toFixed(2)}</div>
          </div>
          <div className="p-3 bg-neutral-900 rounded border border-neutral-700">
            <div className="text-xs text-neutral-400">平均盈利</div>
            <div className="text-xl font-bold text-green-400">¥{avgWin.toFixed(0)}</div>
          </div>
        </div>

        {/* 筛选和排序 */}
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant={sortBy === "date" ? "default" : "outline"}
            onClick={() => setSortBy("date")}
          >
            按日期
          </Button>
          <Button
            size="sm"
            variant={sortBy === "pnl" ? "default" : "outline"}
            onClick={() => setSortBy("pnl")}
          >
            按盈亏
          </Button>
          <Button
            size="sm"
            variant={sortBy === "symbol" ? "default" : "outline"}
            onClick={() => setSortBy("symbol")}
          >
            按品种
          </Button>
          <div className="ml-auto flex items-center gap-2">
            <Filter className="w-4 h-4 text-neutral-400" />
            <Button
              size="sm"
              variant={filterDirection === "all" ? "default" : "outline"}
              onClick={() => setFilterDirection("all")}
            >
              全部
            </Button>
            <Button
              size="sm"
              variant={filterDirection === "long" ? "default" : "outline"}
              onClick={() => setFilterDirection("long")}
            >
              多头
            </Button>
            <Button
              size="sm"
              variant={filterDirection === "short" ? "default" : "outline"}
              onClick={() => setFilterDirection("short")}
            >
              空头
            </Button>
          </div>
        </div>

        {/* 交易列表 */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-700">
                <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">日期</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">品种</th>
                <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">方向</th>
                <th className="text-right py-2 px-3 text-xs font-medium text-neutral-400">价格</th>
                <th className="text-right py-2 px-3 text-xs font-medium text-neutral-400">数量</th>
                <th className="text-right py-2 px-3 text-xs font-medium text-neutral-400">盈亏</th>
              </tr>
            </thead>
            <tbody>
              {filteredTrades.map((trade, index) => {
                const pnl = trade.pnl || trade.profit || 0
                return (
                  <tr key={index} className="border-b border-neutral-700 hover:bg-neutral-750">
                    <td className="py-2 px-3 text-xs text-neutral-300">{trade.date || trade.entry_time || "-"}</td>
                    <td className="py-2 px-3 text-xs text-white">{trade.symbol || "-"}</td>
                    <td className="py-2 px-3 text-xs">
                      <span className={`${(trade.direction || trade.side || "").toLowerCase() === "long" || (trade.direction || trade.side || "").toLowerCase() === "buy" ? "text-green-400" : "text-red-400"}`}>
                        {trade.direction || trade.side || "-"}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-xs text-right text-neutral-300">{(trade.price || trade.entry_price || 0).toFixed(2)}</td>
                    <td className="py-2 px-3 text-xs text-right text-neutral-300">{trade.volume || trade.quantity || 0}</td>
                    <td className={`py-2 px-3 text-xs text-right font-mono ${pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {pnl >= 0 ? "+" : ""}{pnl.toFixed(2)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
