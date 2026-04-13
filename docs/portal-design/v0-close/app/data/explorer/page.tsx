"use client"

import { useState } from "react"
import { Search, Download, Filter, BarChart3, Table2 } from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/lib/utils"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const dailyData = [
  { date: "2025-01-06", open: 3841.2, high: 3902.4, low: 3830.0, close: 3892.4, volume: 15234 },
  { date: "2025-01-05", open: 3810.0, high: 3855.6, low: 3795.2, close: 3841.2, volume: 12891 },
  { date: "2025-01-04", open: 3835.8, high: 3848.0, low: 3798.4, close: 3810.0, volume: 13456 },
  { date: "2025-01-03", open: 3780.4, high: 3852.2, low: 3775.0, close: 3835.8, volume: 18234 },
  { date: "2025-01-02", open: 3792.6, high: 3810.0, low: 3765.8, close: 3780.4, volume: 9876 },
  { date: "2024-12-30", open: 3812.4, high: 3825.6, low: 3780.2, close: 3792.6, volume: 11234 },
]

const chartData = dailyData.slice().reverse().map((d) => ({ date: d.date.slice(5), value: d.close }))

export default function DataExplorerPage() {
  const [symbol, setSymbol] = useState("IF2501")
  const [searchInput, setSearchInput] = useState("IF2501")

  const handleSearch = () => setSymbol(searchInput.toUpperCase())

  return (
    <MainLayout title="数据采集" subtitle="数据浏览">
      <div className="p-4 md:p-6 space-y-6">
        {/* 搜索栏 */}
        <div className="flex gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="输入合约代码..."
              className="pl-9 bg-card border-border text-foreground font-mono focus:border-cyan-500"
            />
          </div>
          <Button onClick={handleSearch} className="bg-cyan-600 hover:bg-cyan-700 text-white">查询</Button>
          <Button variant="outline" className="border-border text-muted-foreground hover:text-foreground">
            <Filter className="w-4 h-4 mr-2" />
            筛选
          </Button>
          <Button variant="outline" className="border-border text-muted-foreground hover:text-foreground">
            <Download className="w-4 h-4 mr-2" />
            导出
          </Button>
        </div>

        <Tabs defaultValue="chart">
          <TabsList className="bg-card border border-border">
            <TabsTrigger value="chart" className="data-[state=active]:bg-accent data-[state=active]:text-foreground text-muted-foreground">
              <BarChart3 className="w-4 h-4 mr-2" />
              图表视图
            </TabsTrigger>
            <TabsTrigger value="table" className="data-[state=active]:bg-accent data-[state=active]:text-foreground text-muted-foreground">
              <Table2 className="w-4 h-4 mr-2" />
              表格视图
            </TabsTrigger>
          </TabsList>

          <TabsContent value="chart">
            <Card className="bg-card border-border">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base text-foreground">
                    <span className="font-mono text-cyan-400">{symbol}</span>
                    <span className="text-muted-foreground text-sm font-normal ml-2">沪深300股指期货 · 日线</span>
                  </CardTitle>
                  <Badge variant="outline" className="border-green-500/30 text-green-400 text-xs">数据正常</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="transparent" />
                      <XAxis dataKey="date" tick={{ fill: "#737373", fontSize: 11 }} />
                      <YAxis domain={["auto", "auto"]} tick={{ fill: "#737373", fontSize: 11 }} tickFormatter={(v) => v.toLocaleString()} />
                      <Tooltip
                        contentStyle={{ background: "#171717", border: "1px solid #404040", borderRadius: 8 }}
                        labelStyle={{ color: "#a3a3a3" }}
                        formatter={(v: number) => [v.toLocaleString(), "收盘价"]}
                      />
                      <Area type="monotone" dataKey="value" stroke="#06b6d4" fill="url(#colorClose)" strokeWidth={2} dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="table">
            <Card className="bg-card border-border">
              <CardHeader className="pb-3">
                <CardTitle className="text-base text-foreground">
                  <span className="font-mono text-cyan-400">{symbol}</span>
                  <span className="text-muted-foreground text-sm font-normal ml-2">日线数据</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      {["日期", "开盘", "最高", "最低", "收盘", "成交量"].map((h) => (
                        <th key={h} className="text-left py-3 px-4 text-xs text-muted-foreground font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {dailyData.map((row) => (
                      <tr key={row.date} className="border-b border-border/50 hover:bg-accent/20">
                        <td className="py-3 px-4 text-muted-foreground font-mono text-xs">{row.date}</td>
                        <td className="py-3 px-4 text-foreground font-mono">{row.open.toLocaleString()}</td>
                        <td className="py-3 px-4 text-green-400 font-mono">{row.high.toLocaleString()}</td>
                        <td className="py-3 px-4 text-red-400 font-mono">{row.low.toLocaleString()}</td>
                        <td className="py-3 px-4 font-mono">
                          <span className={row.close >= row.open ? "text-green-400" : "text-red-400"}>
                            {row.close.toLocaleString()}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-muted-foreground font-mono">{row.volume.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </MainLayout>
  )
}
