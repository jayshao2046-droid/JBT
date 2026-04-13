"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { RefreshCw } from "lucide-react"
import ReviewPanel from "@/components/ReviewPanel"
import StockReviewTable from "@/components/StockReviewTable"

export default function ReviewPage() {
  const [refreshKey, setRefreshKey] = useState(0)

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">策略审核中心</h1>
        <Button
          onClick={handleRefresh}
          variant="outline"
          size="sm"
          className="gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          刷新
        </Button>
      </div>

      <Tabs defaultValue="futures" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="futures">期货策略审核</TabsTrigger>
          <TabsTrigger value="stock">股票策略审核</TabsTrigger>
        </TabsList>

        <TabsContent value="futures" className="mt-6">
          <ReviewPanel key={`futures-${refreshKey}`} />
        </TabsContent>

        <TabsContent value="stock" className="mt-6">
          <StockReviewTable key={`stock-${refreshKey}`} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
