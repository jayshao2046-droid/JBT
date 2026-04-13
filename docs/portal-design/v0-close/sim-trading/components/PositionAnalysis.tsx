"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts"

interface Position {
  instrument_id: string
  direction: string
  volume: number
  open_price: number
  current_price: number
  pnl: number
  open_time?: string
}

interface PositionAnalysisProps {
  positions: Position[]
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8", "#82CA9D", "#FFC658", "#FF6B9D"]

export function PositionAnalysis({ positions }: PositionAnalysisProps) {
  if (!positions || positions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>持仓分析</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">暂无持仓数据</p>
        </CardContent>
      </Card>
    )
  }

  // 按品种分布
  const symbolDistribution = positions.reduce((acc, pos) => {
    const symbol = pos.instrument_id.replace(/\d+/, "")
    acc[symbol] = (acc[symbol] || 0) + pos.volume
    return acc
  }, {} as Record<string, number>)

  const symbolData = Object.entries(symbolDistribution).map(([name, value]) => ({
    name,
    value,
  }))

  // 按方向分布
  const directionDistribution = positions.reduce((acc, pos) => {
    const direction = pos.direction === "long" || pos.direction === "buy" ? "多头" : "空头"
    acc[direction] = (acc[direction] || 0) + pos.volume
    return acc
  }, {} as Record<string, number>)

  const directionData = Object.entries(directionDistribution).map(([name, value]) => ({
    name,
    value,
  }))

  // 盈亏排行
  const pnlRanking = [...positions]
    .sort((a, b) => (b.pnl || 0) - (a.pnl || 0))
    .slice(0, 10)
    .map(pos => ({
      name: pos.instrument_id,
      pnl: pos.pnl || 0,
    }))

  // 持仓集中度
  const totalVolume = positions.reduce((sum, pos) => sum + pos.volume, 0)
  const maxSymbolVolume = Math.max(...Object.values(symbolDistribution))
  const symbolConcentration = ((maxSymbolVolume / totalVolume) * 100).toFixed(2)

  const longVolume = positions
    .filter(p => p.direction === "long" || p.direction === "buy")
    .reduce((sum, pos) => sum + pos.volume, 0)
  const directionConcentration = ((Math.max(longVolume, totalVolume - longVolume) / totalVolume) * 100).toFixed(2)

  // 持仓时长分布
  const now = new Date()
  const durationDistribution = positions.reduce((acc, pos) => {
    if (!pos.open_time) return acc

    const openTime = new Date(pos.open_time)
    const hours = (now.getTime() - openTime.getTime()) / (1000 * 60 * 60)

    let bucket = ""
    if (hours < 1) bucket = "< 1小时"
    else if (hours < 4) bucket = "1-4小时"
    else if (hours < 24) bucket = "4-24小时"
    else if (hours < 72) bucket = "1-3天"
    else bucket = "> 3天"

    acc[bucket] = (acc[bucket] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const durationData = Object.entries(durationDistribution).map(([name, value]) => ({
    name,
    value,
  }))

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* 品种分布饼图 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">持仓品种分布</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={symbolData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {symbolData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 方向分布饼图 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">多空分布</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={directionData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {directionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={index === 0 ? "#00C49F" : "#FF8042"} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 盈亏排行榜 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">盈亏排行榜</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={pnlRanking}>
              <CartesianGrid stroke="transparent" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="pnl" fill="#8884d8">
                {pnlRanking.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? "#00C49F" : "#FF8042"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 持仓集中度 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">持仓集中度分析</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-muted-foreground">单品种最大占比</span>
              <span className="font-medium">{symbolConcentration}%</span>
            </div>
            <div className="w-full bg-secondary rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full"
                style={{ width: `${symbolConcentration}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-muted-foreground">单方向最大占比</span>
              <span className="font-medium">{directionConcentration}%</span>
            </div>
            <div className="w-full bg-secondary rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full"
                style={{ width: `${directionConcentration}%` }}
              />
            </div>
          </div>

          <div className="pt-2 border-t">
            <div className="text-sm text-muted-foreground mb-2">持仓时长分布</div>
            {durationData.map((item, index) => (
              <div key={index} className="flex justify-between text-sm mb-1">
                <span>{item.name}</span>
                <span className="font-medium">{item.value} 个</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
