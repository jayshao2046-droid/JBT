'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface DataQualityKPIProps {
  metrics: {
    completeness: number
    timeliness: number
    accuracy: number
    consistency: number
    success_rate: number
    avg_latency: number
    error_rate: number
  }
}

export function DataQualityKPI({ metrics }: DataQualityKPIProps) {
  const getStatusColor = (value: number, isInverse = false) => {
    if (isInverse) {
      if (value < 5) return 'bg-green-500'
      if (value < 15) return 'bg-yellow-500'
      return 'bg-red-500'
    }
    if (value >= 95) return 'bg-green-500'
    if (value >= 80) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>数据质量 KPI</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">完整性</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{metrics.completeness.toFixed(1)}%</span>
              <Badge className={getStatusColor(metrics.completeness)}>
                {metrics.completeness >= 95 ? '优秀' : metrics.completeness >= 80 ? '良好' : '需改进'}
              </Badge>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">及时性</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{metrics.timeliness.toFixed(1)}%</span>
              <Badge className={getStatusColor(metrics.timeliness)}>
                {metrics.timeliness >= 95 ? '优秀' : metrics.timeliness >= 80 ? '良好' : '需改进'}
              </Badge>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">准确性</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{metrics.accuracy.toFixed(1)}%</span>
              <Badge className={getStatusColor(metrics.accuracy)}>
                {metrics.accuracy >= 95 ? '优秀' : metrics.accuracy >= 80 ? '良好' : '需改进'}
              </Badge>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">一致性</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{metrics.consistency.toFixed(1)}%</span>
              <Badge className={getStatusColor(metrics.consistency)}>
                {metrics.consistency >= 95 ? '优秀' : metrics.consistency >= 80 ? '良好' : '需改进'}
              </Badge>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">成功率</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{metrics.success_rate.toFixed(1)}%</span>
              <Badge className={getStatusColor(metrics.success_rate)}>
                {metrics.success_rate >= 95 ? '优秀' : metrics.success_rate >= 80 ? '良好' : '需改进'}
              </Badge>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">平均延迟</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{metrics.avg_latency.toFixed(1)}s</span>
              <Badge className={getStatusColor(metrics.avg_latency, true)}>
                {metrics.avg_latency < 5 ? '优秀' : metrics.avg_latency < 15 ? '良好' : '需改进'}
              </Badge>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">错误率</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{metrics.error_rate.toFixed(1)}%</span>
              <Badge className={getStatusColor(metrics.error_rate, true)}>
                {metrics.error_rate < 5 ? '优秀' : metrics.error_rate < 15 ? '良好' : '需改进'}
              </Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
