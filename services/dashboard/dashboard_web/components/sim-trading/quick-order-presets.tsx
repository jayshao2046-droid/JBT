"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

interface QuickOrderPresetsProps {
  onOrderClick: (preset: { symbol: string; direction: "long" | "short"; volume: number }) => void
}

const PRESETS = [
  { symbol: "rbM", name: "螺纹钢", direction: "long" as const, volume: 1 },
  { symbol: "rbM", name: "螺纹钢", direction: "short" as const, volume: 1 },
  { symbol: "iM", name: "铁矿石", direction: "long" as const, volume: 1 },
  { symbol: "iM", name: "铁矿石", direction: "short" as const, volume: 1 },
  { symbol: "IF", name: "沪深300", direction: "long" as const, volume: 1 },
  { symbol: "IF", name: "沪深300", direction: "short" as const, volume: 1 },
]

export function QuickOrderPresets({ onOrderClick }: QuickOrderPresetsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>快速下单</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {PRESETS.map((preset, idx) => (
            <Button
              key={idx}
              variant="outline"
              className="flex flex-col items-start h-auto p-3"
              onClick={() => onOrderClick(preset)}
            >
              <div className="flex items-center gap-2 w-full">
                <span className="font-medium">{preset.name}</span>
                <Badge variant={preset.direction === "long" ? "default" : "secondary"}>
                  {preset.direction === "long" ? "多" : "空"}
                </Badge>
              </div>
              <span className="text-xs text-muted-foreground mt-1">{preset.symbol} {preset.volume}手</span>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
