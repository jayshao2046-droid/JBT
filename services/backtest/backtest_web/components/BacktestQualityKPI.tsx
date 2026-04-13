"use client"

import { useState, useEffect } from "react"
import { backtestApi } from "@/lib/backtest-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Shield, AlertTriangle, TrendingUp, Settings, Database } from "lucide-react"

interface QualityKPIProps {
  taskId: string
}

export function BacktestQualityKPI({ taskId }: QualityKPIProps) {
  const [quality, setQuality] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchQuality = async () => {
      try {
        setLoading(true)
        const data = await backtestApi.qualityKPI(taskId)
        setQuality(data.quality)
      } catch (error) {
        console.error("Failed to fetch quality KPI:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchQuality()
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

  if (!quality) {
    return null
  }

  const kpis = [
    {
      label: "样本外表现",
      value: `${quality.out_of_sample_performance.toFixed(1)}分`,
      icon: TrendingUp,
      color: quality.out_of_sample_performance >= 70 ? "text-green-400" : "text-orange-400",
      bgColor: quality.out_of_sample_performance >= 70 ? "bg-green-500/10" : "bg-orange-500/10",
    },
    {
      label: "过拟合检测",
      value: `${quality.overfitting_score.toFixed(1)}分`,
      icon: AlertTriangle,
      color: quality.overfitting_score >= 70 ? "text-green-400" : "text-red-400",
      bgColor: quality.overfitting_score >= 70 ? "bg-green-500/10" : "bg-red-500/10",
    },
    {
      label: "稳定性评分",
      value: `${quality.stability_score.toFixed(1)}分`,
      icon: Shield,
      color: quality.stability_score >= 70 ? "text-green-400" : "text-orange-400",
      bgColor: quality.stability_score >= 70 ? "bg-green-500/10" : "bg-orange-500/10",
    },
    {
      label: "参数敏感度",
      value: `${quality.parameter_sensitivity.toFixed(1)}分`,
      icon: Settings,
      color: quality.parameter_sensitivity >= 70 ? "text-green-400" : "text-orange-400",
      bgColor: quality.parameter_sensitivity >= 70 ? "bg-green-500/10" : "bg-orange-500/10",
    },
    {
      label: "数据质量评分",
      value: `${quality.data_quality_score.toFixed(1)}分`,
      icon: Database,
      color: quality.data_quality_score >= 90 ? "text-green-400" : "text-orange-400",
      bgColor: quality.data_quality_score >= 90 ? "bg-green-500/10" : "bg-orange-500/10",
    },
  ]

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-500" />
          质量 KPI
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
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
      </CardContent>
    </Card>
  )
}
