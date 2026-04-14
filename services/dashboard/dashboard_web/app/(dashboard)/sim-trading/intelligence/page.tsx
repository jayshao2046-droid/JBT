"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useRiskControl } from "@/hooks/use-risk-control"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { CheckCircle2, XCircle, AlertTriangle } from "lucide-react"
import MainLayout from "@/components/layout/main-layout"

export default function IntelligencePage() {
  const { l1Status, l2Status, alerts, loading, refetch } = useRiskControl()

  // 防御性编程：确保数组类型
  const safeAlerts = Array.isArray(alerts) ? alerts : []

  if (loading) {
    return (
      <MainLayout title="风控智能" onRefresh={refetch}>
        <div className="p-6 space-y-6">
          <Skeleton className="h-96" />
        </div>
      </MainLayout>
    )
  }

  const l1Checks = [
    { label: "交易开关", value: l1Status?.trading_enabled, key: "trading_enabled" },
    { label: "CTP连接", value: l1Status?.ctp_connected, key: "ctp_connected" },
    { label: "最大持仓检查", value: l1Status?.max_position_check, key: "max_position_check" },
    { label: "日内亏损检查", value: l1Status?.daily_loss_check, key: "daily_loss_check" },
    { label: "价格偏离检查", value: l1Status?.price_deviation_check, key: "price_deviation_check" },
    { label: "下单频率检查", value: l1Status?.order_frequency_check, key: "order_frequency_check" },
    { label: "保证金率检查", value: l1Status?.margin_rate_check, key: "margin_rate_check" },
    { label: "连接质量检查", value: l1Status?.connection_quality_check, key: "connection_quality_check" },
  ]

  return (
    <MainLayout title="风控智能" onRefresh={refetch}>
      <div className="p-6 space-y-6">
      {/* L1 风控检查 */}
      <Card>
        <CardHeader>
          <CardTitle>L1 预检查</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {l1Checks.map((check) => (
              <div key={check.key} className="flex items-center gap-2 p-3 border rounded">
                {check.value ? (
                  <CheckCircle2 className="w-5 h-5 text-green-500" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-500" />
                )}
                <div>
                  <p className="text-sm font-medium">{check.label}</p>
                  <p className={`text-xs ${check.value ? "text-green-500" : "text-red-500"}`}>
                    {check.value ? "通过" : "未通过"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* L2 风控状态 */}
      <Card>
        <CardHeader>
          <CardTitle>L2 日线级风控</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 border rounded">
              <p className="text-sm text-muted-foreground">连续亏损</p>
              <p className="text-2xl font-bold mt-1">{l2Status?.consecutive_losses || 0} 次</p>
            </div>
            <div className="p-4 border rounded">
              <p className="text-sm text-muted-foreground">保证金率</p>
              <p className="text-2xl font-bold mt-1">
                {l2Status?.margin_rate ? `${(l2Status.margin_rate * 100).toFixed(1)}%` : "N/A"}
              </p>
            </div>
            <div className="p-4 border rounded">
              <p className="text-sm text-muted-foreground">今日交易</p>
              <p className="text-2xl font-bold mt-1">{l2Status?.daily_trade_count || 0} 笔</p>
            </div>
            <div className="p-4 border rounded">
              <p className="text-sm text-muted-foreground">今日盈亏</p>
              <p className={`text-2xl font-bold mt-1 ${(l2Status?.daily_pnl || 0) >= 0 ? "text-green-500" : "text-red-500"}`}>
                {(l2Status?.daily_pnl || 0) >= 0 ? "+" : ""}¥{(l2Status?.daily_pnl || 0).toFixed(2)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 告警历史 */}
      <Card>
        <CardHeader>
          <CardTitle>告警历史 ({safeAlerts.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {safeAlerts.length === 0 ? (
            <p className="text-muted-foreground text-sm">暂无告警</p>
          ) : (
            <div className="space-y-2">
              {safeAlerts.map((alert, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 border rounded">
                  <AlertTriangle
                    className={`w-5 h-5 mt-0.5 ${
                      alert.level === "error"
                        ? "text-red-500"
                        : alert.level === "warning"
                          ? "text-yellow-500"
                          : "text-blue-500"
                    }`}
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          alert.level === "error"
                            ? "destructive"
                            : alert.level === "warning"
                              ? "default"
                              : "secondary"
                        }
                      >
                        {alert.level}
                      </Badge>
                      <p className="text-xs text-muted-foreground">{alert.timestamp}</p>
                    </div>
                    <p className="text-sm mt-1">{alert.message}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 特殊状态 */}
      {l1Status?.reduce_only_mode && (
        <Card className="border-yellow-500/50 bg-yellow-500/10">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              <p className="font-medium">仅平仓模式已启用</p>
            </div>
          </CardContent>
        </Card>
      )}

      {l1Status?.disaster_stop_triggered && (
        <Card className="border-red-500/50 bg-red-500/10">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <XCircle className="w-5 h-5 text-red-500" />
              <p className="font-medium">灾难性止损已触发</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
    </MainLayout>
  )
}
