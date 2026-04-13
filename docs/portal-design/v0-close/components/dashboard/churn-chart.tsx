'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LineChart, Line, RadarChart, Radar, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts'
import { useState } from 'react'
import { ChurnData } from '@/lib/mock-data'

interface ChurnChartProps {
  data: ChurnData[]
}

export function ChurnChart({ data }: ChurnChartProps) {
  const [chartType, setChartType] = useState<'radar' | 'line' | 'bar'>('radar')

  const renderChart = () => {
    switch (chartType) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid stroke="transparent" />
              <XAxis dataKey="metric" stroke="#666" style={{ fontSize: '12px' }} />
              <YAxis stroke="#666" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: "transparent", border: "none" }}
                labelStyle={{ color: "#999" }}
              />
              <Line type="monotone" dataKey="value" stroke="#f97316" dot={{ fill: '#f97316' }} />
            </LineChart>
          </ResponsiveContainer>
        )
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data}>
              <CartesianGrid stroke="transparent" />
              <XAxis dataKey="metric" stroke="#666" style={{ fontSize: '12px' }} />
              <YAxis stroke="#666" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: "transparent", border: "none" }}
                labelStyle={{ color: "#999" }}
              />
              <Bar dataKey="value" fill="#f97316" />
            </BarChart>
          </ResponsiveContainer>
        )
      default:
        return (
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={data}>
              <PolarGrid stroke="#333" />
              <PolarAngleAxis dataKey="metric" stroke="#666" style={{ fontSize: '12px' }} />
              <PolarRadiusAxis stroke="#666" />
              <Radar name="收益" dataKey="value" stroke="#f97316" fill="#f97316" fillOpacity={0.3} />
              <Tooltip 
                contentStyle={{ backgroundColor: "transparent", border: "none" }}
                labelStyle={{ color: "#999" }}
              />
            </RadarChart>
          </ResponsiveContainer>
        )
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="text-base">收益表</CardTitle>
        <div className="flex gap-1">
          {(['radar', 'line', 'bar'] as const).map((type) => (
            <Button
              key={type}
              size="sm"
              variant={chartType === type ? 'default' : 'outline'}
              onClick={() => setChartType(type)}
              className={chartType === type ? 'bg-orange-600 hover:bg-orange-700' : ''}
            >
              {type === 'radar' ? '雷达图' : type === 'line' ? '折线图' : '柱状图'}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {renderChart()}
      </CardContent>
    </Card>
  )
}
