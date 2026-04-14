"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ListOrdered } from "lucide-react"

export default function CollectionQueue() {
  return (
    <Card className="bg-neutral-900 border-neutral-800">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-neutral-300 flex items-center gap-2">
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
