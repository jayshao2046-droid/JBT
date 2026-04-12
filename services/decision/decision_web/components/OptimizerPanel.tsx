"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Play } from "lucide-react"
import { toast } from "sonner"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8104"

interface OptimizeResult {
  best_params: Record<string, any>
  best_sharpe: number
  best_return: number
  best_drawdown: number
  all_results: Array<{
    params: Record<string, any>
    sharpe: number
    total_return: number
    max_drawdown: number
  }>
}

export function OptimizerPanel() {
  const [strategyId, setStrategyId] = useState("")
  const [optimizing, setOptimizing] = useState(false)
  const [result, setResult] = useState<OptimizeResult | null>(null)

  const handleOptimize = async () => {
    if (!strategyId.trim()) {
      toast.error("请输入策略 ID")
      return
    }

    setOptimizing(true)
    try {
      const res = await fetch(`${API_BASE}/api/v1/research/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ strategy_id: strategyId })
      })

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || `${res.status} ${res.statusText}`)
      }

      const data = await res.json()
      setResult(data)
      toast.success("调优完成")
    } catch (err: any) {
      toast.error(`调优失败: ${err.message}`)
    } finally {
      setOptimizing(false)
    }
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
            <Button onClick={handleOptimize} disabled={optimizing} className="gap-2">
              <Play className="h-4 w-4" />
              {optimizing ? "调优中..." : "开始调优"}
            </Button>
          </div>
          <p className="text-sm text-neutral-400">
            使用后端默认参数空间进行网格搜索
          </p>
        </CardContent>
      </Card>

      {result && (
        <>
          <Card className="bg-neutral-900 border-neutral-800">
            <CardHeader>
              <CardTitle className="text-white">最优参数组合</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <div className="text-sm text-neutral-400">夏普比率</div>
                  <div className="text-2xl font-bold text-green-400">
                    {result.best_sharpe.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-neutral-400">总收益</div>
                  <div className="text-2xl font-bold text-white">
                    {(result.best_return * 100).toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-neutral-400">最大回撤</div>
                  <div className="text-2xl font-bold text-red-400">
                    {(result.best_drawdown * 100).toFixed(2)}%
                  </div>
                </div>
              </div>
              <div className="p-4 bg-neutral-800 rounded">
                <div className="text-sm text-neutral-400 mb-2">参数:</div>
                <pre className="text-white text-sm">
                  {JSON.stringify(result.best_params, null, 2)}
                </pre>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-neutral-900 border-neutral-800">
            <CardHeader>
              <CardTitle className="text-white">所有结果</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-neutral-800">
                      <th className="text-left p-3 text-neutral-400">参数</th>
                      <th className="text-right p-3 text-neutral-400">夏普</th>
                      <th className="text-right p-3 text-neutral-400">收益</th>
                      <th className="text-right p-3 text-neutral-400">回撤</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.all_results.map((r, i) => (
                      <tr
                        key={i}
                        className={`border-b border-neutral-800 ${
                          i === 0 ? "bg-green-900/20" : ""
                        }`}
                      >
                        <td className="p-3 text-neutral-300">
                          {JSON.stringify(r.params)}
                        </td>
                        <td className="p-3 text-right text-white">
                          {r.sharpe.toFixed(2)}
                        </td>
                        <td className="p-3 text-right text-white">
                          {(r.total_return * 100).toFixed(2)}%
                        </td>
                        <td className="p-3 text-right text-white">
                          {(r.max_drawdown * 100).toFixed(2)}%
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
