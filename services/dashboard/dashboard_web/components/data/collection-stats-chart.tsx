"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp } from "lucide-react"

export default function CollectionStatsChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-neutral-300 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-orange-500" />
          采集统计图
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-neutral-500">采集统计图功能开发中...</p>
      </CardContent>
    </Card>
  )
}
