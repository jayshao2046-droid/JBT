"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useDecision } from "@/hooks/use-decision"

export function ConfigRuntime() {
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

  const { runtime_status, execution_gate, model_router } = runtimeOverview

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>运行时配置</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">健康状态</span>
            <Badge variant={runtime_status.health === "healthy" ? "default" : "destructive"}>
              {runtime_status.health}
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">状态存储路径</span>
            <span className="text-xs font-mono">{runtime_status.state_store_path}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">状态存储存在</span>
            <Badge variant={runtime_status.state_store_exists ? "default" : "secondary"}>
              {runtime_status.state_store_exists ? "是" : "否"}
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">调度器状态</span>
            <Badge variant="outline">{runtime_status.dispatcher_state}</Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>执行门控配置</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">门控启用</span>
            <Badge variant={execution_gate.enabled ? "default" : "secondary"}>
              {execution_gate.enabled ? "是" : "否"}
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">执行目标</span>
            <span className="text-sm font-medium">{execution_gate.target}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">实盘交易锁定</span>
            <Badge variant={execution_gate.live_trading_locked ? "destructive" : "default"}>
              {execution_gate.live_trading_locked ? "已锁定" : "未锁定"}
            </Badge>
          </div>
          <div className="text-sm text-muted-foreground">
            {execution_gate.summary}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>模型路由器配置</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">需要回测证书</span>
            <Badge variant={model_router.require_backtest_cert ? "default" : "secondary"}>
              {model_router.require_backtest_cert ? "是" : "否"}
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">需要研究快照</span>
            <Badge variant={model_router.require_research_snapshot ? "default" : "secondary"}>
              {model_router.require_research_snapshot ? "是" : "否"}
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">合格策略数</span>
            <span className="text-sm font-medium">{model_router.eligible_strategies}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">阻塞策略数</span>
            <span className="text-sm font-medium text-destructive">{model_router.blocked_strategies}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>统计信息</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-muted-foreground">策略总数:</span>
              <span className="ml-2 font-medium">{runtime_status.strategies_total}</span>
            </div>
            <div>
              <span className="text-muted-foreground">审批总数:</span>
              <span className="ml-2 font-medium">{runtime_status.approvals_total}</span>
            </div>
            <div>
              <span className="text-muted-foreground">回测证书:</span>
              <span className="ml-2 font-medium">{runtime_status.backtest_certs_total}</span>
            </div>
            <div>
              <span className="text-muted-foreground">研究快照:</span>
              <span className="ml-2 font-medium">{runtime_status.research_snapshots_total}</span>
            </div>
            <div>
              <span className="text-muted-foreground">决策记录:</span>
              <span className="ml-2 font-medium">{runtime_status.decision_records_total}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
