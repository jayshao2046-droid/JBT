"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export function FuturesResearchPanel() {
  const panels = [
    {
      title: "活跃合约监控",
      description: "实时跟踪主力合约持仓量和成交量变化"
    },
    {
      title: "跨期价差分析",
      description: "监控近远月合约价差，捕捉套利机会"
    },
    {
      title: "持仓量分析",
      description: "分析多空持仓变化，判断市场情绪"
    }
  ]

  return (
    <div className="space-y-6">
      <div className="text-center py-8">
        <h2 className="text-2xl font-bold text-white mb-2">期货策略研究中心</h2>
        <p className="text-neutral-400">
          依赖 CA6 期货因子加载完成后启用
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {panels.map((panel, idx) => (
          <Card key={idx} className="bg-neutral-900 border-neutral-800">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white text-lg">{panel.title}</CardTitle>
                <Badge variant="secondary" className="bg-yellow-600 text-white">
                  Coming Soon
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-neutral-400 text-sm">{panel.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
