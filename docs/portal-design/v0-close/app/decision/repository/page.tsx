"use client"

import { Database, Search, GitBranch, Star, Clock } from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const strategies = [
  { id: "ST-001", name: "双均线 CTA", category: "趋势", markets: ["商品期货"], version: "v3.2", stars: 24, lastUpdate: "2天前", status: "生产", pnl: "+18.4%" },
  { id: "ST-002", name: "均值回归套利", category: "套利", markets: ["股指期货"], version: "v1.5", stars: 18, lastUpdate: "5天前", status: "测试", pnl: "+9.2%" },
  { id: "ST-003", name: "高频做市", category: "高频", markets: ["商品期货", "股指期货"], version: "v2.0", stars: 31, lastUpdate: "1天前", status: "生产", pnl: "+34.7%" },
  { id: "ST-004", name: "网格交易", category: "网格", markets: ["商品期货"], version: "v1.1", stars: 12, lastUpdate: "1周前", status: "暂停", pnl: "+5.6%" },
  { id: "ST-005", name: "多因子量化选股", category: "多因子", markets: ["股指期货"], version: "v4.1", stars: 45, lastUpdate: "3天前", status: "生产", pnl: "+22.3%" },
  { id: "ST-006", name: "布林带反转", category: "反转", markets: ["商品期货"], version: "v1.8", stars: 8, lastUpdate: "2周前", status: "研发", pnl: "-2.1%" },
]

const statusColors: Record<string, string> = {
  生产: "border-green-500/30 text-green-400",
  测试: "border-blue-500/30 text-blue-400",
  暂停: "border-yellow-500/30 text-yellow-400",
  研发: "border-border text-muted-foreground",
}

export default function DecisionRepositoryPage() {
  return (
    <MainLayout title="智能决策" subtitle="策略仓库">
      <div className="p-4 md:p-6 space-y-6">
        {/* 搜索栏 */}
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="搜索策略名称、类别..."
              className="pl-9 bg-card border-border text-foreground placeholder:text-muted-foreground/50 focus:border-purple-500"
            />
          </div>
          <Button className="bg-purple-600 hover:bg-purple-700 text-white">
            新建策略
          </Button>
        </div>

        {/* 统计 */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "全部策略", value: strategies.length },
            { label: "生产运行", value: strategies.filter((s) => s.status === "生产").length },
            { label: "测试中", value: strategies.filter((s) => s.status === "测试").length },
            { label: "平均收益", value: "+14.7%" },
          ].map((stat) => (
            <Card key={stat.label} className="bg-card border-border">
              <CardContent className="p-4 text-center">
                <p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
                <p className="text-xl font-bold text-foreground">{stat.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* 策略列表 */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {strategies.map((strategy) => (
            <Card key={strategy.id} className="bg-card border-border hover:border-purple-500/30 transition-colors cursor-pointer">
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-foreground font-medium">{strategy.name}</h3>
                    <p className="text-xs text-muted-foreground mt-0.5">{strategy.id} · {strategy.version}</p>
                  </div>
                  <Badge variant="outline" className={cn("text-xs", statusColors[strategy.status])}>
                    {strategy.status}
                  </Badge>
                </div>
                <div className="flex flex-wrap gap-1 mb-3">
                  <Badge variant="outline" className="text-xs border-purple-500/30 text-purple-400">{strategy.category}</Badge>
                  {strategy.markets.map((m) => (
                    <Badge key={m} variant="outline" className="text-xs border-border text-muted-foreground">{m}</Badge>
                  ))}
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <Star className="w-3 h-3" /> {strategy.stars}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {strategy.lastUpdate}
                    </span>
                  </div>
                  <span className={cn("font-mono font-medium", strategy.pnl.startsWith("+") ? "text-green-400" : "text-red-400")}>
                    {strategy.pnl}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </MainLayout>
  )
}
