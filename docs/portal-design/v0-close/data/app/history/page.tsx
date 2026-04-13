'use client'

import { useState, useEffect } from 'react'
import { dataAPI, CollectionHistory } from '@/lib/data-api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export default function HistoryPage() {
  const [history, setHistory] = useState<CollectionHistory[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    source: '',
  })

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    setLoading(true)
    try {
      const result = await dataAPI.collectionHistory(
        filters.startDate,
        filters.endDate,
        filters.source
      )
      setHistory(result.history)
    } catch (error) {
      console.error('加载历史失败:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">采集历史记录</h1>

      <Card>
        <CardHeader>
          <CardTitle>筛选条件</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <Input
              type="date"
              value={filters.startDate}
              onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
              placeholder="开始日期"
            />
            <Input
              type="date"
              value={filters.endDate}
              onChange={(e) => setFilters({ ...filters, endDate: e.target.value })}
              placeholder="结束日期"
            />
            <Input
              value={filters.source}
              onChange={(e) => setFilters({ ...filters, source: e.target.value })}
              placeholder="数据源"
            />
          </div>
          <Button onClick={loadHistory} className="mt-4">
            查询
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>历史记录</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div>加载中...</div>
          ) : (
            <div className="space-y-2">
              {history.map((item) => (
                <div key={item.collection_id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{item.source}</span>
                      <Badge variant={item.status === 'success' ? 'default' : 'destructive'}>
                        {item.status === 'success' ? '成功' : '失败'}
                      </Badge>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {item.records_count} 条记录
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {item.start_time} - {item.end_time} (耗时: {item.duration}s)
                  </div>
                  {item.error && (
                    <div className="text-sm text-red-600 mt-2">错误: {item.error}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
