"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useDecision } from "@/hooks/use-decision"

export function FactorAnalysis() {
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

  const { factor_sync } = runtimeOverview

  return (
    <Card>
      <CardHeader>
        <CardTitle>因子分析</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">{factor_sync.aligned}</div>
            <div className="text-sm text-muted-foreground">已对齐</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-red-600">{factor_sync.mismatch}</div>
            <div className="text-sm text-muted-foreground">不匹配</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-600">{factor_sync.unknown}</div>
            <div className="text-sm text-muted-foreground">未知</div>
          </div>
        </div>

        {factor_sync.note && (
          <div className="text-sm text-muted-foreground border-t pt-3">
            {factor_sync.note}
          </div>
        )}

        <div className="text-sm">
          <div className="font-medium mb-2">同步状态说明</div>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground">
            <li>已对齐: 因子版本与策略要求完全匹配</li>
            <li>不匹配: 因子版本与策略要求不一致，需要更新</li>
            <li>未知: 无法确定因子同步状态</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}
