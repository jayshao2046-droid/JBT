"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AlertTriangle, TrendingUp, Clock } from "lucide-react"
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
  { label: "当前队列数", value: "6", unit: "个", trend: "+2" },
  { label: "运行中任务", value: "2", unit: "个", trend: "→" },
  { label: "今日完成数", value: "8", unit: "个", trend: "+3" },
  { label: "最佳收益提升", value: "15.2%", unit: "", trend: "↑" },
  { label: "平均研究时长", value: "4.5h", unit: "", trend: "-0.3h" },
  { label: "非交易时段算力利用", value: "78%", unit: "", trend: "+5%" },
]

const scheduleData = [
  { time: "00:00", active: 0, label: "00:00" },
  { time: "03:00", active: 1, label: "03:00" },
  { time: "06:00", active: 2, label: "06:00" },
  { time: "09:00", active: 0, label: "09:00交易开始" },
  { time: "12:00", active: 0, label: "12:00" },
  { time: "15:00", active: 0, label: "15:00交易中" },
  { time: "18:00", active: 0, label: "18:00" },
  { time: "21:00", active: 2, label: "21:00" },
  { time: "23:59", active: 1, label: "23:59" },
]

const completionTrendData = [
  { time: "06:00", completed: 0 },
  { time: "09:00", completed: 1 },
  { time: "12:00", completed: 2 },
  { time: "15:00", completed: 2 },
  { time: "18:00", completed: 5 },
  { time: "21:00", completed: 8 },
  { time: "24:00", completed: 8 },
]

const bestResultsData = [
  {
    strategy: "MA交叉策略",
    improvement: 12.3,
    sharpeRatio: 2.14,
    maxDD: 8.5,
    winRate: 62,
  },
  {
    strategy: "动量因子",
    improvement: 15.2,
    sharpeRatio: 2.31,
    maxDD: 7.2,
    winRate: 65,
  },
  {
    strategy: "均值回归",
    improvement: 8.7,
    sharpeRatio: 1.89,
    maxDD: 9.1,
    winRate: 58,
  },
]

const activeTasksData = [
  {
    id: 1,
    strategy: "MA交叉策略-期货",
    taskType: "参数搜索",
    progress: 65,
    eta: "2小时",
    status: "运行中",
  },
  {
    id: 2,
    strategy: "动量因子-多品种",
    taskType: "因子优化",
    progress: 40,
    eta: "3小时",
    status: "运行中",
  },
  {
    id: 3,
    strategy: "均值回归-能源",
    taskType: "回测验证",
    progress: 100,
    eta: "完成",
    status: "已完成",
  },
]

const researchCompleteNotification = {
  strategy: "MA交叉策略-期货",
  bestResult: 12.3,
  sharpeRatio: 2.14,
  maxDD: 8.5,
  winRate: 62,
  version: "v2.2.0",
  timestamp: "2024-04-05 18:32",
}

