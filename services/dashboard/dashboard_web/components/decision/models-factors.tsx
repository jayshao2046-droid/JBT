"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useDecision } from "@/hooks/use-decision"

export function ModelsFactors() {
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

  const { local_models, online_models, model_router, factor_sync } = runtimeOverview

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>模型路由器</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
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
            <span className="text-sm">合格策略</span>
            <span className="text-sm font-medium">{model_router.eligible_strategies}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">阻塞策略</span>
            <span className="text-sm font-medium">{model_router.blocked_strategies}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>因子同步状态</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm">已对齐</span>
            <span className="text-sm font-medium">{factor_sync.aligned}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">不匹配</span>
            <span className="text-sm font-medium text-destructive">{factor_sync.mismatch}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">未知</span>
            <span className="text-sm font-medium">{factor_sync.unknown}</span>
          </div>
          {factor_sync.note && (
            <div className="text-xs text-muted-foreground mt-2">
              {factor_sync.note}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>本地模型 ({local_models.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {local_models.length === 0 ? (
            <div className="text-sm text-muted-foreground">暂无本地模型</div>
          ) : (
            <div className="space-y-2">
              {local_models.map((model) => (
                <div key={model.profile_id} className="flex items-center justify-between border-b pb-2">
                  <div>
                    <div className="text-sm font-medium">{model.model_name}</div>
                    <div className="text-xs text-muted-foreground">
                      {model.deployment_class} · {model.route_role}
                    </div>
                  </div>
                  <Badge variant={model.status === "ready" ? "default" : "secondary"}>
                    {model.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>在线模型 ({online_models.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {online_models.length === 0 ? (
            <div className="text-sm text-muted-foreground">暂无在线模型</div>
          ) : (
            <div className="space-y-2">
              {online_models.map((model) => (
                <div key={model.profile_id} className="flex items-center justify-between border-b pb-2">
                  <div>
                    <div className="text-sm font-medium">{model.model_name}</div>
                    <div className="text-xs text-muted-foreground">
                      {model.deployment_class} · {model.route_role}
                    </div>
                  </div>
                  <Badge variant={model.status === "ready" ? "default" : "secondary"}>
                    {model.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
