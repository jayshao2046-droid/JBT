"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8104"

interface PostMarketData {
  symbol: string
  rating: string
  price_change: number
  volume_ratio: number
  notes: string
}

export function PostMarketReport({ refreshToken }: { refreshToken: number }) {
  const [data, setData] = useState<PostMarketData[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const res = await fetch(`${API_BASE}/api/v1/stock/post-market`)
        if (res.ok) {
          const result = await res.json()
          setData(result.evaluations || [])
        }
      } catch (err) {
        console.error("Failed to fetch post-market data:", err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [refreshToken])

  const getRatingBadge = (rating: string) => {
    const colors: Record<string, string> = {
      strong: "bg-green-900/20 text-green-400 border-green-800",
      positive: "bg-blue-900/20 text-blue-400 border-blue-800",
      neutral: "bg-neutral-700 text-neutral-300 border-neutral-600",
      negative: "bg-orange-900/20 text-orange-400 border-orange-800",
      weak: "bg-red-900/20 text-red-400 border-red-800"
    }
    return (
      <Badge variant="outline" className={colors[rating] || colors.neutral}>
        {rating}
      </Badge>
    )
  }

  return (
    <Card className="bg-neutral-900 border-neutral-800">
      <CardHeader>
        <CardTitle className="text-white">盘后评估</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-neutral-400">加载中...</div>
        ) : data.length === 0 ? (
          <div className="text-neutral-400">暂无数据</div>
        ) : (
          <div className="space-y-3">
            {data.map((item, i) => (
              <div key={i} className="p-3 bg-neutral-800 rounded">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-semibold">{item.symbol}</span>
                  {getRatingBadge(item.rating)}
                </div>
                <div className="text-sm text-neutral-400 space-y-1">
                  <div>涨幅: {(item.price_change * 100).toFixed(2)}%</div>
                  <div>量比: {item.volume_ratio.toFixed(2)}</div>
                  {item.notes && <div className="text-neutral-500">{item.notes}</div>}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
