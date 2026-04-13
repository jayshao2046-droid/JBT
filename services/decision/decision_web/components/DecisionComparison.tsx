"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { GitCompare, TrendingUp, Activity } from "lucide-react"

interface DecisionComparisonProps {
  decisionIds: string[]
}

export function DecisionComparison({ decisionIds }: DecisionComparisonProps) {
  const [selectedDecisions, setSelectedDecisions] = useState<string[]>([])

  if (decisionIds.length === 0) {
    return (
      <Card className="bg-neutral-800 border-neutral-700">
        <CardContent className="pt-6">
          <div className="text-center text-neutral-400">暂无决策可对比</div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <GitCompare className="w-5 h-5 text-purple-500" />
          决策结果对比
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {decisionIds.slice(0, 5).map((id) => (
              <Button
                key={id}
                variant={selectedDecisions.includes(id) ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  if (selectedDecisions.includes(id)) {
                    setSelectedDecisions(selectedDecisions.filter((d) => d !== id))
                  } else if (selectedDecisions.length < 3) {
                    setSelectedDecisions([...selectedDecisions, id])
                  }
                }}
                className="text-xs"
              >
                {id.slice(0, 8)}
              </Button>
            ))}
          </div>

          {selectedDecisions.length >= 2 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {selectedDecisions.map((id) => (
                <div key={id} className="p-4 bg-neutral-900 rounded-lg border border-neutral-700">
                  <div className="text-sm font-medium text-white mb-3">{id.slice(0, 12)}</div>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-neutral-400">信号准确率</span>
                      <span className="text-green-400">65%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-neutral-400">平均收益</span>
                      <span className="text-green-400">+2.3%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-neutral-400">夏普比率</span>
                      <span className="text-orange-400">1.2</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {selectedDecisions.length < 2 && (
            <div className="text-center text-neutral-500 text-sm py-8">
              请选择至少 2 个决策进行对比（最多 3 个）
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
