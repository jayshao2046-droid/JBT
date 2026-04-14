"use client"

import { ReactNode } from "react"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useRouter, usePathname } from "next/navigation"
import { BarChart3, Play, TrendingUp, CheckSquare, Settings } from "lucide-react"

export default function BacktestLayout({ children }: { children: ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()

  const tabs = [
    { value: "/backtest", label: "总览", icon: BarChart3 },
    { value: "/backtest/operations", label: "操作台", icon: Play },
    { value: "/backtest/results", label: "结果查看", icon: TrendingUp },
    { value: "/backtest/review", label: "审查", icon: CheckSquare },
    { value: "/backtest/optimizer", label: "参数优化", icon: Settings },
  ]

  const currentTab = tabs.find(t => pathname === t.value)?.value || "/backtest"

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">回测系统</h1>
          <p className="text-muted-foreground mt-1">策略回测与参数优化 - Air:8103</p>
        </div>
      </div>

      <Tabs value={currentTab} onValueChange={(v) => router.push(v)}>
        <TabsList className="grid w-full grid-cols-5">
          {tabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value} className="flex items-center gap-2">
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {children}
    </div>
  )
}
