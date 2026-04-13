'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface DataSourceComparisonProps {
  sources: Array<{
    id: string
    name: string
    metrics: {
      availability: number
      response_time: number
      error_rate: number
      freshness: number
      coverage: number
    }
  }>
}

export function DataSourceComparison({ sources }: DataSourceComparisonProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>数据源对比</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">指标</th>
                {sources.map((source) => (
                  <th key={source.id} className="text-left p-2">{source.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="border-b">
                <td className="p-2 text-muted-foreground">可用性</td>
                {sources.map((source) => (
                  <td key={source.id} className="p-2">
                    <Badge variant={source.metrics.availability >= 95 ? 'default' : 'secondary'}>
                      {source.metrics.availability.toFixed(1)}%
                    </Badge>
                  </td>
                ))}
              </tr>
              <tr className="border-b">
                <td className="p-2 text-muted-foreground">响应时间</td>
                {sources.map((source) => (
                  <td key={source.id} className="p-2">
                    {source.metrics.response_time.toFixed(0)}ms
                  </td>
                ))}
              </tr>
              <tr className="border-b">
                <td className="p-2 text-muted-foreground">错误率</td>
                {sources.map((source) => (
                  <td key={source.id} className="p-2">
                    <Badge variant={source.metrics.error_rate < 5 ? 'default' : 'destructive'}>
                      {source.metrics.error_rate.toFixed(1)}%
                    </Badge>
                  </td>
                ))}
              </tr>
              <tr className="border-b">
                <td className="p-2 text-muted-foreground">数据新鲜度</td>
                {sources.map((source) => (
                  <td key={source.id} className="p-2">
                    {source.metrics.freshness.toFixed(1)}%
                  </td>
                ))}
              </tr>
              <tr>
                <td className="p-2 text-muted-foreground">覆盖率</td>
                {sources.map((source) => (
                  <td key={source.id} className="p-2">
                    {source.metrics.coverage.toFixed(1)}%
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
