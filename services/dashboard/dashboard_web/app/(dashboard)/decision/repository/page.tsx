"use client"

import { StrategyRepository } from "@/components/decision/strategy-repository"
import { StrategyImport } from "@/components/decision/strategy-import"
import { StockPoolTable } from "@/components/decision/stock-pool-table"

export default function RepositoryPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">策略仓库</h1>
        <p className="text-muted-foreground mt-1">策略管理与导入</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <StrategyImport />
        <StockPoolTable />
      </div>

      <StrategyRepository />
    </div>
  )
}
