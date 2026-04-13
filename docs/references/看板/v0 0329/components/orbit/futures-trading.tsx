'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  ArrowLeft, TrendingUp, TrendingDown, Download, Search, 
  Filter, ChevronDown, Trophy, Target, Percent, Activity,
  Clock, Wallet, BarChart3, Calendar, X, AlertTriangle, Loader2, Eye, EyeOff
} from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, Area, AreaChart, ReferenceLine
} from 'recharts'

interface FuturesTradingProps {
  onBack: () => void
}

// Trading days per month (approximate, for a typical year)
const TRADING_DAYS_PER_MONTH = [22, 20, 21, 22, 21, 22, 23, 22, 21, 23, 21, 22]
const MONTH_LABELS = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']

// Generate equity data per period
function generateEquityDataForPeriod(period: '今日' | '本周' | '本月' | '本年' | '全部') {
  let equity = 500000
  const data: { date: string; equity: number }[] = []

  if (period === '今日') {
    // 09:00 to 23:00, every 30 mins
    for (let h = 9; h <= 23; h++) {
      for (const m of [0, 30]) {
        if (h === 23 && m === 30) break
        const label = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`
        const change = (Math.random() - 0.45) * 2000
        equity = Math.max(equity + change, 400000)
        data.push({ date: label, equity: Math.round(equity) })
      }
    }
  } else if (period === '本周') {
    const days = ['周一','周二','周三','周四','周五','周六','周日']
    for (const day of days) {
      const change = (Math.random() - 0.45) * 8000
      equity = Math.max(equity + change, 400000)
      data.push({ date: day, equity: Math.round(equity) })
    }
  } else if (period === '本月') {
    for (let d = 1; d <= 31; d++) {
      const change = (Math.random() - 0.45) * 5000
      equity = Math.max(equity + change, 400000)
      data.push({ date: `${d}日`, equity: Math.round(equity) })
    }
  } else if (period === '本年') {
    for (let m = 1; m <= 12; m++) {
      const change = (Math.random() - 0.45) * 20000
      equity = Math.max(equity + change, 400000)
      data.push({ date: `${m}月`, equity: Math.round(equity) })
    }
  } else {
    // 全部: last 90 days
    const now = new Date()
    for (let i = 90; i >= 0; i--) {
      const date = new Date(now)
      date.setDate(date.getDate() - i)
      const change = (Math.random() - 0.45) * 5000
      equity = Math.max(equity + change, 400000)
      data.push({
        date: `${date.getMonth() + 1}/${date.getDate()}`,
        equity: Math.round(equity),
      })
    }
  }
  return data
}

// Generate heatmap data for 12 months with actual trading days
function generateHeatmapData() {
  return MONTH_LABELS.map((month, mi) => {
    const days = TRADING_DAYS_PER_MONTH[mi]
    return {
      month,
      days: Array.from({ length: days }, () => (Math.random() - 0.4) * 10000),
    }
  })
}

export function FuturesTrading({ onBack }: FuturesTradingProps) {
  const [equityPeriod, setEquityPeriod] = useState<'今日' | '本周' | '本月' | '本年' | '全部'>('本月')
  const [varietyFilter, setVarietyFilter] = useState('全部')
  const [directionFilter, setDirectionFilter] = useState('全部')
  const [searchText, setSearchText] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  
  // 平仓确认弹窗
  const [closeAllModalOpen, setCloseAllModalOpen] = useState(false)
  const [closeSingleModalOpen, setCloseSingleModalOpen] = useState(false)
  const [selectedPosition, setSelectedPosition] = useState<any>(null)
  const [isClosing, setIsClosing] = useState(false)
  
  const equityData = generateEquityDataForPeriod(equityPeriod)
  const heatmapData = generateHeatmapData()

  // 平仓处理函数
  const handleCloseAllPositions = async () => {
    setIsClosing(true)
    await new Promise(r => setTimeout(r, 1500))
    setIsClosing(false)
    setCloseAllModalOpen(false)
  }

  const handleCloseSinglePosition = async () => {
    setIsClosing(true)
    await new Promise(r => setTimeout(r, 1500))
    setIsClosing(false)
    setCloseSingleModalOpen(false)
  }

  // Trade history data (moved before filteredTrades to avoid initialization error)
  const trades = [
    { time: '03-15 09:30', code: 'rb2405', name: '螺纹钢', direction: '开多', price: 3480, lots: 10, amount: 34800, fee: 35, status: '已成交' },
    { time: '03-14 14:20', code: 'hc2405', name: '热卷', direction: '开空', price: 3720, lots: 5, amount: 18600, fee: 19, status: '已成交' },
    { time: '03-14 10:05', code: 'rb2405', name: '螺纹钢', direction: '平空', price: 3510, lots: 8, amount: 28080, fee: 28, status: '已成交' },
    { time: '03-13 15:00', code: 'i2405', name: '铁矿石', direction: '开多', price: 892, lots: 3, amount: 26760, fee: 27, status: '已成交' },
    { time: '03-13 09:45', code: 'j2405', name: '焦炭', direction: '开空', price: 2180, lots: 2, amount: 43600, fee: 44, status: '已成交' },
  ]

  // 搜索和分页
  const filteredTrades = trades.filter(t => {
    const matchSearch = !searchText || 
      t.code.includes(searchText) || 
      t.name.includes(searchText)
    return matchSearch
  })
  const totalPages = Math.ceil(filteredTrades.length / 20)
  const paginatedTrades = filteredTrades.slice((currentPage - 1) * 20, currentPage * 20)

  // KPI Data
  const kpiData = {
    todayPnl: 12450,
    todayPnlPercent: 3.2,
    totalPnl: 125450,
    totalPnlPercent: 25.1,
    winRate: 58.5,
    profitRatio: 1.8,
    tradeCount: 125,
    winCount: 73,
    lossCount: 52,
    maxDrawdown: -8.2,
  }

  // Position data
  const positions = [
    { code: 'rb2405', name: '螺纹钢', direction: '多', lots: 10, openPrice: 3480, currentPrice: 3520, pnl: 4000, openTime: '03-15 09:30' },
    { code: 'hc2405', name: '热卷', direction: '空', lots: 5, openPrice: 3720, currentPrice: 3680, pnl: 2000, openTime: '03-14 14:20' },
    { code: 'i2405', name: '铁矿石', direction: '多', lots: 3, openPrice: 892, currentPrice: 905, pnl: 3900, openTime: '03-13 10:15' },
    { code: 'j2405', name: '焦炭', direction: '空', lots: 2, openPrice: 2180, currentPrice: 2150, pnl: 1800, openTime: '03-12 11:30' },
  ]

  // Performance metrics
  const performanceMetrics = [
    { name: '夏普比率', value: '2.1', icon: BarChart3 },
    { name: '索提诺比率', value: '2.8', icon: Target },
    { name: '卡尔玛比率', value: '3.2', icon: TrendingUp },
    { name: '最大回撤', value: '-8.2%', icon: TrendingDown, negative: true },
    { name: '平均盈利', value: '2,850', icon: Wallet },
    { name: '平均亏损', value: '-1,580', icon: Wallet, negative: true },
    { name: '盈利因子', value: '1.8', icon: Percent },
    { name: '交易周期', value: '90天', icon: Clock },
  ]

  // Top varieties
  const profitTop5 = [
    { rank: 1, code: '螺纹钢', trades: 45, pnl: 42500, winRate: 62.2 },
    { rank: 2, code: '热卷', trades: 32, pnl: 28300, winRate: 59.4 },
    { rank: 3, code: '铁矿石', trades: 28, pnl: 21200, winRate: 57.1 },
    { rank: 4, code: '焦炭', trades: 15, pnl: 18500, winRate: 60.0 },
    { rank: 5, code: '焦煤', trades: 12, pnl: 12400, winRate: 58.3 },
  ]

  const lossTop5 = [
    { rank: 1, code: '甲醇', trades: 18, pnl: -8500, winRate: 38.9 },
    { rank: 2, code: '豆粕', trades: 14, pnl: -6200, winRate: 42.9 },
    { rank: 3, code: '棕榈油', trades: 10, pnl: -4800, winRate: 40.0 },
    { rank: 4, code: '白糖', trades: 8, pnl: -3200, winRate: 37.5 },
    { rank: 5, code: '棉花', trades: 6, pnl: -2100, winRate: 33.3 },
  ]

  const totalPositionLots = positions.reduce((sum, p) => sum + p.lots, 0)
  const totalFloatPnl = positions.reduce((sum, p) => sum + p.pnl, 0)

  return (
    <div className="flex-1 overflow-auto">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-border/50">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-muted rounded-md transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-muted-foreground" />
            </button>
            <div>
              <h1 className="text-xl font-semibold text-foreground tracking-tight">交易记录 - 中国期货</h1>
              <p className="text-sm text-muted-foreground">查看交易记录、持仓、绩效数据</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-primary bg-primary/10 hover:bg-primary/20 rounded-md transition-colors">
              <Download className="w-4 h-4" />
              导出报表
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Row 1: KPI Cards - 8 cards in 2 rows of 4 */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-4 gap-4"
        >
          {[
            { label: '今日盈亏', value: kpiData.todayPnl.toLocaleString(), sub: `+${kpiData.todayPnlPercent}%`, positive: true, icon: TrendingUp },
            { label: '累计盈亏', value: kpiData.totalPnl.toLocaleString(), sub: `+${kpiData.totalPnlPercent}%`, positive: true, icon: Wallet },
            { label: '胜率', value: `${kpiData.winRate}%`, icon: Target },
            { label: '盈亏比', value: kpiData.profitRatio.toString(), icon: Percent },
            { label: '交易次数', value: kpiData.tradeCount.toString(), icon: Activity },
            { label: '盈利次数', value: kpiData.winCount.toString(), positive: true, icon: TrendingUp },
            { label: '亏损次数', value: kpiData.lossCount.toString(), negative: true, icon: TrendingDown },
            { label: '最大回撤', value: `${kpiData.maxDrawdown}%`, negative: true, icon: BarChart3 },
          ].map((kpi, i) => (
            <div key={i} className="card-surface p-4 flex flex-col items-center justify-center text-center min-h-[100px]">
              <div className="flex items-center gap-1.5 mb-2">
                <kpi.icon className={cn(
                  'w-4 h-4',
                  kpi.positive && 'text-#FF3B30',
                  kpi.negative && 'text-#3FB950',
                  !kpi.positive && !kpi.negative && 'text-primary'
                )} />
                <span className="text-xs text-muted-foreground">{kpi.label}</span>
              </div>
              <p className={cn(
                'text-xl font-semibold font-mono',
                kpi.positive && 'text-#FF3B30',
                kpi.negative && 'text-#3FB950',
                !kpi.positive && !kpi.negative && 'text-foreground'
              )}>
                {kpi.value}
              </p>
              {kpi.sub && (
                <p className={cn(
                  'text-xs font-mono mt-1',
                  kpi.positive ? 'text-#FF3B30' : 'text-#3FB950'
                )}>
                  {kpi.sub}
                </p>
              )}
            </div>
          ))}
        </motion.div>

        {/* Row 2: Equity Curve */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card-surface p-5"
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-foreground tracking-tight">权益曲线</h3>
              <p className="text-xs text-muted-foreground mt-1">
                当前权益: <span className="font-mono text-foreground">625,450</span>
              </p>
            </div>
            <div className="flex gap-1">
              {(['今日', '本周', '本月', '本年', '全部'] as const).map((period) => (
                <button
                  key={period}
                  onClick={() => setEquityPeriod(period)}
                  className={cn(
                    'px-2.5 py-1 text-xs font-medium rounded transition-colors',
                    equityPeriod === period
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                  )}
                >
                  {period}
                </button>
              ))}
            </div>
          </div>
          {/* Re-key AreaChart to force remount on period change */}
          
          <div className="h-[240px]" key={equityPeriod}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={equityData}>
                <defs>
                  <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(156, 163, 175, 0.1)" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 10, fill: '#9ca3af' }}
                  axisLine={{ stroke: 'rgba(156, 163, 175, 0.2)' }}
                />
                <YAxis 
                  tick={{ fontSize: 10, fill: '#9ca3af' }}
                  axisLine={{ stroke: 'rgba(156, 163, 175, 0.2)' }}
                  tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }}
                  formatter={(value: number) => [value.toLocaleString(), '权益']}
                />
                <Area 
                  type="monotone" 
                  dataKey="equity" 
                  stroke="#ef4444" 
                  strokeWidth={2}
                  fill="url(#equityGradient)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Row 3: Position Details */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="card-surface p-5"
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-foreground tracking-tight">持仓详情</h3>
              <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                <span>总持仓: <span className="font-mono text-foreground">{totalPositionLots} 手</span></span>
                <span>总浮盈: <span className={cn('font-mono', totalFloatPnl >= 0 ? 'text-#FF3B30' : 'text-#3FB950')}>
                  {totalFloatPnl >= 0 ? '+' : ''}{totalFloatPnl.toLocaleString()}
                </span></span>
                <span>保证金占用: <span className="font-mono text-foreground">85,000</span></span>
              </div>
            </div>
            <div className="flex gap-2">
              <button 
                onClick={() => setCloseAllModalOpen(true)}
                className="px-3 py-1.5 text-xs font-medium text-white bg-[#FF3B30] hover:bg-[#FF3B30]/90 rounded-md transition-colors"
              >
                一键平仓
              </button>
              <button className="px-3 py-1.5 text-xs font-medium text-primary bg-primary/10 hover:bg-primary/20 rounded-md transition-colors">
                部分平仓
              </button>
              <button className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground border border-border/50 hover:border-border rounded-md transition-colors">
                <Download className="w-3.5 h-3.5" />
                导出持仓
              </button>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            {positions.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Eye className="w-8 h-8 text-muted-foreground/30 mb-2" />
                <p className="text-sm text-muted-foreground">暂无持仓数据</p>
              </div>
            ) : (
              <table className="w-full text-xs min-w-[800px]">
              <thead className="border-b border-border/50">
                <tr>
                  <th className="text-left py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">代码</th>
                  <th className="text-left py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">名称</th>
                  <th className="text-center py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">方向</th>
                  <th className="text-right py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">手数</th>
                  <th className="text-right py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">开仓价</th>
                  <th className="text-right py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">当前价</th>
                  <th className="text-right py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">浮盈</th>
                  <th className="text-left py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">开仓时间</th>
                  <th className="text-center py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">操作</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((pos, i) => (
                  <tr key={i} className="border-b border-border/30 hover:bg-muted/30 transition-colors">
                    <td className="py-3 px-3 font-mono font-semibold whitespace-nowrap">{pos.code}</td>
                    <td className="py-3 px-3 whitespace-nowrap">{pos.name}</td>
                    <td className="py-3 px-3 text-center whitespace-nowrap">
                      <span className={cn(
                        'px-2 py-0.5 rounded text-xs font-medium',
                        pos.direction === '多' ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'
                      )}>
                        {pos.direction}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right font-mono whitespace-nowrap">{pos.lots}</td>
                    <td className="py-3 px-3 text-right font-mono whitespace-nowrap">{pos.openPrice}</td>
                    <td className="py-3 px-3 text-right font-mono whitespace-nowrap">{pos.currentPrice}</td>
                    <td className={cn(
                      'py-3 px-3 text-right font-mono font-medium whitespace-nowrap',
                      pos.pnl >= 0 ? 'text-#FF3B30' : 'text-#3FB950'
                    )}>
                      {pos.pnl >= 0 ? '+' : ''}{pos.pnl.toLocaleString()}
                    </td>
                    <td className="py-3 px-3 text-muted-foreground whitespace-nowrap">{pos.openTime}</td>
                    <td className="py-3 px-3 text-center whitespace-nowrap">
                      <button 
                        onClick={() => {
                          setSelectedPosition(pos)
                          setCloseSingleModalOpen(true)
                        }}
                        className="px-2 py-1 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                      >
                        平仓
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            )}
          </div>
        </motion.div>

        {/* Row 4: Trade History */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card-surface p-5"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground tracking-tight">成交明细</h3>
            <div className="flex items-center gap-2">
              <div className="relative">
                <select 
                  value={varietyFilter}
                  onChange={(e) => setVarietyFilter(e.target.value)}
                  className="appearance-none px-3 py-1.5 pr-8 text-xs bg-muted/50 border border-border/50 rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="全部">全部品种</option>
                  <option value="rb">螺纹钢</option>
                  <option value="hc">热卷</option>
                  <option value="i">铁矿石</option>
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
              </div>
              <div className="relative">
                <select
                  value={directionFilter}
                  onChange={(e) => setDirectionFilter(e.target.value)}
                  className="appearance-none px-3 py-1.5 pr-8 text-xs bg-muted/50 border border-border/50 rounded-md focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="全部">全部方向</option>
                  <option value="开仓">开仓</option>
                  <option value="平仓">平仓</option>
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground pointer-events-none" />
              </div>
              <div className="flex items-center gap-1 px-2 py-1.5 bg-muted/50 border border-border/50 rounded-md">
                <Search className="w-3.5 h-3.5 text-muted-foreground" />
                <input 
                  type="text" 
                  placeholder="搜索代码或名称..." 
                  value={searchText}
                  onChange={(e) => {
                    setSearchText(e.target.value)
                    setCurrentPage(1)
                  }}
                  className="w-20 text-xs bg-transparent focus:outline-none"
                />
              </div>
              <button className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground border border-border/50 hover:border-border rounded-md transition-colors">
                <Download className="w-3.5 h-3.5" />
                导出 CSV
              </button>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            {filteredTrades.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Search className="w-8 h-8 text-muted-foreground/30 mb-2" />
                <p className="text-sm text-muted-foreground">暂无成交记录</p>
              </div>
            ) : (
              <>
              <table className="w-full text-xs min-w-[900px]">
              <thead className="border-b border-border/50">
                <tr>
                  <th className="text-left py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">时间</th>
                  <th className="text-left py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">代码</th>
                  <th className="text-left py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">名称</th>
                  <th className="text-center py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">方向</th>
                  <th className="text-right py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">价格</th>
                  <th className="text-right py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">手数</th>
                  <th className="text-right py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">金额</th>
                  <th className="text-right py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">手续费</th>
                  <th className="text-center py-2 px-3 font-medium text-muted-foreground whitespace-nowrap">状态</th>
                </tr>
              </thead>
              <tbody>
                {paginatedTrades.map((trade, i) => (
                  <tr key={i} className="border-b border-border/30 hover:bg-muted/30 transition-colors">
                    <td className="py-3 px-3 text-muted-foreground whitespace-nowrap">{trade.time}</td>
                    <td className="py-3 px-3 font-mono font-semibold whitespace-nowrap">{trade.code}</td>
                    <td className="py-3 px-3 whitespace-nowrap">{trade.name}</td>
                    <td className="py-3 px-3 text-center whitespace-nowrap">
                      <span className={cn(
                        'px-2 py-0.5 rounded text-xs font-medium',
                        trade.direction.includes('多') ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'
                      )}>
                        {trade.direction}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right font-mono whitespace-nowrap">{trade.price}</td>
                    <td className="py-3 px-3 text-right font-mono whitespace-nowrap">{trade.lots}</td>
                    <td className="py-3 px-3 text-right font-mono whitespace-nowrap">{trade.amount.toLocaleString()}</td>
                    <td className="py-3 px-3 text-right font-mono text-muted-foreground whitespace-nowrap">{trade.fee}</td>
                    <td className="py-3 px-3 text-center whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-700">
                        {trade.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {/* 分页器 */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4 px-3 py-2 border-t border-border/30">
                <span className="text-xs text-muted-foreground">
                  第 {currentPage} / {totalPages} 页，共 {filteredTrades.length} 条
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-2 py-1 text-xs bg-muted hover:bg-muted/80 disabled:opacity-50 rounded transition-colors"
                  >
                    上一页
                  </button>
                  <button
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="px-2 py-1 text-xs bg-muted hover:bg-muted/80 disabled:opacity-50 rounded transition-colors"
                  >
                    下一页
                  </button>
                </div>
              </div>
            )}
            </>
            )}
          </div>
        </motion.div>

        {/* Row 5: Performance Stats (50/50) */}
        <div className="grid grid-cols-2 gap-4">
          {/* Performance Metrics */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="card-surface p-5"
          >
            <h3 className="text-sm font-semibold text-foreground tracking-tight mb-4">绩效指标</h3>
            <div className="grid grid-cols-2 gap-3">
              {performanceMetrics.map((metric, i) => (
                <div key={i} className="p-3 bg-muted/30 rounded-lg flex flex-col items-center justify-center text-center">
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <metric.icon className={cn(
                      'w-3.5 h-3.5',
                      metric.negative ? 'text-#3FB950' : 'text-primary'
                    )} />
                    <span className="text-xs text-muted-foreground">{metric.name}</span>
                  </div>
                  <p className={cn(
                    'text-lg font-semibold font-mono',
                    metric.negative ? 'text-#3FB950' : 'text-foreground'
                  )}>
                    {metric.value}
                  </p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Monthly Heatmap */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="card-surface p-5"
          >
            <h3 className="text-sm font-semibold text-foreground tracking-tight mb-4">月度盈亏热力图</h3>
            <div className="space-y-1.5 overflow-y-auto max-h-[320px] pr-1">
              {heatmapData.map(({ month, days }) => (
                <div key={month} className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground w-8 shrink-0">{month}</span>
                  <div className="flex gap-0.5 flex-1">
                    {days.map((value, i) => (
                      <div
                        key={i}
                        className={cn(
                          'flex-1 h-5 rounded-sm transition-colors cursor-pointer hover:ring-1 hover:ring-primary',
                          value > 5000  ? 'bg-#FF3B30' :
                          value > 2000  ? 'bg-red-400' :
                          value > 0     ? 'bg-red-300' :
                          value > -2000 ? 'bg-emerald-300' :
                          value > -5000 ? 'bg-emerald-400' :
                                          'bg-#3FB950'
                        )}
                        title={`${Math.round(value).toLocaleString()}`}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-center gap-4 mt-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 bg-#3FB950 rounded-sm inline-block" /> 亏损
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 bg-#FF3B30 rounded-sm inline-block" /> 盈利
              </span>
            </div>
          </motion.div>
        </div>

        {/* Row 6: Variety Ranking (50/50) */}
        <div className="grid grid-cols-2 gap-4">
          {/* Profit Top 5 */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="card-surface p-5"
          >
            <div className="flex items-center gap-2 mb-4">
              <Trophy className="w-4 h-4 text-amber-500" />
              <h3 className="text-sm font-semibold text-foreground tracking-tight">盈利 Top5 品种</h3>
            </div>
            <div className="space-y-2">
              {profitTop5.map((item) => (
                <div key={item.rank} className="flex items-center gap-3 p-2 bg-muted/30 rounded-lg">
                  <span className={cn(
                    'w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold',
                    item.rank === 1 && 'bg-amber-100 text-amber-700',
                    item.rank === 2 && 'bg-gray-200 text-gray-700',
                    item.rank === 3 && 'bg-orange-100 text-orange-700',
                    item.rank > 3 && 'bg-muted text-muted-foreground'
                  )}>
                    {item.rank}
                  </span>
                  <span className="flex-1 text-sm font-medium">{item.code}</span>
                  <span className="text-xs text-muted-foreground">{item.trades}笔</span>
                  <span className="text-sm font-mono font-medium text-#FF3B30">+{item.pnl.toLocaleString()}</span>
                  <span className="text-xs text-muted-foreground">{item.winRate}%</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Loss Top 5 */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="card-surface p-5"
          >
            <div className="flex items-center gap-2 mb-4">
              <TrendingDown className="w-4 h-4 text-#3FB950" />
              <h3 className="text-sm font-semibold text-foreground tracking-tight">亏损 Top5 品种</h3>
            </div>
            <div className="space-y-2">
              {lossTop5.map((item) => (
                <div key={item.rank} className="flex items-center gap-3 p-2 bg-muted/30 rounded-lg">
                  <span className="w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold bg-emerald-100 text-emerald-700">
                    {item.rank}
                  </span>
                  <span className="flex-1 text-sm font-medium">{item.code}</span>
                  <span className="text-xs text-muted-foreground">{item.trades}笔</span>
                  <span className="text-sm font-mono font-medium text-#3FB950">{item.pnl.toLocaleString()}</span>
                  <span className="text-xs text-muted-foreground">{item.winRate}%</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      {/* 一键平仓确认弹窗 */}
      {closeAllModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <motion.div
            className="bg-card rounded-lg border border-border shadow-xl max-w-[540px] w-[90%]"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/30">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-[#FF3B30]" />
                <h2 className="text-sm font-semibold text-foreground">一键平仓所有持仓？</h2>
              </div>
              <button
                onClick={() => setCloseAllModalOpen(false)}
                disabled={isClosing}
                className="p-1 hover:bg-muted rounded transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content */}
            <div className="px-6 py-4 space-y-4 max-h-[400px] overflow-y-auto">
              <p className="text-xs text-muted-foreground">
                将平仓以下 {positions.length} 手持仓：
              </p>
              <div className="space-y-2">
                {positions.map((pos, i) => (
                  <div key={i} className="text-xs text-muted-foreground flex justify-between p-2 bg-muted/30 rounded">
                    <span>• {pos.code} {pos.direction} {pos.lots} 手</span>
                    <span className={pos.pnl >= 0 ? 'text-[#FF3B30]' : 'text-[#3FB950]'}>
                      {pos.pnl >= 0 ? '+' : ''}¥{pos.pnl.toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>

              <div className="space-y-1 pt-2 border-t border-border/30">
                <div className="text-xs flex justify-between text-muted-foreground">
                  <span>预估总盈亏：</span>
                  <span className="text-[#FF3B30] font-mono font-semibold">+¥{totalFloatPnl.toLocaleString()}</span>
                </div>
                <div className="text-xs flex justify-between text-muted-foreground">
                  <span>预估手续费：</span>
                  <span className="font-mono">约 ¥{Math.round(totalPositionLots * 15)}</span>
                </div>
              </div>

              <div className="p-2 bg-[#FF3B30]/10 border border-[#FF3B30]/30 rounded text-xs text-[#FF3B30]">
                ⚠️⚠️⚠️ 警告：此操作不可逆，所有持仓将被平掉！
              </div>
            </div>

            {/* Footer */}
            <div className="flex gap-3 px-6 py-4 border-t border-border/30 bg-muted/20">
              <button
                onClick={() => setCloseAllModalOpen(false)}
                disabled={isClosing}
                className="flex-1 px-4 py-2 text-sm font-medium text-foreground border border-border rounded-md hover:bg-muted transition-colors disabled:opacity-50"
              >
                取消
              </button>
              <button
                onClick={handleCloseAllPositions}
                disabled={isClosing}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-[#FF3B30] hover:bg-[#FF3B30]/90 rounded-md transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isClosing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    处理中...
                  </>
                ) : (
                  '确认全部平仓'
                )}
              </button>
            </div>
          </motion.div>
        </div>
      )}

      {/* 单个平仓确认弹窗 */}
      {closeSingleModalOpen && selectedPosition && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <motion.div
            className="bg-card rounded-lg border border-border shadow-xl max-w-[540px] w-[90%]"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/30">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-[#FF3B30]" />
                <h2 className="text-sm font-semibold text-foreground">确认平仓？</h2>
              </div>
              <button
                onClick={() => setCloseSingleModalOpen(false)}
                disabled={isClosing}
                className="p-1 hover:bg-muted rounded transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content */}
            <div className="px-6 py-4 space-y-3">
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">品种：</span>
                  <span className="font-semibold">{selectedPosition.code} {selectedPosition.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">方向：</span>
                  <span className={selectedPosition.direction === '多' ? 'text-[#FF3B30]' : 'text-[#3FB950]'}>
                    🔴 {selectedPosition.direction === '多' ? '做多' : '做空'} → 平仓
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">手数：</span>
                  <span className="font-mono">{selectedPosition.lots} 手</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">开仓价：</span>
                  <span className="font-mono">¥{selectedPosition.openPrice}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">当前价：</span>
                  <span className="font-mono">¥{selectedPosition.currentPrice}</span>
                </div>
                <div className="flex justify-between border-t border-border/30 pt-2 mt-2">
                  <span className="text-muted-foreground">浮动盈亏：</span>
                  <span className={selectedPosition.pnl >= 0 ? 'text-[#FF3B30]' : 'text-[#3FB950]'}>
                    {selectedPosition.pnl >= 0 ? '+' : ''}¥{selectedPosition.pnl.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">预估手续费：</span>
                  <span className="font-mono">约 ¥{Math.round(selectedPosition.lots * 15)}</span>
                </div>
              </div>

              <div className="p-2 bg-[#FF3B30]/10 border border-[#FF3B30]/30 rounded text-xs text-[#FF3B30]">
                ⚠️ 注意：平仓后无法恢复，请确认
              </div>
            </div>

            {/* Footer */}
            <div className="flex gap-3 px-6 py-4 border-t border-border/30 bg-muted/20">
              <button
                onClick={() => setCloseSingleModalOpen(false)}
                disabled={isClosing}
                className="flex-1 px-4 py-2 text-sm font-medium text-foreground border border-border rounded-md hover:bg-muted transition-colors disabled:opacity-50"
              >
                取消
              </button>
              <button
                onClick={handleCloseSinglePosition}
                disabled={isClosing}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-[#FF3B30] hover:bg-[#FF3B30]/90 rounded-md transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isClosing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    处理中...
                  </>
                ) : (
                  '确认平仓'
                )}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
