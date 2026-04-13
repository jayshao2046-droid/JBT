"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ReportViewer } from "@/components/ReportViewer"

export default function ReportsPage() {
  return (
    <div className="min-h-screen bg-black p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white">回测报告</h1>
          <p className="text-neutral-400 mt-1">
            查看策略回测详细报告
          </p>
        </div>

        <ReportViewer />
      </div>
    </div>
  )
}
