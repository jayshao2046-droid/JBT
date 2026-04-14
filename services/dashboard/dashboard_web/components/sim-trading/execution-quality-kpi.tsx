"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, Clock, XCircle, Percent } from "lucide-react"

interface ExecutionQualityKpiProps {
  data: {
    avg_slippage: number
    rejection_rate: number
    avg_latency_ms: number
    cancel_rate: number
    partial_fill_rate: number
  } | null
}

export function ExecutionQualityKpi({ data }: ExecutionQualityKpiProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>执行质量</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">暂无数据</p>
        </CardContent>
      </Card>
    )
  }

  const metrics = [
    {
      label: "平均滑点",
      value: `${data.avg_slippage.toFixed(2)} 跳`,
      icon: Activity,
      status: data.avg_slippage <= 2 ? "good" : "warning",
    },
    {
      label: "拒单率",
      value: `${(data.rejection_rate * 100).toFixed(2)}%`,
      icon: XCircle,
      status: data.rejection_rate <= 0.05 ? "good" : "warning",
    },
    {
      label: "平均延迟",
      value: `${data.avg_latency_ms.toFixed(0)} ms`,
      icon: Clock,
      status: data.avg_latency_ms <= 100 ? "good" : "warning",
    },
    {
      label: "撤单率",
      value: `${(data.cancel_rate * 100).toFixed(2)}%`,
      icon: Percent,
      status: data.cancel_rate <= 0.1 ? "good" : "warning",
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>执行质量</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {metrics.map((metric, idx) => (
            <div key={idx} className="p-3 border rounded">
              <div className="flex items-center gap-2">
                <metric.icon className={`w-4 h-4 ${metric.status === "good" ? "text-green-500" : "text-yellow-500"}`} />
                <p className="text-sm text-muted-foreground">{metric.label}</p>
              </div>
              <p className={`text-lg font-bold mt-1 ${metric.status === "good" ? "text-green-500" : "text-yellow-500"}`}>
                {metric.value}
              </p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