export default function ResearchCenter() {
  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* KPI 卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        {kpiData.map((kpi, idx) => (
          <Card key={idx} className="bg-neutral-900 border-neutral-700">
            <CardContent className="p-4">
              <p className="text-xs text-neutral-400 mb-2">{kpi.label}</p>
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-2xl font-bold text-white">{kpi.value}</p>
                  {kpi.unit && <p className="text-xs text-neutral-500 mt-1">{kpi.unit}</p>}
                </div>
                <span className={`text-sm font-medium ${kpi.trend.startsWith("+") || kpi.trend === "↑" ? "text-green-400" : kpi.trend === "→" ? "text-neutral-400" : "text-orange-400"}`}>
                  {kpi.trend}
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 研究调度时间轴 + 完成趋势 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 研究调度时间轴 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">24小时研究调度时间轴</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {scheduleData.map((slot, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <div className="w-10 text-xs text-neutral-400 font-mono">{slot.time}</div>
                  <div className="flex-1 h-6 bg-neutral-800 rounded flex items-center">
                    {slot.active > 0 && (
                      <div
                        className="h-full bg-green-600 rounded flex items-center justify-center text-xs text-white font-bold"
                        style={{ width: `${slot.active * 40}%` }}
                      >
                        {slot.active > 0 && `${slot.active}任务`}
                      </div>
                    )}
                    {slot.label.includes("交易") && (
                      <div className="ml-2 text-xs text-orange-400 font-medium">{slot.label.split("交")[1]}</div>
                    )}
                  </div>
                  <div className="text-xs text-neutral-500">{slot.label}</div>
                </div>
              ))}
            </div>
            <div className="mt-4 p-3 bg-orange-900/20 border border-orange-600/50 rounded">
              <p className="text-xs text-orange-300 font-medium">⏰ 交易时段规则</p>
              <p className="text-xs text-orange-400/70 mt-1">
                09:30-15:00 期货交易时段禁止自动调参和重训练，保护生产策略。非交易时段可持续研究。
              </p>
            </div>
          </CardContent>
        </Card>

        {/* 完成趋势 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-neutral-300">研究完成趋势</CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={completionTrendData} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
                  <defs>
                    <linearGradient id="completeGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                  <XAxis dataKey="time" stroke="#737373" style={{ fontSize: "11px" }} tick={{ fill: "#a3a3a3" }} tickMargin={8} />
                  <YAxis stroke="#737373" style={{ fontSize: "11px" }} tick={{ fill: "#a3a3a3" }} tickMargin={8} width={30} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1f2937",
                      border: "1px solid #404040",
                      borderRadius: "6px",
                      padding: "8px 12px",
                    }}
                    labelStyle={{ color: "#fff", marginBottom: "4px" }}
                    itemStyle={{ color: "#22c55e" }}
                  />
                  <Area type="monotone" dataKey="completed" fill="url(#completeGradient)" stroke="#22c55e" strokeWidth={2} name="完成数" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 最优回��结果 + 正在运行任务 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 最优回测结果卡 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">本轮最优回测结果</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {bestResultsData.map((result, idx) => (
              <div key={idx} className="border border-neutral-700 rounded p-3">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-white">{result.strategy}</p>
                  <Badge className="bg-green-900 text-green-400">↑ {result.improvement}%</Badge>
                </div>
                <div className="grid grid-cols-4 gap-2 text-xs">
                  <div>
                    <p className="text-neutral-400">Sharpe</p>
                    <p className="text-neutral-200 font-medium">{result.sharpeRatio.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-neutral-400">最大回撤</p>
                    <p className="text-neutral-200 font-medium">{result.maxDD}%</p>
                  </div>
                  <div>
                    <p className="text-neutral-400">胜率</p>
                    <p className="text-neutral-200 font-medium">{result.winRate}%</p>
                  </div>
                  <div>
                    <p className="text-neutral-400">推荐</p>
                    <Button size="sm" className="mt-1 h-6 text-xs bg-orange-600 hover:bg-orange-700">
                      采用
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* 正在运行任务列表 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">当前运行任务</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {activeTasksData.map((task) => (
              <div key={task.id} className="border border-neutral-700 rounded p-3">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="text-sm font-medium text-white">{task.strategy}</p>
                    <p className="text-xs text-neutral-400 mt-1">{task.taskType}</p>
                  </div>
                  <Badge className={task.status === "运行中" ? "bg-green-900 text-green-400" : "bg-blue-900 text-blue-400"}>
                    {task.status}
                  </Badge>
                </div>
                <div className="h-2 bg-neutral-800 rounded overflow-hidden mb-2">
                  <div
                    className="h-full bg-orange-500"
                    style={{ width: `${task.progress}%` }}
                  ></div>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-neutral-400">{task.progress}%</span>
                  <span className="text-neutral-500">预计 {task.eta}</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* 研究完成通知卡 */}
      <Card className="bg-neutral-900 border-green-600/50">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-green-400 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            研究完成通知卡
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-neutral-800 border border-neutral-700 rounded p-4 space-y-3">
            <div>
              <p className="text-xs text-neutral-400 mb-1">策略</p>
              <p className="text-white font-medium">{researchCompleteNotification.strategy}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-neutral-400 mb-1">收益提升</p>
                <p className="text-lg font-bold text-green-400">+{researchCompleteNotification.bestResult}%</p>
              </div>
              <div>
                <p className="text-xs text-neutral-400 mb-1">Sharpe比率</p>
                <p className="text-lg font-bold text-blue-400">{researchCompleteNotification.sharpeRatio}</p>
              </div>
              <div>
                <p className="text-xs text-neutral-400 mb-1">最大回撤</p>
                <p className="text-lg font-bold text-neutral-300">{researchCompleteNotification.maxDD}%</p>
              </div>
              <div>
                <p className="text-xs text-neutral-400 mb-1">胜率</p>
                <p className="text-lg font-bold text-cyan-400">{researchCompleteNotification.winRate}%</p>
              </div>
            </div>

            <div className="border-t border-neutral-700 pt-3">
              <p className="text-xs text-neutral-400 mb-2">通知详情</p>
              <div className="space-y-1 text-xs text-neutral-300">
                <p>✓ 已推送至飞书 @量化团队</p>
                <p>✓ 最优回测结果版本: {researchCompleteNotification.version}</p>
                <p>✓ 因子版本: v1.2.3 已同步</p>
                <p>✓ 推荐动作: 导出冻结版后人工审核</p>
              </div>
              <p className="text-xs text-neutral-500 mt-2">时间: {researchCompleteNotification.timestamp}</p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button className="flex-1 bg-green-600 hover:bg-green-700 text-white text-sm">
              查看飞书通知
            </Button>
            <Button variant="outline" className="flex-1 border-neutral-700 text-neutral-400 hover:bg-neutral-800 text-sm">
              导出策略包
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 参数搜索结果面板 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300">参数搜索结果面板</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="text-left py-2 px-3 text-neutral-400 font-medium">参数组合</th>
                  <th className="text-center py-2 px-3 text-neutral-400 font-medium">年化收益</th>
                  <th className="text-center py-2 px-3 text-neutral-400 font-medium">Sharpe</th>
                  <th className="text-center py-2 px-3 text-neutral-400 font-medium">最大回撤</th>
                  <th className="text-center py-2 px-3 text-neutral-400 font-medium">胜率</th>
                  <th className="text-center py-2 px-3 text-neutral-400 font-medium">推荐</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { params: "MA5, MA20, RSI≥70", return: 15.2, sharpe: 2.14, dd: 8.5, wr: 62, rank: 1 },
                  { params: "MA5, MA20, RSI≥65", return: 14.8, sharpe: 2.09, dd: 8.8, wr: 61, rank: 2 },
                  { params: "MA5, MA20, RSI≥75", return: 13.5, sharpe: 1.98, dd: 7.9, wr: 63, rank: 3 },
                ].map((row, idx) => (
                  <tr key={idx} className="border-b border-neutral-800 hover:bg-neutral-800/50">
                    <td className="py-2 px-3 text-neutral-300">{row.params}</td>
                    <td className="py-2 px-3 text-center text-green-400 font-medium">+{row.return}%</td>
                    <td className="py-2 px-3 text-center text-cyan-400">{row.sharpe.toFixed(2)}</td>
                    <td className="py-2 px-3 text-center text-neutral-400">{row.dd}%</td>
                    <td className="py-2 px-3 text-center text-neutral-400">{row.wr}%</td>
                    <td className="py-2 px-3 text-center">
                      {row.rank === 1 && <Badge className="bg-orange-600 text-white">最优</Badge>}
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
