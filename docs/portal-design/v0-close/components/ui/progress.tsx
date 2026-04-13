"use client"

import * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"

import { cn } from "@/lib/utils"

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>
>(({ className, value, ...props }, ref) => {
  const pct = value || 0

  // 根据百分比返回渐变色：深到浅，左侧深右侧亮
  const getGradient = (val: number): string => {
    if (val < 50) {
      // 绿色系：深墨绿 → 亮绿
      return "linear-gradient(90deg, hsl(142 60% 15%) 0%, hsl(142 70% 45%) 100%)"
    }
    if (val < 80) {
      // 琥珀/橙色系：深橙褐 → 亮橙
      return "linear-gradient(90deg, hsl(24 80% 15%) 0%, hsl(38 95% 55%) 100%)"
    }
    // 红色系：深暗红 → 亮红
    return "linear-gradient(90deg, hsl(0 70% 15%) 0%, hsl(0 85% 55%) 100%)"
  }

  // 轨道背景：从黑到极淡白，完全去除灰色
  const trackGradient = "linear-gradient(90deg, hsl(0 0% 0% / 0.6) 0%, hsl(0 0% 100% / 0.04) 100%)"

  return (
    <ProgressPrimitive.Root
      ref={ref}
      className={cn(
        "relative h-1.5 w-full overflow-hidden rounded-full",
        className
      )}
      style={{ background: trackGradient }}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className="h-full w-full flex-1 transition-all duration-500"
        style={{
          transform: `translateX(-${100 - pct}%)`,
          background: getGradient(pct),
          boxShadow: pct > 0
            ? `0 0 6px hsl(${pct < 50 ? "142 70% 40%" : pct < 80 ? "30 95% 50%" : "0 85% 50%"} / 0.5)`
            : "none",
        }}
      />
    </ProgressPrimitive.Root>
  )
})
Progress.displayName = ProgressPrimitive.Root.displayName

export { Progress }
