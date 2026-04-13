"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ServiceStatusCard } from "./service-status-card"

interface StatusOverviewProps {
  services?: Array<{
    name: string
    status: "running" | "stopped" | "error" | "unknown"
    port: number
    description?: string
    lastUpdate?: string
  }>
}

const defaultServices = [
  {
    name: "模拟交易端",
    status: "running" as const,
    port: 8101,
    description: "实盘模拟交易服务",
    lastUpdate: "刚刚",
  },
  {
    name: "回测端",
    status: "running" as const,
    port: 8103,
    description: "策略回测服务",
    lastUpdate: "1分钟前",
  },
  {
    name: "决策端",
    status: "running" as const,
    port: 8104,
    description: "智能决策服务",
    lastUpdate: "2分钟前",
  },
  {
    name: "数据端",
    status: "running" as const,
    port: 8105,
    description: "数据采集与处理服务",
    lastUpdate: "3分钟前",
  },
]

export function StatusOverview({ services = defaultServices }: StatusOverviewProps) {
  const runningCount = services.filter((s) => s.status === "running").length
  const totalCount = services.length

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>系统总览</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {runningCount} / {totalCount}
          </div>
          <p className="text-xs text-muted-foreground">服务运行中</p>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {services.map((service) => (
          <ServiceStatusCard key={service.name} {...service} />
        ))}
      </div>
    </div>
  )
}
