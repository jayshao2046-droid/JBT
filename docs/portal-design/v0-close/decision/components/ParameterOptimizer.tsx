"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Settings, Play } from "lucide-react"
import { decisionApi } from "@/lib/decision-api"

export function ParameterOptimizer() {
  const [strategyId, setStrategyId] = useState("strategy_001")
  const [paramGrid, setParamGrid] = useState({
    stop_loss: [0.02, 0.03, 0.05],
    take_profit: [0.05, 0.08, 0.10],
  })
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const handleOptimize = async () => {
    try {
      setLoading(true)
      const data = await decisionApi.batchDecision({
        strategy_id: strategyId,
        param_grid: paramGrid,
      })
      setResults(data.tasks || [])
    } catch (error) {
      console.error("Failed to optimize:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Settings className="w-5 h-5 text-purple-500" />
          参数优化器
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <Label className="text-neutral-300">策略 ID</Label>
            <Input
              value={strategyId}
              onChange={(e) => setStrategyId(e.target.value)}
              className="bg-neutral-900 border-neutral-700 text-white"
            />
          </div>

          <div>
            <Label className="text-neutral-300">参数网格（JSON）</Label>
            <textarea
              value={JSON.stringify(paramGrid, null, 2)}
              onChange={(e) => {
                try {
                  setParamGrid(JSON.parse(e.target.value))
                } catch (err) {
                  // 忽略解析错误
                }
              }}
              className="w-full h-32 p-2 bg-neutral-900 border border-neutral-700 text-white rounded font-mono text-sm"
            />
          </div>

          <Button onClick={handleOptimize} disabled={loading} className="w-full">
            <Play className="w-4 h-4 mr-2" />
            {loading ? "优化中..." : "开始优化"}
          </Button>

          {results.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-white mb-2">优化结果 ({results.length} 个任务)</h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {results.slice(0, 10).map((task, index) => (
                  <div key={index} className="p-3 bg-neutral-900 rounded border border-neutral-700 text-xs">
                    <div className="text-neutral-400">任务 {index + 1}</div>
                    <div className="text-white font-mono">{JSON.stringify(task.params)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
