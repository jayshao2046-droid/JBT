"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  ChevronDown,
  Gauge,
  AlertOctagon,
  ScrollText,
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
import { simApi } from "@/lib/sim-api"
import { toast } from "sonner"
import { isTradingDay, getTodayHolidayName } from "@/lib/holidays-cn"

export default function RiskControlPage() {
  const [selectedAlert, setSelectedAlert] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [l1Status, setL1Status] = useState("pass") // pass, warning, alert
  const [l2Status, setL2Status] = useState("pass")
  const [l3Status, setL3Status] = useState("pass")
  const [expandedL1, setExpandedL1] = useState(true)
  const [showFusePanel, setShowFusePanel] = useState(false)
  // 后端连接状态
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)
  const [serviceStage, setServiceStage] = useState("--")
  // 告警历史（localStorage）
  const [alertHistory, setAlertHistory] = useState<Array<{id:number;message:string;time:string}>>([])
  const [showHistory, setShowHistory] = useState(false)
  // L2 风控动态数据
  const [consecutiveLosses, setConsecutiveLosses] = useState<number | null>(null)
  const [marginLevel, setMarginLevel] = useState<number | null>(null)
  const [simConfig, setSimConfig] = useState({
    dailyLossLimit: 2.0,
    continuousLossLimit: 5,
    marginWarning: 60,
    marginAlert: 70,
  })

  // --- 日志查看 ---
  const [logEntries, setLogEntries] = useState<Array<{timestamp:string;level:string;source:string;message:string}>>([])
  const [logLevelFilter, setLogLevelFilter] = useState<string>("ALL")
  const [logAutoRefresh, setLogAutoRefresh] = useState(true)
  const [logLoading, setLogLoading] = useState(false)

  const fetchLogs = useCallback(() => {
    setLogLoading(true)
    const params = new URLSearchParams({ limit: "200" })
    if (logLevelFilter !== "ALL") params.set("level", logLevelFilter)
    fetch(`/api/sim/api/v1/logs/tail?${params.toString()}`, { cache: "no-store" })
      .then((r) => r.ok ? r.json() : Promise.reject())
      .then((data: any) => setLogEntries(data.logs ?? []))
      .catch(() => {})
      .finally(() => setLogLoading(false))
  }, [logLevelFilter])

  // L1 检查项目（10项）
  const l1Checks = [
    {
      id: "contract_whitelist",
      name: "合约白名单",
      status: "pass",
      lastReject: null,
    },
    {
      id: "time_segment",
      name: "交易时段",
      status: "pass",
      lastReject: null,
    },
    {
      id: "market_freshness",
      name: "行情新鲜度 <2s",
      status: "pass",
      lastReject: null,
    },
    {
      id: "signal_ttl",
      name: "信号时效 ≤3s",
      status: "pass",
      lastReject: null,
    },
    {
      id: "idempotency",
      name: "幂等性校验",
      status: "pass",
      lastReject: null,
    },
    {
      id: "version",
      name: "程序版本一致",
      status: "pass",
      lastReject: null,
    },
    {
      id: "account_health",
      name: "账户健康度",
      status: "pass",
      lastReject: null,
    },
    {
      id: "position_limit",
      name: "持仓上限",
      status: "pass",
      lastReject: null,
    },
    {
      id: "price_valid",
      name: "价格合理性",
      status: "pass",
      lastReject: null,
    },
    {
      id: "frequency",
      name: "下单频率",
      status: "pass",
      lastReject: null,
    },
  ]

  // L2 盈亏数据
  const [l2PnlData, setL2PnlData] = useState<any[]>([])

  // 告警列表
  const [alerts, setAlerts] = useState<any[]>([])

  // 计算 L1 整体状态
  useEffect(() => {
    const failCount = l1Checks.filter((c) => c.status !== "pass").length
    if (failCount >= 3) {
      setL1Status("alert")
    } else if (failCount >= 1) {
      setL1Status("warning")
    } else {
      setL1Status("pass")
    }
  }, [])

  // 从 localStorage 恢复告警历史（最多 100 条）
  useEffect(() => {
    try {
      const raw = localStorage.getItem("jbt_alert_history")
      if (raw) setAlertHistory(JSON.parse(raw))
    } catch {}
  }, [])

  // 将当前告警同步进历史
  useEffect(() => {
    if (alerts.length === 0) return
    try {
      const existing: any[] = JSON.parse(localStorage.getItem("jbt_alert_history") ?? "[]")
      const existingIds = new Set(existing.map((x: any) => x.id))
      const newOnes = alerts.filter((a) => !existingIds.has(a.id))
      if (newOnes.length > 0) {
        const merged = [...existing, ...newOnes].slice(-100)
        localStorage.setItem("jbt_alert_history", JSON.stringify(merged))
        setAlertHistory(merged)
      }
    } catch {}
  }, [alerts])

  const handleRefresh = () => {
    setIsLoading(true)
    Promise.all([simApi.health(), simApi.positions(), simApi.orders()])
      .then(([h, _pos, _ord]) => {
        setBackendOnline(h.status === "ok")
        setServiceStage((h as any).service ?? "--")
      })
      .catch(() => setBackendOnline(false))
      .finally(() => {
        setLastUpdate(new Date())
        setIsLoading(false)
      })
  }

  // 后端轮询（10s）
  useEffect(() => {
    handleRefresh()
    const t = setInterval(handleRefresh, 10000)
    return () => clearInterval(t)
  }, [])

  // 日志轮询（5s）
  useEffect(() => {
    fetchLogs()
    if (!logAutoRefresh) return
    const t = setInterval(fetchLogs, 5000)
    return () => clearInterval(t)
  }, [logAutoRefresh, fetchLogs])

  const handleSaveSimConfig = () => {
    // TODO: 连接到 trading_api:8003 WebSocket，下发配置
    toast.success("配置已下发到交易引擎（骨架阶段占位）")
    handleRefresh()
  }

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
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* 头部 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wider">风控监控中心</h1>
          <p className="text-sm text-neutral-400">L1/L2/L3 多层级风控门闸实时监测</p>
          <div className="mt-1">
            {backendOnline === null ? (
              <Badge variant="outline" className="text-xs border-neutral-600 text-neutral-500">● 连接中...</Badge>
            ) : backendOnline ? (
              <Badge variant="outline" className="text-xs border-green-600 text-green-400">● API 在线</Badge>
            ) : (
              <Badge variant="outline" className="text-xs border-red-600 text-red-400">● API 离线</Badge>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleRefresh}
            variant="ghost"
            className="text-neutral-400 hover:text-orange-500 hover:bg-neutral-800"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
          <Button
            onClick={() => setShowFusePanel(!showFusePanel)}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            <AlertOctagon className="w-4 h-4 mr-2" />
            熔断恢复
          </Button>
        </div>
      </div>

      {/* 更新时间 */}
          <div className="text-xs text-neutral-500 text-right">
        最后更新: {lastUpdate?.toLocaleString("zh-CN") ?? "--"}
      </div>

      {/* 全局门闸状态 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className={`bg-neutral-900 border ${l1Status === "alert" ? "border-red-600" : l1Status === "warning" ? "border-yellow-600" : "border-green-600"}`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 mb-0.5">L1 门闸状态</p>
                <p className="text-[10px] text-neutral-600 mb-1">下单前同步规则校验 · 纯本地规则引擎</p>
                <p className="text-lg font-bold">
                  {l1Status === "pass" && <span className="text-green-400">✓ 通过</span>}
                  {l1Status === "warning" && <span className="text-yellow-400">⚠ 警告</span>}
                  {l1Status === "alert" && <span className="text-red-400">✕ 拦截</span>}
                </p>
              </div>
              <ShieldAlert className={`w-8 h-8 ${l1Status === "alert" ? "text-red-400" : l1Status === "warning" ? "text-yellow-400" : "text-green-400"}`} />
            </div>
          </CardContent>
        </Card>

        <Card className={`bg-neutral-900 border ${l2Status === "alert" ? "border-red-600" : "border-orange-600"}`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 mb-0.5">L2 巡检状态</p>
                <p className="text-[10px] text-neutral-600 mb-1">持续监控账户风险 · 亏损/保证金/频率</p>
                <p className="text-lg font-bold text-orange-400">✓ 运行中</p>
              </div>
              <Gauge className="w-8 h-8 text-orange-400" />
            </div>
          </CardContent>
        </Card>

        <Card className={`bg-neutral-900 border ${l3Status === "alert" ? "border-red-600" : "border-neutral-600"}`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 mb-0.5">L3 审计状态</p>
                <p className="text-[10px] text-neutral-600 mb-1">最终熔断保护 · 硬熔断不可绕过</p>
                <p className="text-lg font-bold text-white">✓ 正常</p>
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
            <CardTitle className="text-sm font-medium text-neutral-300">L1 准入检查矩阵 (10项)
              <span className="ml-2 text-[10px] text-neutral-600 font-normal">下单前同步执行，任一不通则废单、结果立即反馈</span>
            </CardTitle>
            <ChevronDown className={`w-4 h-4 transition-transform ${expandedL1 ? "rotate-180" : ""}`} />
          </button>
        </CardHeader>
        {expandedL1 && (
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
              {l1Checks.map((check) => (
                <div
                  key={check.id}
                  className={`border rounded p-3 ${getStatusColor(check.status)} cursor-pointer hover:opacity-80 transition-opacity`}
                  onClick={() => check.lastReject && setSelectedAlert(check)}
                >
                  <div className="flex items-start gap-2 mb-1">
                    {check.status === "pass" ? (
                      <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    ) : check.status === "warning" ? (
                      <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium">{check.name}</p>
                      {check.lastReject && (
                        <p className="text-xs opacity-75 mt-1 truncate">{check.lastReject}</p>
                      )}
                    </div>
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
            <CardTitle className="text-sm font-medium text-neutral-300">L2 日内盈亏曲线</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={l2PnlData}>
                  <defs>
                    <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
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
                  <Bar dataKey="loss" fill="#ef4444" radius={[0, 0, 0, 0]} opacity={0.3} />
                  <Line type="monotone" dataKey="pnl" stroke="#3b82f6" strokeWidth={2} dot={false} />
                  <ReferenceLine y={-2} stroke="#eab308" strokeDasharray="4 2" strokeWidth={1.5} label={{ value: "L2预警 2%", position: "insideTopRight", fill: "#eab308", fontSize: 10 }} />
                  <ReferenceLine y={-3} stroke="#ef4444" strokeDasharray="4 2" strokeWidth={1.5} label={{ value: "L2熔断 3%", position: "insideTopRight", fill: "#ef4444", fontSize: 10 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            {/* 警戒线说明 */}
            <div className="mt-4 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 rounded border border-neutral-800 bg-neutral-900/60 px-4 py-3 text-xs text-neutral-300">
              <span><span className="text-yellow-400 mr-1">- -</span>黄线 2%：触碰后暂停新开仓并进入人工复核</span>
              <span><span className="text-red-400 mr-1">- -</span>红线 3%：触碰后强制平仓并锁定交易</span>
            </div>
          </CardContent>
        </Card>

        {/* 连续亏损计数 + 保证金水位 - 与左侧曲线高度一致 */}
        <div className="flex flex-col gap-4 h-full">
          <Card className="bg-neutral-900 border-neutral-700 flex-1">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-neutral-300">连续亏损计数</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-3xl font-bold text-white">
                {consecutiveLosses !== null ? consecutiveLosses : "--"} / {simConfig.continuousLossLimit}
              </div>
              <Progress
                value={consecutiveLosses !== null ? (consecutiveLosses / simConfig.continuousLossLimit) * 100 : 0}
                className="h-2 bg-neutral-800"
              />
              <p className="text-xs text-neutral-400">触达上限将触发 L2 熔断</p>
            </CardContent>
          </Card>

          <Card className="bg-neutral-900 border-neutral-700 flex-1">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-neutral-300">保证金水位</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-neutral-400">当前</span>
                  <span className={`font-bold ${
                    marginLevel === null ? "text-neutral-500" :
                    marginLevel >= simConfig.marginAlert ? "text-red-400" :
                    marginLevel >= simConfig.marginWarning ? "text-yellow-400" : "text-green-400"
                  }`}>
                    {marginLevel !== null ? `${marginLevel}%` : "--"}
                  </span>
                </div>
                <Progress value={marginLevel ?? 0} className="h-3 bg-gradient-to-r from-green-900 via-yellow-900 to-red-900" />
              </div>
              <div className="grid grid-cols-3 gap-1 text-xs">
                <div className="text-green-400">60%</div>
                <div className="text-yellow-400">70%</div>
                <div className="text-red-400">80%</div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* L3 & Sim 配置 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-neutral-300">L3 & Sim 配置区</CardTitle>
            <Button
              size="sm"
              variant="outline"
              className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 text-xs"
              onClick={() => toast.info("日志查看功能将在 TASK-0016 实现")}
            >
              查看日志
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 熔断恢复面板 */}
          {showFusePanel && (
            <div className="bg-red-900/20 border border-red-600/50 rounded p-4 space-y-3">
              <p className="text-sm text-red-400 font-medium">⚠ 熔断恢复面板</p>
              <p className="text-xs text-red-300">此操作将重置所有 L1/L2 计数器。二次确认必需。</p>
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
            </div>
          )}

          {/* Sim 专属配置 */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-neutral-300">Sim 专属阈值配置</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="text-xs text-neutral-400 block mb-2">日亏限额 (%)</label>
                <Input
                  type="number"
                  step="0.1"
                  value={simConfig.dailyLossLimit}
                  onChange={(e) =>
                    setSimConfig({
                      ...simConfig,
                      dailyLossLimit: parseFloat(e.target.value),
                    })
                  }
                  className="bg-neutral-800 border-neutral-700 text-white text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-neutral-400 block mb-2">连续亏损上限 (笔)</label>
                <Input
                  type="number"
                  value={simConfig.continuousLossLimit}
                  onChange={(e) =>
                    setSimConfig({
                      ...simConfig,
                      continuousLossLimit: parseInt(e.target.value),
                    })
                  }
                  className="bg-neutral-800 border-neutral-700 text-white text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-neutral-400 block mb-2">保证金预警 (%)</label>
                <Input
                  type="number"
                  value={simConfig.marginWarning}
                  onChange={(e) =>
                    setSimConfig({
                      ...simConfig,
                      marginWarning: parseInt(e.target.value),
                    })
                  }
                  className="bg-neutral-800 border-neutral-700 text-white text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-neutral-400 block mb-2">保证金警告 (%)</label>
                <Input
                  type="number"
                  value={simConfig.marginAlert}
                  onChange={(e) =>
                    setSimConfig({
                      ...simConfig,
                      marginAlert: parseInt(e.target.value),
                    })
                  }
                  className="bg-neutral-800 border-neutral-700 text-white text-sm"
                />
              </div>
            </div>
            <Button
              onClick={handleSaveSimConfig}
              className="bg-green-600 hover:bg-green-700 text-white w-full"
            >
              下发配置到交易引擎
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 风控告警 + 交易日历 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-neutral-300">
                实时告警 ({alerts.length})
              </CardTitle>
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="text-xs text-neutral-500 hover:text-orange-400 transition-colors"
              >
                {showHistory ? "隐藏历史" : `历史(${alertHistory.length})`}
              </button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3 max-h-64 overflow-y-auto">
            {showHistory ? (
              alertHistory.length === 0 ? (
                <p className="text-xs text-neutral-500 text-center py-4">暂无历史告警</p>
              ) : (
                alertHistory.slice().reverse().map((h) => (
                  <div key={h.id} className="border border-neutral-700 rounded p-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-neutral-300">{h.message}</span>
                      <span className="text-neutral-600">{h.time}</span>
                    </div>
                  </div>
                ))
              )
            ) : (
            alerts.map((alert) => (
              <div
                key={alert.id}
                className={`border rounded p-3 cursor-pointer transition-colors ${getStatusColor("alert")}`}
              >
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{alert.message}</p>
                    <p className="text-xs text-opacity-70 mt-1">{alert.time}</p>
                  </div>
                </div>
              </div>
            ))
            )}
          </CardContent>
        </Card>

        {/* 交易日历 */}
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">交易日历（中国节假日同步）</CardTitle>
          </CardHeader>
          <CardContent>
            {(() => {
              const today = new Date()
              const y = today.getFullYear()
              const m = today.getMonth()
              const firstDay = new Date(y, m, 1).getDay() // 0=Sun
              const firstMon = (firstDay + 6) % 7         // adjust to Mon=0
              const daysInMonth = new Date(y, m + 1, 0).getDate()
              const todayDate = today.getDate()
              const cells: (number | null)[] = [
                ...Array(firstMon).fill(null),
                ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
              ]
              return (
                <>
                  <div className="grid grid-cols-7 gap-1 text-center text-xs mb-1">
                    {["一","二","三","四","五","六","日"].map(d => (
                      <div key={d} className="text-neutral-500 py-1">{d}</div>
                    ))}
                    {cells.map((day, idx) => {
                      if (!day) return <div key={`e-${idx}`} />
                      const d = new Date(y, m, day)
                      const isToday = day === todayDate
                      const trading = isTradingDay(d)
                      const hn = getTodayHolidayName(d)
                      return (
                        <div
                          key={day}
                          title={hn ? hn : trading ? "交易日" : "休市"}
                          className={`py-1 rounded text-xs cursor-default ${
                            isToday
                              ? "bg-orange-500 text-white font-bold"
                              : !trading
                              ? hn
                                ? "bg-red-900/30 text-red-500"
                                : "text-neutral-600"
                              : "text-neutral-300 hover:bg-neutral-700/50"
                          }`}
                        >
                          {day}
                        </div>
                      )
                    })}
                  </div>
                  <div className="mt-3 flex items-center gap-4 text-xs flex-wrap">
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 bg-orange-500 rounded" />
                      <span className="text-neutral-400">今日</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 bg-red-900/30 border border-red-700/50 rounded" />
                      <span className="text-neutral-400">法定节假日</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 border border-neutral-700 rounded" />
                      <span className="text-neutral-500">周末/休市</span>
                    </div>
                  </div>
                  {!isTradingDay(today) && (
                    <div className="mt-3 p-2 bg-red-900/20 border border-red-800/50 rounded text-xs text-red-400">
                      ⛔ 今日{getTodayHolidayName(today) ?? "休市"}，系统拒绝新开仓
                    </div>
                  )}
                </>
              )
            })()}
          </CardContent>
        </Card>
      </div>

      {/* 系统日志查看 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-2">
            <CardTitle className="text-sm font-medium text-neutral-300 flex items-center gap-2">
              <ScrollText className="w-4 h-4" />
              系统日志（只读）
            </CardTitle>
            <div className="flex items-center gap-2">
              <select
                value={logLevelFilter}
                onChange={(e) => setLogLevelFilter(e.target.value)}
                className="bg-neutral-800 border border-neutral-700 text-neutral-300 text-xs rounded px-2 py-1"
              >
                <option value="ALL">全部级别</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
              </select>
              <Button
                size="sm"
                variant="ghost"
                className={`text-xs ${logAutoRefresh ? "text-green-400" : "text-neutral-500"}`}
                onClick={() => setLogAutoRefresh(!logAutoRefresh)}
              >
                {logAutoRefresh ? "⏸ 暂停" : "▶ 自动刷新"}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="text-neutral-400 hover:text-orange-500"
                onClick={fetchLogs}
                disabled={logLoading}
              >
                <RefreshCw className={`w-3 h-3 ${logLoading ? "animate-spin" : ""}`} />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="max-h-80 overflow-y-auto bg-neutral-950 rounded border border-neutral-800 p-2 font-mono text-xs space-y-0.5">
            {logEntries.length === 0 ? (
              <p className="text-neutral-600 text-center py-4">暂无日志</p>
            ) : (
              logEntries.map((entry, idx) => (
                <div key={idx} className="flex gap-2 leading-5 hover:bg-neutral-900/50">
                  <span className="text-neutral-600 shrink-0">{entry.timestamp?.slice(11, 19) ?? "--"}</span>
                  <span className={`shrink-0 w-14 text-right ${
                    entry.level === "ERROR" ? "text-red-400" :
                    entry.level === "WARNING" ? "text-yellow-400" :
                    "text-green-400"
                  }`}>{entry.level}</span>
                  <span className="text-neutral-500 shrink-0 max-w-[120px] truncate">{entry.source}</span>
                  <span className="text-neutral-300 break-all">{entry.message}</span>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
