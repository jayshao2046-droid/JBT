"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { FileText, Download } from "lucide-react"
import { toast } from "sonner"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8104"

interface Report {
  strategy_id: string
  total_return: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  total_trades: number
  avg_trade_return: number
  profit_factor: number
  trades: Array<{
    entry_time: string
    exit_time: string
    symbol: string
    direction: string
    pnl: number
  }>
}

export function ReportViewer() {
  const [strategyId, setStrategyId] = useState("")
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<Report | null>(null)

  const handleFetch = async () => {
    if (!strategyId.trim()) {
      toast.error("请输入策略 ID")
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/v1/research/report/${encodeURIComponent(strategyId)}`)
      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || `${res.status} ${res.statusText}`)
      }

      const data = await res.json()
      setReport(data)
      toast.success("报告加载成功")
    } catch (err: any) {
      toast.error(`加载失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = () => {
    if (!report) return

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `report_${strategyId}_${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
    toast.success("导出成功")
  }

  return (
    <div className="space-y-6">
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader>
          <CardTitle className="text-white">策略选择</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Input
              placeholder="输入策略 ID"
              value={strategyId}
              onChange={(e) => setStrategyId(e.target.value)}
              className="bg-neutral-800 border-neutral-700 text-white"
            />
            <Button onClick={handleFetch} disabled={loading} className="gap-2">
              <FileText className="h-4 w-4" />
              {loading ? "加载中..." : "查看报告"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {report && (
        <>
          <Card className="bg-neutral-900 border-neutral-800">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white">报告概览</CardTitle>
                <Button onClick={handleExport} variant="outline" size="sm" className="gap-2">
                  <Download className="h-4 w-4" />
                  导出 JSON
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                <div>
                  <div className="text-sm text-neutral-400">总收益</div>
                  <div className="text-xl font-bold text-white">
                    {(report.total_return * 100).toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-neutral-400">夏普比率</div>
                  <div className="text-xl font-bold text-white">
                    {report.sharpe_ratio.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-neutral-400">最大回撤</div>
                  <div className="text-xl font-bold text-red-400">
                    {(report.max_drawdown * 100).toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-neutral-400">胜率</div>
                  <div className="text-xl font-bold text-white">
                    {(report.win_rate * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-neutral-400">交易次数</div>
                  <div className="text-xl font-bold text-white">
                    {report.total_trades}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-neutral-900 border-neutral-800">
            <CardHeader>
              <CardTitle className="text-white">交易明细</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-neutral-800">
                      <th className="text-left p-3 text-neutral-400">入场时间</th>
                      <th className="text-left p-3 text-neutral-400">出场时间</th>
                      <th className="text-left p-3 text-neutral-400">标的</th>
                      <th className="text-left p-3 text-neutral-400">方向</th>
                      <th className="text-right p-3 text-neutral-400">盈亏</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.trades.map((trade, i) => (
                      <tr key={i} className="border-b border-neutral-800">
                        <td className="p-3 text-neutral-300">{trade.entry_time}</td>
                        <td className="p-3 text-neutral-300">{trade.exit_time}</td>
                        <td className="p-3 text-white">{trade.symbol}</td>
                        <td className="p-3 text-neutral-300">{trade.direction}</td>
                        <td className={`p-3 text-right font-semibold ${
                          trade.pnl >= 0 ? "text-green-400" : "text-red-400"
                        }`}>
                          {trade.pnl >= 0 ? "+" : ""}{trade.pnl.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
