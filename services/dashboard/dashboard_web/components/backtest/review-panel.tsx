"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function ReviewPanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>审查面板</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground text-sm">审查面板开发中...</p>
      </CardContent>
    </Card>
  )
}
