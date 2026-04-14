"use client"

import { NotificationsReport } from "@/components/decision/notifications-report"
import { ConfigRuntime } from "@/components/decision/config-runtime"
import { OptimizerPanel } from "@/components/decision/optimizer-panel"

export default function ReportsPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">通知与日报</h1>
        <p className="text-muted-foreground mt-1">通知渠道与日报管理</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ConfigRuntime />
        <OptimizerPanel />
      </div>

      <NotificationsReport />
    </div>
  )
}
