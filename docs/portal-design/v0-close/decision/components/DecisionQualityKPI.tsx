"use client"

import { useState, useEffect } from "react"
import { decisionApi } from "@/lib/decision-api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Shield, CheckCircle, TrendingUp, AlertTriangle, Database } from "lucide-react"

interface DecisionQualityKPIProps {
  decisionId: string
}

export function DecisionQualityKPI({ decisionId }: DecisionQualityKPIProps) {
  const [quality, setQuality] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchQuality = async () => {
      try {
        setLoading(true)
        const data = await decisionApi.qualityKPI(decisionId)
        setQuality(data.quality)
      } catch (error) {
        console.error("Failed to fetch quality KPI:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchQuality()
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

  if (!quality) {
    return null
  }

  const kpis = [
    {
      label: "信号质量评分",
      value: quality.signal_quality.toFixed(1),
      icon: CheckCircle,
      color: quality.signal_quality >= 70 ? "text-green-400" : "text-orange-400",
      bgColor: quality.signal_quality >= 70 ? "bg-green-500/10" : "bg-orange-500/10",
    },
    {
      label: "因子有效性",
      value: `${quality.factor_effectiveness}%`,
      icon: TrendingUp,
      color: quality.factor_effectiveness >= 60 ? "text-green-400" : "text-orange-400",
      bgColor: quality.factor_effectiveness >= 60 ? "bg-green-500/10" : "bg-orange-500/10",
    },
    {
      label: "策略稳定性",
      value: `${quality.strategy_stability}%`,
      icon: Shield,
      color: quality.strategy_stability >= 70 ? "text-green-400" : "text-orange-400",
      bgColor: quality.strategy_stability >= 70 ? "bg-green-500/10" : "bg-orange-500/10",
    },
    {
      label: "风控有效性",
      value: `${quality.risk_control_effectiveness}%`,
      icon: AlertTriangle,
      color: quality.risk_control_effectiveness >= 80 ? "text-green-400" : "text-orange-400",
      bgColor: quality.risk_control_effectiveness >= 80 ? "bg-green-500/10" : "bg-orange-500/10",
    },
    {
      label: "数据完整性",
      value: `${quality.data_completeness}%`,
      icon: Database,
      color: quality.data_completeness >= 95 ? "text-green-400" : "text-orange-400",
      bgColor: quality.data_completeness >= 95 ? "bg-green-500/10" : "bg-orange-500/10",
    },
  ]

  return (
    <Card className="bg-neutral-800 border-neutral-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-500" />
          决策质量 KPI
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
