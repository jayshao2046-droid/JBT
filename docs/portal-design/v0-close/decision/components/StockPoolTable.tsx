"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

interface StockPoolData {
  pool_id: string
  symbols: string[]
  max_size: number
  updated_at: string
}

export function StockPoolTable({ refreshToken }: { refreshToken?: number }) {
  const [poolData, setPoolData] = useState<StockPoolData | null>(null)
  const [newSymbol, setNewSymbol] = useState("")
  const [loading, setLoading] = useState(false)

  const fetchPool = async () => {
    try {
      const res = await fetch("/api/decision/v1/stock/pool")
      const data = await res.json()
      setPoolData(data)
    } catch (error) {
      console.error("Failed to fetch pool:", error)
    }
  }

  useEffect(() => {
    fetchPool()
  }, [refreshToken])

  const handleAdd = async () => {
    if (!newSymbol.trim()) return
    setLoading(true)
    try {
      await fetch("/api/decision/v1/stock/pool", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol: newSymbol.trim() })
      })
      setNewSymbol("")
      await fetchPool()
    } catch (error) {
      console.error("Failed to add symbol:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleRemove = async (symbol: string) => {
    setLoading(true)
    try {
      await fetch(`/api/decision/v1/stock/pool/${symbol}`, {
        method: "DELETE"
      })
      await fetchPool()
    } catch (error) {
      console.error("Failed to remove symbol:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="bg-neutral-900 border-neutral-800">
      <CardHeader>
        <CardTitle className="text-white">股票池管理</CardTitle>
        <p className="text-sm text-neutral-400">
          当前 {poolData?.symbols.length || 0} / {poolData?.max_size || 30} 只股票
        </p>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2 mb-4">
          {poolData?.symbols.map((symbol) => (
            <Badge
              key={symbol}
              variant="secondary"
              className="bg-neutral-800 text-white hover:bg-neutral-700 cursor-pointer"
              onClick={() => handleRemove(symbol)}
            >
              {symbol} ×
            </Badge>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value)}
            placeholder="输入股票代码（如 600000.SH）"
            className="flex-1 px-3 py-2 bg-neutral-950 border border-neutral-800 rounded text-white placeholder:text-neutral-500"
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          />
          <Button
            onClick={handleAdd}
            disabled={loading || !newSymbol.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            添加
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
