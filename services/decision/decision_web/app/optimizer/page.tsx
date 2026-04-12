"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { OptimizerPanel } from "@/components/OptimizerPanel"

export default function OptimizerPage() {
  return (
    <div className="min-h-screen bg-black p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white">参数调优</h1>
          <p className="text-neutral-400 mt-1">
            网格搜索最优参数组合
          </p>
        </div>

        <OptimizerPanel />
      </div>
    </div>
  )
}
