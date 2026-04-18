"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { simTradingApi, type KlinePoint } from "@/lib/api/sim-trading"

interface KlineChartProps {
  symbol: string
}

export function KlineChart({ symbol }: KlineChartProps) {
  const [timeInterval, setTimeInterval] = useState("1m")
  const [data, setData] = useState<KlinePoint[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchKline = async () => {
      try {
        const res = await simTradingApi.getMarketKline(symbol, timeInterval)
        setData(res.klines || [])
      } catch (err) {
        console.error("Failed to fetch kline:", err)
        setData([])
      } finally {
        setLoading(false)
      }
    }

    fetchKline()
    const intervalMs = timeInterval === "1m" ? 60000 : 300000
    const timer = setInterval(() => { fetchKline() }, intervalMs)
    return () => clearInterval(timer)
  }, [symbol, timeInterval])

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>K 线图 - {symbol}</CardTitle>
        <Select value={timeInterval} onValueChange={setTimeInterval}>
          <SelectTrigger className="w-[120px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1m">1 分钟</SelectItem>
            <SelectItem value="5m">5 分钟</SelectItem>
            <SelectItem value="15m">15 分钟</SelectItem>
            <SelectItem value="30m">30 分钟</SelectItem>
            <SelectItem value="60m">60 分钟</SelectItem>
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-[400px] flex items-center justify-center text-muted-foreground">
            加载中...
          </div>
        ) : data.length === 0 ? (
          <div className="h-[400px] flex items-center justify-center text-muted-foreground">
            暂无数据
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis yAxisId="price" />
              <YAxis yAxisId="volume" orientation="right" />
              <Tooltip />
              <Bar yAxisId="volume" dataKey="volume" fill="#8884d8" opacity={0.3} />
              <Line yAxisId="price" type="monotone" dataKey="close" stroke="#82ca9d" strokeWidth={2} />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
