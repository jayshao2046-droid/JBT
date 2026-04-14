"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useDecision } from "@/hooks/use-decision"

export function StockPoolTable() {
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

  const stockStrategies = strategyOverview.strategies.filter(
    (s) => s.template_id?.includes("stock") || s.strategy_id.includes("stock")
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle>股票池 ({stockStrategies.length})</CardTitle>
      </CardHeader>
      <CardContent>
        {stockStrategies.length === 0 ? (
          <div className="text-sm text-muted-foreground">暂无股票策略</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">策略名称</th>
                  <th className="text-left py-2">状态</th>
                  <th className="text-left py-2">因子同步</th>
                  <th className="text-left py-2">发布目标</th>
                  <th className="text-left py-2">更新时间</th>
                </tr>
              </thead>
              <tbody>
                {stockStrategies.map((strategy) => (
                  <tr key={strategy.strategy_id} className="border-b">
                    <td className="py-2">{strategy.strategy_name}</td>
                    <td className="py-2">
                      <Badge variant="outline">{strategy.lifecycle_status}</Badge>
                    </td>
                    <td className="py-2">
                      <Badge variant={strategy.factor_sync_status === "aligned" ? "default" : "secondary"}>
                        {strategy.factor_sync_status}
                      </Badge>
                    </td>
                    <td className="py-2">{strategy.publish_target || "-"}</td>
                    <td className="py-2 text-muted-foreground">
                      {new Date(strategy.updated_at).toLocaleDateString("zh-CN")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
