"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8104"

interface RotationPlan {
  symbol: string
  momentum_score: number
  action: string
}

export function EveningRotationPlan({ refreshToken }: { refreshToken: number }) {
  const [plan, setPlan] = useState<RotationPlan[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const res = await fetch(`${API_BASE}/api/v1/stock/rotation`)
        if (res.ok) {
          const result = await res.json()
          setPlan(result.rotation_plan || [])
        }
      } catch (err) {
        console.error("Failed to fetch rotation plan:", err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [refreshToken])

  return (
    <Card className="bg-neutral-900 border-neutral-800">
      <CardHeader>
        <CardTitle className="text-white">晚间轮换计划</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-neutral-400">加载中...</div>
        ) : plan.length === 0 ? (
          <div className="text-neutral-400">暂无轮换计划</div>
        ) : (
          <div className="space-y-2">
            {plan.map((item, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-neutral-800 rounded">
                <div>
                  <div className="text-white font-semibold">{item.symbol}</div>
                  <div className="text-sm text-neutral-400">
                    动量分: {item.momentum_score.toFixed(2)}
                  </div>
                </div>
                <div className={`text-sm font-semibold ${
                  item.action === "add" ? "text-green-400" : "text-red-400"
                }`}>
                  {item.action === "add" ? "加入" : "移除"}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
