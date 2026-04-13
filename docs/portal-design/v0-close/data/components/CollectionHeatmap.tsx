'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface CollectionHeatmapProps {
  data: Array<{
    date: string
    count: number
  }>
}

export function CollectionHeatmap({ data }: CollectionHeatmapProps) {
  const maxCount = Math.max(...data.map(d => d.count))

  const getColor = (count: number) => {
    const intensity = count / maxCount
    if (intensity > 0.75) return 'bg-green-700'
    if (intensity > 0.5) return 'bg-green-500'
    if (intensity > 0.25) return 'bg-green-300'
    return 'bg-green-100'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>采集热力图</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-7 gap-2">
          {data.map((item) => (
            <div
              key={item.date}
              className={`aspect-square rounded ${getColor(item.count)} flex items-center justify-center text-xs`}
              title={`${item.date}: ${item.count}次`}
            >
              {item.count}
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2 mt-4 text-sm">
          <span className="text-muted-foreground">少</span>
          <div className="flex gap-1">
            <div className="w-4 h-4 bg-green-100 rounded" />
            <div className="w-4 h-4 bg-green-300 rounded" />
            <div className="w-4 h-4 bg-green-500 rounded" />
            <div className="w-4 h-4 bg-green-700 rounded" />
          </div>
          <span className="text-muted-foreground">多</span>
        </div>
      </CardContent>
    </Card>
  )
}
