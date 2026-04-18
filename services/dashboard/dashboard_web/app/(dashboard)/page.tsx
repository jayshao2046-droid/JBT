"use client"

import { useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useDashboardData } from "@/hooks/use-dashboard-data"
import { useServiceStatus } from "@/hooks/use-service-status"
import { useToast } from "@/hooks/use-toast"
import { KpiCard } from "@/components/dashboard/kpi-card"
import { ChurnChart } from "@/components/dashboard/churn-chart"
import { TodayTradingSummary } from "@/components/dashboard/today-trading-summary"
import { CurrentPositions } from "@/components/dashboard/current-positions"
import { StrategySignals } from "@/components/dashboard/strategy-signals"
import { RealTimeRisk } from "@/components/dashboard/real-time-risk"
import { DataSourceStatus } from "@/components/dashboard/data-source-status"
import { NewsList } from "@/components/dashboard/news-list"
import { SignalConfirmDialog } from "@/components/dashboard/signal-confirm-dialog"
import { ClosePositionDialog } from "@/components/dashboard/close-position-dialog"
import { ManualOpenDialog } from "@/components/dashboard/manual-open-dialog"
import { DisableSignalDialog } from "@/components/dashboard/disable-signal-dialog"
import { EquityChart } from "@/components/dashboard/equity-chart"
import { DailyReportCard } from "@/components/dashboard/daily-report-card"
import { EmergencyStopButton } from "@/components/dashboard/emergency-stop-button"
import { TrendingUp, DollarSign, Activity, AlertTriangle, RefreshCw } from "lucide-react"
import { simTradingApi } from "@/lib/api/sim-trading"
import { reviewSignal } from "@/lib/api/decision"
import type { Position, StrategySignal } from "@/lib/api/types"

