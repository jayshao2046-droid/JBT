'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import { AlertTriangle } from 'lucide-react'

export function RealTimeRiskIndicators() {
  const riskMetrics = [
    {
      label: '保证金使用率',
      value: 65,
      unit: '%',
      status: 'warning' as const,
      description: '占总权益',
    },
    {
      label: '当日回撤',
      value: 45000,
      unit: '¥',
      status: 'normal' as const,
      description: '相对权益 3.6%',
    },
    {
      label: '杠杆倍数',
      value: 2.5,
      unit: '倍',
      status: 'normal' as const,
      description: '风险等级 中等',
    },
    {
      label: '集中度风险',
      value: 28,
      unit: '%',
      status: 'normal' as const,
      description: '最大持仓占比',
    },
  ]

  const getRiskColor = (status: string, value?: number) => {
    if (status === 'danger') {
      return { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' }
    }
    if (status === 'warning') {
      return { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500/30' }
    }
    return { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30' }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-yellow-400" />
          实时风险指标
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {riskMetrics.map((metric, idx) => {
          const color = getRiskColor(metric.status, metric.value)
          const progressValue = typeof metric.value === 'number' ? Math.min(metric.value, 100) : 0

          return (
            <div key={idx} className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-white">{metric.label}</p>
                  <p className="text-xs text-neutral-400">{metric.description}</p>
                </div>
                <span className={cn('text-lg font-semibold', color.text)}>
                  {metric.value}{metric.unit}
                </span>
              </div>
              {metric.value <= 100 && (
                <Progress value={metric.value as number} className="h-2" />
              )}
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
