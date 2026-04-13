"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TrendingUp, ArrowUpDown } from "lucide-react"

interface Factor {
  name: string
  value: number
  contribution: number
  correlation: number
  effectiveness: number
  stability: number
  coverage: number
}

interface FactorAnalysisProps {
  factors: Factor[]
}

export function FactorAnalysis({ factors }: FactorAnalysisProps) {
  const [sortBy, setSortBy] = useState<"contribution" | "correlation" | "effectiveness">("contribution")
  const [filterType, setFilterType] = useState<"all" | "high" | "medium" | "low">("all")

  const sortedFactors = [...factors].sort((a, b) => {
    return b[sortBy] - a[sortBy]
  })

  const filteredFactors = sortedFactors.filter((f) => {
    if (filterType === "all") return true
    if (filterType === "high") return f.effectiveness >= 0.7
    if (filterType === "medium") return f.effectiveness >= 0.4 && f.effectiveness < 0.7
    if (filterType === "low") return f.effectiveness < 0.4
    return true
  })

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-green-500" />
          因子分析详情
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* 排序和筛选 */}
          <div className="flex flex-wrap gap-2">
            <div className="flex gap-2">
              <Button
                size="sm"
                variant={sortBy === "contribution" ? "default" : "outline"}
                onClick={() => setSortBy("contribution")}
              >
                按贡献度
              </Button>
              <Button
                size="sm"
                variant={sortBy === "correlation" ? "default" : "outline"}
                onClick={() => setSortBy("correlation")}
              >
                按相关性
              </Button>
              <Button
                size="sm"
                variant={sortBy === "effectiveness" ? "default" : "outline"}
                onClick={() => setSortBy("effectiveness")}
              >
                按有效性
              </Button>
            </div>

            <div className="flex gap-2 ml-auto">
              <Button
                size="sm"
                variant={filterType === "all" ? "default" : "outline"}
                onClick={() => setFilterType("all")}
              >
                全部
              </Button>
              <Button
                size="sm"
                variant={filterType === "high" ? "default" : "outline"}
                onClick={() => setFilterType("high")}
              >
                高效
              </Button>
              <Button
                size="sm"
                variant={filterType === "medium" ? "default" : "outline"}
                onClick={() => setFilterType("medium")}
              >
                中效
              </Button>
              <Button
                size="sm"
                variant={filterType === "low" ? "default" : "outline"}
                onClick={() => setFilterType("low")}
              >
                低效
              </Button>
            </div>
          </div>

          {/* 因子列表 */}
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {filteredFactors.map((factor, index) => (
              <div key={index} className="p-3 bg-neutral-900 rounded-lg border border-neutral-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-white">{factor.name}</span>
                  <span className="text-xs text-neutral-400">值: {factor.value.toFixed(2)}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div>
                    <span className="text-neutral-400">贡献度</span>
                    <div className="text-green-400 font-mono">{(factor.contribution * 100).toFixed(1)}%</div>
                  </div>
                  <div>
                    <span className="text-neutral-400">相关性</span>
                    <div className="text-blue-400 font-mono">{factor.correlation.toFixed(2)}</div>
                  </div>
                  <div>
                    <span className="text-neutral-400">有效性</span>
                    <div
                      className={`font-mono ${
                        factor.effectiveness >= 0.7
                          ? "text-green-400"
                          : factor.effectiveness >= 0.4
                          ? "text-orange-400"
                          : "text-red-400"
                      }`}
                    >
                      {(factor.effectiveness * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {filteredFactors.length === 0 && (
            <div className="text-center text-neutral-500 py-8">暂无符合条件的因子</div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
