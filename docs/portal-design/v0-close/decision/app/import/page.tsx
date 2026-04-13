"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { StrategyImport } from "@/components/StrategyImport"

export default function ImportPage() {
  return (
    <div className="min-h-screen bg-black p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white">策略导入</h1>
          <p className="text-neutral-400 mt-1">
            上传 YAML 策略文件到决策系统
          </p>
        </div>

        <StrategyImport />
      </div>
    </div>
  )
}
