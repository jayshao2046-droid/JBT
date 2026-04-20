"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Settings } from "lucide-react"

export default function DataSourceConfigEditor() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-neutral-300 flex items-center gap-2">
          <Settings className="w-4 h-4 text-orange-500" />
          数据源配置编辑器
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-neutral-500">数据源配置编辑器功能开发中...</p>
      </CardContent>
    </Card>
  )
}
