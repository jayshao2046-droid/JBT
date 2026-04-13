"use client"

import { useState, useEffect } from "react"
import {
  TrendingUp, TrendingDown, Activity, ShoppingCart, BarChart3,
  AlertTriangle, CheckCircle, RefreshCw, ChevronUp, ChevronDown
} from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

const positions = [
  { symbol: "IF2501", name: "沪深300股指期货", direction: "多", qty: 2, cost: 3850.2, current: 3892.4, pnl: 8360, margin: 115506 },
  { symbol: "IC2501", name: "中证500股指期货", direction: "空", qty: 1, cost: 5623.8, current: 5588.6, pnl: 3520, margin: 112476 },
  { symbol: "RB2501", name: "螺纹钢主力", direction: "多", qty: 5, cost: 3240, current: 3268, pnl: 1400, margin: 48600 },
  { symbol: "CU2501", name: "铜主力", direction: "多", qty: 1, cost: 74850, current: 75200, pnl: 3500, margin: 37425 },
  { symbol: "AU2506", name: "黄金主力", direction: "空", qty: 2, cost: 628.5, current: 624.2, pnl: 860, margin: 25140 },
]

const orders = [
  { id: "20250101001", symbol: "IF2501", direction: "多", qty: 2, price: 3880.0, status: "已成交", time: "09:31:24" },
  { id: "20250101002", symbol: "IC2501", direction: "空", qty: 1, price: 5625.0, status: "已成交", time: "09:35:18" },
  { id: "20250101003", symbol: "RU2501", direction: "多", qty: 3, price: 13550, status: "已撤销", time: "10:12:05" },
  { id: "20250101004", symbol: "RB2501", direction: "多", qty: 5, price: 3240, status: "已成交", time: "10:45:33" },
]

export default function SimOperationsPage() {
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const totalPnl = positions.reduce((sum, p) => sum + p.pnl, 0)
  const totalMargin = positions.reduce((sum, p) => sum + p.margin, 0)

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => { setLastUpdate(new Date()); setIsRefreshing(false) }, 800)
  }

  useEffect(() => { setLastUpdate(new Date()) }, [])

  return (
    <MainLayout
      title="模拟交易"
      subtitle="交易终端"
      onRefresh={handleRefresh}
      isRefreshing={isRefreshing}
      lastUpdate={lastUpdate}
    >
      <div className="p-4 md:p-6 space-y-6">
        {/* 账户概览 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "动态权益", value: "¥1,245,680", sub: "+¥17,640", positive: true },
            { label: "今日盈亏", value: `+¥${totalPnl.toLocaleString()}`, sub: "+1.43%", positive: true },
            { label: "占用保证金", value: `¥${totalMargin.toLocaleString()}`, sub: "占比 26.8%", positive: null },
            { label: "可用资金", value: "¥910,153", sub: "风险度 27%", positive: null },
          ].map((item) => (
            <Card key={item.label}>
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground mb-1">{item.label}</p>
                <p className={cn("text-xl font-bold font-mono", item.positive === true ? "text-red-400" : item.positive === false ? "text-green-400" : "text-foreground")}>
                  {item.value}
                </p>
                <p className="text-xs text-muted-foreground mt-1">{item.sub}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 持仓列表 */}
          <div className="lg:col-span-2">
            <Card className="bg-card border-border">
              <CardHeader className="flex flex-row items-center justify-between pb-3">
                <CardTitle className="text-base text-foreground flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-orange-500" />
                  当前持仓
                  <Badge variant="outline" className="border-border text-muted-foreground text-xs">
                    {positions.length} 个品种
                  </Badge>
                </CardTitle>
                <Button variant="ghost" size="sm" onClick={handleRefresh} className="text-muted-foreground hover:text-orange-500">
                  <RefreshCw className={cn("w-4 h-4", isRefreshing && "animate-spin")} />
                </Button>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border">
                        {["合约", "方向", "持仓量", "成本价", "现价", "盈亏"].map((h) => (
                          <th key={h} className="text-left py-3 px-4 text-xs text-muted-foreground font-medium">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {positions.map((pos) => (
                        <tr key={pos.symbol} className="border-b border-border/50 hover:bg-accent/30 transition-colors">
                          <td className="py-3 px-4">
                            <div>
                              <p className="text-foreground font-medium font-mono">{pos.symbol}</p>
                              <p className="text-xs text-muted-foreground">{pos.name}</p>
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <Badge className={cn("text-xs", pos.direction === "多" ? "bg-red-500/10 text-red-400 border-red-500/30" : "bg-green-500/10 text-green-400 border-green-500/30")} variant="outline">
                              {pos.direction === "多" ? <ChevronUp className="w-3 h-3 mr-1" /> : <ChevronDown className="w-3 h-3 mr-1" />}
                              {pos.direction}
                            </Badge>
                          </td>
                          <td className="py-3 px-4 text-foreground font-mono">{pos.qty} 手</td>
                          <td className="py-3 px-4 text-muted-foreground font-mono">{pos.cost.toLocaleString()}</td>
                          <td className="py-3 px-4 font-mono">
                            <span className={pos.current > pos.cost ? "text-red-400" : "text-green-400"}>
                              {pos.current.toLocaleString()}
                            </span>
                          </td>
                          <td className="py-3 px-4 font-mono">
                            <span className={pos.pnl >= 0 ? "text-red-400" : "text-green-400"}>
                              {pos.pnl >= 0 ? "+" : ""}¥{pos.pnl.toLocaleString()}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 风控状态 */}
          <div className="space-y-4">
            <Card className="bg-card border-border">
              <CardHeader className="pb-3">
                <CardTitle className="text-base text-foreground flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-yellow-500" />
                  风控状态
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                  { label: "账户风险度", value: 27, warn: 60, danger: 80 },
                  { label: "持仓集中度", value: 45, warn: 70, danger: 90 },
                  { label: "日亏损限额", value: 18, warn: 50, danger: 80 },
                ].map((item) => (
                  <div key={item.label}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted-foreground">{item.label}</span>
                      <span className={cn(
                        "font-mono font-medium",
                        item.value >= item.danger ? "text-red-400" : item.value >= item.warn ? "text-yellow-400" : "text-green-400"
                      )}>{item.value}%</span>
                    </div>
                    <Progress
                      value={item.value}
                      className="h-2"
                    />
                  </div>
                ))}
                <div className="pt-2 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-green-400">风控正常，无预警</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border-border">
              <CardHeader className="pb-3">
                <CardTitle className="text-base text-foreground flex items-center gap-2">
                  <ShoppingCart className="w-4 h-4 text-blue-500" />
                  今日委托
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {orders.map((order) => (
                  <div key={order.id} className="flex items-center justify-between py-2 border-b border-border/50 last:border-0">
                    <div>
                      <p className="text-sm text-foreground font-mono">{order.symbol}</p>
                      <p className="text-xs text-muted-foreground">{order.time}</p>
                    </div>
                    <div className="text-right">
                      <Badge variant="outline" className={cn(
                        "text-xs mb-1",
                        order.status === "已成交" ? "border-green-500/30 text-green-400" : "border-border text-muted-foreground"
                      )}>
                        {order.status}
                      </Badge>
                      <p className="text-xs text-muted-foreground font-mono">{order.qty}手 @{order.price}</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
