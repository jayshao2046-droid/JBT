"use client"

import { useState } from "react"
import { LineChart, Play, Square, RotateCcw, BarChart3, TrendingUp, TrendingDown } from "lucide-react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import {
  Area, AreaChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts"

const equityCurveData = [
  { date: "2024-01", value: 1000000 },
  { date: "2024-02", value: 1045000 },
  { date: "2024-03", value: 1028000 },
  { date: "2024-04", value: 1098000 },
  { date: "2024-05", value: 1135000 },
  { date: "2024-06", value: 1089000 },
  { date: "2024-07", value: 1178000 },
  { date: "2024-08", value: 1245000 },
  { date: "2024-09", value: 1201000 },
  { date: "2024-10", value: 1312000 },
  { date: "2024-11", value: 1356000 },
  { date: "2024-12", value: 1398000 },
]

const kpis = [
  { label: "总收益率", value: "39.8%", positive: true },
  { label: "年化收益率", value: "39.8%", positive: true },
  { label: "最大回撤", value: "-8.2%", positive: false },
  { label: "夏普比率", value: "2.34", positive: true },
  { label: "胜率", value: "58.3%", positive: true },
  { label: "盈亏比", value: "1.85", positive: true },
  { label: "交易次数", value: "324", positive: null },
  { label: "平均持仓", value: "3.2天", positive: null },
]

const recentTasks = [
  { id: "BT-1234", strategy: "双均线CTA策略", symbol: "RB主力", status: "完成", pnl: "+18.4%", time: "5分钟前" },
  { id: "BT-1233", strategy: "多因子选股", symbol: "沪深300成分", status: "运行中", pnl: "--", time: "正在运行" },
  { id: "BT-1232", strategy: "网格交易", symbol: "IF2501", status: "完成", pnl: "+9.2%", time: "1小时前" },
  { id: "BT-1231", strategy: "布林带反转", symbol: "CU主力", status: "失败", pnl: "--", time: "2小时前" },
]

export default function BacktestOperationsPage() {
  const [runningProgress, setRunningProgress] = useState(67)

  return (
    <MainLayout title="策略回测" subtitle="回测详情">
      <div className="p-4 md:p-6 space-y-6">
        {/* 运行中任务 */}
        <Card className="bg-card border-blue-500/30">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base text-foreground flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                当前运行：多因子选股策略
              </CardTitle>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" className="border-border text-muted-foreground hover:text-foreground h-8 text-xs">
                  <Square className="w-3 h-3 mr-1" />
                  停止
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">进度</span>
                <span className="text-foreground font-mono">{runningProgress}%</span>
              </div>
              <Progress value={runningProgress} className="h-2" />
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground text-xs">回测区间</p>
                  <p className="text-foreground">2023-01 ~ 2024-12</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">已处理</p>
                  <p className="text-foreground font-mono">486 / 730 天</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">预计剩余</p>
                  <p className="text-foreground font-mono">约 42 秒</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 收益曲线 */}
          <div className="lg:col-span-2">
            <Card className="bg-card border-border">
              <CardHeader className="pb-3">
                <CardTitle className="text-base text-foreground flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-blue-500" />
                  最近回测：双均线CTA策略
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-3 mb-4">
                  {kpis.slice(0, 4).map((kpi) => (
                    <div key={kpi.label} className="p-2 bg-accent rounded-lg text-center">
                      <p className="text-xs text-muted-foreground">{kpi.label}</p>
                      <p className={cn("text-sm font-semibold font-mono mt-0.5", kpi.positive === true ? "text-green-400" : kpi.positive === false ? "text-red-400" : "text-foreground")}>
                        {kpi.value}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={equityCurveData}>
                      <defs>
                        <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="transparent" />
                      <XAxis dataKey="date" tick={{ fill: "#737373", fontSize: 10 }} />
                      <YAxis tick={{ fill: "#737373", fontSize: 10 }} tickFormatter={(v) => `${(v / 10000).toFixed(0)}万`} />
                      <Tooltip
                        contentStyle={{ background: "#171717", border: "1px solid #404040", borderRadius: 8 }}
                        labelStyle={{ color: "#a3a3a3" }}
                        formatter={(v: number) => [`¥${v.toLocaleString()}`, "净值"]}
                      />
                      <Area type="monotone" dataKey="value" stroke="#3b82f6" fill="url(#colorValue)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 任务列表 */}
          <Card className="bg-card border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-base text-foreground flex items-center gap-2">
                <LineChart className="w-4 h-4 text-blue-500" />
                近期任务
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {recentTasks.map((task) => (
                <div key={task.id} className="p-3 bg-accent/50 rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-muted-foreground font-mono">{task.id}</span>
                    <Badge variant="outline" className={cn(
                      "text-xs",
                      task.status === "完成" ? "border-green-500/30 text-green-400" :
                      task.status === "运行中" ? "border-blue-500/30 text-blue-400" :
                      "border-red-500/30 text-red-400"
                    )}>
                      {task.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-foreground">{task.strategy}</p>
                  <div className="flex justify-between mt-1">
                    <span className="text-xs text-muted-foreground">{task.symbol}</span>
                    <span className={cn("text-xs font-mono", task.pnl.startsWith("+") ? "text-green-400" : "text-muted-foreground")}>
                      {task.pnl}
                    </span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </MainLayout>
  )
}
