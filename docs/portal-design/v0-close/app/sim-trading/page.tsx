"use client"

import { useState, useEffect } from "react"
import { MainLayout } from "@/components/layout/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Gauge,
  ChevronDown,
  AlertOctagon,
} from "lucide-react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  Bar,
  ReferenceLine,
} from "recharts"
import { toast } from "sonner"
import { cn } from "@/lib/utils"

export default function SimTradingPage() {
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [expandedL1, setExpandedL1] = useState(true)
  const [showFusePanel, setShowFusePanel] = useState(false)
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)

  // 风控状态
  const [l1Status] = useState("pass")
  const [l2Status] = useState("pass")
  const [l3Status] = useState("pass")

  // L2 数据
  const [consecutiveLosses] = useState(2)
  const [marginLevel] = useState(45)
  const [simConfig] = useState({
    dailyLossLimit: 2.0,
    continuousLossLimit: 5,
    marginWarning: 60,
    marginAlert: 70,
  })

  // L2 盈亏曲线数据
  const [l2PnlData] = useState([
    { time: "09:00", pnl: 0, loss: 0 },
    { time: "09:30", pnl: 0.5, loss: 0 },
    { time: "10:00", pnl: 0.8, loss: 0 },
    { time: "10:30", pnl: 0.3, loss: -0.5 },
    { time: "11:00", pnl: 0.6, loss: 0 },
    { time: "11:30", pnl: 1.2, loss: 0 },
    { time: "13:30", pnl: 1.5, loss: 0 },
    { time: "14:00", pnl: 1.0, loss: -0.5 },
    { time: "14:30", pnl: 1.3, loss: 0 },
    { time: "15:00", pnl: 1.8, loss: 0 },
  ])

  // L1 检查项目
  const l1Checks = [
    { id: "contract_whitelist", name: "合约白名单", status: "pass" },
    { id: "time_segment", name: "交易时段", status: "pass" },
    { id: "market_freshness", name: "行情新鲜度", status: "pass" },
    { id: "signal_ttl", name: "信号时效", status: "pass" },
    { id: "idempotency", name: "幂等性校验", status: "pass" },
    { id: "version", name: "程序版本", status: "pass" },
    { id: "account_health", name: "账户健康度", status: "pass" },
    { id: "position_limit", name: "持仓上限", status: "pass" },
    { id: "price_valid", name: "价格合理性", status: "pass" },
    { id: "frequency", name: "下单频率", status: "pass" },
  ]

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => {
      setLastUpdate(new Date())
      setIsRefreshing(false)
      setBackendOnline(true)
      toast.success("数据已刷新")
    }, 1000)
  }

  useEffect(() => {
    setLastUpdate(new Date())
    setBackendOnline(true)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pass":
        return "bg-green-900/20 text-green-400 border-green-600/50"
      case "warning":
        return "bg-yellow-900/20 text-yellow-400 border-yellow-600/50"
      case "alert":
        return "bg-red-900/20 text-red-400 border-red-600/50"
      default:
        return "bg-neutral-900/20 text-neutral-400 border-neutral-600/50"
    }
  }

  return (
    <MainLayout
      title="模拟交易"
      subtitle="风控监控"
      onRefresh={handleRefresh}
      isRefreshing={isRefreshing}
      lastUpdate={lastUpdate}
    >
      <div className="p-4 md:p-6 space-y-6">
        {/* 头部 */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-wider">
              风控监控中心
            </h1>
            <p className="text-sm text-neutral-400">
              L1/L2/L3 多层级风控门闸实时监测
            </p>
            <div className="mt-1">
              {backendOnline === null ? (
                <Badge
                  variant="outline"
                  className="text-xs border-neutral-600 text-neutral-500"
                >
                  连接中...
                </Badge>
              ) : backendOnline ? (
                <Badge
                  variant="outline"
                  className="text-xs border-green-600 text-green-400"
                >
                  API 在线
                </Badge>
              ) : (
                <Badge
                  variant="outline"
                  className="text-xs border-red-600 text-red-400"
                >
                  API 离线
                </Badge>
              )}
            </div>
          </div>
          <Button
            onClick={() => setShowFusePanel(!showFusePanel)}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            <AlertOctagon className="w-4 h-4 mr-2" />
            熔断恢复
          </Button>
        </div>

        {/* 全局门闸状态 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card
            className={cn(
              "bg-neutral-900 border",
              l1Status === "alert"
                ? "border-red-600"
                : l1Status === "warning"
                  ? "border-yellow-600"
                  : "border-green-600"
            )}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-neutral-400 mb-0.5">L1 门闸状态</p>
                  <p className="text-[10px] text-neutral-600 mb-1">
                    下单前同步规则校验
                  </p>
                  <p className="text-lg font-bold text-green-400">通过</p>
                </div>
                <ShieldAlert className="w-8 h-8 text-green-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-neutral-900 border border-orange-600">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-neutral-400 mb-0.5">L2 巡检状态</p>
                  <p className="text-[10px] text-neutral-600 mb-1">
                    持续监控账户风险
                  </p>
                  <p className="text-lg font-bold text-orange-400">运行中</p>
                </div>
                <Gauge className="w-8 h-8 text-orange-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-neutral-900 border border-neutral-600">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-neutral-400 mb-0.5">L3 审计状态</p>
                  <p className="text-[10px] text-neutral-600 mb-1">
                    最终熔断保护
                  </p>
                  <p className="text-lg font-bold text-white">正常</p>
                </div>
                <CheckCircle className="w-8 h-8 text-white" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* L1 检查矩阵 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <button
              onClick={() => setExpandedL1(!expandedL1)}
              className="w-full flex items-center justify-between hover:text-white transition-colors"
            >
              <CardTitle className="text-sm font-medium text-neutral-300">
                L1 准入检查矩阵 (10项)
              </CardTitle>
              <ChevronDown
                className={cn(
                  "w-4 h-4 transition-transform",
                  expandedL1 && "rotate-180"
                )}
              />
            </button>
          </CardHeader>
          {expandedL1 && (
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {l1Checks.map((check) => (
                  <div
                    key={check.id}
                    className={cn(
                      "border rounded p-3",
                      getStatusColor(check.status)
                    )}
                  >
                    <div className="flex items-center gap-2">
                      {check.status === "pass" ? (
                        <CheckCircle className="w-4 h-4" />
                      ) : check.status === "warning" ? (
                        <AlertTriangle className="w-4 h-4" />
                      ) : (
                        <XCircle className="w-4 h-4" />
                      )}
                      <span className="text-sm font-medium">{check.name}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>

        {/* L2 仪表板 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 盈亏曲线 */}
          <Card className="bg-neutral-900 border-neutral-700 lg:col-span-2">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-neutral-300">
                L2 日内盈亏曲线
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={l2PnlData}>
                    <CartesianGrid stroke="transparent" />
                    <XAxis dataKey="time" stroke="#737373" />
                    <YAxis stroke="#737373" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f2937",
                        border: "1px solid #404040",
                        borderRadius: "4px",
                      }}
                      labelStyle={{ color: "#fff" }}
                    />
                    <Bar dataKey="loss" fill="#ef4444" opacity={0.3} />
                    <Line
                      type="monotone"
                      dataKey="pnl"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={false}
                    />
                    <ReferenceLine
                      y={-2}
                      stroke="#eab308"
                      strokeDasharray="4 2"
                      strokeWidth={1.5}
                    />
                    <ReferenceLine
                      y={-3}
                      stroke="#ef4444"
                      strokeDasharray="4 2"
                      strokeWidth={1.5}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* 连续亏损 + 保证金 */}
          <div className="flex flex-col gap-4">
            <Card className="bg-neutral-900 border-neutral-700 flex-1">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium text-neutral-300">
                  连续亏损计数
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-3xl font-bold text-white">
                  {consecutiveLosses} / {simConfig.continuousLossLimit}
                </div>
                <Progress
                  value={
                    (consecutiveLosses / simConfig.continuousLossLimit) * 100
                  }
                  className="h-2"
                />
                <p className="text-xs text-neutral-400">触达上限将触发 L2 熔断</p>
              </CardContent>
            </Card>

            <Card className="bg-neutral-900 border-neutral-700 flex-1">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium text-neutral-300">
                  保证金水位
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between text-xs">
                  <span className="text-neutral-400">当前</span>
                  <span
                    className={cn(
                      "font-bold",
                      marginLevel >= simConfig.marginAlert
                        ? "text-red-400"
                        : marginLevel >= simConfig.marginWarning
                          ? "text-yellow-400"
                          : "text-green-400"
                    )}
                  >
                    {marginLevel}%
                  </span>
                </div>
                <Progress value={marginLevel} className="h-3" />
                <div className="grid grid-cols-3 gap-1 text-xs">
                  <div className="text-green-400">60%</div>
                  <div className="text-yellow-400">70%</div>
                  <div className="text-red-400">80%</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* 熔断恢复面板 */}
        {showFusePanel && (
          <Card className="bg-red-900/20 border border-red-600/50">
            <CardContent className="p-4 space-y-3">
              <p className="text-sm text-red-400 font-medium">熔断恢复面板</p>
              <p className="text-xs text-red-300">
                此操作将重置所有 L1/L2 计数器。二次确认必需。
              </p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  className="bg-red-600 hover:bg-red-700 text-white flex-1"
                  onClick={() => {
                    toast.success("熔断已重置，系统恢复正常")
                    setShowFusePanel(false)
                  }}
                >
                  确认恢复
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 flex-1"
                  onClick={() => setShowFusePanel(false)}
                >
                  取消
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </MainLayout>
  )
}
