"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { Wifi, WifiOff, Activity, AlertTriangle } from "lucide-react"

interface ConnectionQuality {
  md_quality: {
    latency_ms: number
    packet_loss_rate: number
    reconnect_count: number
    last_reconnect_time: string | null
  }
  td_quality: {
    latency_ms: number
    rejection_rate: number
    reconnect_count: number
    last_reconnect_time: string | null
  }
}

interface ConnectionQualityProps {
  mdConnected: boolean
  tdConnected: boolean
}

export function ConnectionQuality({ mdConnected, tdConnected }: ConnectionQualityProps) {
  const [quality, setQuality] = useState<ConnectionQuality>({
    md_quality: {
      latency_ms: 0,
      packet_loss_rate: 0,
      reconnect_count: 0,
      last_reconnect_time: null,
    },
    td_quality: {
      latency_ms: 0,
      rejection_rate: 0,
      reconnect_count: 0,
      last_reconnect_time: null,
    },
  })

  const [latencyHistory, setLatencyHistory] = useState<
    Array<{ time: string; md: number; td: number }>
  >([])

  useEffect(() => {
    // TODO: 从后端获取连接质量数据
    // const fetchQuality = async () => {
    //   const data = await simApi.getConnectionQuality()
    //   setQuality(data)
    // }
    // fetchQuality()
    // const interval = setInterval(fetchQuality, 5000)
    // return () => clearInterval(interval)

    // 模拟数据
    const interval = setInterval(() => {
      const now = new Date()
      const mdLatency = Math.random() * 100 + 20
      const tdLatency = Math.random() * 80 + 10

      setQuality({
        md_quality: {
          latency_ms: mdLatency,
          packet_loss_rate: Math.random() * 0.02,
          reconnect_count: 0,
          last_reconnect_time: null,
        },
        td_quality: {
          latency_ms: tdLatency,
          rejection_rate: Math.random() * 0.001,
          reconnect_count: 0,
          last_reconnect_time: null,
        },
      })

      setLatencyHistory(prev => {
        const newHistory = [
          ...prev,
          {
            time: now.toLocaleTimeString(),
            md: mdLatency,
            td: tdLatency,
          },
        ]
        return newHistory.slice(-20) // 只保留最近 20 个数据点
      })
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const getLatencyBadge = (latency: number) => {
    if (latency < 50) return <Badge variant="default">优秀</Badge>
    if (latency < 100) return <Badge variant="secondary">良好</Badge>
    if (latency < 200) return <Badge variant="outline">一般</Badge>
    return <Badge variant="destructive">较差</Badge>
  }

  return (
    <div className="space-y-4">
      {/* 连接状态概览 */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              {mdConnected ? (
                <Wifi className="h-4 w-4 text-green-600" />
              ) : (
                <WifiOff className="h-4 w-4 text-red-600" />
              )}
              行情连接质量
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">延迟</span>
              <div className="flex items-center gap-2">
                <span className="font-medium">{quality.md_quality.latency_ms.toFixed(0)} ms</span>
                {getLatencyBadge(quality.md_quality.latency_ms)}
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">丢包率</span>
              <span className="font-medium">
                {(quality.md_quality.packet_loss_rate * 100).toFixed(2)}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">重连次数</span>
              <span className="font-medium">{quality.md_quality.reconnect_count}</span>
            </div>
            {quality.md_quality.last_reconnect_time && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <AlertTriangle className="h-3 w-3" />
                最后重连: {new Date(quality.md_quality.last_reconnect_time).toLocaleString()}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              {tdConnected ? (
                <Wifi className="h-4 w-4 text-green-600" />
              ) : (
                <WifiOff className="h-4 w-4 text-red-600" />
              )}
              交易连接质量
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">延迟</span>
              <div className="flex items-center gap-2">
                <span className="font-medium">{quality.td_quality.latency_ms.toFixed(0)} ms</span>
                {getLatencyBadge(quality.td_quality.latency_ms)}
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">拒绝率</span>
              <span className="font-medium">
                {(quality.td_quality.rejection_rate * 100).toFixed(3)}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">重连次数</span>
              <span className="font-medium">{quality.td_quality.reconnect_count}</span>
            </div>
            {quality.td_quality.last_reconnect_time && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <AlertTriangle className="h-3 w-3" />
                最后重连: {new Date(quality.td_quality.last_reconnect_time).toLocaleString()}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 延迟历史图表 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="h-4 w-4" />
            延迟历史（最近 2 分钟）
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={latencyHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} label={{ value: "延迟 (ms)", angle: -90, position: "insideLeft" }} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="md"
                stroke="#8884d8"
                name="行情延迟"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="td"
                stroke="#82ca9d"
                name="交易延迟"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
