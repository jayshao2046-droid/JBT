"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export function BacktestTemplates() {
  const templates = [
    { name: "趋势跟踪", description: "基于均线的趋势策略" },
    { name: "均值回归", description: "价格回归策略" },
    { name: "动量策略", description: "动量因子策略" },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>策略模板</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {templates.map((template, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 border rounded">
              <div>
                <p className="font-medium">{template.name}</p>
                <p className="text-xs text-muted-foreground">{template.description}</p>
              </div>
              <Button size="sm" variant="outline">使用</Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
