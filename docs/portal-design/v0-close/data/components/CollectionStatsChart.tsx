'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface CollectionStatsChartProps {
  data: Array<{
    time: string
    count: number
    duration: number
  }>
}

export function CollectionStatsChart({ data }: CollectionStatsChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>采集统计图表</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid stroke="transparent" />
            <XAxis dataKey="time" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="count" stroke="#8884d8" name="采集数量" />
            <Line yAxisId="right" type="monotone" dataKey="duration" stroke="#82ca9d" name="耗时(秒)" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
