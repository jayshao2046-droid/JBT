"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useDecision } from "@/hooks/use-decision"

export function StrategyRepository() {
  const { strategyOverview, loading, error } = useDecision()

  if (loading) {
    return <div className="text-muted-foreground">加载中...</div>
  }

  if (error) {
    return <div className="text-destructive">错误: {error}</div>
  }

  if (!strategyOverview) {
    return <div className="text-muted-foreground">暂无数据</div>
  }

  const { strategies } = strategyOverview

  return (
    <div className="space-y-4">
      <div className="text-sm text-muted-foreground">
        共 {strategies.length} 个策略
      </div>

      {strategies.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-muted-foreground">暂无策略</div>
          </CardContent>
        </Card>
      ) : (
        strategies.map((strategy) => (
          <Card key={strategy.strategy_id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{strategy.strategy_name}</CardTitle>
                <Badge variant="outline">{strategy.lifecycle_status}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">策略ID:</span>
                  <span className="ml-2 font-mono text-xs">{strategy.strategy_id}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">版本:</span>
                  <span className="ml-2 font-medium">{strategy.strategy_version || "N/A"}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">因子同步:</span>
                  <Badge variant={strategy.factor_sync_status === "aligned" ? "default" : "secondary"}>
                    {strategy.factor_sync_status}
                  </Badge>
                </div>
                <div>
                  <span className="text-muted-foreground">发布目标:</span>
                  <span className="ml-2 font-medium">{strategy.publish_target || "未设置"}</span>
                </div>
              </div>

              {strategy.factor_ids && strategy.factor_ids.length > 0 && (
                <div className="text-sm">
                  <span className="text-muted-foreground">因子列表:</span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {strategy.factor_ids.map((factorId) => (
                      <Badge key={factorId} variant="outline" className="text-xs">
                        {factorId}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {strategy.allowed_targets && strategy.allowed_targets.length > 0 && (
                <div className="text-sm">
                  <span className="text-muted-foreground">允许目标:</span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {strategy.allowed_targets.map((target) => (
                      <Badge key={target} variant="secondary" className="text-xs">
                        {target}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 text-xs text-muted-foreground">
                <div>导入时间: {new Date(strategy.imported_at).toLocaleString("zh-CN")}</div>
                <div>更新时间: {new Date(strategy.updated_at).toLocaleString("zh-CN")}</div>
              </div>

              {strategy.backtest_cert_status && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-muted-foreground">回测证书:</span>
                  <Badge variant={strategy.backtest_cert_status === "valid" ? "default" : "secondary"}>
                    {strategy.backtest_cert_status}
                  </Badge>
                  {strategy.backtest_cert_expires_at && (
                    <span className="text-xs text-muted-foreground">
                      过期: {new Date(strategy.backtest_cert_expires_at).toLocaleString("zh-CN")}
                    </span>
                  )}
                </div>
              )}

              {strategy.research_snapshot_status && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-muted-foreground">研究快照:</span>
                  <Badge variant={strategy.research_snapshot_status === "valid" ? "default" : "secondary"}>
                    {strategy.research_snapshot_status}
                  </Badge>
                </div>
              )}

              {strategy.pending_approvals !== undefined && strategy.pending_approvals > 0 && (
                <div className="text-sm">
                  <Badge variant="destructive">待审批: {strategy.pending_approvals}</Badge>
                </div>
              )}
            </CardContent>
          </Card>
        ))
      )}
    </div>
  )
}
