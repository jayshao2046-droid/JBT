"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useSignals } from "@/hooks/use-signals"

export function NotificationsReport() {
  const { overview, loading, error } = useSignals()

  if (loading) {
    return <div className="text-muted-foreground">加载中...</div>
  }

  if (error) {
    return <div className="text-destructive">错误: {error}</div>
  }

  if (!overview) {
    return <div className="text-muted-foreground">暂无数据</div>
  }

  const { notification_channels, recent_events, daily_report } = overview

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>通知渠道状态</CardTitle>
        </CardHeader>
        <CardContent>
          {notification_channels.length === 0 ? (
            <div className="text-sm text-muted-foreground">暂无通知渠道</div>
          ) : (
            <div className="space-y-3">
              {notification_channels.map((channel) => (
                <div key={channel.channel} className="border-b pb-3 last:border-b-0">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">{channel.channel}</span>
                    <div className="flex gap-2">
                      <Badge variant={channel.enabled ? "default" : "secondary"}>
                        {channel.enabled ? "启用" : "禁用"}
                      </Badge>
                      <Badge variant={channel.status === "healthy" ? "default" : "destructive"}>
                        {channel.status}
                      </Badge>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                    <div>尝试: {channel.attempts}</div>
                    <div>成功: {channel.successes}</div>
                    <div>失败: {channel.failures}</div>
                    <div>
                      成功率: {channel.success_rate !== null ? `${(channel.success_rate * 100).toFixed(1)}%` : "N/A"}
                    </div>
                  </div>
                  {channel.last_success_at && (
                    <div className="text-xs text-muted-foreground mt-1">
                      最后成功: {new Date(channel.last_success_at).toLocaleString("zh-CN")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>最近事件 ({recent_events.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {recent_events.length === 0 ? (
            <div className="text-sm text-muted-foreground">暂无事件</div>
          ) : (
            <div className="space-y-2">
              {recent_events.map((event, idx) => (
                <div key={idx} className="border-b pb-2 last:border-b-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{event.title}</span>
                    <Badge variant="outline">{event.notify_level}</Badge>
                  </div>
                  <div className="text-xs text-muted-foreground space-y-1">
                    <div>事件码: {event.event_code}</div>
                    <div>类型: {event.event_type}</div>
                    <div>派发时间: {new Date(event.dispatched_at).toLocaleString("zh-CN")}</div>
                    <div className="flex gap-2">
                      {event.channels.feishu && <Badge variant="secondary" className="text-xs">飞书</Badge>}
                      {event.channels.email && <Badge variant="secondary" className="text-xs">邮件</Badge>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>日报摘要</CardTitle>
        </CardHeader>
        <CardContent>
          {!daily_report.latest_report ? (
            <div className="text-sm text-muted-foreground">暂无日报</div>
          ) : (
            <div className="space-y-3">
              <div className="text-sm text-muted-foreground">
                报告日期: {daily_report.latest_report.report_date}
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-muted-foreground">策略总数:</span>
                  <span className="ml-2 font-medium">{daily_report.latest_report.strategies_total}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">活跃策略:</span>
                  <span className="ml-2 font-medium">{daily_report.latest_report.strategies_active}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">信号生成:</span>
                  <span className="ml-2 font-medium">{daily_report.latest_report.signals_generated}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">信号批准:</span>
                  <span className="ml-2 font-medium">{daily_report.latest_report.signals_approved}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">研究会话:</span>
                  <span className="ml-2 font-medium">{daily_report.latest_report.research_sessions_total}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">发布成功:</span>
                  <span className="ml-2 font-medium">{daily_report.latest_report.publishes_success}</span>
                </div>
              </div>
              {daily_report.last_sent_at && (
                <div className="text-xs text-muted-foreground">
                  最后发送: {new Date(daily_report.last_sent_at).toLocaleString("zh-CN")}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
