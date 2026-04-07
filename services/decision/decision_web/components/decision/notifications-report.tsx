"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AlertTriangle, Mail, MessageSquare } from "lucide-react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

const kpiData = [
  { label: "今日报警数", value: "12", unit: "条", color: "red" },
  { label: "因子同步异常", value: "2", unit: "条", color: "yellow" },
  { label: "研究完成通知", value: "8", unit: "条", color: "green" },
  { label: "信号工作流汇报", value: "128", unit: "条", color: "blue" },
  { label: "日报发送状态", value: "已发送", unit: "", color: "green" },
  { label: "邮件通道状态", value: "正常", unit: "", color: "green" },
]

const systemAlerts = [
  { id: 1, message: "Ollama 本地模型服务高CPU占用", time: "14:35", severity: "warning" },
  { id: 2, message: "在线L3模型响应延迟 > 50ms", time: "14:28", severity: "alert" },
  { id: 3, message: "研究任务队列已满", time: "14:15", severity: "warning" },
]

const riskControlAlerts = [
  { id: 1, message: "因子同步失败: BOLL 回测数据缺失", time: "14:42", severity: "alert" },
  { id: 2, message: "KDJ 因子有效性持续下降", time: "13:50", severity: "warning" },
]

const notificationChannels = [
  { channel: "飞书", status: "正常", lastSent: "14:45", successRate: 100, icon: MessageSquare },
  { channel: "邮件", status: "正常", lastSent: "14:40", successRate: 95, icon: Mail },
]

const dailyStats = {
  strategyResearch: 6,
  completedResearch: 3,
  enterProduction: 2,
  intercepted: 8,
  sentToSim: 92,
}

const trendData = [
  { time: "06:00", alerts: 2 },
  { time: "09:00", alerts: 5 },
  { time: "12:00", alerts: 8 },
  { time: "15:00", alerts: 10 },
  { time: "18:00", alerts: 12 },
  { time: "21:00", alerts: 9 },
]

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case "warning":
      return "bg-yellow-900/20 text-yellow-400 border-yellow-600/50"
    case "alert":
      return "bg-red-900/20 text-red-400 border-red-600/50"
    default:
      return "bg-neutral-900/20 text-neutral-400"
  }
}

const getKPIColor = (color: string) => {
  switch (color) {
    case "red":
      return "text-red-400"
    case "yellow":
      return "text-yellow-400"
    case "green":
      return "text-green-400"
    case "blue":
      return "text-blue-400"
    default:
      return "text-white"
  }
}

