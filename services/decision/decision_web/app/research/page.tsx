"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { StockPoolTable } from "@/components/StockPoolTable"
import { IntradaySignal } from "@/components/IntradaySignal"
import { PostMarketReport } from "@/components/PostMarketReport"
import { EveningRotationPlan } from "@/components/EveningRotationPlan"
import { FuturesResearchPanel } from "@/components/FuturesResearchPanel"

export default function ResearchPage() {
  const [refreshToken, setRefreshToken] = useState(0)

  return (
    <div className="min-h-screen bg-black p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">策略研究中心</h1>
            <p className="text-neutral-400 mt-1">
              Phase C · 股票日线策略 + 期货研究框架
            </p>
          </div>
          <button
            onClick={() => setRefreshToken(Date.now())}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            刷新数据
          </button>
        </div>

        <Tabs defaultValue="stock" className="w-full">
          <TabsList className="bg-neutral-900 border border-neutral-800">
            <TabsTrigger value="stock" className="data-[state=active]:bg-neutral-800">
              股票策略
            </TabsTrigger>
            <TabsTrigger value="futures" className="data-[state=active]:bg-neutral-800">
              期货研究
            </TabsTrigger>
          </TabsList>

          <TabsContent value="stock" className="space-y-6 mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <StockPoolTable refreshToken={refreshToken} />
              <IntradaySignal refreshToken={refreshToken} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <PostMarketReport refreshToken={refreshToken} />
              <EveningRotationPlan refreshToken={refreshToken} />
            </div>
          </TabsContent>

          <TabsContent value="futures" className="mt-6">
            <FuturesResearchPanel />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
