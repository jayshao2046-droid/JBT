"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart3 } from "lucide-react"

export default function CollectionAnalysis() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-foreground flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-orange-500" />
          采集分析
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground">采集分析功能开发中...</p>
      </CardContent>
    </Card>
  )
}