export default function NotificationsReport() {
  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* KPI 卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        {kpiData.map((kpi, idx) => (
          <Card key={idx} className="bg-neutral-900 border-neutral-700">
            <CardContent className="p-3">
              <p className="text-xs text-neutral-400 mb-1 truncate">{kpi.label}</p>
              <p className={`text-lg font-bold ${getKPIColor(kpi.color)}`}>{kpi.value}</p>
              {kpi.unit && <p className="text-xs text-neutral-500 mt-1">{kpi.unit}</p>}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 系统报警 + 风控报警 + 因子与同步告警 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 系统报警 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">系统报警 ({systemAlerts.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-80 overflow-y-auto">
            {systemAlerts.map((alert) => (
              <div key={alert.id} className={`border rounded p-2 ${getSeverityColor(alert.severity)}`}>
                <p className="text-xs font-medium mb-1">{alert.message}</p>
                <p className="text-xs opacity-70">{alert.time}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* 风控报警 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">风控报警 ({riskControlAlerts.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-80 overflow-y-auto">
            {riskControlAlerts.map((alert) => (
              <div key={alert.id} className={`border rounded p-2 ${getSeverityColor(alert.severity)}`}>
                <p className="text-xs font-medium mb-1">{alert.message}</p>
                <p className="text-xs opacity-70">{alert.time}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* 因子与同步告警 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">因子与同步告警</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-80 overflow-y-auto">
            <div className="border border-red-600/50 bg-red-900/20 rounded p-2">
              <p className="text-xs font-medium text-red-400 mb-1">BOLL 同步失败</p>
              <p className="text-xs text-red-300">需要重新计算回测数据</p>
              <p className="text-xs text-red-400/70 mt-1">14:42</p>
            </div>
            <div className="border border-yellow-600/50 bg-yellow-900/20 rounded p-2">
              <p className="text-xs font-medium text-yellow-400 mb-1">KDJ 漂移</p>
              <p className="text-xs text-yellow-300">有效性从 82% 下降到 72%</p>
              <p className="text-xs text-yellow-400/70 mt-1">13:50</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 信号工作流汇报 + 通知通道状态 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 信号工作流汇报 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-neutral-300">信号工作流汇报</CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
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
                    itemStyle={{ color: "#f97316" }}
                  />
                  <Line type="monotone" dataKey="alerts" stroke="#f97316" strokeWidth={2} dot={false} name="信号数" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 通知通道状态 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">通知通道状态</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {notificationChannels.map((channel, idx) => (
              <div key={idx} className="border border-neutral-700 rounded p-3">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <channel.icon className="w-4 h-4 text-neutral-400" />
                    <span className="text-sm font-medium text-white">{channel.channel}</span>
                  </div>
                  <Badge className="bg-green-900 text-green-400">{channel.status}</Badge>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <p className="text-neutral-400 mb-1">最后发送</p>
                    <p className="text-neutral-200">{channel.lastSent}</p>
                  </div>
                  <div>
                    <p className="text-neutral-400 mb-1">成功率</p>
                    <p className="text-neutral-200">{channel.successRate}%</p>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* 日报周报月报 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 今日统计 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">今日统计</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="border border-neutral-700 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-neutral-400">策略研究数</span>
                <span className="text-xl font-bold text-orange-400">{dailyStats.strategyResearch}</span>
              </div>
            </div>
            <div className="border border-neutral-700 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-neutral-400">完成研究数</span>
                <span className="text-xl font-bold text-green-400">{dailyStats.completedResearch}</span>
              </div>
            </div>
            <div className="border border-neutral-700 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-neutral-400">进入生产候选</span>
                <span className="text-xl font-bold text-blue-400">{dailyStats.enterProduction}</span>
              </div>
            </div>
            <div className="border border-neutral-700 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-neutral-400">被拦截数</span>
                <span className="text-xl font-bold text-red-400">{dailyStats.intercepted}</span>
              </div>
            </div>
            <div className="border border-neutral-700 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-neutral-400">推送模拟交易</span>
                <span className="text-xl font-bold text-cyan-400">{dailyStats.sentToSim}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 日报发送状态 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">日报发送状态</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="border border-green-600/50 bg-green-900/20 rounded p-3">
              <div className="flex items-start gap-2 mb-2">
                <div className="w-2 h-2 rounded-full bg-green-400 mt-1 flex-shrink-0"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-400">日报已发送</p>
                  <p className="text-xs text-green-300/70 mt-1">2024-04-05 21:00</p>
                </div>
              </div>
              <p className="text-xs text-green-300 ml-4">
                收件组: @量化决策组, @运营团队
              </p>
            </div>
            <div className="border border-neutral-700 rounded p-3">
              <p className="text-sm font-medium text-neutral-300 mb-2">周报计划</p>
              <p className="text-xs text-neutral-400">周一 09:30 发送本周回顾</p>
            </div>
            <div className="border border-neutral-700 rounded p-3">
              <p className="text-sm font-medium text-neutral-300 mb-2">月报计划</p>
              <p className="text-xs text-neutral-400">每月1日 10:00 发送月度总结</p>
            </div>
            <div className="space-y-2 pt-2">
              <Button className="w-full bg-orange-600 hover:bg-orange-700 text-white text-sm">
                立即发送日报
              </Button>
              <Button variant="outline" className="w-full border-neutral-700 text-neutral-400 hover:bg-neutral-800 text-sm">
                查看日报模板
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 失败重试情况 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300">失败重试情况</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="text-left py-2 px-3 text-neutral-400 font-medium">通知类型</th>
                  <th className="text-center py-2 px-3 text-neutral-400 font-medium">发送时间</th>
                  <th className="text-center py-2 px-3 text-neutral-400 font-medium">状态</th>
                  <th className="text-center py-2 px-3 text-neutral-400 font-medium">重试次数</th>
                  <th className="text-left py-2 px-3 text-neutral-400 font-medium">详情</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-neutral-800 hover:bg-neutral-800/50">
                  <td className="py-2 px-3 text-neutral-300">研究完成通知</td>
                  <td className="py-2 px-3 text-center text-neutral-300">14:32</td>
                  <td className="py-2 px-3 text-center">
                    <Badge className="bg-green-900 text-green-400">成功</Badge>
                  </td>
                  <td className="py-2 px-3 text-center text-neutral-400">0</td>
                  <td className="py-2 px-3 text-neutral-500">MA交叉策略 v2.2.0</td>
                </tr>
                <tr className="border-b border-neutral-800 hover:bg-neutral-800/50">
                  <td className="py-2 px-3 text-neutral-300">因子同步告警</td>
                  <td className="py-2 px-3 text-center text-neutral-300">14:42</td>
                  <td className="py-2 px-3 text-center">
                    <Badge className="bg-green-900 text-green-400">成功</Badge>
                  </td>
                  <td className="py-2 px-3 text-center text-neutral-400">1</td>
                  <td className="py-2 px-3 text-neutral-500">BOLL 回测缺失</td>
                </tr>
                <tr className="border-b border-neutral-800 hover:bg-neutral-800/50">
                  <td className="py-2 px-3 text-neutral-300">模型状态通知</td>
                  <td className="py-2 px-3 text-center text-neutral-300">13:15</td>
                  <td className="py-2 px-3 text-center">
                    <Badge className="bg-yellow-900 text-yellow-400">超时</Badge>
                  </td>
                  <td className="py-2 px-3 text-center text-yellow-400">3</td>
                  <td className="py-2 px-3 text-neutral-500">邮件通道暂时故障</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
