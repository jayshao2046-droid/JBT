'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

interface DataSource {
  id: string
  name: string
  category: string
  status: string
  availability: number
  response_time: number
  coverage: number
}

interface DataSourceAnalysisProps {
  sources: DataSource[]
  onSort?: (field: string) => void
}

export function DataSourceAnalysis({ sources, onSort }: DataSourceAnalysisProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>数据源详情分析</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => onSort?.('availability')}>
              按可用性排序
            </Button>
            <Button variant="outline" size="sm" onClick={() => onSort?.('response_time')}>
              按响应时间排序
            </Button>
            <Button variant="outline" size="sm" onClick={() => onSort?.('coverage')}>
              按覆盖率排序
            </Button>
          </div>

          <div className="space-y-2">
            {sources.map((source) => (
              <div key={source.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{source.name}</span>
                    <Badge variant="outline">{source.category}</Badge>
                    <Badge variant={source.status === 'available' ? 'default' : 'destructive'}>
                      {source.status === 'available' ? '可用' : '不可用'}
                    </Badge>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">可用性: </span>
                    <span className="font-medium">{source.availability.toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">响应时间: </span>
                    <span className="font-medium">{source.response_time.toFixed(0)}ms</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">覆盖率: </span>
                    <span className="font-medium">{source.coverage.toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
