"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from "recharts"

interface Trade {
  instrument_id: string
  direction: string
  open_time: string
  close_time: string
  pnl: number
  return_rate: number
}

interface BacktestResult {
  task_id: string
  strategy_name: string
  start_date: string
  end_date: string
  initial_capital: number
  final_capital: number
  total_return: number
  trades: Trade[]
}

interface BacktestAnalysisProps {
  result: BacktestResult
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8", "#82CA9D"]

export function BacktestAnalysis({ result }: BacktestAnalysisProps) {
  if (!result || !result.trades || result.trades.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>回测结果分析</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">暂无交易数据</p>
        </CardContent>
      </Card>
    )
  }

  const { trades } = result

  // 月度收益计算
  const monthlyReturns = trades.reduce((acc, trade) => {
    const month = trade.close_time.substring(0, 7) // YYYY-MM
    if (!acc[month]) {
      acc[month] = { month, pnl: 0, trades: 0 }
    }
    acc[month].pnl += trade.pnl
    acc[month].trades += 1
    return acc
  }, {} as Record<string, { month: string; pnl: number; trades: number }>)

  const monthlyData = Object.values(monthlyReturns).sort((a, b) => a.month.localeCompare(b.month))

  // 年度收益对比
  const yearlyReturns = trades.reduce((acc, trade) => {
    const year = trade.close_time.substring(0, 4) // YYYY
    if (!acc[year]) {
      acc[year] = { year, pnl: 0, trades: 0, winTrades: 0 }
    }
    acc[year].pnl += trade.pnl
    acc[year].trades += 1
    if (trade.pnl > 0) acc[year].winTrades += 1
    return acc
  }, {} as Record<string, { year: string; pnl: number; trades: number; winTrades: number }>)

  const yearlyData = Object.values(yearlyReturns).map(item => ({
    ...item,
    winRate: ((item.winTrades / item.trades) * 100).toFixed(1),
  }))

  // 分品种绩效
  const symbolPerformance = trades.reduce((acc, trade) => {
    const symbol = trade.instrument_id.replace(/\d+/, "") // 去掉合约月份
    if (!acc[symbol]) {
      acc[symbol] = { symbol, pnl: 0, trades: 0, winTrades: 0 }
    }
    acc[symbol].pnl += trade.pnl
    acc[symbol].trades += 1
    if (trade.pnl > 0) acc[symbol].winTrades += 1
    return acc
  }, {} as Record<string, { symbol: string; pnl: number; trades: number; winTrades: number }>)

  const symbolData = Object.values(symbolPerformance)
    .sort((a, b) => b.pnl - a.pnl)
    .slice(0, 10)
    .map(item => ({
      ...item,
      winRate: ((item.winTrades / item.trades) * 100).toFixed(1),
    }))

  // 交易方向分布
  const directionDistribution = trades.reduce((acc, trade) => {
    const direction = trade.direction === "long" || trade.direction === "buy" ? "多头" : "空头"
    if (!acc[direction]) {
      acc[direction] = { name: direction, value: 0, pnl: 0 }
    }
    acc[direction].value += 1
    acc[direction].pnl += trade.pnl
    return acc
  }, {} as Record<string, { name: string; value: number; pnl: number }>)

  const directionData = Object.values(directionDistribution)

  // 盈亏分布
  const winTrades = trades.filter(t => t.pnl > 0).length
  const loseTrades = trades.filter(t => t.pnl < 0).length
  const breakEvenTrades = trades.filter(t => t.pnl === 0).length

  const winLossData = [
    { name: "盈利", value: winTrades, fill: "#00C49F" },
    { name: "亏损", value: loseTrades, fill: "#FF8042" },
    { name: "持平", value: breakEvenTrades, fill: "#FFBB28" },
  ].filter(item => item.value > 0)

  return (
    <div className="space-y-4">
      {/* 月度收益热力图 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">月度收益分析</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={monthlyData}>
              <CartesianGrid stroke="transparent" />
              <XAxis dataKey="month" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip
                formatter={(value: number, name: string) => {
                  if (name === "pnl") return [`¥${value.toFixed(2)}`, "盈亏"]
                  if (name === "trades") return [value, "交易次数"]
                  return value
                }}
              />
              <Bar dataKey="pnl" name="盈亏">
                {monthlyData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? "#00C49F" : "#FF8042"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {/* 年度收益对比 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">年度收益对比</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {yearlyData.map((item, index) => (
                <div key={index} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">{item.year}</span>
                    <span className={item.pnl >= 0 ? "text-green-600" : "text-red-600"}>
                      ¥{item.pnl.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>交易 {item.trades} 次</span>
                    <span>胜率 {item.winRate}%</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-1.5">
                    <div
                      className={item.pnl >= 0 ? "bg-green-500 h-1.5 rounded-full" : "bg-red-500 h-1.5 rounded-full"}
                      style={{
                        width: `${Math.min(Math.abs(item.pnl) / Math.max(...yearlyData.map(d => Math.abs(d.pnl))) * 100, 100)}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 盈亏分布饼图 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">盈亏分布</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={winLossData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  dataKey="value"
                >
                  {winLossData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">总交易次数</span>
                <span className="font-medium">{trades.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">胜率</span>
                <span className="font-medium">{((winTrades / trades.length) * 100).toFixed(2)}%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 分品种绩效 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">分品种绩效排行</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={symbolData} layout="vertical">
              <CartesianGrid stroke="transparent" />
              <XAxis type="number" />
              <YAxis dataKey="symbol" type="category" width={60} />
              <Tooltip
                formatter={(value: number, name: string) => {
                  if (name === "pnl") return [`¥${value.toFixed(2)}`, "盈亏"]
                  return value
                }}
              />
              <Bar dataKey="pnl" name="盈亏">
                {symbolData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? "#00C49F" : "#FF8042"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 交易方向分析 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">交易方向分析</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {directionData.map((item, index) => (
              <div key={index} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="font-medium">{item.name}</span>
                  <span className={item.pnl >= 0 ? "text-green-600" : "text-red-600"}>
                    ¥{item.pnl.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>交易 {item.value} 次</span>
                  <span>占比 {((item.value / trades.length) * 100).toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
