"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useState } from "react"

export function OptimizerPanel() {
  const [strategyId, setStrategyId] = useState("")
  const [paramRanges, setParamRanges] = useState("")
  const [optimizing, setOptimizing] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleOptimize = async () => {
    try {
      setOptimizing(true)
      setResult(null)

      // 后端路由: POST /api/v1/optimizer/run (prefix /api/v1/optimizer + /run)
      // 代理: /api/decision/api/v1/optimizer/run → http://8104/api/v1/optimizer/run
      const res = await fetch("/api/decision/api/v1/optimizer/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategy_id: strategyId,
          param_ranges: JSON.parse(paramRanges || "{}"),
        }),
      })

      if (!res.ok) {
        throw new Error(`Optimization failed: ${res.status}`)
      }

      const data = await res.json()
      setResult(`优化完成: ${JSON.stringify(data, null, 2)}`)
    } catch (err) {
      setResult(`优化失败: ${err instanceof Error ? err.message : "Unknown error"}`)
    } finally {
      setOptimizing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>参数优化器</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="opt-strategy-id">策略ID</Label>
          <Input
            id="opt-strategy-id"
            value={strategyId}
            onChange={(e) => setStrategyId(e.target.value)}
            placeholder="例如: strategy_001"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="param-ranges">参数范围（JSON格式）</Label>
          <textarea
            id="param-ranges"
            value={paramRanges}
            onChange={(e) => setParamRanges(e.target.value)}
            placeholder='例如: {"lookback": [10, 20, 30], "threshold": [0.5, 1.0, 1.5]}'
            rows={4}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </div>

        <Button onClick={handleOptimize} disabled={optimizing || !strategyId}>
          {optimizing ? "优化中..." : "开始优化"}
        </Button>

        {result && (
          <div className="text-sm">
            <pre className="bg-muted p-3 rounded-md overflow-x-auto">
              {result}
            </pre>
          </div>
        )}

        <div className="text-xs text-muted-foreground">
          <div className="font-medium mb-1">使用说明:</div>
          <ul className="list-disc list-inside space-y-1">
            <li>输入策略ID和参数范围</li>
            <li>参数范围使用JSON格式，每个参数对应一个数组</li>
            <li>优化器会遍历所有参数组合并返回最优结果</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}
