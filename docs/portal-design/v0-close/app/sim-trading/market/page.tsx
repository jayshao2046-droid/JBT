"use client"

import { useState, useEffect } from "react"
import { TrendingUp, TrendingDown, Wifi, RefreshCw, ChevronUp, ChevronDown } from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const quotes = [
  { symbol: "IF2501", name: "沪深300", price: 3892.4, change: 42.2, changePct: 1.09, vol: 15234, oi: 98456 },
  { symbol: "IC2501", name: "中证500", price: 5588.6, change: -35.2, changePct: -0.63, vol: 8921, oi: 45678 },
  { symbol: "IH2501", name: "上证50", price: 2756.4, change: 18.6, changePct: 0.68, vol: 6234, oi: 32456 },
  { symbol: "IM2501", name: "中证1000", price: 5234.8, change: -28.4, changePct: -0.54, vol: 12456, oi: 67890 },
  { symbol: "RB2501", name: "螺纹钢", price: 3268, change: 28, changePct: 0.86, vol: 456789, oi: 2345678 },
  { symbol: "HC2501", name: "热轧卷板", price: 3512, change: 32, changePct: 0.92, vol: 234567, oi: 1234567 },
  { symbol: "CU2501", name: "铜", price: 75200, change: 350, changePct: 0.47, vol: 56789, oi: 345678 },
  { symbol: "AL2501", name: "铝", price: 20450, change: -120, changePct: -0.58, vol: 78901, oi: 456789 },
  { symbol: "AU2506", name: "黄金", price: 624.2, change: -4.3, changePct: -0.68, vol: 23456, oi: 123456 },
  { symbol: "AG2506", name: "白银", price: 7856, change: 56, changePct: 0.72, vol: 34567, oi: 234567 },
]

export default function SimMarketPage() {
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [latency, setLatency] = useState(12)

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => { setLastUpdate(new Date()); setIsRefreshing(false) }, 600)
  }

  useEffect(() => {
    setLastUpdate(new Date())
    const timer = setInterval(() => {
      setLatency(Math.floor(Math.random() * 20) + 5)
    }, 3000)
    return () => clearInterval(timer)
  }, [])

  return (
    <MainLayout
      title="模拟交易"
      subtitle="行情报价"
      onRefresh={handleRefresh}
      isRefreshing={isRefreshing}
      lastUpdate={lastUpdate}
    >
      <div className="p-4 md:p-6 space-y-6">
        {/* 连接状态 */}
        <div className="flex items-center gap-4 p-3 glass-card rounded-lg">
          <div className="flex items-center gap-2">
            <Wifi className="w-4 h-4 text-green-500" />
            <span className="text-sm text-green-400 font-medium">行情已连接</span>
          </div>
          <div className="text-sm text-muted-foreground">
            延迟: <span className="text-foreground font-mono">{latency}ms</span>
          </div>
          <div className="text-sm text-muted-foreground">
            CTP 行情服务器: <span className="text-foreground">tcp://180.168.146.187:10131</span>
          </div>
          <Button variant="ghost" size="sm" onClick={handleRefresh} className="ml-auto text-muted-foreground hover:text-orange-500">
            <RefreshCw className={cn("w-4 h-4", isRefreshing && "animate-spin")} />
          </Button>
        </div>

        {/* 行情表格 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-foreground flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-orange-500" />
              实时行情
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-neutral-800">
                    {["合约", "品名", "最新价", "涨跌", "涨跌幅", "成交量", "持仓量"].map((h) => (
                      <th key={h} className="text-left py-3 px-4 text-xs text-neutral-500 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {quotes.map((q) => (
                    <tr key={q.symbol} className="border-b border-neutral-800/50 hover:bg-neutral-800/30 transition-colors">
                      <td className="py-3 px-4 text-white font-mono font-medium">{q.symbol}</td>
                      <td className="py-3 px-4 text-neutral-400">{q.name}</td>
                      <td className="py-3 px-4 font-mono">
                        <span className={q.change >= 0 ? "text-green-400" : "text-red-400"}>
                          {q.price.toLocaleString()}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono">
                        <div className={cn("flex items-center gap-1", q.change >= 0 ? "text-green-400" : "text-red-400")}>
                          {q.change >= 0 ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          {Math.abs(q.change).toLocaleString()}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="outline" className={cn(
                          "text-xs font-mono",
                          q.changePct >= 0 ? "border-green-500/30 text-green-400 bg-green-500/5" : "border-red-500/30 text-red-400 bg-red-500/5"
                        )}>
                          {q.changePct >= 0 ? "+" : ""}{q.changePct.toFixed(2)}%
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-neutral-400 font-mono">{q.vol.toLocaleString()}</td>
                      <td className="py-3 px-4 text-neutral-400 font-mono">{q.oi.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
