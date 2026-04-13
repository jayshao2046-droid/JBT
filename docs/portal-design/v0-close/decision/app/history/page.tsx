"use client"

import { useState, useEffect } from "react"
import { decisionApi } from "@/lib/decision-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { History, Calendar } from "lucide-react"

export default function HistoryPage() {
  const [decisions, setDecisions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")

  const fetchHistory = async () => {
    try {
      setLoading(true)
      const data = await decisionApi.decisionHistory(startDate, endDate)
      setDecisions(data.decisions)
    } catch (error) {
      console.error("Failed to fetch decision history:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  return (
    <div className="min-h-screen bg-neutral-950 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white flex items-center gap-2">
            <History className="w-8 h-8 text-orange-500" />
            决策历史
          </h1>
        </div>

        {/* 筛选器 */}
        <Card className="bg-neutral-800 border-neutral-700">
          <CardContent className="pt-6">
            <div className="flex flex-wrap gap-4 items-end">
              <div className="flex-1 min-w-[200px]">
                <label className="text-sm text-neutral-400 mb-2 block">开始日期</label>
                <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="bg-neutral-900 border-neutral-700 text-white"
                />
              </div>
              <div className="flex-1 min-w-[200px]">
                <label className="text-sm text-neutral-400 mb-2 block">结束日期</label>
                <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="bg-neutral-900 border-neutral-700 text-white"
                />
              </div>
              <Button onClick={fetchHistory} className="bg-orange-600 hover:bg-orange-700">
                <Calendar className="w-4 h-4 mr-2" />
                查询
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 决策列表 */}
        <Card className="bg-neutral-800 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-white">历史记录 ({decisions.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center text-neutral-400 py-8">加载中...</div>
            ) : decisions.length === 0 ? (
              <div className="text-center text-neutral-500 py-8">暂无历史记录</div>
            ) : (
              <div className="space-y-3">
                {decisions.map((decision, index) => (
                  <div key={index} className="p-4 bg-neutral-900 rounded-lg border border-neutral-700">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-white">
                        {decision.decision_id || `决策-${index + 1}`}
                      </span>
                      <span className="text-xs text-neutral-400">{decision.created_at}</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                      <div>
                        <span className="text-neutral-400">策略</span>
                        <div className="text-white">{decision.strategy_id || "未知"}</div>
                      </div>
                      <div>
                        <span className="text-neutral-400">标的</span>
                        <div className="text-white">{decision.symbol || "未知"}</div>
                      </div>
                      <div>
                        <span className="text-neutral-400">信号</span>
                        <div
                          className={
                            decision.signal > 0
                              ? "text-green-400"
                              : decision.signal < 0
                              ? "text-red-400"
                              : "text-neutral-400"
                          }
                        >
                          {decision.signal > 0 ? "买入" : decision.signal < 0 ? "卖出" : "持有"}
                        </div>
                      </div>
                      <div>
                        <span className="text-neutral-400">状态</span>
                        <div className="text-blue-400">{decision.status || "已完成"}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
