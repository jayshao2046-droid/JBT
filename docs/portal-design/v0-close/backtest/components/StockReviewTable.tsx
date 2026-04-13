"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { CheckCircle } from "lucide-react"
import { toast } from "sonner"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8103"

interface StockStrategy {
  strategy_id: string
  name: string
  symbols: string[]
  total_return: number
  max_drawdown: number
  sharpe_ratio: number
  submitted_at: string
}

export default function StockReviewTable() {
  const [strategies, setStrategies] = useState<StockStrategy[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(false)

  const fetchPending = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/v1/stock/approval/pending`)
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
      const data = await res.json()
      setStrategies(Array.isArray(data.strategies) ? data.strategies : [])
    } catch (err: any) {
      toast.error(`加载失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPending()
  }, [])

  const handleToggle = (strategyId: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(strategyId)) {
        next.delete(strategyId)
      } else {
        next.add(strategyId)
      }
      return next
    })
  }

  const handleToggleAll = () => {
    if (selected.size === strategies.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(strategies.map(s => s.strategy_id)))
    }
  }

  const handleApprove = async (strategyId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/stock/approval/${strategyId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      })
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
      toast.success("审核通过")
      fetchPending()
    } catch (err: any) {
      toast.error(`审核失败: ${err.message}`)
    }
  }

  const handleBatchApprove = async () => {
    if (selected.size === 0) {
      toast.error("请先选择策略")
      return
    }

    const promises = Array.from(selected).map(id => handleApprove(id))
    await Promise.all(promises)
    setSelected(new Set())
  }

  if (loading) {
    return <div className="text-neutral-400">加载中...</div>
  }

  if (strategies.length === 0) {
    return (
      <Card className="bg-neutral-900 border-neutral-800">
        <CardContent className="p-6 text-center text-neutral-400">
          暂无待审核股票策略
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="bg-neutral-900 border-neutral-800">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-white">股票策略待审列表</CardTitle>
          <Button
            onClick={handleBatchApprove}
            disabled={selected.size === 0}
            size="sm"
            className="gap-2 bg-green-600 hover:bg-green-700"
          >
            <CheckCircle className="h-4 w-4" />
            批量通过 ({selected.size})
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="text-left p-3">
                  <Checkbox
                    checked={selected.size === strategies.length && strategies.length > 0}
                    onCheckedChange={handleToggleAll}
                  />
                </th>
                <th className="text-left p-3 text-neutral-400">策略名</th>
                <th className="text-left p-3 text-neutral-400">符号列表</th>
                <th className="text-right p-3 text-neutral-400">回测收益</th>
                <th className="text-right p-3 text-neutral-400">最大回撤</th>
                <th className="text-right p-3 text-neutral-400">夏普比率</th>
                <th className="text-center p-3 text-neutral-400">操作</th>
              </tr>
            </thead>
            <tbody>
              {strategies.map((strategy) => (
                <tr key={strategy.strategy_id} className="border-b border-neutral-800 hover:bg-neutral-800/50">
                  <td className="p-3">
                    <Checkbox
                      checked={selected.has(strategy.strategy_id)}
                      onCheckedChange={() => handleToggle(strategy.strategy_id)}
                    />
                  </td>
                  <td className="p-3 text-white">{strategy.name}</td>
                  <td className="p-3 text-neutral-300">
                    {strategy.symbols.slice(0, 3).join(", ")}
                    {strategy.symbols.length > 3 && ` +${strategy.symbols.length - 3}`}
                  </td>
                  <td className="p-3 text-right text-white">
                    {(strategy.total_return * 100).toFixed(2)}%
                  </td>
                  <td className="p-3 text-right text-white">
                    {(strategy.max_drawdown * 100).toFixed(2)}%
                  </td>
                  <td className="p-3 text-right text-white">
                    {strategy.sharpe_ratio.toFixed(2)}
                  </td>
                  <td className="p-3 text-center">
                    <Button
                      onClick={() => handleApprove(strategy.strategy_id)}
                      size="sm"
                      variant="outline"
                      className="gap-2"
                    >
                      <CheckCircle className="h-4 w-4" />
                      通过
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
