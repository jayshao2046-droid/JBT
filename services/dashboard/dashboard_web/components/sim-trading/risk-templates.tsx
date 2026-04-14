"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

interface RiskTemplatesProps {
  templates: Array<{
    name: string
    description: string
    config: {
      max_lots: number
      max_position: number
      daily_loss_pct: number
    }
  }>
  onApply: (template: { name: string; description: string; config: { max_lots: number; max_position: number; daily_loss_pct: number } }) => void
}

const DEFAULT_TEMPLATES = [
  {
    name: "保守型",
    description: "低风险，适合新手",
    config: { max_lots: 1, max_position: 3, daily_loss_pct: 0.02 },
  },
  {
    name: "稳健型",
    description: "中等风险，适合有经验者",
    config: { max_lots: 3, max_position: 10, daily_loss_pct: 0.05 },
  },
  {
    name: "激进型",
    description: "高风险，适合专业交易者",
    config: { max_lots: 5, max_position: 20, daily_loss_pct: 0.1 },
  },
]

export function RiskTemplates({ templates = DEFAULT_TEMPLATES, onApply }: RiskTemplatesProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>风控模板</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {templates.map((template, idx) => (
            <div key={idx} className="p-3 border rounded">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{template.name}</p>
                    <Badge variant="outline">{template.description}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    最大手数: {template.config.max_lots} | 最大持仓: {template.config.max_position} | 日亏损: {(template.config.daily_loss_pct * 100).toFixed(0)}%
                  </p>
                </div>
                <Button size="sm" variant="outline" onClick={() => onApply(template)}>
                  应用
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
