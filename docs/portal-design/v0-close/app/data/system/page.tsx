"use client"

import { useState, useEffect } from "react"
import { Server, Cpu, HardDrive, Wifi, Thermometer, Activity } from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

function generateHistory(base: number, len = 20) {
  return Array.from({ length: len }, (_, i) => ({
    t: `${i}s`,
    v: Math.max(0, Math.min(100, base + (Math.random() - 0.5) * 15)),
  }))
}

const processes = [
  { name: "data_collector_main", pid: 1234, cpu: 8.2, mem: 312, status: "运行中" },
  { name: "sina_quotes_worker", pid: 1235, cpu: 2.1, mem: 128, status: "运行中" },
  { name: "tushare_daily_worker", pid: 1236, cpu: 0.1, mem: 96, status: "空闲" },
  { name: "akshare_index_worker", pid: 1237, cpu: 1.4, mem: 112, status: "运行中" },
  { name: "ctp_tick_worker", pid: 1238, cpu: 0.0, mem: 64, status: "错误" },
  { name: "redis_server", pid: 1001, cpu: 0.8, mem: 256, status: "运行中" },
  { name: "mongodb_server", pid: 1002, cpu: 1.2, mem: 512, status: "运行中" },
]

export default function DataSystemPage() {
  const [cpuHistory] = useState(() => generateHistory(23))
  const [memHistory] = useState(() => generateHistory(45))

  const metrics = {
    cpu: 23, mem: 45, disk: 62,
    temp: 52, uptime: "12天 5小时 34分", network: { in: "12.4 MB/s", out: "3.2 MB/s" },
  }

  return (
    <MainLayout title="数据采集" subtitle="硬件系统">
      <div className="p-4 md:p-6 space-y-6">
        {/* 系统概览卡片 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "CPU 使用率", value: `${metrics.cpu}%`, icon: Cpu, color: "text-cyan-400", progress: metrics.cpu },
            { label: "内存使用率", value: `${metrics.mem}%`, icon: Server, color: "text-blue-400", progress: metrics.mem },
            { label: "磁盘使用率", value: `${metrics.disk}%`, icon: HardDrive, color: "text-purple-400", progress: metrics.disk },
            { label: "CPU 温度", value: `${metrics.temp}°C`, icon: Thermometer, color: "text-orange-400", progress: metrics.temp },
          ].map((metric) => {
            const Icon = metric.icon
            return (
              <Card key={metric.label} className="bg-card border-border">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs text-muted-foreground">{metric.label}</p>
                    <Icon className={cn("w-4 h-4", metric.color)} />
                  </div>
                  <p className={cn("text-2xl font-bold font-mono mb-2", metric.color)}>{metric.value}</p>
                  <Progress value={metric.progress} className="h-1.5" />
                </CardContent>
              </Card>
            )
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* CPU 历史 */}
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-base text-foreground flex items-center gap-2">
                <Cpu className="w-4 h-4 text-cyan-500" />
                CPU 使用率历史
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={cpuHistory}>
                    <CartesianGrid stroke="transparent" />
                    <XAxis dataKey="t" tick={{ fill: "#737373", fontSize: 10 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: "#737373", fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
                    <Tooltip
                      contentStyle={{ background: "#171717", border: "1px solid #404040", borderRadius: 8 }}
                      formatter={(v: number) => [`${v.toFixed(1)}%`, "CPU"]}
                    />
                    <Line type="monotone" dataKey="v" stroke="#06b6d4" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* 内存历史 */}
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-base text-foreground flex items-center gap-2">
                <Server className="w-4 h-4 text-blue-500" />
                内存使用率历史
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={memHistory}>
                    <CartesianGrid stroke="transparent" />
                    <XAxis dataKey="t" tick={{ fill: "#737373", fontSize: 10 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: "#737373", fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
                    <Tooltip
                      contentStyle={{ background: "#171717", border: "1px solid #404040", borderRadius: 8 }}
                      formatter={(v: number) => [`${v.toFixed(1)}%`, "内存"]}
                    />
                    <Line type="monotone" dataKey="v" stroke="#3b82f6" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 进程列表 */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-foreground flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-500" />
              进程监控
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["进程名", "PID", "CPU%", "内存(MB)", "状态"].map((h) => (
                    <th key={h} className="text-left py-3 px-4 text-xs text-muted-foreground font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {processes.map((proc) => (
                  <tr key={proc.pid} className="border-b border-border/50 hover:bg-accent/20">
                    <td className="py-3 px-4 text-foreground font-mono text-xs">{proc.name}</td>
                    <td className="py-3 px-4 text-muted-foreground font-mono text-xs">{proc.pid}</td>
                    <td className="py-3 px-4 font-mono text-xs">
                      <span className={proc.cpu > 5 ? "text-yellow-400" : "text-foreground"}>{proc.cpu.toFixed(1)}</span>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground font-mono text-xs">{proc.mem}</td>
                    <td className="py-3 px-4">
                      <Badge variant="outline" className={cn(
                        "text-xs",
                        proc.status === "运行中" ? "border-green-500/30 text-green-400" :
                        proc.status === "错误" ? "border-red-500/30 text-red-400" :
                        "border-border text-muted-foreground"
                      )}>
                        {proc.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
