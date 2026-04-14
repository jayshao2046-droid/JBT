"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { useState } from "react"

interface RiskConfigEditorProps {
  symbol: string
  config: {
    max_lots: number
    max_position: number
    daily_loss_pct: number
    price_dev_pct: number
  }
  onSave: (config: { max_lots: number; max_position: number; daily_loss_pct: number; price_dev_pct: number }) => void
}

export function RiskConfigEditor({ symbol, config, onSave }: RiskConfigEditorProps) {
  const [form, setForm] = useState(config)

  return (
    <Card>
      <CardHeader>
        <CardTitle>{symbol} 风控配置</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label>最大手数</Label>
          <Input
            type="number"
            value={form.max_lots}
            onChange={(e) => setForm({ ...form, max_lots: parseInt(e.target.value) || 0 })}
          />
        </div>
        <div>
          <Label>最大持仓</Label>
          <Input
            type="number"
            value={form.max_position}
            onChange={(e) => setForm({ ...form, max_position: parseInt(e.target.value) || 0 })}
          />
        </div>
        <div>
          <Label>日内亏损比例 (%)</Label>
          <Input
            type="number"
            value={(form.daily_loss_pct * 100).toFixed(1)}
            onChange={(e) => setForm({ ...form, daily_loss_pct: parseFloat(e.target.value) / 100 || 0 })}
          />
        </div>
        <div>
          <Label>价格偏离比例 (%)</Label>
          <Input
            type="number"
            value={(form.price_dev_pct * 100).toFixed(1)}
            onChange={(e) => setForm({ ...form, price_dev_pct: parseFloat(e.target.value) / 100 || 0 })}
          />
        </div>
        <Button onClick={() => onSave(form)} className="w-full">
          保存配置
        </Button>
      </CardContent>
    </Card>
  )
}
