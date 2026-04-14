"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useDecision } from "@/hooks/use-decision"

export function ResearchCenter() {
  const { runtimeOverview, loading, error } = useDecision()

  if (loading) {
    return <div className="text-muted-foreground">加载中...</div>
  }

  if (error) {
    return <div className="text-destructive">错误: {error}</div>
  }

  if (!runtimeOverview) {
    return <div className="text-muted-foreground">暂无数据</div>
  }

  const { research_window, service_integrations } = runtimeOverview

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>研究窗口</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">时区</span>
            <span className="text-sm font-medium">{research_window.timezone}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">开放时间</span>
            <span className="text-sm font-medium">
              {research_window.start} - {research_window.end}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">当前时间</span>
            <span className="text-sm font-medium">{research_window.current_time}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">窗口状态</span>
            <Badge variant={research_window.is_open ? "default" : "secondary"}>
              {research_window.is_open ? "开放" : "关闭"}
            </Badge>
          </div>
          <div className="text-xs text-muted-foreground">
            规则: {research_window.rule}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>服务集成 ({service_integrations.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {service_integrations.length === 0 ? (
            <div className="text-sm text-muted-foreground">暂无服务集成</div>
          ) : (
            <div className="space-y-3">
              {service_integrations.map((service, idx) => (
                <div key={idx} className="border-b pb-3 last:border-b-0">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">{service.name}</span>
                    <Badge variant={service.status === "healthy" ? "default" : "destructive"}>
                      {service.status}
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground space-y-1">
                    <div>URL: {service.url}</div>
                    {service.timeout_seconds !== null && (
                      <div>超时: {service.timeout_seconds}s</div>
                    )}
                    {service.note && <div>备注: {service.note}</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
