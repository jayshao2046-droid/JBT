"use client"

import { ReactNode } from "react"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useRouter, usePathname } from "next/navigation"
import { Activity, TrendingUp, BarChart3, Shield, Settings, Gauge } from "lucide-react"

export default function SimTradingLayout({ children }: { children: ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()

  const tabs = [
    { value: "/sim-trading", label: "总览", icon: Gauge },
    { value: "/sim-trading/operations", label: "交易终端", icon: Activity },
    { value: "/sim-trading/market", label: "行情报价", icon: TrendingUp },
    { value: "/sim-trading/intelligence", label: "风控监控", icon: Shield },
    { value: "/sim-trading/risk-presets", label: "品种风控", icon: BarChart3 },
    { value: "/sim-trading/ctp-config", label: "CTP配置", icon: Settings },
  ]

  const currentTab = tabs.find(t => pathname === t.value)?.value || "/sim-trading"

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">模拟交易</h1>
          <p className="text-muted-foreground mt-1">期货模拟交易系统 - Mini:8101</p>
        </div>
      </div>

      <Tabs value={currentTab} onValueChange={(v) => router.push(v)}>
        <TabsList className="grid w-full grid-cols-6">
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
