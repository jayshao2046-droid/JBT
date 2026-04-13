"use client"

import { useState } from "react"
import { ParameterOptimizer } from "@/components/ParameterOptimizer"

export default function OptimizerPage() {
  const [selectedStrategy, setSelectedStrategy] = useState("default_strategy")

  const handleOptimize = async (algorithm: string, config: any) => {
    // 调用后端 API 进行参数优化
    // 这里是示例实现
    const response = await fetch("/api/backtest/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        strategy_id: selectedStrategy,
        algorithm,
        config,
      }),
    })

    if (!response.ok) {
      throw new Error("Optimization failed")
    }

    const data = await response.json()
    return data.results || []
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">策略参数优化</h1>
        <p className="text-muted-foreground mt-2">
          使用网格搜索、遗传算法或贝叶斯优化来寻找最佳策略参数
        </p>
      </div>

      <ParameterOptimizer
        strategyName={selectedStrategy}
        onOptimize={handleOptimize}
      />
    </div>
  )
}
