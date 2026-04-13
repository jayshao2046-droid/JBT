"use client"

import { useState, useEffect } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Database,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Cpu,
  HardDrive,
  Activity,
  FileText,
  ArrowRight,
  Server,
  Wifi,
} from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

// 采集器类型
interface Collector {
  id: string
  name: string
  displayName: string
  status: "success" | "failed" | "delayed" | "idle"
  category: string
  lastUpdate: string
}

export default function DataPage() {
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // 资源状态
  const [cpu] = useState({ usage: 23, cores: 8 })
  const [memory] = useState({ used: 45, total: 32 })
  const [disk] = useState({ used: 62, free: 256 })

  // 采集器列表
  const [collectors] = useState<Collector[]>([
    { id: "1", name: "sina_quotes", displayName: "新浪行情", status: "success", category: "行情", lastUpdate: "2分钟前" },
    { id: "2", name: "eastmoney_news", displayName: "东财资讯", status: "success", category: "资讯", lastUpdate: "5分钟前" },
    { id: "3", name: "wind_data", displayName: "万得数据", status: "delayed", category: "数据", lastUpdate: "15分钟前" },
    { id: "4", name: "ctp_market", displayName: "CTP行情", status: "success", category: "行情", lastUpdate: "1分钟前" },
    { id: "5", name: "tushare_daily", displayName: "Tushare日线", status: "success", category: "数据", lastUpdate: "3分钟前" },
    { id: "6", name: "akshare_fund", displayName: "AKShare基金", status: "failed", category: "数据", lastUpdate: "30分钟前" },
    { id: "7", name: "jqdata_factor", displayName: "聚宽因子", status: "idle", category: "因子", lastUpdate: "1小时前" },
    { id: "8", name: "rqdata_option", displayName: "米筐期权", status: "success", category: "期权", lastUpdate: "2分钟前" },
  ])

  // 日志
  const [logs] = useState([
    { time: "14:35:12", level: "INFO", message: "sina_quotes 数据更新完成，共 2,456 条" },
    { time: "14:34:58", level: "WARNING", message: "wind_data 响应延迟 > 10s" },
    { time: "14:34:45", level: "INFO", message: "eastmoney_news 获取新闻 128 篇" },
    { time: "14:34:30", level: "ERROR", message: "akshare_fund 连接超时，重试中..." },
    { time: "14:34:15", level: "INFO", message: "ctp_market Tick 数据正常推送" },
  ])

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => {
      setLastUpdate(new Date())
      setIsRefreshing(false)
      toast.success("数据已刷新")
    }, 1000)
  }

  useEffect(() => {
    setLastUpdate(new Date())
  }, [])

  const summary = {
    total: collectors.length,
    success: collectors.filter((c) => c.status === "success").length,
    failed: collectors.filter((c) => c.status === "failed").length,
    delayed: collectors.filter((c) => c.status === "delayed").length,
  }

  const getStatusDot = (status: string) => {
    switch (status) {
      case "success":
        return "bg-green-500"
      case "failed":
        return "bg-red-500"
      case "delayed":
        return "bg-yellow-500"
      case "idle":
        return "bg-neutral-500"
      default:
        return "bg-neutral-500"
    }
  }

  const getStatusBg = (status: string) => {
    switch (status) {
      case "success":
        return "bg-green-500/10 border-green-500/20"
      case "failed":
        return "bg-red-500/10 border-red-500/20"
      case "delayed":
        return "bg-yellow-500/10 border-yellow-500/20"
      case "idle":
        return "bg-neutral-500/10 border-neutral-500/20"
      default:
        return "bg-neutral-500/10 border-neutral-500/20"
    }
  }

  return (
    <MainLayout
      title="数据采集"
      subtitle="总览"
      onRefresh={handleRefresh}
      isRefreshing={isRefreshing}
      lastUpdate={lastUpdate}
    >
      <div className="p-4 md:p-6 space-y-6">
        {/* KPI 卡片 */}
        <div className="grid grid-cols-3 lg:grid-cols-7 gap-3">
          {[
            { icon: Database, label: "采集源", value: `${summary.success}/${summary.total}`, color: "text-foreground", bg: "bg-blue-500/10", ic: "text-blue-500" },
            { icon: CheckCircle, label: "正常", value: summary.success, color: "text-green-400", bg: "bg-green-500/10", ic: "text-green-500" },
            { icon: XCircle, label: "失败", value: summary.failed, color: "text-red-400", bg: "bg-red-500/10", ic: "text-red-500" },
            { icon: AlertTriangle, label: "延迟", value: summary.delayed, color: "text-yellow-400", bg: "bg-yellow-500/10", ic: "text-yellow-500" },
            { icon: Cpu, label: "CPU", value: `${cpu.usage}%`, color: "text-blue-400", bg: "bg-blue-500/10", ic: "text-blue-500" },
            { icon: Server, label: "内存", value: `${memory.used}%`, color: "text-purple-400", bg: "bg-purple-500/10", ic: "text-purple-500" },
            { icon: HardDrive, label: "磁盘", value: `${disk.used}%`, color: "text-orange-400", bg: "bg-orange-500/10", ic: "text-orange-500" },
          ].map((kpi) => (
            <Card key={kpi.label} className="bg-card border-border">
              <CardContent className="p-3 flex flex-col items-center text-center">
                <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center mb-2", kpi.bg)}>
                  <kpi.icon className={cn("w-4 h-4", kpi.ic)} />
                </div>
                <p className="text-[10px] text-muted-foreground">{kpi.label}</p>
                <p className={cn("text-lg font-bold font-mono", kpi.color)}>{kpi.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 采集源状态矩阵 */}
          <Card className="bg-card border-border lg:col-span-2">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-foreground flex items-center gap-2">
                  <Activity className="w-4 h-4 text-cyan-500" />
                  采集源状态矩阵
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs text-muted-foreground hover:text-cyan-400"
                >
                  查看全部
                  <ArrowRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {collectors.map((collector) => (
                  <div
                    key={collector.id}
                    className={cn(
                      "p-3 rounded-lg border cursor-pointer hover:opacity-90 transition-opacity",
                      getStatusBg(collector.status)
                    )}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className={cn("w-2 h-2 rounded-full", getStatusDot(collector.status))} />
                      <p className="text-xs font-bold text-cyan-400 font-mono tracking-wider truncate">
                        {collector.name}
                      </p>
                    </div>
                    <p className="text-[10px] text-muted-foreground truncate">
                      {collector.displayName} | {collector.category}
                    </p>
                    <p className="text-[10px] text-muted-foreground/70 mt-0.5">{collector.lastUpdate}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 近期日志 */}
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-foreground flex items-center gap-2">
                  <FileText className="w-4 h-4 text-cyan-500" />
                  近期日志
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs text-muted-foreground hover:text-cyan-400"
                >
                  更多
                  <ArrowRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {logs.map((log, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className="text-[10px] text-muted-foreground font-mono whitespace-nowrap mt-0.5">
                      {log.time}
                    </span>
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-[10px] px-1 py-0 flex-shrink-0",
                        log.level === "ERROR"
                          ? "border-red-500/50 text-red-400"
                          : log.level === "WARNING"
                            ? "border-yellow-500/50 text-yellow-400"
                            : "border-blue-500/50 text-blue-400"
                      )}
                    >
                      {log.level}
                    </Badge>
                    <span className="text-xs text-muted-foreground break-all">{log.message}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 资源监控 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { label: "CPU", pct: cpu.usage, sub: `${cpu.cores} 核`, color: "bg-blue-500" },
            { label: "内存", pct: memory.used, sub: `${(memory.total * memory.used / 100).toFixed(1)}G / ${memory.total}G`, color: "bg-purple-500" },
            { label: "磁盘", pct: disk.used, sub: `剩余 ${disk.free} GB`, color: "bg-orange-500" },
          ].map((r) => (
            <Card key={r.label} className="bg-card border-border">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-muted-foreground">{r.label}</span>
                  <span className="text-sm font-bold text-foreground font-mono">{r.pct}%</span>
                </div>
                <Progress value={r.pct} className="h-2" />
                <p className="text-[10px] text-muted-foreground/70 mt-1">{r.sub}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* 网络状态 */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-base text-foreground flex items-center gap-2">
              <Wifi className="w-4 h-4 text-cyan-500" />
              数据源连接状态
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { name: "CTP 主席", status: "connected", latency: "12ms" },
                { name: "CTP 次席", status: "standby", latency: "--" },
                { name: "新浪 API", status: "connected", latency: "45ms" },
                { name: "Tushare API", status: "connected", latency: "28ms" },
              ].map((conn) => (
                <div key={conn.name} className="p-3 bg-accent/50 rounded-lg border border-border">
                  <div className="flex items-center gap-2 mb-1">
                    <div
                      className={cn(
                        "w-2 h-2 rounded-full",
                        conn.status === "connected" ? "bg-green-500" : "bg-muted-foreground"
                      )}
                    />
                    <span className="text-sm text-foreground font-medium">{conn.name}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span
                      className={cn(
                        conn.status === "connected" ? "text-green-400" : "text-muted-foreground"
                      )}
                    >
                      {conn.status === "connected" ? "已连接" : "备用"}
                    </span>
                    <span className="text-muted-foreground font-mono">{conn.latency}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
