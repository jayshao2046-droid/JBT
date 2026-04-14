"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useSimTrading } from "@/hooks/use-sim-trading"
import { useRiskControl } from "@/hooks/use-risk-control"
import { Skeleton } from "@/components/ui/skeleton"
import { DollarSign, TrendingUp, Activity, AlertTriangle } from "lucide-react"
import MainLayout from "@/components/layout/main-layout"

export default function SimTradingOverviewPage() {
  const { account, performance, positions, orders, loading: simLoading, refetch } = useSimTrading()
  const { l1Status, l2Status, loading: riskLoading } = useRiskControl()

  // 防御性编程：确保数组类型
  const safePositions = Array.isArray(positions) ? positions : []
  const safeOrders = Array.isArray(orders) ? orders : []

  if (simLoading || riskLoading) {
    return (
      <MainLayout title="模拟交易" onRefresh={refetch}>
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        </div>
      </MainLayout>
    )
  }

  const kpiData = [
    {
      title: "总权益",
      value: account?.equity || 0,
      icon: DollarSign,
      change: performance ? `${performance.daily_pnl >= 0 ? "+" : ""}${performance.daily_pnl.toFixed(2)}` : undefined,
      changeType: performance && performance.daily_pnl >= 0 ? "positive" : "negative",
    },
    {
      title: "可用资金",
      value: account?.available || 0,
      icon: TrendingUp,
    },
    {
      title: "浮动盈亏",
      value: account?.float_pnl || 0,
      icon: Activity,
      changeType: account && account.float_pnl >= 0 ? "positive" : "negative",
    },
    {
      title: "保证金占用",
      value: account?.margin || 0,
      icon: AlertTriangle,
      progress: account && account.equity ? (account.margin / account.equity) * 100 : 0,
    },
  ]

  return (
    <MainLayout title="模拟交易" onRefresh={refetch}>
      <div className="p-6 space-y-6">
        {/* KPI 卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiData.map((kpi, idx) => (
          <Card key={idx}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{kpi.title}</CardTitle>
              <kpi.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">¥{kpi.value.toLocaleString()}</div>
              {kpi.change && (
                <p className={`text-xs ${kpi.changeType === "positive" ? "text-green-500" : "text-red-500"}`}>
                  {kpi.change}
                </p>
              )}
              {kpi.progress !== undefined && (
                <div className="mt-2">
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full"
                      style={{ width: `${Math.min(kpi.progress, 100)}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{kpi.progress.toFixed(1)}% 占用</p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 持仓与订单 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>当前持仓 ({safePositions.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {safePositions.length === 0 ? (
              <p className="text-muted-foreground text-sm">暂无持仓</p>
            ) : (
              <div className="space-y-2">
                {safePositions.slice(0, 5).map((pos, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 border rounded">
                    <div>
                      <p className="font-medium">{pos.instrument_id}</p>
                      <p className="text-xs text-muted-foreground">
                        {pos.direction === "long" ? "多" : "空"} {pos.volume}手
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={pos.float_pnl >= 0 ? "text-green-500" : "text-red-500"}>
                        {pos.float_pnl >= 0 ? "+" : ""}¥{pos.float_pnl.toFixed(2)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>今日订单 ({safeOrders.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {safeOrders.length === 0 ? (
              <p className="text-muted-foreground text-sm">暂无订单</p>
            ) : (
              <div className="space-y-2">
                {safeOrders.slice(0, 5).map((order, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 border rounded">
                    <div>
                      <p className="font-medium">{order.instrument_id}</p>
                      <p className="text-xs text-muted-foreground">
                        {order.direction} {order.volume}手 @ ¥{order.price}
                      </p>
                    </div>
                    <div className="text-right">
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          order.status === "filled"
                            ? "bg-green-500/10 text-green-500"
                            : order.status === "rejected"
                              ? "bg-red-500/10 text-red-500"
                              : "bg-yellow-500/10 text-yellow-500"
                        }`}
                      >
                        {order.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 风控状态 */}
      <Card>
        <CardHeader>
          <CardTitle>风控状态</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">交易开关</p>
              <p className={`font-medium ${l1Status?.trading_enabled ? "text-green-500" : "text-red-500"}`}>
                {l1Status?.trading_enabled ? "已开启" : "已关闭"}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">CTP连接</p>
              <p className={`font-medium ${l1Status?.ctp_connected ? "text-green-500" : "text-red-500"}`}>
                {l1Status?.ctp_connected ? "已连接" : "未连接"}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">连续亏损</p>
              <p className="font-medium">{l2Status?.consecutive_losses || 0} 次</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">今日交易</p>
              <p className="font-medium">{l2Status?.daily_trade_count || 0} 笔</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">今日盈亏</p>
              <p className={`font-medium ${(l2Status?.daily_pnl || 0) >= 0 ? "text-green-500" : "text-red-500"}`}>
                {(l2Status?.daily_pnl || 0) >= 0 ? "+" : ""}¥{(l2Status?.daily_pnl || 0).toFixed(2)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
    </MainLayout>
  )
}
