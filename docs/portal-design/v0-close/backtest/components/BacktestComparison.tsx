"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { BarChart3 } from "lucide-react"

interface BacktestComparisonProps {
  results: any[]
}

export function BacktestComparison({ results }: BacktestComparisonProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([])

  const toggleSelection = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  const selectedResults = results.filter((r) => selectedIds.includes(r.id))

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-500" />
          回测结果对比
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 选择列表 */}
        <div className="space-y-2">
          <div className="text-sm text-neutral-400">选择要对比的回测（最多 3 个）</div>
          {results.slice(0, 10).map((result) => (
            <div key={result.id} className="flex items-center gap-2">
              <Checkbox
                checked={selectedIds.includes(result.id)}
                onCheckedChange={() => toggleSelection(result.id)}
                disabled={!selectedIds.includes(result.id) && selectedIds.length >= 3}
              />
              <span className="text-sm text-white">{result.name}</span>
            </div>
          ))}
        </div>

        {/* 对比表格 */}
        {selectedResults.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="text-left py-2 px-3 text-xs font-medium text-neutral-400">指标</th>
                  {selectedResults.map((result) => (
                    <th key={result.id} className="text-right py-2 px-3 text-xs font-medium text-neutral-400">
                      {result.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-neutral-700">
                  <td className="py-2 px-3 text-xs text-neutral-300">总收益率</td>
                  {selectedResults.map((result) => (
                    <td key={result.id} className={`py-2 px-3 text-xs text-right font-mono ${result.totalReturn >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {result.totalReturn >= 0 ? "+" : ""}{result.totalReturn?.toFixed(2)}%
                    </td>
                  ))}
                </tr>
                <tr className="border-b border-neutral-700">
                  <td className="py-2 px-3 text-xs text-neutral-300">年化收益</td>
                  {selectedResults.map((result) => (
                    <td key={result.id} className={`py-2 px-3 text-xs text-right font-mono ${result.annualReturn >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {result.annualReturn >= 0 ? "+" : ""}{result.annualReturn?.toFixed(2)}%
                    </td>
                  ))}
                </tr>
                <tr className="border-b border-neutral-700">
                  <td className="py-2 px-3 text-xs text-neutral-300">最大回撤</td>
                  {selectedResults.map((result) => (
                    <td key={result.id} className="py-2 px-3 text-xs text-right font-mono text-red-400">
                      -{result.maxDrawdown?.toFixed(2)}%
                    </td>
                  ))}
                </tr>
                <tr className="border-b border-neutral-700">
                  <td className="py-2 px-3 text-xs text-neutral-300">夏普比率</td>
                  {selectedResults.map((result) => (
                    <td key={result.id} className="py-2 px-3 text-xs text-right font-mono text-neutral-300">
                      {result.sharpeRatio?.toFixed(2)}
                    </td>
                  ))}
                </tr>
                <tr className="border-b border-neutral-700">
                  <td className="py-2 px-3 text-xs text-neutral-300">胜率</td>
                  {selectedResults.map((result) => (
                    <td key={result.id} className="py-2 px-3 text-xs text-right font-mono text-neutral-300">
                      {result.winRate?.toFixed(1)}%
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
