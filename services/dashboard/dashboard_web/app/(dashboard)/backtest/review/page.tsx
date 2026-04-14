"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import MainLayout from "@/components/layout/main-layout"

export default function ReviewPage() {
  return (
    <MainLayout title="策略审查">
      <div className="p-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>策略审查</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-sm">审查功能开发中...</p>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
