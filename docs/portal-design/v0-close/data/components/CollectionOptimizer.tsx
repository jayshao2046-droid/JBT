'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { dataAPI } from '@/lib/data-api'

interface CollectionOptimizerProps {
  onOptimized?: (result: any) => void
}

export function CollectionOptimizer({ onOptimized }: CollectionOptimizerProps) {
  const [paramGrid, setParamGrid] = useState({
    interval: '60,300,600',
    timeout: '10,30,60',
    retry_count: '1,3,5',
  })
  const [optimizing, setOptimizing] = useState(false)
  const [results, setResults] = useState<any[]>([])

  const handleOptimize = async () => {
    setOptimizing(true)
    try {
      const grid = Object.entries(paramGrid).reduce((acc, [key, value]) => {
        acc[key] = value.split(',').map(v => parseFloat(v.trim()))
        return acc
      }, {} as Record<string, number[]>)

      const optimizationResults = await dataAPI.gridSearch(grid, 'success_rate')
      setResults(optimizationResults)
      if (onOptimized) {
        onOptimized(optimizationResults[0])
      }
    } catch (error) {
      console.error('优化失败:', error)
    } finally {
      setOptimizing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>采集参数优化器</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>采集间隔 (秒)</Label>
          <Input
            value={paramGrid.interval}
            onChange={(e) => setParamGrid({ ...paramGrid, interval: e.target.value })}
            placeholder="60,300,600"
          />
        </div>

        <div className="space-y-2">
          <Label>超时时间 (秒)</Label>
          <Input
            value={paramGrid.timeout}
            onChange={(e) => setParamGrid({ ...paramGrid, timeout: e.target.value })}
            placeholder="10,30,60"
          />
        </div>

        <div className="space-y-2">
          <Label>重试次数</Label>
          <Input
            value={paramGrid.retry_count}
            onChange={(e) => setParamGrid({ ...paramGrid, retry_count: e.target.value })}
            placeholder="1,3,5"
          />
        </div>

        <Button onClick={handleOptimize} disabled={optimizing} className="w-full">
          {optimizing ? '优化中...' : '开始优化'}
        </Button>

        {results.length > 0 && (
          <div className="space-y-2 pt-4 border-t">
            <div className="font-medium">优化结果 (按成功率排序):</div>
            {results.slice(0, 5).map((result, index) => (
              <div key={index} className="border rounded p-2 text-sm">
                <div className="flex justify-between mb-1">
                  <span className="font-medium">方案 {index + 1}</span>
                  <span className="text-green-600">分数: {result.score.toFixed(2)}</span>
                </div>
                <div className="text-muted-foreground">
                  间隔: {result.params.interval}s,
                  超时: {result.params.timeout}s,
                  重试: {result.params.retry_count}次
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
