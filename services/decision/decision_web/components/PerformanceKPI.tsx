"use client"

import { useState, useEffect } from "react"
import { decisionApi } from "@/lib/decision-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, TrendingDown, Activity, Target, Award, BarChart3, Hash } from "lucide-react"

interface PerformanceKPIProps {
  decisionId: string
}

export function PerformanceKPI({ decisionId }: PerformanceKPIProps) {
  const [performance, setPerformance] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPerformance = async () => {
      try {
        setLoading(true)
        const data = await decisionApi.performanceKPI(decisionId)
        setPerformance(data.performance)
      } catch (error) {
        console.error("Failed to fetch performance KPI:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchPerformance()
  }, [decisionId])

  if (loading) {
    return (
      <Card className="bg-neutral-800 border-neutral-700">
        <CardContent className="pt-6">
          <div className="text-center text-neutral-400">加载中...</div>
        </CardContent>
      </Card>
    )
  }

  if (!performance) {
    return null
  }

  const kpis = [
    {
      label: "信号准确率",
      value: `${performance.signal_accuracy}%`,
      icon: Target,
      color: performance.signal_accuracy >= 60 ? "text-green-400" : "text-orange-400",
      bgColor: performance.signal_accuracy >= 60 ? "bg-green-500/10" : "bg-orange-500/10",
    },
    {
      label: "平均收益率",
      value: `${performance.avg_return >= 0 ? "+" : ""}${performance.avg_return}%`,
      icon: TrendingUp,
      color: performance.avg_return >= 0 ? "text-green-400" : "text-red-400",
      bgColor: performance.avg_return >= 0 ? "bg-green-500/10" : "bg-red-500/10",
    },
    {
      label: "最大回撤",
      value: `-${performance.max_drawdown}%`,
      icon: TrendingDown,
      color: "text-red-400",
      bgColor: "bg-red-500/10",
    },
    {
      label: "夏普比率",
      value: performance.sharpe_ratio.toFixed(2),
      icon: Activity,
      color: performance.sharpe_ratio >= 1 ? "text-green-400" : "text-orange-400",
      bgColor: performance.sharpe_ratio >= 1 ? "bg-green-500/10" : "bg-orange-500/10",
    },
    {
      label: "信号数量",
      value: performance.signal_count,
      icon: Hash,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
    },
    {
      label: "执行成功率",
      value: `${performance.execution_success_rate}%`,
      icon: Award,
      color: performance.execution_success_rate >= 90 ? "text-green-400" : "text-orange-400",
      bgColor: performance.execution_success_rate >= 90 ? "bg-green-500/10" : "bg-orange-500/10",
    },
    {
      label: "平均响应时间",
      value: `${performance.avg_response_time.toFixed(0)}ms`,
      icon: BarChart3,
      color: performance.avg_response_time <= 100 ? "text-green-400" : "text-orange-400",
      bgColor: performance.avg_response_time <= 100 ? "bg-green-500/10" : "bg-orange-500/10",
    },
  ]

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Activity className="w-5 h-5 text-orange-500" />
          决策绩效 KPI
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {kpis.map((kpi, index) => (
            <div key={index} className={`p-4 rounded-lg ${kpi.bgColor} border border-neutral-700`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-neutral-400">{kpi.label}</span>
                <kpi.icon className={`w-4 h-4 ${kpi.color}`} />
              </div>
              <div className={`text-2xl font-bold ${kpi.color}`}>{kpi.value}</div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
