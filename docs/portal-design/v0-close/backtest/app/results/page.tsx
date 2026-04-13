"use client"

import { useState, useEffect } from "react"
import { backtestApi, BacktestResult } from "@/lib/backtest-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { toast } from "sonner"
import { Calendar, TrendingUp, TrendingDown, Activity } from "lucide-react"

export default function ResultsPage() {
  const [results, setResults] = useState<BacktestResult[]>([])
  const [loading, setLoading] = useState(true)
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")

  const fetchHistory = async () => {
    try {
      setLoading(true)
      const data = await backtestApi.backtestHistory({
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      })
      setResults(data.history)
    } catch (error: any) {
      toast.error(`加载历史失败: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  const handleFilter = () => {
    fetchHistory()
  }

  const handleReset = () => {
    setStartDate("")
    setEndDate("")
    setTimeout(() => fetchHistory(), 100)
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">回测历史</h1>
        <Button onClick={fetchHistory} disabled={loading}>
          刷新
        </Button>
      </div>

      {/* 日期筛选 */}
      <Card className="bg-neutral-800 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            日期筛选
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm text-neutral-400 mb-2 block">开始日期</label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="bg-neutral-900 border-neutral-700 text-white"
              />
            </div>
            <div>
              <label className="text-sm text-neutral-400 mb-2 block">结束日期</label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="bg-neutral-900 border-neutral-700 text-white"
              />
            </div>
            <div className="flex items-end gap-2">
              <Button onClick={handleFilter} className="flex-1">
                筛选
              </Button>
              <Button onClick={handleReset} variant="outline">
                重置
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-neutral-800 border-neutral-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-400">总回测数</p>
                <p className="text-2xl font-bold text-white">{results.length}</p>
              </div>
              <Activity className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-800 border-neutral-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-400">已完成</p>
                <p className="text-2xl font-bold text-green-500">
                  {results.filter((r) => r.status === "completed").length}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-800 border-neutral-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-400">运行中</p>
                <p className="text-2xl font-bold text-orange-500">
                  {results.filter((r) => r.status === "running" || r.status === "submitted").length}
                </p>
              </div>
              <Activity className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-800 border-neutral-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-400">失败</p>
                <p className="text-2xl font-bold text-red-500">
                  {results.filter((r) => r.status === "failed").length}
                </p>
              </div>
              <TrendingDown className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 回测列表 */}
      <Card className="bg-neutral-800 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-white">回测记录</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-neutral-400">加载中...</div>
          ) : results.length === 0 ? (
            <div className="text-center py-8 text-neutral-400">暂无回测记录</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-neutral-700">
                    <th className="text-left py-3 px-4 text-sm font-medium text-neutral-400">策略名称</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-neutral-400">状态</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-neutral-400">时间范围</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-neutral-400">总收益率</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-neutral-400">年化收益</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-neutral-400">最大回撤</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-neutral-400">夏普比率</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-neutral-400">交易次数</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((result) => (
                    <tr key={result.id} className="border-b border-neutral-700 hover:bg-neutral-750">
                      <td className="py-3 px-4 text-sm text-white">{result.name}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                            result.status === "completed"
                              ? "bg-green-500/20 text-green-400"
                              : result.status === "running" || result.status === "submitted"
                              ? "bg-orange-500/20 text-orange-400"
                              : "bg-red-500/20 text-red-400"
                          }`}
                        >
                          {result.status === "completed"
                            ? "已完成"
                            : result.status === "running"
                            ? "运行中"
                            : result.status === "submitted"
                            ? "已提交"
                            : "失败"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-neutral-300">
                        {result.payload?.start} ~ {result.payload?.end}
                      </td>
                      <td
                        className={`py-3 px-4 text-sm text-right font-mono ${
                          result.totalReturn >= 0 ? "text-green-400" : "text-red-400"
                        }`}
                      >
                        {result.totalReturn >= 0 ? "+" : ""}
                        {result.totalReturn?.toFixed(2)}%
                      </td>
                      <td
                        className={`py-3 px-4 text-sm text-right font-mono ${
                          result.annualReturn >= 0 ? "text-green-400" : "text-red-400"
                        }`}
                      >
                        {result.annualReturn >= 0 ? "+" : ""}
                        {result.annualReturn?.toFixed(2)}%
                      </td>
                      <td className="py-3 px-4 text-sm text-right font-mono text-red-400">
                        -{result.maxDrawdown?.toFixed(2)}%
                      </td>
                      <td className="py-3 px-4 text-sm text-right font-mono text-neutral-300">
                        {result.sharpeRatio?.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-sm text-right font-mono text-neutral-300">
                        {result.totalTrades}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
