"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AlertTriangle, TrendingUp, Zap, CheckCircle } from "lucide-react"
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  Bar,
} from "recharts"

const kpiData = [
  { label: "当前活跃策略数", value: "24", unit: "个", trend: "+2" },
  { label: "可执行策略数", value: "18", unit: "个", trend: "+1" },
  { label: "研究队列数", value: "6", unit: "个", trend: "-1" },
  { label: "今日新增信号数", value: "128", unit: "条", trend: "+15" },
  { label: "L1 拦截数", value: "8", unit: "条", trend: "+2" },
  { label: "L2 升级数", value: "3", unit: "条", trend: "→" },
  { label: "L3 在线复核数", value: "12", unit: "条", trend: "+5" },
  { label: "通知异常数", value: "0", unit: "条", trend: "✓" },
]

const pipelineData = [
  { stage: "策略包入库", count: 24, color: "#f97316" },
  { stage: "因子同步", count: 24, color: "#22c55e" },
  { stage: "回测验证", count: 22, color: "#3b82f6" },
  { stage: "研究完成", count: 20, color: "#8b5cf6" },
  { stage: "人工确认", count: 18, color: "#ec4899" },
  { stage: "执行发布", count: 18, color: "#06b6d4" },
  { stage: "模拟交易", count: 18, color: "#10b981" },
]

const blockageItems = [
  { type: "因子失配", count: 2, severity: "warning" },
  { type: "回测过期", count: 3, severity: "alert" },
  { type: "模型离线", count: 0, severity: "pass" },
  { type: "通知失败", count: 1, severity: "warning" },
]

const signalTrendData = [
  { time: "09:00", count: 5 },
  { time: "10:00", count: 8 },
  { time: "11:00", count: 12 },
  { time: "12:00", count: 7 },
  { time: "13:30", count: 15 },
  { time: "14:00", count: 18 },
  { time: "15:00", count: 12 },
]

const researchTrendData = [
  { time: "06:00", completed: 0, running: 2 },
  { time: "09:00", completed: 1, running: 3 },
  { time: "12:00", completed: 3, running: 2 },
  { time: "15:00", completed: 5, running: 1 },
  { time: "18:00", completed: 8, running: 3 },
  { time: "21:00", completed: 12, running: 2 },
]

const pendingStrategies = [
  { id: 1, name: "MA交叉策略-期货", status: "待确认", progress: "研究完成", lastUpdate: "2小时前" },
  { id: 2, name: "动量因子-多品种", status: "待确认", progress: "回测通过", lastUpdate: "3小时前" },
  { id: 3, name: "均值回归-能源", status: "待执行", progress: "人工审核中", lastUpdate: "5小时前" },
]

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case "pass":
      return "bg-green-900/20 text-green-400 border-green-600/50"
    case "warning":
      return "bg-yellow-900/20 text-yellow-400 border-yellow-600/50"
    case "alert":
      return "bg-red-900/20 text-red-400 border-red-600/50"
    default:
      return "bg-neutral-900/20 text-neutral-400"
  }
}

export default function DecisionOverview() {
  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* KPI 第一行 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiData.map((kpi, idx) => (
          <Card key={idx} className="bg-neutral-900 border-neutral-700">
            <CardContent className="p-4">
              <p className="text-xs text-neutral-400 mb-2">{kpi.label}</p>
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-2xl font-bold text-white">{kpi.value}</p>
                  <p className="text-xs text-neutral-500 mt-1">{kpi.unit}</p>
                </div>
                <span className={`text-sm font-medium ${kpi.trend === "✓" ? "text-green-400" : kpi.trend === "→" ? "text-neutral-400" : kpi.trend.startsWith("+") ? "text-green-400" : "text-orange-400"}`}>
                  {kpi.trend}
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 决策流水线 + 阻塞事项 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 决策流水线总图 */}
        <Card className="bg-neutral-900 border-neutral-700 lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">决策流水线总图</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between gap-2 overflow-x-auto pb-4">
              {pipelineData.map((stage, idx) => (
                <div key={idx} className="flex flex-col items-center flex-shrink-0">
                  <div
                    className="w-14 h-14 rounded-lg flex items-center justify-center text-white font-bold text-sm mb-2"
                    style={{ backgroundColor: stage.color }}
                  >
                    {stage.count}
                  </div>
                  <p className="text-xs text-neutral-400 text-center w-16">{stage.stage}</p>
                  {idx < pipelineData.length - 1 && (
                    <div className="text-orange-500 text-lg mt-2">→</div>
                  )}
                </div>
              ))}
            </div>
            <p className="text-xs text-neutral-500 text-center mt-4">
              今日策略经历：24 入库 → 18 成功发布 → 18 模拟交易
            </p>
          </CardContent>
        </Card>

        {/* 阻塞事项卡 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">阻塞事项</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {blockageItems.map((item, idx) => (
              <div
                key={idx}
                className={`border rounded p-3 ${getSeverityColor(item.severity)}`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{item.type}</span>
                  <Badge className="bg-opacity-20">{item.count}</Badge>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* 趋势图 + 待处理列表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 今日信号趋势 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">今日信号趋势</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={signalTrendData}>
                  <defs>
                    <linearGradient id="signalGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                  <XAxis dataKey="time" stroke="#737373" style={{ fontSize: "12px" }} />
                  <YAxis stroke="#737373" style={{ fontSize: "12px" }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1f2937",
                      border: "1px solid #404040",
                      borderRadius: "4px",
                    }}
                    labelStyle={{ color: "#fff" }}
                  />
                  <Area type="monotone" dataKey="count" fill="url(#signalGradient)" stroke="#f97316" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 研究任务完成趋势 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">研究任务完成趋势</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={researchTrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                  <XAxis dataKey="time" stroke="#737373" style={{ fontSize: "12px" }} />
                  <YAxis stroke="#737373" style={{ fontSize: "12px" }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1f2937",
                      border: "1px solid #404040",
                      borderRadius: "4px",
                    }}
                    labelStyle={{ color: "#fff" }}
                  />
                  <Bar dataKey="completed" fill="#22c55e" radius={[0, 0, 0, 0]} />
                  <Line type="monotone" dataKey="running" stroke="#f97316" strokeWidth={2} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 待人工确认策略列表 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300">待人工确认/执行 ({pendingStrategies.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="text-left py-2 px-3 text-neutral-400 font-medium">策略名称</th>
                  <th className="text-left py-2 px-3 text-neutral-400 font-medium">状态</th>
                  <th className="text-left py-2 px-3 text-neutral-400 font-medium">进度</th>
                  <th className="text-left py-2 px-3 text-neutral-400 font-medium">最后更新</th>
                  <th className="text-right py-2 px-3 text-neutral-400 font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                {pendingStrategies.map((strategy) => (
                  <tr key={strategy.id} className="border-b border-neutral-800 hover:bg-neutral-800/50 transition-colors">
                    <td className="py-3 px-3 text-white">{strategy.name}</td>
                    <td className="py-3 px-3">
                      <Badge
                        className={strategy.status === "待确认" ? "bg-yellow-900 text-yellow-400" : "bg-blue-900 text-blue-400"}
                      >
                        {strategy.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-3 text-neutral-400">{strategy.progress}</td>
                    <td className="py-3 px-3 text-neutral-500 text-xs">{strategy.lastUpdate}</td>
                    <td className="py-3 px-3 text-right">
                      <Button size="sm" variant="ghost" className="text-orange-500 hover:bg-orange-500/10 text-xs h-7">
                        查看详情
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
  )
}
