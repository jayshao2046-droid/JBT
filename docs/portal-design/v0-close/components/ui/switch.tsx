"use client"

import * as React from "react"
import * as SwitchPrimitives from "@radix-ui/react-switch"

import { cn } from "@/lib/utils"

const Switch = React.forwardRef<
  React.ElementRef<typeof SwitchPrimitives.Root>,
  React.ComponentPropsWithoutRef<typeof SwitchPrimitives.Root>
>(({ className, ...props }, ref) => (
  <SwitchPrimitives.Root
    className={cn(
      // 轨道：透明背景 + 描边，选中时橙色描边发光，未选中时白色低透明描边
      "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50",
      "data-[state=checked]:border-orange-500 data-[state=checked]:bg-orange-500/10 data-[state=checked]:shadow-[0_0_10px_hsl(24_95%_53%/0.35)]",
      "data-[state=unchecked]:border-white/20 data-[state=unchecked]:bg-white/5",
      className
    )}
    {...props}
    ref={ref}
  >
    <SwitchPrimitives.Thumb
      className={cn(
        // 旋钮：选中时橙色实心+发光，未选中时白色半透明
        "pointer-events-none block h-4 w-4 rounded-full shadow-lg ring-0 transition-all duration-300",
        "data-[state=checked]:translate-x-6 data-[state=checked]:bg-orange-400 data-[state=checked]:shadow-[0_0_6px_hsl(24_95%_53%/0.8)]",
        "data-[state=unchecked]:translate-x-1 data-[state=unchecked]:bg-white/40"
      )}
    />
  </SwitchPrimitives.Root>
))
Switch.displayName = SwitchPrimitives.Root.displayName

export { Switch }
