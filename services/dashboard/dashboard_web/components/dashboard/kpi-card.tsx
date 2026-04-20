"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import type { LucideIcon } from "lucide-react"

interface KPICardProps {
  title: string
  value: string | number
  icon: LucideIcon
  change?: string
  changeType?: "positive" | "negative" | "neutral"
  description?: string
  progress?: number
  status?: "success" | "warning" | "danger" | "default"
}

export function KpiCard({
  title,
  value,
  icon: Icon,
  change,
  changeType,
  description,
  progress,
  status = "default",
}: KPICardProps) {
  const getChangeColor = (type?: string) => {
    switch (type) {
      case "positive":
        return "text-red-400"
      case "negative":
        return "text-green-400"
      default:
        return "text-muted-foreground"
    }
  }

  const getStatusColor = (currentStatus?: string) => {
    switch (currentStatus) {
      case "success":
        return { bg: "bg-green-500/20", text: "text-green-400", border: "border-green-500/30" }
      case "warning":
        return { bg: "bg-yellow-500/20", text: "text-yellow-400", border: "border-yellow-500/30" }
      case "danger":
        return { bg: "bg-red-500/20", text: "text-red-400", border: "border-red-500/30" }
      default:
        return { bg: "bg-orange-500/20", text: "text-orange-400", border: "border-orange-500/30" }
    }
  }

  const statusStyle = getStatusColor(status)

  return (
    <Card className={cn("transition-all duration-300 overflow-hidden glass-card", statusStyle.border)}>
      <CardContent className="p-4 relative">
        <div className="space-y-3">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-xs text-muted-foreground mb-1">{title}</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-foreground">
                  {typeof value === "number"
                    ? value.toLocaleString(undefined, {
                        maximumFractionDigits: value > 100 ? 0 : 2,
                      })
                    : value}
                </span>
                {change && (
                  <span className={cn("text-xs font-medium", getChangeColor(changeType))}>
                    {change}
                  </span>
                )}
              </div>
            </div>
            <div className={cn("p-2 rounded-lg backdrop-blur-sm shadow-lg", statusStyle.bg)}>
              <Icon className={cn("w-5 h-5 drop-shadow-lg", statusStyle.text)} />
            </div>
          </div>

          {progress !== undefined && (
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">{description}</span>
                <span className="text-foreground font-mono">{progress}%</span>
              </div>
              <Progress value={progress} className="h-1" />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
