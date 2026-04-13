'use client'

import { useState } from 'react'
import { CollectionOptimizer } from '@/components/CollectionOptimizer'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function OptimizerPage() {
  const [optimizedResult, setOptimizedResult] = useState<any>(null)

  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">参数优化器</h1>

      <CollectionOptimizer onOptimized={setOptimizedResult} />

      {optimizedResult && (
        <Card>
          <CardHeader>
            <CardTitle>推荐配置</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div>
                <span className="text-muted-foreground">采集间隔: </span>
                <span className="font-medium">{optimizedResult.params.interval}秒</span>
              </div>
              <div>
                <span className="text-muted-foreground">超时时间: </span>
                <span className="font-medium">{optimizedResult.params.timeout}秒</span>
              </div>
              <div>
                <span className="text-muted-foreground">重试次数: </span>
                <span className="font-medium">{optimizedResult.params.retry_count}次</span>
              </div>
              <div>
                <span className="text-muted-foreground">预期分数: </span>
                <span className="font-medium text-green-600">{optimizedResult.score.toFixed(2)}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
