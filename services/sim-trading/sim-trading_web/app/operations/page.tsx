"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Send,
  X,
  AlertTriangle,
  Clock,
  TrendingUp,
} from "lucide-react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import { simApi } from "@/lib/sim-api"
import { toast } from "sonner"

export default function SimNowTradingTerminal() {
  const [isLoading, setIsLoading] = useState(false)
  const [pauseTrading, setPauseTrading] = useState(false)
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const updateRef = useRef<HTMLSpanElement>(null)

  // 账户状态
  const [accountState, setAccountState] = useState<any>(null)

  // 下单参数
  const [orderParams, setOrderParams] = useState({
    contract: "螺纹钢2510",
    direction: "buy",
    openClose: "open",
    quantity: 1,
    priceType: "market",
    limitPrice: 3850,
  })

  const [orderError, setOrderError] = useState("")

  // 合约白名单
  const contractWhitelist = [
    "螺纹钢2510",
    "沪铜2509",
    "豆粕2509",
    "沪金2512",
  ]

  // 持仓
  const [positions, setPositions] = useState<any[]>([])

  // 订单/成交流
  const [orderStream, setOrderStream] = useState<any[]>([])

  // 后端状态
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)

  // 权益曲线数据（CTP 连接后从后端更新）
  const [equityCurveData, setEquityCurveData] = useState<any[]>([])
  const [equityPeriod, setEquityPeriod] = useState<"day"|"week"|"month"|"year"|"all">("day")

  // 当前合约 5 档盘口
  const [orderBook, setOrderBook] = useState<any>(null)

  // 判断当前是否在交易时段（期货：09:00-11:30 / 13:30-15:00 / 21:00-23:30）
  const isTradingHours = useCallback(() => {
    const d = new Date()
    const mins = d.getHours() * 60 + d.getMinutes()
    return (
      (mins >= 9 * 60 && mins < 11 * 60 + 30) ||
      (mins >= 13 * 60 + 30 && mins < 15 * 60) ||
      (mins >= 21 * 60 && mins < 23 * 60 + 30)
    )
  }, [])

  // 轮询函数
  const poll = useCallback(async () => {
    try {
      const [h, pos, ord, acct, ticksRes] = await Promise.all([
        simApi.health(),
        simApi.positions(),
        simApi.orders(),
        fetch("/api/sim/api/v1/account").then(r => r.ok ? r.json() : null).catch(() => null),
        fetch("/api/sim/api/v1/ticks").then(r => r.ok ? r.json() : null).catch(() => null),
      ])
      setBackendOnline(h.status === "ok")
      setPositions((pos as any).positions ?? [])
      setOrderStream((ord as any).orders ?? [])
      if (acct !== null) setAccountState(acct)
      if (ticksRes?.ticks) {
        // 取第一个有数据的 tick 做盘口展示
        const entries = Object.entries<any>(ticksRes.ticks)
        if (entries.length > 0) {
          const [, t] = entries[0]
          setOrderBook(t)
        }
      }
    } catch {
      setBackendOnline(false)
    }
    // 直写 DOM，不触发 React re-render
    if (updateRef.current) {
      updateRef.current.textContent = new Date().toLocaleString("zh-CN")
    }
  }, [])

  // 自适应间隔：交易时段 3s，否则 30s
  useEffect(() => {
    poll()
    let timer: ReturnType<typeof setTimeout>
    const schedule = () => {
      const delay = isTradingHours() ? 3000 : 30000
      timer = setTimeout(() => { poll(); schedule() }, delay)
    }
    schedule()
    return () => clearTimeout(timer)
  }, [poll, isTradingHours])

  const handlePlaceOrder = () => {
    setOrderError("")
    
    if (pauseTrading) {
      setOrderError("交易已暂停，无法下单")
      return
    }

    if ((accountState?.margin_rate ?? 0) > 80) {
      setOrderError("保证金率触达 80%，无法开仓")
      return
    }

    // TODO: 连接到 trading_api:8003 WebSocket 发送订单
    setIsLoading(true)
    setTimeout(() => {
      setIsLoading(false)
      toast.success(`已下单：${orderParams.direction === "buy" ? "买入" : "卖出"} ${orderParams.contract} ${orderParams.quantity}手`)
    }, 300)
  }

  const handleClosePosition = (positionId: number) => {
    toast.info(`平仓指令已发送（ID: ${positionId}）·骨架阶段未连接`)
    // TODO: 连接到 trading_api:8003 WebSocket
  }

  const handleReversePosition = (positionId: number) => {
    toast.warning(`反手指令已发送（ID: ${positionId}）·骨架阶段未连接`)
    // TODO: 连接到 trading_api:8003 WebSocket
  }

  const handleModifyStopLoss = (positionId: number) => {
    toast.info(`止损修改指令已发送（ID: ${positionId}）·骨架阶段未连接`)
    // TODO: 连接到 trading_api:8003 WebSocket
  }

  const handleClearAllPositions = () => {
    toast.error("一键清仓指令已发送 · 骨架阶段未连接，实际未执行")
    // TODO: 连接到 trading_api:8003 WebSocket
    setShowClearConfirm(false)
  }

  return (
    <div className="p-6 space-y-6 bg-neutral-950 min-h-screen">
      {/* 头部 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wider">SimNow 交易终端</h1>
          <p className="text-sm text-neutral-400">极简、低延迟的模拟交易操作界面</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => setPauseTrading(!pauseTrading)}
            className={pauseTrading ? "bg-orange-600 hover:bg-orange-700" : "bg-neutral-700 hover:bg-neutral-600"}
          >
            <Clock className="w-4 h-4 mr-2" />
            {pauseTrading ? "交易已暂停" : "交易正常"}
          </Button>
          <Button
            onClick={() => setShowClearConfirm(true)}
            className="bg-red-600 hover:bg-red-700 text-white font-bold"
          >
            <AlertTriangle className="w-4 h-4 mr-2" />
            一键清仓
          </Button>
        </div>
      </div>

      {/* 更新时间 */}
      <div className="text-xs text-neutral-500 text-right">
        最后更新: <span ref={updateRef}>--</span>
      </div>

      {/* 账户概览 - 大字体卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <p className="text-xs text-neutral-400 mb-1">动态权益</p>
            <p className="text-2xl font-bold text-white font-mono transition-[color] duration-300">
              {accountState?.equity != null ? `¥${accountState.equity.toLocaleString()}` : "--"}
            </p>
          </CardContent>
        </Card>

        <Card className={`bg-neutral-900 border transition-colors duration-300 ${(accountState?.floating_pnl ?? 0) >= 0 ? "border-green-600" : "border-red-600"}`}>
          <CardContent className="p-4">
            <p className="text-xs text-neutral-400 mb-1">浮动盈亏</p>
            <p className={`text-2xl font-bold font-mono transition-[color] duration-300 ${(accountState?.floating_pnl ?? 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
              {accountState?.floating_pnl != null
                ? `${accountState.floating_pnl >= 0 ? "+" : ""}¥${accountState.floating_pnl.toLocaleString()}`
                : "--"}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <p className="text-xs text-neutral-400 mb-1">可用资金</p>
            <p className="text-2xl font-bold text-white font-mono transition-[color] duration-300">
              {accountState?.available != null ? `¥${accountState.available.toLocaleString()}` : "--"}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-600">
          <CardContent className="p-4">
            <p className="text-xs text-neutral-400 mb-1">风险度</p>
            <p className="text-2xl font-bold font-mono text-white">
              --
            </p>
          </CardContent>
        </Card>

        <Card className={`bg-neutral-900 border transition-colors duration-300 ${(accountState?.margin_rate ?? 0) > 70 ? "border-red-600" : "border-yellow-600"}`}>
          <CardContent className="p-4">
            <p className="text-xs text-neutral-400 mb-1">保证金率</p>
            <p className={`text-2xl font-bold font-mono transition-[color] duration-300 ${(accountState?.margin_rate ?? 0) > 70 ? "text-red-400" : "text-yellow-400"}`}>
              {accountState?.margin_rate != null ? `${accountState.margin_rate}%` : "--"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 系统净收益统计行 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-neutral-900 border border-neutral-700 rounded p-3">
          <p className="text-xs text-neutral-500 mb-1">初始资金</p>
          <p className="text-sm font-mono text-neutral-300">
            {accountState?.initial_balance != null ? `¥${accountState.initial_balance.toLocaleString()}` : "--"}
          </p>
        </div>
        <div className="bg-neutral-900 border border-neutral-700 rounded p-3">
          <p className="text-xs text-neutral-500 mb-1">累计手续费</p>
          <p className="text-sm font-mono text-red-400">
            {accountState?.total_commission != null ? `-¥${accountState.total_commission.toLocaleString()}` : "--"}
          </p>
        </div>
        <div className="bg-neutral-900 border border-neutral-700 rounded p-3">
          <p className="text-xs text-neutral-500 mb-1">累计滑点损耗</p>
          <p className="text-sm font-mono text-red-400">
            {accountState?.total_slippage != null ? `-¥${accountState.total_slippage.toLocaleString()}` : "--"}
          </p>
        </div>
        <div className="bg-neutral-900 border border-neutral-700 rounded p-3">
          <p className="text-xs text-neutral-500 mb-1">系统净收益</p>
          <p className={`text-sm font-mono transition-[color] duration-300 ${
            accountState?.net_pnl != null
              ? accountState.net_pnl >= 0 ? "text-green-400" : "text-red-400"
              : "text-neutral-400"
          }`}>
            {accountState?.net_pnl != null
              ? `${accountState.net_pnl >= 0 ? "+" : ""}¥${accountState.net_pnl.toLocaleString()}`
              : "--"}
          </p>
        </div>
      </div>

      {/* 下单面板 + 权益曲线 */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 下单面板 */}
        <Card className="bg-neutral-900 border-neutral-700 lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300">快速下单</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* 5 档盘口 */}
            <div className="rounded bg-neutral-800/60 p-2 text-xs font-mono">
              <div className="flex justify-between text-neutral-500 mb-1 px-1">
                <span>价格</span><span>买量</span><span>卖量</span>
              </div>
              {[5,4,3,2,1].map(i => (
                <div key={`ask${i}`} className="flex justify-between py-0.5 px-1 text-red-300">
                  <span>{orderBook ? (orderBook[`ask${i}`] ?? "--") : "--"}</span>
                  <span className="text-neutral-500">--</span>
                  <span>{orderBook ? (orderBook[`ask_vol${i}`] ?? "--") : "--"}</span>
                </div>
              ))}
              <div className="border-t border-neutral-600 my-1" />
              {[1,2,3,4,5].map(i => (
                <div key={`bid${i}`} className="flex justify-between py-0.5 px-1 text-green-300">
                  <span>{orderBook ? (orderBook[`bid${i}`] ?? "--") : "--"}</span>
                  <span>{orderBook ? (orderBook[`bid_vol${i}`] ?? "--") : "--"}</span>
                  <span className="text-neutral-500">--</span>
                </div>
              ))}
            </div>
            {/* 品种选择 */}
            <div className="space-y-3">
            <div>
              <label className="text-xs text-neutral-400 block mb-2">品种</label>
              <select
                value={orderParams.contract}
                onChange={(e) => setOrderParams({ ...orderParams, contract: e.target.value })}
                className="w-full bg-neutral-800 border border-neutral-700 text-white text-sm p-2 rounded"
              >
                {contractWhitelist.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            {/* 方向/开平 */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-neutral-400 block mb-2">方向</label>
                <select
                  value={orderParams.direction}
                  onChange={(e) => setOrderParams({ ...orderParams, direction: e.target.value as any })}
                  className="w-full bg-neutral-800 border border-neutral-700 text-white text-sm p-2 rounded"
                >
                  <option value="buy">买</option>
                  <option value="sell">卖</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-neutral-400 block mb-2">开平</label>
                <select
                  value={orderParams.openClose}
                  onChange={(e) => setOrderParams({ ...orderParams, openClose: e.target.value as any })}
                  className="w-full bg-neutral-800 border border-neutral-700 text-white text-sm p-2 rounded"
                >
                  <option value="open">开仓</option>
                  <option value="close">平仓</option>
                </select>
              </div>
            </div>

            {/* 手数 */}
            <div>
              <label className="text-xs text-neutral-400 block mb-2">手数</label>
              <Input
                type="number"
                min="1"
                value={orderParams.quantity}
                onChange={(e) =>
                  setOrderParams({
                    ...orderParams,
                    quantity: parseInt(e.target.value) || 1,
                  })
                }
                className="bg-neutral-800 border-neutral-700 text-white text-sm"
              />
              <p className="text-xs text-neutral-500 mt-1">
                智能推荐: {accountState?.available != null ? `${Math.floor(accountState.available / 10000)} 手` : "--"}
              </p>
            </div>

            {/* 价格类型 */}
            <div>
              <label className="text-xs text-neutral-400 block mb-2">价格类型</label>
              <div className="flex gap-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={orderParams.priceType === "market"}
                    onChange={() =>
                      setOrderParams({ ...orderParams, priceType: "market" })
                    }
                    className="accent-orange-500"
                  />
                  <span className="text-sm text-neutral-300">市价</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={orderParams.priceType === "limit"}
                    onChange={() =>
                      setOrderParams({ ...orderParams, priceType: "limit" })
                    }
                    className="accent-orange-500"
                  />
                  <span className="text-sm text-neutral-300">限价</span>
                </label>
              </div>
            </div>

            {/* 限价 */}
            {orderParams.priceType === "limit" && (
              <div>
                <label className="text-xs text-neutral-400 block mb-2">限价</label>
                <Input
                  type="number"
                  step="0.5"
                  value={orderParams.limitPrice}
                  onChange={(e) =>
                    setOrderParams({
                      ...orderParams,
                      limitPrice: parseFloat(e.target.value),
                    })
                  }
                  className="bg-neutral-800 border-neutral-700 text-white text-sm"
                />
              </div>
            )}

            {/* 一键下单 */}
            <Button
              onClick={handlePlaceOrder}
              disabled={isLoading || pauseTrading}
              className={`w-full font-bold h-10 ${
                orderParams.direction === "buy"
                  ? "bg-green-600 hover:bg-green-700"
                  : "bg-red-600 hover:bg-red-700"
              } text-white`}
            >
              <Send className="w-4 h-4 mr-2" />
              {orderParams.direction === "buy" ? "买入" : "卖出"}
            </Button>

            {/* 错误提示 */}
            {orderError && (
              <div className="bg-red-900/20 border border-red-600/50 rounded p-2">
                <p className="text-xs text-red-400">{orderError}</p>
              </div>
            )}
            </div>{/* end inner space-y-3 */}
          </CardContent>
        </Card>

        {/* 权益曲线 */}
        <Card className="bg-neutral-900 border-neutral-700 lg:col-span-3 flex flex-col">
          <CardHeader className="shrink-0">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-neutral-300">实时权益曲线</CardTitle>
              <div className="flex gap-1">
                {(["day","week","month","year","all"] as const).map(p => (
                  <button key={p} onClick={() => setEquityPeriod(p)}
                    className={`text-xs px-2 py-0.5 rounded transition-colors ${
                      equityPeriod === p
                        ? "bg-orange-600 text-white"
                        : "text-neutral-400 hover:text-white hover:bg-neutral-700"
                    }`}>
                    {p === "day" ? "日" : p === "week" ? "周" : p === "month" ? "月" : p === "year" ? "年" : "全部"}
                  </button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col min-h-0 pb-4">
            {equityCurveData.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-neutral-600 gap-2 min-h-[240px]">
                <TrendingUp className="w-10 h-10 opacity-20" />
                <p className="text-sm">CTP 连接后开始记录权益曲线</p>
                <p className="text-xs opacity-60">当前{equityPeriod === "day" ? "日" : equityPeriod === "week" ? "周" : equityPeriod === "month" ? "月" : equityPeriod === "year" ? "年" : "全部"}无数据</p>
              </div>
            ) : (
              <div className="flex-1 min-h-[240px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={equityCurveData}>
                    <defs>
                      <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
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
                    <Line
                      type="monotone"
                      dataKey="equity"
                      stroke="#f97316"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 持仓表格 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300">
            持仓 ({positions.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">合约</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">方向</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">手数</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">均价</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">最新价</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">浮盈亏</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">止损/止盈</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">操作</th>
                </tr>
              </thead>
              <tbody>
                {positions.length === 0 ? (
                  <tr><td colSpan={8} className="text-center text-neutral-500 py-8">骨架阶段 · 暂无持仓数据</td></tr>
                ) : positions.map((position) => (
                  <tr
                    key={position.id}
                    className={`border-b border-neutral-800 ${
                      position.touched
                        ? "bg-red-900/10 animate-pulse"
                        : "hover:bg-neutral-800/50"
                    }`}
                  >
                    <td className="py-3 px-4 text-white font-mono">{position.contract}</td>
                    <td className="py-3 px-4">
                      <Badge
                        className={
                          position.direction === "buy"
                            ? "bg-green-900/30 text-green-400"
                            : "bg-red-900/30 text-red-400"
                        }
                      >
                        {position.direction === "buy" ? "买" : "卖"}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-white font-mono">{position.quantity}</td>
                    <td className="py-3 px-4 text-neutral-300 font-mono">
                      {position.avgPrice}
                    </td>
                    <td className="py-3 px-4 text-white font-mono">{position.currentPrice}</td>
                    <td
                      className={`py-3 px-4 font-mono ${
                        position.floatPnl >= 0
                          ? "text-green-400"
                          : "text-red-400"
                      }`}
                    >
                      {position.floatPnl >= 0 ? "+" : ""}¥{position.floatPnl.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-xs text-neutral-400">
                      <div className="flex gap-1">
                        <span>SL: {position.stopLoss}</span>
                        <span>/</span>
                        <span>TP: {position.takeProfit}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="bg-neutral-800 text-neutral-300 hover:bg-neutral-700 hover:text-white text-xs h-7 px-2"
                          onClick={() => handleClosePosition(position.id)}
                        >
                          平
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="bg-neutral-800 text-neutral-300 hover:bg-neutral-700 hover:text-white text-xs h-7 px-2"
                          onClick={() => handleReversePosition(position.id)}
                        >
                          反
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="bg-neutral-800 text-neutral-300 hover:bg-neutral-700 hover:text-white text-xs h-7 px-2"
                          onClick={() => handleModifyStopLoss(position.id)}
                        >
                          改
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* 订单/成交流 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300">
            订单记录 ({orderStream.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {orderStream.length === 0 ? (
              <div className="text-center text-neutral-500 py-6">骨架阶段 · 暂无订单记录</div>
            ) : orderStream.map((order) => (
              <div
                key={order.id}
                className={`border rounded p-2 text-xs flex justify-between items-start ${
                  order.status === "废单"
                    ? "bg-red-900/20 border-red-600/50"
                    : "bg-neutral-800/30 border-neutral-700"
                }`}
              >
                <div className="flex-1">
                  <div className="flex gap-2">
                    <span className="text-neutral-400">{order.time}</span>
                    <span className="font-mono text-white">{order.contract}</span>
                    <span
                      className={
                        order.action.includes("买")
                          ? "text-green-400"
                          : "text-red-400"
                      }
                    >
                      {order.action}
                    </span>
                    <span className="text-neutral-300">{order.quantity}手</span>
                    <span className="text-neutral-500">@{order.price}</span>
                  </div>
                  {order.reason && (
                    <div className="text-red-400 mt-1">⚠ {order.reason}</div>
                  )}
                </div>
                <Badge
                  className={
                    order.status === "已成交"
                      ? "bg-green-900/30 text-green-400"
                      : "bg-red-900/30 text-red-400"
                  }
                >
                  {order.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 一键清仓确认对话 */}
      {showClearConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <Card className="bg-neutral-900 border-red-600 w-full max-w-md">
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle className="text-lg font-bold text-red-400">
                  一键清仓确认
                </CardTitle>
                <Button
                  variant="ghost"
                  onClick={() => setShowClearConfirm(false)}
                  className="text-neutral-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-neutral-300">
                即将平仓所有 <span className="font-bold">{positions.length}</span> 个持仓，此操作不可撤销。
              </p>
              <div className="flex gap-3">
                <Button
                  onClick={handleClearAllPositions}
                  className="bg-red-600 hover:bg-red-700 text-white flex-1 font-bold"
                >
                  确认清仓
                </Button>
                <Button
                  onClick={() => setShowClearConfirm(false)}
                  variant="outline"
                  className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 flex-1"
                >
                  取消
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
