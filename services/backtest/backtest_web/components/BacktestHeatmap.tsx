"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Flame } from "lucide-react"

interface BacktestHeatmapProps {
  data?: any[]
}

export function BacktestHeatmap({ data = [] }: BacktestHeatmapProps) {
  // 生成月度收益热力图数据
  const months = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
  const years = ["2024", "2025", "2026"]

  // 模拟数据
  const heatmapData = years.map((year) =>
    months.map((month) => ({
      year,
      month,
      return: (Math.random() - 0.5) * 20,
    }))
  ).flat()

  const getColor = (value: number) => {
    if (value > 10) return "bg-green-600"
    if (value > 5) return "bg-green-500"
    if (value > 0) return "bg-green-400"
    if (value > -5) return "bg-red-400"
    if (value > -10) return "bg-red-500"
    return "bg-red-600"
  }

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Flame className="w-5 h-5 text-orange-500" />
          月度收益热力图
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {years.map((year) => (
            <div key={year} className="flex items-center gap-2">
              <div className="w-12 text-xs text-neutral-400">{year}</div>
              <div className="flex gap-1 flex-1">
                {months.map((month, index) => {
                  const dataPoint = heatmapData.find((d) => d.year === year && d.month === month)
                  const value = dataPoint?.return || 0
                  return (
                    <div
                      key={month}
                      className={`flex-1 h-8 rounded ${getColor(value)} flex items-center justify-center text-xs text-white font-mono cursor-pointer hover:opacity-80`}
                      title={`${year} ${month}: ${value.toFixed(1)}%`}
                    >
                      {Math.abs(value) > 5 ? `${value > 0 ? "+" : ""}${value.toFixed(0)}%` : ""}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>

        {/* 图例 */}
        <div className="mt-4 flex items-center justify-center gap-2">
          <span className="text-xs text-neutral-400">收益率:</span>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-red-600 rounded"></div>
            <span className="text-xs text-neutral-400">&lt;-10%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-red-400 rounded"></div>
            <span className="text-xs text-neutral-400">-5%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-green-400 rounded"></div>
            <span className="text-xs text-neutral-400">+5%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 bg-green-600 rounded"></div>
            <span className="text-xs text-neutral-400">&gt;+10%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
