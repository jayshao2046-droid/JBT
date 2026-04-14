"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function SystemMonitor() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>系统监控</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">系统监控页面</p>
      </CardContent>
    </Card>
  )
}
