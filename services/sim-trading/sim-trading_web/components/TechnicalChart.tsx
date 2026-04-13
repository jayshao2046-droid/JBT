"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { simApi, type KlinePoint } from "@/lib/sim-api"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"

interface TechnicalChartProps {
  symbol: string
  interval?: string
}

export function TechnicalChart({ symbol, interval = "1m" }: TechnicalChartProps) {
  const [klines, setKlines] = useState<KlinePoint[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchKlines = async () => {
      try {
        const data = await simApi.marketKline(symbol, interval)
        setKlines(data.klines)
      } catch (err) {
        console.error("获取K线数据失败:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchKlines()
    const intervalId = setInterval(fetchKlines, 60000) // 每分钟刷新
    return () => clearInterval(intervalId)
  }, [symbol, interval])

  if (loading) {
    return <div className="text-sm text-muted-foreground">加载中...</div>
  }

  if (klines.length === 0) {
    return <div className="text-sm text-muted-foreground">暂无数据</div>
  }

  // 计算技术指标
  const chartData = klines.map((k, idx) => {
    // MA5
    const ma5Start = Math.max(0, idx - 4)
    const ma5Data = klines.slice(ma5Start, idx + 1)
    const ma5 = ma5Data.reduce((sum, d) => sum + d.close, 0) / ma5Data.length

    // MA10
    const ma10Start = Math.max(0, idx - 9)
    const ma10Data = klines.slice(ma10Start, idx + 1)
    const ma10 = ma10Data.reduce((sum, d) => sum + d.close, 0) / ma10Data.length

    // MA20
    const ma20Start = Math.max(0, idx - 19)
    const ma20Data = klines.slice(ma20Start, idx + 1)
    const ma20 = ma20Data.reduce((sum, d) => sum + d.close, 0) / ma20Data.length

    return {
      time: new Date(k.timestamp).toLocaleTimeString("zh-CN", {
        hour: "2-digit",
        minute: "2-digit",
      }),
      close: k.close,
      volume: k.volume,
      ma5: ma5Data.length >= 5 ? ma5 : null,
      ma10: ma10Data.length >= 10 ? ma10 : null,
      ma20: ma20Data.length >= 20 ? ma20 : null,
    }
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          {symbol} 技术指标 ({interval})
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 价格和均线 */}
        <div>
          <div className="text-xs text-muted-foreground mb-2">价格 & 均线</div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} domain={["auto", "auto"]} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Line type="monotone" dataKey="close" stroke="#8884d8" dot={false} name="收盘价" />
              <Line type="monotone" dataKey="ma5" stroke="#82ca9d" dot={false} name="MA5" />
              <Line type="monotone" dataKey="ma10" stroke="#ffc658" dot={false} name="MA10" />
              <Line type="monotone" dataKey="ma20" stroke="#ff7c7c" dot={false} name="MA20" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* 成交量 */}
        <div>
          <div className="text-xs text-muted-foreground mb-2">成交量</div>
          <ResponsiveContainer width="100%" height={100}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="volume" fill="#8884d8" name="成交量" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