export default function DashboardPage() {
  const { toast } = useToast()
  const { account, performance, risk, positions, signals, collectors, news, orders, loading, error, refetch } =
    useDashboardData()
  const serviceStatuses = useServiceStatus()

  const [manualOpenDialog, setManualOpenDialog] = useState(false)
  const [confirmSignalDialog, setConfirmSignalDialog] = useState<{ open: boolean; signal: StrategySignal | null }>({
    open: false,
    signal: null,
  })
  const [closePositionDialog, setClosePositionDialog] = useState<{ open: boolean; position: Position | null }>({
    open: false,
    position: null,
  })
  const [disableSignalDialog, setDisableSignalDialog] = useState<{ open: boolean; signal: StrategySignal | null }>({
    open: false,
    signal: null,
  })

  const handleManualOpen = async (data: {
    symbol: string
    direction: "long" | "short"
    quantity: number
    price: number
    stopLoss: number
    takeProfit: number
  }) => {
    try {
      await simTradingApi.placeOrder({
        instrument_id: data.symbol,
        direction: data.direction,
        volume: data.quantity,
        price: data.price,
        order_type: "limit",
      })
      toast({
        title: "开仓成功",
        description: `${data.symbol} ${data.direction === "long" ? "做多" : "做空"} ${data.quantity} 手`,
      })
      refetch()
      setManualOpenDialog(false)
    } catch (err) {
      toast({
        title: "开仓失败",
        description: err instanceof Error ? err.message : "未知错误",
        variant: "destructive",
      })
    }
  }

  const handleConfirmSignal = async (signal: StrategySignal) => {
    try {
      await simTradingApi.placeOrder({
        instrument_id: signal.instrument_id,
        direction: signal.direction,
        volume: 1,
        order_type: "market",
      })
      toast({
        title: "信号确认成功",
        description: `已根据信号开仓 ${signal.instrument_id}`,
      })
      refetch()
      setConfirmSignalDialog({ open: false, signal: null })
    } catch (err) {
      toast({
        title: "信号确认失败",
        description: err instanceof Error ? err.message : "未知错误",
        variant: "destructive",
      })
    }
  }

  const handleClosePosition = async (position: Position, data: { quantity: number; closeType: "full" | "partial" }) => {
    try {
      await simTradingApi.closePosition({
        instrument_id: position.instrument_id,
        direction: position.direction === "long" ? "short" : "long",
        volume: data.quantity,
      })
      toast({
        title: "平仓成功",
        description: `已平仓 ${position.instrument_id} ${data.quantity} 手`,
      })
      refetch()
      setClosePositionDialog({ open: false, position: null })
    } catch (err) {
      toast({
        title: "平仓失败",
        description: err instanceof Error ? err.message : "未知错误",
        variant: "destructive",
      })
    }
  }

  const handleDisableSignal = async (signal: StrategySignal, data: { reason: string; remarks: string }) => {
    try {
      await reviewSignal({ decision_id: signal.id, action: "reject", reason: data.reason })
      toast({
        title: "信号已禁用",
        description: `已禁用信号 ${signal.instrument_id}`,
      })
      refetch()
      setDisableSignalDialog({ open: false, signal: null })
    } catch (err) {
      toast({
        title: "信号禁用失败",
        description: err instanceof Error ? err.message : "未知错误",
        variant: "destructive",
      })
    }
  }

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    )
  }

  const kpiData = [
    {
      title: "总权益",
      value: account?.equity || 0,
      icon: DollarSign,
      change: performance ? `${performance.daily_pnl >= 0 ? "+" : ""}${performance.daily_pnl}` : undefined,
      changeType: performance && performance.daily_pnl >= 0 ? ("positive" as const) : ("negative" as const),
      status: "success" as const,
    },
    {
      title: "可用资金",
      value: account?.available || 0,
      icon: TrendingUp,
      status: "default" as const,
    },
    {
      title: "浮动盈亏",
      value: account?.float_pnl || 0,
      icon: Activity,
      changeType: account && account.float_pnl >= 0 ? ("positive" as const) : ("negative" as const),
      status: account && account.float_pnl >= 0 ? ("success" as const) : ("danger" as const),
    },
    {
      title: "保证金占用",
      value: account?.margin || 0,
      icon: AlertTriangle,
      progress: risk ? risk.position_usage * 100 : 0,
      description: "占总权益",
      status: risk && risk.position_usage > 0.8 ? ("danger" as const) : ("warning" as const),
    },
  ]

  const riskMetrics = [
    {
      label: "保证金使用率",
      value: risk ? Math.round(risk.position_usage * 100) : 0,
      unit: "%",
      status: risk && risk.position_usage > 0.8 ? ("danger" as const) : ("normal" as const),
      description: "占总权益",
    },
    {
      label: "当日回撤",
      value: risk ? Math.abs(risk.drawdown) : 0,
      unit: "¥",
      status: "normal" as const,
      description: "最大回撤",
    },
    {
      label: "VaR风险值",
      value: risk ? Math.abs(risk.var_1d) : 0,
      unit: "¥",
      status: "normal" as const,
      description: "单日风险敞口",
    },
  ]

  return (
    <div className="p-6 space-y-6">
        {/* 错误提示 */}
        {error && (
          <Card className="border-red-500/50 bg-red-500/10">
            <CardContent className="p-4 flex items-center justify-between">
              <p className="text-red-400 text-sm">{error}</p>
              <Button onClick={refetch} variant="outline" size="sm">
                <RefreshCw className="w-4 h-4 mr-2" />
                重试
              </Button>
            </CardContent>
          </Card>
        )}

        {/* KPI 卡片 + 服务状态 + 紧急暂停 */}
        <div className="flex items-start gap-4">
          <div className="flex-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {kpiData.map((kpi, idx) => (
              <KpiCard key={idx} {...kpi} />
            ))}
          </div>
          <div className="flex gap-2">
            <EmergencyStopButton />
            {Object.entries(serviceStatuses).map(([name, status]) => (
              <div key={name} className="flex items-center gap-1" title={name}>
                <div
                  className={`w-2 h-2 rounded-full ${
                    status === "ok"
                      ? "bg-green-500"
                      : status === "error"
                        ? "bg-red-500"
                        : "bg-yellow-500"
                  }`}
                />
              </div>
            ))}
          </div>
        </div>

        {/* 权益曲线 + 日报卡片 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <EquityChart />
          </div>
          <DailyReportCard />
        </div>

        {/* 收益表 + 今日交易汇总 */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3">
            <ChurnChart
              data={
                performance
                  ? [
                      { metric: "日盈亏", value: performance.daily_pnl },
                      { metric: "胜率", value: performance.win_rate },
                      { metric: "盈亏比", value: performance.pnl_ratio },
                      { metric: "交易次数", value: performance.total_trades },
                    ]
                  : []
              }
            />
          </div>
          <div className="lg:col-span-2">
            <TodayTradingSummary
              data={{
                tradeCount: Array.isArray(orders) ? orders.length : 0,
                openCount: Array.isArray(orders) ? orders.filter((o) => o.direction === "buy").length : 0,
                closeCount: Array.isArray(orders) ? orders.filter((o) => o.direction === "sell").length : 0,
                buyAmount: Array.isArray(orders)
                  ? orders
                      .filter((o) => o.direction === "buy")
                      .reduce((sum, o) => sum + o.price * o.volume, 0)
                  : 0,
                sellAmount: Array.isArray(orders)
                  ? orders
                      .filter((o) => o.direction === "sell")
                      .reduce((sum, o) => sum + o.price * o.volume, 0)
                  : 0,
                commission: Array.isArray(orders) ? orders.length * 5 : 0,
              }}
            />
          </div>
        </div>

        {/* 持仓 + 信号 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CurrentPositions
            positions={Array.isArray(positions) ? positions : []}
            onClose={(position) => setClosePositionDialog({ open: true, position })}
          />
          <StrategySignals
            signals={Array.isArray(signals) ? signals : []}
            onManualOpen={() => setManualOpenDialog(true)}
            onConfirmSignal={(signal) => setConfirmSignalDialog({ open: true, signal })}
            onDisableSignal={(signal) => setDisableSignalDialog({ open: true, signal })}
          />
        </div>

        {/* 风控 + 数据源 + 新闻 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <RealTimeRisk metrics={riskMetrics} />
          <DataSourceStatus dataSources={Array.isArray(collectors) ? collectors : []} />
          <NewsList news={Array.isArray(news) ? news : []} />
        </div>

        {/* Dialogs */}
        <ManualOpenDialog open={manualOpenDialog} onOpenChange={setManualOpenDialog} onConfirm={handleManualOpen} />
        <SignalConfirmDialog
          open={confirmSignalDialog.open}
          signal={confirmSignalDialog.signal}
          onOpenChange={(open) => setConfirmSignalDialog({ open, signal: null })}
          onConfirm={() => confirmSignalDialog.signal && handleConfirmSignal(confirmSignalDialog.signal)}
        />
        <ClosePositionDialog
          open={closePositionDialog.open}
          position={closePositionDialog.position}
          onOpenChange={(open) => setClosePositionDialog({ open, position: null })}
          onConfirm={(data) => closePositionDialog.position && handleClosePosition(closePositionDialog.position, data)}
        />
        <DisableSignalDialog
          open={disableSignalDialog.open}
          signal={disableSignalDialog.signal}
          onOpenChange={(open) => setDisableSignalDialog({ open, signal: null })}
          onConfirm={(data) => disableSignalDialog.signal && handleDisableSignal(disableSignalDialog.signal, data)}
        />
      </div>
    )
  }
