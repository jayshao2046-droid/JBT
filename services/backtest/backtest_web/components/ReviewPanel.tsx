"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Play, CheckCircle, XCircle } from "lucide-react"
import { toast } from "sonner"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8103"

interface Strategy {
  strategy_id: string
  name: string
  submitted_at: string
  status: string
  total_return?: number
  max_drawdown?: number
  sharpe_ratio?: number
  win_rate?: number
}

export default function ReviewPanel() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [loading, setLoading] = useState(false)

  const fetchQueue = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/v1/strategy/queue`)
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
    fetchQueue()
  }, [])

  const handleRun = async (strategyId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/strategy/queue/${strategyId}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      })
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
      toast.success("回测已启动")
      fetchQueue()
    } catch (err: any) {
      toast.error(`执行失败: ${err.message}`)
    }
  }

  const handleApprove = async (strategyId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/strategy/queue/${strategyId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      })
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
      toast.success("审核通过")
      fetchQueue()
    } catch (err: any) {
      toast.error(`审核失败: ${err.message}`)
    }
  }

  const handleReject = async (strategyId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/strategy/queue/${strategyId}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      })
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
      toast.success("已拒绝")
      fetchQueue()
    } catch (err: any) {
      toast.error(`拒绝失败: ${err.message}`)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "pending":
        return <Badge variant="outline" className="bg-yellow-900/20 text-yellow-400 border-yellow-800">待审核</Badge>
      case "running":
        return <Badge variant="outline" className="bg-blue-900/20 text-blue-400 border-blue-800">运行中</Badge>
      case "completed":
        return <Badge variant="outline" className="bg-green-900/20 text-green-400 border-green-800">已完成</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  if (loading) {
    return <div className="text-neutral-400">加载中...</div>
  }

  if (strategies.length === 0) {
    return (
      <Card className="bg-neutral-900 border-neutral-800">
        <CardContent className="p-6 text-center text-neutral-400">
          暂无待审核策略
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {strategies.map((strategy) => (
        <Card key={strategy.strategy_id} className="bg-neutral-900 border-neutral-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg text-white">{strategy.name}</CardTitle>
              {getStatusBadge(strategy.status)}
            </div>
            <div className="text-sm text-neutral-400">
              提交时间: {new Date(strategy.submitted_at).toLocaleString("zh-CN")}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {strategy.status === "completed" && (
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="text-neutral-400">总收益</div>
                  <div className="text-white font-semibold">
                    {strategy.total_return != null ? `${(strategy.total_return * 100).toFixed(2)}%` : "N/A"}
                  </div>
                </div>
                <div>
                  <div className="text-neutral-400">最大回撤</div>
                  <div className="text-white font-semibold">
                    {strategy.max_drawdown != null ? `${(strategy.max_drawdown * 100).toFixed(2)}%` : "N/A"}
                  </div>
                </div>
                <div>
                  <div className="text-neutral-400">夏普比率</div>
                  <div className="text-white font-semibold">
                    {strategy.sharpe_ratio != null ? strategy.sharpe_ratio.toFixed(2) : "N/A"}
                  </div>
                </div>
                <div>
                  <div className="text-neutral-400">胜率</div>
                  <div className="text-white font-semibold">
                    {strategy.win_rate != null ? `${(strategy.win_rate * 100).toFixed(1)}%` : "N/A"}
                  </div>
                </div>
              </div>
            )}

            <div className="flex gap-2">
              {strategy.status === "pending" && (
                <Button
                  onClick={() => handleRun(strategy.strategy_id)}
                  size="sm"
                  className="gap-2"
                >
                  <Play className="h-4 w-4" />
                  执行回测
                </Button>
              )}
              {strategy.status === "completed" && (
                <>
                  <Button
                    onClick={() => handleApprove(strategy.strategy_id)}
                    size="sm"
                    className="gap-2 bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircle className="h-4 w-4" />
                    审核通过
                  </Button>
                  <Button
                    onClick={() => handleReject(strategy.strategy_id)}
                    size="sm"
                    variant="destructive"
                    className="gap-2"
                  >
                    <XCircle className="h-4 w-4" />
                    审核拒绝
                  </Button>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
