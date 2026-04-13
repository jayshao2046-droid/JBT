"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { Eye, EyeOff, Plus } from "lucide-react"
import { useState } from "react"
import type { StrategySignal } from "@/lib/api/types"

interface StrategySignalsProps {
  signals: StrategySignal[]
  onManualOpen?: () => void
  onConfirmSignal?: (signal: StrategySignal) => void
  onDisableSignal?: (signal: StrategySignal) => void
}

export function StrategySignals({
  signals,
  onManualOpen,
  onConfirmSignal,
  onDisableSignal,
}: StrategySignalsProps) {
  const [disabledSignals, setDisabledSignals] = useState<string[]>(
    signals.filter((s) => s.status === "disabled").map((s) => s.id)
  )

  const toggleDisable = (signal: StrategySignal) => {
    setDisabledSignals((prev) =>
      prev.includes(signal.id) ? prev.filter((sid) => sid !== signal.id) : [...prev, signal.id]
    )
    onDisableSignal?.(signal)
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="text-base">策略信号推荐</CardTitle>
        <Button size="sm" className="bg-orange-600 hover:bg-orange-700 gap-1" onClick={onManualOpen}>
          <Plus className="w-4 h-4" />
          手动开仓
        </Button>
      </CardHeader>
      <CardContent className="space-y-2">
        {signals.map((signal) => {
          const isDisabled = disabledSignals.includes(signal.id)
          const signalColor = {
            long: "text-red-400 bg-red-500/20 border-red-500/30",
            short: "text-green-400 bg-green-500/20 border-green-500/30",
          }[signal.direction]

          const signalLabel = {
            long: "看多",
            short: "看空",
          }[signal.direction]

          return (
            <div
              key={signal.id}
              className={cn(
                "flex items-center gap-3 p-3 bg-white/[0.03] hover:bg-white/[0.06] rounded transition-colors",
                isDisabled && "opacity-50"
              )}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono font-semibold text-white text-sm">{signal.instrument_id}</span>
                  <span className="text-xs text-neutral-400">{new Date(signal.timestamp).toLocaleTimeString("zh-CN")}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-neutral-400">{signal.strategy_name}</span>
                  <Badge variant="outline" className={cn("text-xs px-1.5 py-0", signalColor)}>
                    {signalLabel}
                  </Badge>
                  <Badge
                    variant="outline"
                    className="text-xs px-1.5 py-0 bg-neutral-700/50 text-neutral-300 border-neutral-600/50"
                  >
                    置信度 {signal.confidence}%
                  </Badge>
                </div>
              </div>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-8 px-2 hover:bg-orange-500/20 hover:text-orange-400"
                  title="开仓"
                  onClick={() => onConfirmSignal?.(signal)}
                >
                  <Plus className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className={cn(
                    "h-8 px-2",
                    isDisabled
                      ? "hover:bg-green-500/20 hover:text-green-400"
                      : "hover:bg-red-500/20 hover:text-red-400"
                  )}
                  onClick={() => toggleDisable(signal)}
                  title={isDisabled ? "恢复" : "禁止"}
                >
                  {isDisabled ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                </Button>
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
