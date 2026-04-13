"use client"

import { useState } from "react"
import { Database, Play, Square, RotateCcw, Plus, Wifi, WifiOff } from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

const collectors = [
  { id: "sina_quotes", name: "新浪行情", source: "新浪财经", type: "实时", interval: "1s", enabled: true, status: "运行中", dataCount: "12,453", latency: "23ms", errorRate: "0.0%" },
  { id: "tushare_daily", name: "Tushare 日线", source: "Tushare Pro", type: "定时", interval: "每日 17:00", enabled: true, status: "运行中", dataCount: "8,901", latency: "450ms", errorRate: "0.1%" },
  { id: "akshare_index", name: "AkShare 指数", source: "AkShare", type: "定时", interval: "1min", enabled: true, status: "运行中", dataCount: "3,241", latency: "120ms", errorRate: "0.0%" },
  { id: "akshare_news", name: "AkShare 新闻", source: "AkShare", type: "定时", interval: "5min", enabled: false, status: "已停止", dataCount: "456", latency: "--", errorRate: "--" },
  { id: "eastmoney_fund", name: "东方财富基金", source: "东方财富", type: "定时", interval: "每日 18:00", enabled: true, status: "运行中", dataCount: "2,134", latency: "890ms", errorRate: "0.3%" },
  { id: "ctp_tick", name: "CTP Tick 数据", source: "CTP", type: "实时", interval: "实时", enabled: true, status: "错误", dataCount: "0", latency: "--", errorRate: "100%" },
  { id: "joinquant_factor", name: "聚宽因子库", source: "聚宽", type: "定时", interval: "每周一", enabled: true, status: "运行中", dataCount: "567", latency: "1.2s", errorRate: "0.0%" },
  { id: "wind_macro", name: "万得宏观数据", source: "Wind", type: "定时", interval: "每日", enabled: false, status: "未配置", dataCount: "0", latency: "--", errorRate: "--" },
]

export default function DataCollectorsPage() {
  const [collectorList, setCollectorList] = useState(collectors)

  const handleToggle = (id: string) => {
    setCollectorList((prev) => prev.map((c) => {
      if (c.id !== id) return c
      const enabled = !c.enabled
      return { ...c, enabled, status: enabled ? "运行中" : "已停止" }
    }))
    toast.success("采集器状态已更新")
  }

  const handleRestart = (id: string, name: string) => {
    toast.success(`${name} 已重启`)
  }

  const running = collectorList.filter((c) => c.status === "运行中").length
  const errored = collectorList.filter((c) => c.status === "错误").length

  return (
    <MainLayout title="数据采集" subtitle="采集器管理">
      <div className="p-4 md:p-6 space-y-6">
        {/* 概览 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "全部采集器", value: collectorList.length, color: "text-foreground" },
            { label: "运行中", value: running, color: "text-green-400" },
            { label: "异常", value: errored, color: "text-red-400" },
            { label: "今日采集", value: "27,752 条", color: "text-cyan-400" },
          ].map((stat) => (
            <Card key={stat.label} className="bg-card border-border">
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
                <p className={cn("text-2xl font-bold", stat.color)}>{stat.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* 采集器列表 */}
        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-base text-foreground flex items-center gap-2">
              <Database className="w-4 h-4 text-cyan-500" />
              采集器列表
            </CardTitle>
            <Button size="sm" className="bg-cyan-600 hover:bg-cyan-700 text-white text-xs">
              <Plus className="w-3 h-3 mr-1" />
              新增采集器
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    {["采集器", "数据源", "类型", "间隔", "状态", "今日数量", "延迟", "错误率", "启用", "操作"].map((h) => (
                      <th key={h} className="text-left py-3 px-4 text-xs text-muted-foreground font-medium whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {collectorList.map((c) => (
                    <tr key={c.id} className="border-b border-border/50 hover:bg-accent/20">
                      <td className="py-3 px-4">
                        <p className="text-foreground text-sm">{c.name}</p>
                        <p className="text-xs text-muted-foreground font-mono">{c.id}</p>
                      </td>
                      <td className="py-3 px-4 text-muted-foreground text-xs">{c.source}</td>
                      <td className="py-3 px-4">
                        <Badge variant="outline" className={cn("text-xs", c.type === "实时" ? "border-cyan-500/30 text-cyan-400" : "border-border text-muted-foreground")}>
                          {c.type}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-muted-foreground text-xs font-mono">{c.interval}</td>
                      <td className="py-3 px-4">
                        <Badge variant="outline" className={cn(
                          "text-xs",
                          c.status === "运行中" ? "border-green-500/30 text-green-400" :
                          c.status === "错误" ? "border-red-500/30 text-red-400" :
                          c.status === "已停止" ? "border-yellow-500/30 text-yellow-400" :
                          "border-border text-muted-foreground"
                        )}>
                          {c.status === "运行中" ? <Wifi className="w-3 h-3 mr-1" /> : <WifiOff className="w-3 h-3 mr-1" />}
                          {c.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-foreground font-mono text-xs">{c.dataCount}</td>
                      <td className="py-3 px-4 font-mono text-xs">
                        <span className={c.latency === "--" ? "text-muted-foreground/50" : parseInt(c.latency) > 500 ? "text-yellow-400" : "text-green-400"}>
                          {c.latency}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-xs">
                        <span className={c.errorRate === "100%" ? "text-red-400" : c.errorRate === "--" ? "text-muted-foreground/50" : "text-green-400"}>
                          {c.errorRate}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <Switch
                          checked={c.enabled}
                          onCheckedChange={() => handleToggle(c.id)}
                          className="data-[state=checked]:bg-cyan-600"
                        />
                      </td>
                      <td className="py-3 px-4">
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => handleRestart(c.id, c.name)}
                          className="h-7 w-7 text-muted-foreground hover:text-foreground hover:bg-accent"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                        </Button>
                      </td>
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
