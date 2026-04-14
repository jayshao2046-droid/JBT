"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import MainLayout from "@/components/layout/main-layout"

export default function OptimizerPage() {
  return (
    <MainLayout title="参数优化">
      <div className="p-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>参数优化</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-sm">参数优化功能开发中...</p>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
