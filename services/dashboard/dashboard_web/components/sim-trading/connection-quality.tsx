"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Wifi, WifiOff } from "lucide-react"

interface ConnectionQualityProps {
  mdConnected: boolean
  tdConnected: boolean
  latency?: number
}

export function ConnectionQuality({ mdConnected, tdConnected, latency }: ConnectionQualityProps) {
  const overallStatus = mdConnected && tdConnected ? "connected" : "disconnected"

  return (
    <Card>
      <CardHeader>
        <CardTitle>连接质量</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 border rounded">
            <div className="flex items-center gap-2">
              {mdConnected ? (
                <Wifi className="w-5 h-5 text-green-500" />
              ) : (
                <WifiOff className="w-5 h-5 text-red-500" />
              )}
              <span className="text-sm">行情前置</span>
            </div>
            <Badge variant={mdConnected ? "default" : "secondary"}>
              {mdConnected ? "已连接" : "未连接"}
            </Badge>
          </div>

          <div className="flex items-center justify-between p-3 border rounded">
            <div className="flex items-center gap-2">
              {tdConnected ? (
                <Wifi className="w-5 h-5 text-green-500" />
              ) : (
                <WifiOff className="w-5 h-5 text-red-500" />
              )}
              <span className="text-sm">交易前置</span>
            </div>
            <Badge variant={tdConnected ? "default" : "secondary"}>
              {tdConnected ? "已连接" : "未连接"}
            </Badge>
          </div>

          {latency !== undefined && (
            <div className="flex items-center justify-between p-3 border rounded">
              <span className="text-sm">网络延迟</span>
              <Badge variant={latency <= 100 ? "default" : "secondary"}>
                {latency.toFixed(0)} ms
              </Badge>
            </div>
          )}

          <div className="flex items-center justify-between p-3 border rounded bg-muted/50">
            <span className="text-sm font-medium">整体状态</span>
            <Badge variant={overallStatus === "connected" ? "default" : "destructive"}>
              {overallStatus === "connected" ? "正常" : "异常"}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
