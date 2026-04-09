"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Target,
  Percent,
  RefreshCw,
  Save,
  Settings,
} from "lucide-react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts"

export default function BacktestDetailPage() {
  const [selectedBacktest, setSelectedBacktest] = useState(null)
  const [showParamPanel, setShowParamPanel] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  
  // 参数调整状态
  const [adjustedParams, setAdjustedParams] = useState({
    slippage: 0.5,
    commission: 0.05,
    initialCapital: 100000,
    positionSize: 100,
    maxDrawdownLimit: 20,
  })

  // 权益曲线数据
  const equityCurveData = [
    { date: "01/01", equity: 100000, benchmark: 100000 },
    { date: "01/15", equity: 102500, benchmark: 101000 },
    { date: "02/01", equity: 105800, benchmark: 102500 },
    { date: "02/15", equity: 103200, benchmark: 101800 },
    { date: "03/01", equity: 108500, benchmark: 103200 },
    { date: "03/15", equity: 112000, benchmark: 104500 },
    { date: "04/01", equity: 115800, benchmark: 105000 },
    { date: "04/15", equity: 118500, benchmark: 106200 },
    { date: "05/01", equity: 122000, benchmark: 107500 },
    { date: "05/15", equity: 125800, benchmark: 108000 },
    { date: "06/01", equity: 128500, benchmark: 109200 },
  ]

  // 回测记录
  const backtests = [
    {
      id: "BT-2025-001",
      strategy: "均线突破策略",
      contract: "螺纹钢2510",
      status: "completed",
      startDate: "2024-01-01",
      endDate: "2025-06-01",
      initialCapital: 100000,
      finalCapital: 128500,
      totalReturn: 28.5,
      annualReturn: 18.9,
      maxDrawdown: 8.2,
      sharpeRatio: 1.85,
      winRate: 62,
      totalTrades: 156,
      profitTrades: 97,
      lossTrades: 59,
    },
    {
      id: "BT-2025-002",
      strategy: "MACD动量策略",
      contract: "沪铜2509",
      status: "running",
      startDate: "2024-06-01",
      endDate: "2025-06-01",
      initialCapital: 200000,
      finalCapital: 245000,
      totalReturn: 22.5,
      annualReturn: 22.5,
      maxDrawdown: 6.8,
      sharpeRatio: 2.12,
      winRate: 68,
      totalTrades: 89,
      profitTrades: 61,
      lossTrades: 28,
    },
    {
      id: "BT-2025-003",
      strategy: "布林带反转策略",
      contract: "豆粕2509",
      status: "failed",
      startDate: "2024-03-01",
      endDate: "2025-03-01",
      initialCapital: 150000,
      finalCapital: 142500,
      totalReturn: -5.0,
      annualReturn: -5.0,
      maxDrawdown: 12.5,
      sharpeRatio: -0.35,
      winRate: 45,
      totalTrades: 124,
      profitTrades: 56,
      lossTrades: 68,
    },
    {
      id: "BT-2025-004",
      strategy: "RSI超卖策略",
      contract: "沪金2512",
      status: "completed",
      startDate: "2024-01-01",
      endDate: "2025-06-01",
      initialCapital: 300000,
      finalCapital: 351000,
      totalReturn: 17.0,
      annualReturn: 11.3,
      maxDrawdown: 5.2,
      sharpeRatio: 1.65,
      winRate: 71,
      totalTrades: 78,
      profitTrades: 55,
      lossTrades: 23,
    },
  ]

  // 交易明细
  const tradeDetails = [
    {
      id: 1,
      time: "2025/06/25 09:30",
      contract: "螺纹钢2510",
      direction: "多",
      action: "开仓",
      price: 3852,
      quantity: 10,
      profit: null,
      commission: 45,
    },
    {
      id: 2,
      time: "2025/06/25 14:15",
      contract: "螺纹钢2510",
      direction: "多",
      action: "平仓",
      price: 3895,
      quantity: 10,
      profit: 4300,
      commission: 45,
    },
    {
      id: 3,
      time: "2025/06/24 10:00",
      contract: "沪铜2509",
      direction: "空",
      action: "开仓",
      price: 78650,
      quantity: 5,
      profit: null,
      commission: 120,
    },
    {
      id: 4,
      time: "2025/06/24 15:30",
      contract: "沪铜2509",
      direction: "空",
      action: "平仓",
      price: 78200,
      quantity: 5,
      profit: 11250,
      commission: 120,
    },
    {
      id: 5,
      time: "2025/06/23 09:45",
      contract: "豆粕2509",
      direction: "多",
      action: "开仓",
      price: 3125,
      quantity: 20,
      profit: null,
      commission: 30,
    },
    {
      id: 6,
      time: "2025/06/23 11:20",
      contract: "豆粕2509",
      direction: "多",
      action: "平仓",
      price: 3098,
      quantity: 20,
      profit: -5400,
      commission: 30,
    },
  ]

  const handleParamChange = (key, value) => {
    setAdjustedParams({
      ...adjustedParams,
      [key]: parseFloat(value) || 0,
    })
  }

  const handleSaveParams = () => {
    setIsLoading(true)
    setTimeout(() => {
      setLastUpdate(new Date())
      setIsLoading(false)
      alert("参数已保存，回测数据已更新")
    }, 800)
  }

  const handleRefresh = () => {
    setIsLoading(true)
    setTimeout(() => {
      setLastUpdate(new Date())
      setIsLoading(false)
    }, 500)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-white/20 text-white"
      case "running":
        return "bg-orange-500/20 text-orange-500"
      case "failed":
        return "bg-red-500/20 text-red-500"
      default:
        return "bg-neutral-500/20 text-neutral-300"
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "completed":
        return "已完成"
      case "running":
        return "运行中"
      case "failed":
        return "失败"
      default:
        return status
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* 头部 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wider">回测详情</h1>
          <p className="text-sm text-neutral-400">查看回测结果、权益曲线和交易明细</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => setShowParamPanel(!showParamPanel)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Settings className="w-4 h-4 mr-2" />
            参数调整
          </Button>
          <Button
            onClick={handleRefresh}
            variant="outline"
            className="border-neutral-700 text-neutral-400 hover:bg-neutral-800"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
          <Button className="bg-orange-500 hover:bg-orange-600 text-white">导出报告</Button>
        </div>
      </div>

      {/* 更新时间戳 */}
      <div className="text-xs text-neutral-500 text-right">
        最后更新: {lastUpdate.toLocaleString("zh-CN")}
      </div>

      {/* 参数调整面板 */}
      {showParamPanel && (
        <Card className="bg-neutral-900 border-orange-600/50 border-2">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-orange-400 tracking-wider">参数调整面板</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {/* 滑点 */}
              <div>
                <label className="text-xs text-neutral-400 block mb-2">滑点 (点)</label>
                <Input
                  type="number"
                  step="0.1"
                  value={adjustedParams.slippage}
                  onChange={(e) => handleParamChange("slippage", e.target.value)}
                  className="bg-neutral-800 border-neutral-600 text-white"
                  placeholder="0.5"
                />
                <p className="text-xs text-neutral-500 mt-1">每笔成交的价格偏差</p>
              </div>

              {/* 手续费 */}
              <div>
                <label className="text-xs text-neutral-400 block mb-2">手续费 (%)</label>
                <Input
                  type="number"
                  step="0.01"
                  value={adjustedParams.commission}
                  onChange={(e) => handleParamChange("commission", e.target.value)}
                  className="bg-neutral-800 border-neutral-600 text-white"
                  placeholder="0.05"
                />
                <p className="text-xs text-neutral-500 mt-1">每笔交易的手续费比例</p>
              </div>

              {/* 初始资金 */}
              <div>
                <label className="text-xs text-neutral-400 block mb-2">初始资金 (元)</label>
                <Input
                  type="number"
                  step="1000"
                  value={adjustedParams.initialCapital}
                  onChange={(e) => handleParamChange("initialCapital", e.target.value)}
                  className="bg-neutral-800 border-neutral-600 text-white"
                  placeholder="100000"
                />
                <p className="text-xs text-neutral-500 mt-1">回测启动资金</p>
              </div>

              {/* 持仓占比 */}
              <div>
                <label className="text-xs text-neutral-400 block mb-2">持仓占比 (%)</label>
                <Input
                  type="number"
                  step="1"
                  value={adjustedParams.positionSize}
                  onChange={(e) => handleParamChange("positionSize", e.target.value)}
                  className="bg-neutral-800 border-neutral-600 text-white"
                  placeholder="100"
                />
                <p className="text-xs text-neutral-500 mt-1">每次开仓的资金占比</p>
              </div>

              {/* 最大回撤限制 */}
              <div>
                <label className="text-xs text-neutral-400 block mb-2">回撤上限 (%)</label>
                <Input
                  type="number"
                  step="1"
                  value={adjustedParams.maxDrawdownLimit}
                  onChange={(e) => handleParamChange("maxDrawdownLimit", e.target.value)}
                  className="bg-neutral-800 border-neutral-600 text-white"
                  placeholder="20"
                />
                <p className="text-xs text-neutral-500 mt-1">触发止损的回撤阈值</p>
              </div>
            </div>

            {/* 预览效果 */}
            <div className="bg-neutral-800 rounded border border-neutral-700 p-4 mt-4">
              <p className="text-sm text-neutral-300 mb-3">调整效果预览:</p>
              <div className="grid grid-cols-3 gap-4 text-xs">
                <div>
                  <p className="text-neutral-500">预期收益率</p>
                  <p className="text-green-400 font-bold text-lg">+24.8%</p>
                </div>
                <div>
                  <p className="text-neutral-500">预期最大回撤</p>
                  <p className="text-orange-400 font-bold text-lg">-7.5%</p>
                </div>
                <div>
                  <p className="text-neutral-500">预期夏普比率</p>
                  <p className="text-white font-bold text-lg">1.92</p>
                </div>
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="flex gap-3 pt-4">
              <Button
                onClick={handleSaveParams}
                className="bg-orange-500 hover:bg-orange-600 text-white flex-1"
                disabled={isLoading}
              >
                <Save className="w-4 h-4 mr-2" />
                保存并回测
              </Button>
              <Button
                onClick={() => setShowParamPanel(false)}
                variant="outline"
                className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 flex-1"
              >
                关闭
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 关键指标统计 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">总收益率</p>
                <p className="text-2xl font-bold text-green-400 font-mono">+28.5%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">最大回撤</p>
                <p className="text-2xl font-bold text-red-400 font-mono">-8.2%</p>
              </div>
              <TrendingDown className="w-8 h-8 text-red-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">夏普比率</p>
                <p className="text-2xl font-bold text-white font-mono">1.85</p>
              </div>
              <BarChart3 className="w-8 h-8 text-white" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-neutral-400 tracking-wider">胜率</p>
                <p className="text-2xl font-bold text-orange-500 font-mono">62%</p>
              </div>
              <Percent className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 权益曲线 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">权益曲线</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={equityCurveData}>
                <defs>
                  <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                <XAxis dataKey="date" stroke="#737373" />
                <YAxis stroke="#737373" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #404040",
                    borderRadius: "4px",
                  }}
                  labelStyle={{ color: "#fff" }}
                />
                <Area
                  type="monotone"
                  dataKey="equity"
                  stroke="#f97316"
                  fillOpacity={1}
                  fill="url(#equityGradient)"
                  isAnimationActive={true}
                />
                <Line
                  type="monotone"
                  dataKey="benchmark"
                  stroke="#6b7280"
                  strokeDasharray="5 5"
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* 回测记录 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">回测记录</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">回测ID</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">策略</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">合约</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">状态</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">总收益</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">最大回撤</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">夏普比率</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">胜率</th>
                </tr>
              </thead>
              <tbody>
                {backtests.map((backtest, index) => (
                  <tr
                    key={backtest.id}
                    className={`border-b border-neutral-800 hover:bg-neutral-800 transition-colors cursor-pointer ${
                      index % 2 === 0 ? "bg-neutral-900" : "bg-neutral-850"
                    }`}
                    onClick={() => setSelectedBacktest(backtest)}
                  >
                    <td className="py-3 px-4 text-white font-mono">{backtest.id}</td>
                    <td className="py-3 px-4 text-white">{backtest.strategy}</td>
                    <td className="py-3 px-4 text-neutral-300">{backtest.contract}</td>
                    <td className="py-3 px-4">
                      <Badge className={getStatusColor(backtest.status)}>
                        {getStatusText(backtest.status)}
                      </Badge>
                    </td>
                    <td className={`py-3 px-4 font-mono ${backtest.totalReturn >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {backtest.totalReturn >= 0 ? "+" : ""}{backtest.totalReturn.toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-red-400 font-mono">-{backtest.maxDrawdown.toFixed(1)}%</td>
                    <td className="py-3 px-4 text-white font-mono">{backtest.sharpeRatio.toFixed(2)}</td>
                    <td className="py-3 px-4 text-white font-mono">{backtest.winRate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* 交易明细 */}
      <Card className="bg-neutral-900 border-neutral-700">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">
            交易明细 ({tradeDetails.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-700">
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">时间</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">合约</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">方向</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">操作</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">价格</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">数量</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">盈亏</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-neutral-400">手续费</th>
                </tr>
              </thead>
              <tbody>
                {tradeDetails.map((trade, index) => (
                  <tr
                    key={trade.id}
                    className={`border-b border-neutral-800 ${index % 2 === 0 ? "bg-neutral-900" : "bg-neutral-850"}`}
                  >
                    <td className="py-3 px-4 text-neutral-300 font-mono">{trade.time}</td>
                    <td className="py-3 px-4 text-white">{trade.contract}</td>
                    <td className="py-3 px-4">
                      {trade.direction === "多" ? (
                        <span className="text-green-400 font-mono">{trade.direction}</span>
                      ) : (
                        <span className="text-red-400 font-mono">{trade.direction}</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-white">{trade.action}</td>
                    <td className="py-3 px-4 text-white font-mono">{trade.price}</td>
                    <td className="py-3 px-4 text-white font-mono">{trade.quantity}</td>
                    <td className={`py-3 px-4 font-mono ${trade.profit ? (trade.profit >= 0 ? "text-green-400" : "text-red-400") : "text-neutral-400"}`}>
                      {trade.profit ? (trade.profit >= 0 ? "+" : "") + trade.profit.toLocaleString() : "-"}
                    </td>
                    <td className="py-3 px-4 text-neutral-300 font-mono">{trade.commission}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* 回测详情模态框 */}
      {selectedBacktest && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedBacktest(null)}
          onKeyDown={(e) => {
            if (e.key === "Escape") setSelectedBacktest(null)
          }}
        >
          <Card
            className="bg-neutral-900 border-neutral-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg font-bold text-white">{selectedBacktest.strategy}</CardTitle>
                  <p className="text-sm text-neutral-400">{selectedBacktest.id}</p>
                </div>
                <Button
                  variant="ghost"
                  onClick={() => setSelectedBacktest(null)}
                  className="text-neutral-400 hover:text-white"
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-neutral-500 mb-1">初始资金</p>
                  <p className="text-sm text-white font-mono">{selectedBacktest.initialCapital.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-neutral-500 mb-1">最终资金</p>
                  <p className="text-sm text-green-400 font-mono">{selectedBacktest.finalCapital.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-neutral-500 mb-1">年化收益</p>
                  <p className="text-sm text-white font-mono">{selectedBacktest.annualReturn}%</p>
                </div>
                <div>
                  <p className="text-xs text-neutral-500 mb-1">总交易数</p>
                  <p className="text-sm text-white font-mono">{selectedBacktest.totalTrades}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
