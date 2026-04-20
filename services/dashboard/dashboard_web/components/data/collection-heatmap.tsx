"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Grid3x3 } from "lucide-react"

export default function CollectionHeatmap() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-neutral-300 flex items-center gap-2">
          <Grid3x3 className="w-4 h-4 text-orange-500" />
          采集热力图
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-neutral-500">采集热力图功能开发中...</p>
      </CardContent>
    </Card>
  )
}
