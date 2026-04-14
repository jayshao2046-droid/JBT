"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { Database } from "lucide-react"
import type { CollectorStatus } from "@/lib/api/types"

interface DataSourceStatusProps {
  dataSources: CollectorStatus[]
}

function formatTimeAgo(timestamp: string): string {
  const now = new Date()
  const past = new Date(timestamp)
  const diffMs = now.getTime() - past.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return "刚刚"
  if (diffMins < 60) return `${diffMins}分钟前`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}小时前`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}天前`
}

export function DataSourceStatus({ dataSources }: DataSourceStatusProps) {
  const safeSources = Array.isArray(dataSources) ? dataSources : []

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return { dot: "bg-green-500", text: "text-green-400", label: "在线" }
      case "stopped":
        return { dot: "bg-yellow-500", text: "text-yellow-400", label: "警告" }
      case "error":
        return { dot: "bg-red-500", text: "text-red-400", label: "离线" }
      default:
        return { dot: "bg-neutral-500", text: "text-neutral-400", label: "未知" }
    }
  }

  const onlineCount = safeSources.filter((d) => d.status === "running").length
  const health = safeSources.length > 0 ? Math.round((onlineCount / safeSources.length) * 100) : 0

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Database className="w-4 h-4 text-cyan-400" />
          数据源状态监控
        </CardTitle>
        <div className="text-sm">
          <span className="text-neutral-400">健康度</span>
          <span className="text-green-400 font-semibold ml-2">{health}%</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {safeSources.length === 0 ? (
          <p className="text-sm text-muted-foreground">暂无数据源</p>
        ) :
          safeSources.map((source) => {
          const statusColor = getStatusColor(source.status)
          return (
            <div
              key={source.name}
              className="flex items-center gap-3 p-3 bg-white/[0.03] hover:bg-white/[0.06] rounded transition-colors"
            >
              <div className={cn("w-2 h-2 rounded-full", statusColor.dot)} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-white">{source.name}</span>
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs px-1.5 py-0",
                      statusColor.text.replace("text-", "bg-").replace("-400", "-500/20"),
                      statusColor.text,
                      "border-opacity-30"
                    )}
                  >
                    {statusColor.label}
                  </Badge>
                </div>
                <div className="flex items-center gap-3 text-xs text-neutral-400">
                  {source.data_count !== undefined && <span>数据量：{source.data_count}</span>}
                  <span>更新于：{formatTimeAgo(source.last_update)}</span>
                </div>
              </div>
            </div>
          )
        })}
        <Button
          variant="outline"
          className="w-full mt-3 border-neutral-700 hover:border-orange-500/50 hover:bg-orange-500/10 text-neutral-400 hover:text-orange-400"
        >
          查看详情
        </Button>
      </CardContent>
    </Card>
  )
}
