"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MessageSquare } from "lucide-react"
import {
  fetchSignalOverview,
  type SignalOverviewResponse,
  type NotificationChannelStatus,
  type NotificationEventRecord,
  type DailyReportSummary,
} from "@/lib/api"

const getSeverityColor = (level: string) => {
  switch (level) {
    case "P0":
    case "alert":
      return "bg-red-900/20 text-red-400 border-red-600/50"
    case "P1":
    case "warning":
      return "bg-yellow-900/20 text-yellow-400 border-yellow-600/50"
    default:
      return "bg-neutral-900/20 text-neutral-400 border-neutral-700"
  }
}

export default function NotificationsReport({ refreshToken }: { refreshToken?: number }) {
  const [overview, setOverview] = useState<SignalOverviewResponse | null>(null)

  useEffect(() => {
    fetchSignalOverview().then(setOverview).catch(() => {})
  }, [refreshToken])

  const channels: NotificationChannelStatus[] = overview?.notification_channels ?? []
  const events: NotificationEventRecord[] = overview?.recent_events ?? []
  const dailyReport: DailyReportSummary | null = overview?.daily_report?.latest_report ?? null
  const dispatcherState = overview?.dispatcher_state ?? "unknown"
  const emptyStates = overview?.empty_states

  const kpiData = dailyReport
    ? [
        { label: "策略总数", value: String(dailyReport.strategies_total), color: "white" },
        { label: "活跃策略", value: String(dailyReport.strategies_active), color: "green" },
        { label: "信号生成", value: String(dailyReport.signals_generated), color: "orange" },
        { label: "信号通过", value: String(dailyReport.signals_approved), color: "green" },
        { label: "信号拒绝", value: String(dailyReport.signals_rejected), color: "red" },
        { label: "推送模拟", value: String(dailyReport.publishes_to_sim), color: "blue" },
      ]
    : []

  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* 派发器状态 */}
      <div className="flex items-center gap-3 mb-2">
        <span className="text-sm text-neutral-400">派发器状态：</span>
        <Badge className={dispatcherState === "idle" ? "bg-green-900 text-green-400" : "bg-yellow-900 text-yellow-400"}>
          {dispatcherState}
        </Badge>
      </div>

      {/* KPI 卡片 */}
      {kpiData.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {kpiData.map((kpi, idx) => (
            <Card key={idx} className="bg-neutral-900 border-neutral-700">
              <CardContent className="p-3">
                <p className="text-xs text-neutral-400 mb-1 truncate">{kpi.label}</p>
                <p className={`text-lg font-bold ${kpi.color === "green" ? "text-green-400" : kpi.color === "red" ? "text-red-400" : kpi.color === "orange" ? "text-orange-400" : kpi.color === "blue" ? "text-blue-400" : "text-white"}`}>
                  {kpi.value}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* 最近事件 + 通知通道 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 最近通知事件 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">最近通知事件 ({events.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-96 overflow-y-auto">
            {events.length > 0 ? events.map((evt, idx) => (
              <div key={idx} className={`border rounded p-2 ${getSeverityColor(evt.notify_level)}`}>
                <div className="flex items-start justify-between gap-2 mb-1">
                  <p className="text-xs font-medium">{evt.title}</p>
                  <Badge className="bg-neutral-800 text-neutral-300 text-[10px]">{evt.event_type}</Badge>
                </div>
                <div className="flex items-center gap-3 text-xs opacity-70">
                  <span>{evt.dispatched_at?.slice(11, 19)}</span>
                  <span>{evt.dispatch_state}</span>
                  <span>
                    {evt.channels.feishu && "飞书 "}
                    {evt.channels.email && "邮件"}
                  </span>
                </div>
              </div>
            )) : (
              <p className="text-sm text-neutral-500 text-center py-8">
                {emptyStates?.events ? "暂无通知事件" : "加载中…"}
              </p>
            )}
          </CardContent>
        </Card>

        {/* 通知通道状态 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">通知通道状态</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {channels.length > 0 ? channels.map((ch, idx) => (
              <div key={idx} className="border border-neutral-700 rounded p-3">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-neutral-400" />
                    <span className="text-sm font-medium text-white">{ch.channel}</span>
                  </div>
                  <Badge className={ch.status === "configured" || ch.status === "active" ? "bg-green-900 text-green-400" : "bg-neutral-700 text-neutral-300"}>
                    {ch.status}
                  </Badge>
                </div>
                <div className="grid grid-cols-3 gap-3 text-xs">
                  <div>
                    <p className="text-neutral-400 mb-1">尝试</p>
                    <p className="text-neutral-200">{ch.attempts}</p>
                  </div>
                  <div>
                    <p className="text-neutral-400 mb-1">成功</p>
                    <p className="text-green-400">{ch.successes}</p>
                  </div>
                  <div>
                    <p className="text-neutral-400 mb-1">成功率</p>
                    <p className="text-neutral-200">{ch.success_rate != null ? `${(ch.success_rate * 100).toFixed(0)}%` : "—"}</p>
                  </div>
                </div>
                {ch.last_error && (
                  <p className="text-xs text-red-400 mt-2">最近错误：{ch.last_error}</p>
                )}
              </div>
            )) : (
              <p className="text-sm text-neutral-500 text-center py-8">暂无通道数据</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 日报 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 日报详情 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">最新日报</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {dailyReport ? (
              <>
                <div className="text-xs text-neutral-500 mb-3">{dailyReport.report_date} · 生成于 {dailyReport.generated_at?.slice(11, 19)}</div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="border border-neutral-700 rounded p-3">
                    <span className="text-sm text-neutral-400">研究会话</span>
                    <p className="text-xl font-bold text-orange-400">{dailyReport.research_sessions_total}</p>
                    <p className="text-xs text-neutral-500">完成 {dailyReport.research_sessions_completed} / 失败 {dailyReport.research_sessions_failed}</p>
                  </div>
                  <div className="border border-neutral-700 rounded p-3">
                    <span className="text-sm text-neutral-400">发布到模拟</span>
                    <p className="text-xl font-bold text-cyan-400">{dailyReport.publishes_to_sim}</p>
                    <p className="text-xs text-neutral-500">成功 {dailyReport.publishes_success} / 失败 {dailyReport.publishes_failed}</p>
                  </div>
                </div>
              </>
            ) : (
              <p className="text-sm text-neutral-500 text-center py-8">暂无日报数据</p>
            )}
          </CardContent>
        </Card>

        {/* 日报历史 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">日报发送历史</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-80 overflow-y-auto">
            {overview?.daily_report?.history && overview.daily_report.history.length > 0 ? (
              overview.daily_report.history.map((h, idx) => (
                <div key={idx} className="border border-neutral-700 rounded p-2 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-neutral-300">{h.report_date}</p>
                    <p className="text-xs text-neutral-500">{h.generated_at?.slice(11, 19)}</p>
                  </div>
                  <Badge className={h.dispatch_state === "sent" ? "bg-green-900 text-green-400" : "bg-yellow-900 text-yellow-400"}>
                    {h.dispatch_state}
                  </Badge>
                </div>
              ))
            ) : (
              <p className="text-sm text-neutral-500 text-center py-8">
                {emptyStates?.daily_history ? "暂无发送历史" : "加载中…"}
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
