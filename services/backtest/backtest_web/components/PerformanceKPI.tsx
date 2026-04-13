"use client"

import { useState, useEffect } from "react"
import { backtestApi } from "@/lib/backtest-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, TrendingDown, Activity, Target, Award, BarChart3, Hash } from "lucide-react"

interface PerformanceKPIProps {
  taskId: string
}

export function PerformanceKPI({ taskId }: PerformanceKPIProps) {
  const [performance, setPerformance] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPerformance = async () => {
      try {
        setLoading(true)
        const data = await backtestApi.performanceKPI(taskId)
        setPerformance(data.performance)
      } catch (error) {
        console.error("Failed to fetch performance KPI:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchPerformance()
  }, [taskId])

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
      label: "年化收益率",
      value: `${performance.annual_return >= 0 ? "+" : ""}${performance.annual_return}%`,
      icon: TrendingUp,
      color: performance.annual_return >= 0 ? "text-green-400" : "text-red-400",
      bgColor: performance.annual_return >= 0 ? "bg-green-500/10" : "bg-red-500/10",
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
      label: "卡玛比率",
      value: performance.calmar_ratio.toFixed(2),
      icon: Target,
      color: performance.calmar_ratio >= 1 ? "text-green-400" : "text-orange-400",
      bgColor: performance.calmar_ratio >= 1 ? "bg-green-500/10" : "bg-orange-500/10",
    },
    {
      label: "胜率",
      value: `${performance.win_rate}%`,
      icon: Award,
      color: performance.win_rate >= 50 ? "text-green-400" : "text-orange-400",
      bgColor: performance.win_rate >= 50 ? "bg-green-500/10" : "bg-orange-500/10",
    },
    {
      label: "盈亏比",
      value: performance.profit_loss_ratio.toFixed(2),
      icon: BarChart3,
      color: performance.profit_loss_ratio >= 1.5 ? "text-green-400" : "text-orange-400",
      bgColor: performance.profit_loss_ratio >= 1.5 ? "bg-green-500/10" : "bg-orange-500/10",
    },
    {
      label: "总交易次数",
      value: performance.total_trades,
      icon: Hash,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
    },
  ]

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Activity className="w-5 h-5 text-orange-500" />
          绩效 KPI
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {kpis.map((kpi, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg ${kpi.bgColor} border border-neutral-700`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-neutral-400">{kpi.label}</span>
                <kpi.icon className={`w-4 h-4 ${kpi.color}`} />
              </div>
              <div className={`text-2xl font-bold ${kpi.color}`}>{kpi.value}</div>
            </div>
          ))}
        </div>

        {/* 绩效评级 */}
        <div className="mt-6 p-4 bg-neutral-900 rounded-lg border border-neutral-700">
          <div className="flex items-center justify-between">
            <span className="text-sm text-neutral-400">综合评级</span>
            <span className={`text-lg font-bold ${getOverallRating(performance).color}`}>
              {getOverallRating(performance).label}
            </span>
          </div>
          <div className="mt-2 text-xs text-neutral-500">
            {getOverallRating(performance).description}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function getOverallRating(performance: any): { label: string; color: string; description: string } {
  let score = 0

  // 年化收益率评分（0-25分）
  if (performance.annual_return >= 30) score += 25
  else if (performance.annual_return >= 20) score += 20
  else if (performance.annual_return >= 10) score += 15
  else if (performance.annual_return >= 5) score += 10
  else if (performance.annual_return >= 0) score += 5

  // 最大回撤评分（0-25分）
  if (performance.max_drawdown <= 10) score += 25
  else if (performance.max_drawdown <= 20) score += 20
  else if (performance.max_drawdown <= 30) score += 15
  else if (performance.max_drawdown <= 40) score += 10
  else score += 5

  // 夏普比率评分（0-25分）
  if (performance.sharpe_ratio >= 2) score += 25
  else if (performance.sharpe_ratio >= 1.5) score += 20
  else if (performance.sharpe_ratio >= 1) score += 15
  else if (performance.sharpe_ratio >= 0.5) score += 10
  else score += 5

  // 胜率评分（0-25分）
  if (performance.win_rate >= 60) score += 25
  else if (performance.win_rate >= 50) score += 20
  else if (performance.win_rate >= 40) score += 15
  else if (performance.win_rate >= 30) score += 10
  else score += 5

  if (score >= 80) {
    return {
      label: "优秀 (A)",
      color: "text-green-400",
      description: "策略表现优异，各项指标均达到较高水平",
    }
  } else if (score >= 60) {
    return {
      label: "良好 (B)",
      color: "text-blue-400",
      description: "策略表现良好，大部分指标达标",
    }
  } else if (score >= 40) {
    return {
      label: "一般 (C)",
      color: "text-orange-400",
      description: "策略表现一般，部分指标需要优化",
    }
  } else {
    return {
      label: "较差 (D)",
      color: "text-red-400",
      description: "策略表现较差，建议重新调整参数或策略逻辑",
    }
  }
}
