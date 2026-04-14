"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useSignals } from "@/hooks/use-signals"

export function PostMarketReport() {
  const { overview, loading, error } = useSignals()

  if (loading) {
    return <div className="text-muted-foreground">加载中...</div>
  }

  if (error) {
    return <div className="text-destructive">错误: {error}</div>
  }

  if (!overview || !overview.daily_report.latest_report) {
    return <div className="text-muted-foreground">暂无盘后报告</div>
  }

  const report = overview.daily_report.latest_report

  return (
    <Card>
      <CardHeader>
        <CardTitle>盘后总结</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-sm text-muted-foreground">
          报告日期: {report.report_date}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="text-sm font-medium">策略统计</div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">总数:</span>
                <span className="font-medium">{report.strategies_total}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">活跃:</span>
                <span className="font-medium">{report.strategies_active}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">待处理:</span>
                <span className="font-medium">{report.strategies_pending}</span>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="text-sm font-medium">信号统计</div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">生成:</span>
                <span className="font-medium">{report.signals_generated}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">批准:</span>
                <span className="font-medium text-green-600">{report.signals_approved}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">拒绝:</span>
                <span className="font-medium text-red-600">{report.signals_rejected}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">待审:</span>
                <span className="font-medium">{report.signals_pending}</span>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="text-sm font-medium">研究会话</div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">总数:</span>
                <span className="font-medium">{report.research_sessions_total}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">完成:</span>
                <span className="font-medium text-green-600">{report.research_sessions_completed}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">失败:</span>
                <span className="font-medium text-red-600">{report.research_sessions_failed}</span>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="text-sm font-medium">发布统计</div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">发布到模拟:</span>
                <span className="font-medium">{report.publishes_to_sim}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">成功:</span>
                <span className="font-medium text-green-600">{report.publishes_success}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">失败:</span>
                <span className="font-medium text-red-600">{report.publishes_failed}</span>
              </div>
            </div>
          </div>
        </div>

        {report.research_summaries && report.research_summaries.length > 0 && (
          <div>
            <div className="text-sm font-medium mb-2">研究摘要</div>
            <div className="space-y-2">
              {report.research_summaries.map((summary, idx) => (
                <div key={idx} className="text-xs text-muted-foreground border-l-2 pl-2">
                  {JSON.stringify(summary)}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="text-xs text-muted-foreground">
          生成时间: {new Date(report.generated_at).toLocaleString("zh-CN")}
        </div>
      </CardContent>
    </Card>
  )
}
