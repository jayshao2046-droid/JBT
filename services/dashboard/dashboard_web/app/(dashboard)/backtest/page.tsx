"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useBacktest } from "@/hooks/use-backtest"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { Cpu, HardDrive, Clock } from "lucide-react"
import MainLayout from "@/components/layout/main-layout"

export default function BacktestOverviewPage() {
  const { strategies, jobs, systemStatus, loading, refetch } = useBacktest()

  const safeStrategies = Array.isArray(strategies) ? strategies : []
  const safeJobs = Array.isArray(jobs) ? jobs : []

  if (loading) {
    return (
      <MainLayout title="回测系统" onRefresh={refetch}>
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout title="回测系统" onRefresh={refetch}>
      <div className="p-6 space-y-6">
      {/* 系统状态 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU 使用率</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemStatus?.cpu_usage.toFixed(1) || 0}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">内存使用率</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemStatus?.memory_usage.toFixed(1) || 0}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">运行时间</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.floor((systemStatus?.uptime || 0) / 3600)}h</div>
          </CardContent>
        </Card>
      </div>

      {/* 运行中任务 */}
      <Card>
        <CardHeader>
          <CardTitle>运行中任务 ({safeJobs.filter(j => j.status === "running").length})</CardTitle>
        </CardHeader>
        <CardContent>
          {safeJobs.filter(j => j.status === "running").length === 0 ? (
            <p className="text-muted-foreground text-sm">暂无运行中任务</p>
          ) : (
            <div className="space-y-2">
              {safeJobs.filter(j => j.status === "running").map((job) => (
                <div key={job.id} className="flex items-center justify-between p-3 border rounded">
                  <div>
                    <p className="font-medium">{job.strategy_name}</p>
                    <p className="text-xs text-muted-foreground">{job.created_at}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-secondary rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full"
                        style={{ width: `${job.progress}%` }}
                      />
                    </div>
                    <span className="text-sm">{job.progress}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 策略列表 */}
      <Card>
        <CardHeader>
          <CardTitle>策略列表 ({safeStrategies.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {safeStrategies.length === 0 ? (
            <p className="text-muted-foreground text-sm">暂无策略</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {safeStrategies.map((strategy) => (
                <div key={strategy.name} className="p-4 border rounded">
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-medium">{strategy.name}</p>
                    <Badge variant={strategy.status === "active" ? "default" : "secondary"}>
                      {strategy.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{strategy.description}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
    </MainLayout>
  )
}
