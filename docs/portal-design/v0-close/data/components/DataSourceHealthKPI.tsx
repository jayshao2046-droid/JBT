'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface DataSourceHealthKPIProps {
  metrics: {
    availability: number
    response_time: number
    error_rate: number
    freshness: number
    coverage: number
  }
}

export function DataSourceHealthKPI({ metrics }: DataSourceHealthKPIProps) {
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
        <CardTitle>数据源健康 KPI</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">可用性</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{metrics.availability.toFixed(1)}%</span>
              <Badge className={getStatusColor(metrics.availability)}>
                {metrics.availability >= 95 ? '优秀' : metrics.availability >= 80 ? '良好' : '需改进'}
              </Badge>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">响应时间</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{metrics.response_time.toFixed(0)}ms</span>
              <Badge className={metrics.response_time < 200 ? 'bg-green-500' : metrics.response_time < 500 ? 'bg-yellow-500' : 'bg-red-500'}>
                {metrics.response_time < 200 ? '优秀' : metrics.response_time < 500 ? '良好' : '需改进'}
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

          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">数据新鲜度</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{metrics.freshness.toFixed(1)}%</span>
              <Badge className={getStatusColor(metrics.freshness)}>
                {metrics.freshness >= 95 ? '优秀' : metrics.freshness >= 80 ? '良好' : '需改进'}
              </Badge>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">覆盖率</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{metrics.coverage.toFixed(1)}%</span>
              <Badge className={getStatusColor(metrics.coverage)}>
                {metrics.coverage >= 95 ? '优秀' : metrics.coverage >= 80 ? '良好' : '需改进'}
              </Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
