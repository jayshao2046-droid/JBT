"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity } from "lucide-react"

export default function DataSourceHealthKPI() {
  return (
    <Card className="bg-neutral-900 border-neutral-800">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-neutral-300 flex items-center gap-2">
          <Activity className="w-4 h-4 text-orange-500" />
          数据源健康度 KPI
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-neutral-500">数据源健康度 KPI 功能开发中...</p>
      </CardContent>
    </Card>
  )
}
