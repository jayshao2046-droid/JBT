"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface ServiceStatusCardProps {
  name: string
  status: "running" | "stopped" | "error" | "unknown"
  port: number
  description?: string
  lastUpdate?: string
}

const statusConfig = {
  running: {
    label: "运行中",
    className: "bg-green-500/10 text-green-500 border-green-500/20",
  },
  stopped: {
    label: "已停止",
    className: "bg-gray-500/10 text-gray-500 border-gray-500/20",
  },
  error: {
    label: "错误",
    className: "bg-red-500/10 text-red-500 border-red-500/20",
  },
  unknown: {
    label: "未知",
    className: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
  },
}

export function ServiceStatusCard({
  name,
  status,
  port,
  description,
  lastUpdate,
}: ServiceStatusCardProps) {
  const config = statusConfig[status]

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{name}</CardTitle>
        <Badge variant="outline" className={cn(config.className)}>
          {config.label}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">:{port}</div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
        {lastUpdate && (
          <p className="text-xs text-muted-foreground mt-2">
            最后更新: {lastUpdate}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
