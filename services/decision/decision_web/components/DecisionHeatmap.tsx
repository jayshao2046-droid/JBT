"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Flame } from "lucide-react"

interface DecisionHeatmapProps {
  data?: any[]
}

export function DecisionHeatmap({ data = [] }: DecisionHeatmapProps) {
  // 生成参数热力图数据（参数组合 vs 收益率）
  const paramHeatmapData = [
    { stopLoss: 0.02, takeProfit: 0.05, return: 2.3 },
    { stopLoss: 0.02, takeProfit: 0.08, return: 3.5 },
    { stopLoss: 0.02, takeProfit: 0.10, return: 4.2 },
    { stopLoss: 0.03, takeProfit: 0.05, return: 1.8 },
    { stopLoss: 0.03, takeProfit: 0.08, return: 3.1 },
    { stopLoss: 0.03, takeProfit: 0.10, return: 3.8 },
    { stopLoss: 0.05, takeProfit: 0.05, return: 1.2 },
    { stopLoss: 0.05, takeProfit: 0.08, return: 2.5 },
    { stopLoss: 0.05, takeProfit: 0.10, return: 3.2 },
  ]

  // 时间热力图数据（月度信号分布）
  const timeHeatmapData = [
    { month: "2026-01", signals: 45 },
    { month: "2026-02", signals: 52 },
    { month: "2026-03", signals: 38 },
    { month: "2026-04", signals: 61 },
  ]

  const getColorByReturn = (ret: number) => {
    if (ret >= 4) return "bg-green-600"
    if (ret >= 3) return "bg-green-500"
    if (ret >= 2) return "bg-green-400"
    if (ret >= 1) return "bg-yellow-500"
    return "bg-red-500"
  }

  const getColorBySignals = (count: number) => {
    if (count >= 60) return "bg-orange-600"
    if (count >= 50) return "bg-orange-500"
    if (count >= 40) return "bg-orange-400"
    return "bg-orange-300"
  }

  return (
    <div className="space-y-6">
      <Card className="bg-neutral-800 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Flame className="w-5 h-5 text-orange-500" />
            参数热力图（参数组合 vs 收益率）
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="grid grid-cols-4 gap-2 text-xs text-neutral-400">
              <div></div>
              <div className="text-center">止盈 5%</div>
              <div className="text-center">止盈 8%</div>
              <div className="text-center">止盈 10%</div>
            </div>
            {[0.02, 0.03, 0.05].map((stopLoss) => (
              <div key={stopLoss} className="grid grid-cols-4 gap-2">
                <div className="text-xs text-neutral-400 flex items-center">止损 {(stopLoss * 100).toFixed(0)}%</div>
                {[0.05, 0.08, 0.1].map((takeProfit) => {
                  const item = paramHeatmapData.find((d) => d.stopLoss === stopLoss && d.takeProfit === takeProfit)
                  return (
                    <div
                      key={takeProfit}
                      className={`h-16 rounded flex items-center justify-center ${getColorByReturn(item?.return || 0)}`}
                    >
                      <span className="text-white font-bold">{item?.return.toFixed(1)}%</span>
                    </div>
                  )
                })}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="bg-neutral-800 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Flame className="w-5 h-5 text-orange-500" />
            时间热力图（月度信号分布）
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {timeHeatmapData.map((item) => (
              <div
                key={item.month}
                className={`p-4 rounded-lg ${getColorBySignals(item.signals)} flex flex-col items-center justify-center`}
              >
                <div className="text-white font-bold text-2xl">{item.signals}</div>
                <div className="text-white text-sm mt-1">{item.month}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
