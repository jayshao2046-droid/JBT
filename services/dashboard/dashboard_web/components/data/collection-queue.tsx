"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ListOrdered } from "lucide-react"

export default function CollectionQueue() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-foreground flex items-center gap-2">
          <ListOrdered className="w-4 h-4 text-orange-500" />
          采集队列
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-neutral-500">采集队列功能开发中...</p>
      </CardContent>
    </Card>
  )
}
