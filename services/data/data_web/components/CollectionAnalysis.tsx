'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface CollectionAnalysisProps {
  monthlyData: Array<{
    month: string
    count: number
  }>
}

export function CollectionAnalysis({ monthlyData }: CollectionAnalysisProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>月度采集分析</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={monthlyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#8884d8" name="采集次数" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
