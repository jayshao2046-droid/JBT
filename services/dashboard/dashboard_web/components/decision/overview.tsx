"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useDecision } from "@/hooks/use-decision"

export function Overview() {
  const { strategyOverview, runtimeOverview, loading, error } = useDecision()

  if (loading) {
    return <div className="text-muted-foreground">加载中...</div>
  }

  if (error) {
    return <div className="text-destructive">错误: {error}</div>
  }

  if (!strategyOverview || !runtimeOverview) {
    return <div className="text-muted-foreground">暂无数据</div>
  }

  const { kpis } = strategyOverview
  const { runtime_status, execution_gate, research_window } = runtimeOverview

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="glass-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">策略总数</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpis.total}</div>
            <p className="text-xs text-muted-foreground">
              发布就绪: {kpis.publish_ready}
            </p>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">已发布</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpis.published}</div>
            <p className="text-xs text-muted-foreground">
              研究就绪: {kpis.research_ready}
            </p>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">因子对齐</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpis.factor_aligned}</div>
            <p className="text-xs text-muted-foreground">
              回测就绪: {kpis.backtest_ready}
            </p>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">待审批</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpis.pending_approvals}</div>
            <p className="text-xs text-muted-foreground">
              审批数量
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>运行时状态</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm">健康状态</span>
              <Badge variant={runtime_status.health === "healthy" ? "default" : "destructive"}>
                {runtime_status.health}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">策略数</span>
              <span className="text-sm font-medium">{runtime_status.strategies_total}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">决策记录</span>
              <span className="text-sm font-medium">{runtime_status.decision_records_total}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">调度器状态</span>
              <Badge variant="outline">{runtime_status.dispatcher_state}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle>执行门控</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm">门控启用</span>
              <Badge variant={execution_gate.enabled ? "default" : "secondary"}>
                {execution_gate.enabled ? "是" : "否"}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">目标</span>
              <span className="text-sm font-medium">{execution_gate.target}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">实盘锁定</span>
              <Badge variant={execution_gate.live_trading_locked ? "destructive" : "default"}>
                {execution_gate.live_trading_locked ? "已锁定" : "未锁定"}
              </Badge>
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              {execution_gate.summary}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="glass-card">
        <CardHeader>
          <CardTitle>研究窗口</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm">时区</span>
            <span className="text-sm font-medium">{research_window.timezone}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">窗口时间</span>
            <span className="text-sm font-medium">
              {research_window.start} - {research_window.end}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">当前状态</span>
            <Badge variant={research_window.is_open ? "default" : "secondary"}>
              {research_window.is_open ? "开放" : "关闭"}
            </Badge>
          </div>
          <div className="text-xs text-muted-foreground mt-2">
            当前时间: {research_window.current_time}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
