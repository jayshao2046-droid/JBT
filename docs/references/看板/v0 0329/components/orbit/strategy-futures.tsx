'use client'

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  ArrowLeft, TrendingUp, TrendingDown, Download, Search, 
  Trophy, Target, Percent, Activity,
  Zap, AlertTriangle, BarChart3, Play, RotateCcw,
  Check, X, Lightbulb, FlaskConical, Sparkles, Calendar,
  ChevronRight, ChevronLeft, Filter, FileDown
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useToast } from "@/hooks/use-toast"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, AreaChart, Area, Legend, PieChart, Pie, Cell
} from 'recharts'

interface StrategyFuturesProps {
  onBack: () => void
}

// KPI data
const kpiData = {
  todaySignals: 31,
  longSignals: 12,
  shortSignals: 8,
  neutralSignals: 11,
  avgConfidence: 72,
  highConfidence: 8,
  expectedReturn: 24500,
  riskLevel: '中等',
}

// Complete 31 Factor categories
const factorCategories = [
  {
    name: '动量类',
    factors: [
      { id: 'price_momentum', name: '价格动量', checked: true },
      { id: 'relative_strength', name: '相对强弱', checked: true },
      { id: 'trend_strength', name: '趋势强度', checked: false },
      { id: 'momentum_breakout', name: '动量突破', checked: false },
      { id: 'macd', name: 'MACD', checked: false },
      { id: 'rsi', name: 'RSI', checked: false },
      { id: 'kdj', name: 'KDJ', checked: false },
      { id: 'cci', name: 'CCI', checked: false },
    ]
  },
  {
    name: '均值回归类',
    factors: [
      { id: 'bollinger', name: '布林带', checked: true },
      { id: 'bias', name: '乖离率', checked: false },
      { id: 'mean_reversion', name: '均值回复', checked: false },
      { id: 'zscore', name: 'Z-Score', checked: false },
      { id: 'percentile', name: '百分位', checked: false },
      { id: 'deviation', name: '标准差', checked: false },
    ]
  },
  {
    name: '突破类',
    factors: [
      { id: 'channel_breakout', name: '通道突破', checked: false },
      { id: 'high_low_breakout', name: '高低点突破', checked: false },
      { id: 'donchian', name: '唐奇安通道', checked: false },
      { id: 'atr_breakout', name: 'ATR突破', checked: false },
      { id: 'range_breakout', name: '区间突破', checked: false },
    ]
  },
  {
    name: '成交量类',
    factors: [
      { id: 'volume_surge', name: '放量', checked: true },
      { id: 'volume_shrink', name: '缩量', checked: true },
      { id: 'volume_price_div', name: '量价背离', checked: false },
      { id: 'obv', name: 'OBV', checked: false },
      { id: 'vwap', name: 'VWAP', checked: false },
      { id: 'volume_ratio', name: '量比', checked: false },
    ]
  },
  {
    name: '波动率类',
    factors: [
      { id: 'atr', name: 'ATR', checked: false },
      { id: 'historical_vol', name: '历史波动率', checked: false },
      { id: 'implied_vol', name: '隐含波动率', checked: false },
      { id: 'vix', name: 'VIX', checked: false },
      { id: 'range', name: '振幅', checked: false },
      { id: 'parkinson', name: 'Parkinson', checked: false },
    ]
  },
]

// All 31 factors for IC heatmap
const allFactorNames = [
  '价格动量', '相对强弱', '趋势强度', '动量突破', 'MACD', 'RSI', 'KDJ', 'CCI',
  '布林带', '乖离率', '均值回复', 'Z-Score', '百分位', '标准差',
  '通道突破', '高低点突破', '唐奇安通道', 'ATR突破', '区间突破',
  '放量', '缩量', '量价背离', 'OBV', 'VWAP', '量比',
  'ATR', '历史波动率', '隐含波动率', 'VIX', '振幅', 'Parkinson'
]

// Signal list data
const signalData = [
  { time: '17:08', code: 'rb2405', name: '螺纹钢', price: 3520, trend: '上升', pressure: 3550, support: 3480, entry: 3515, exit: 3580, confidence: 78, reason: '均线突破+放量', signal: '多' },
  { time: '17:05', code: 'hc2405', name: '热卷', price: 3680, trend: '下降', pressure: 3720, support: 3650, entry: 3685, exit: 3620, confidence: 65, reason: '量能萎缩', signal: '空' },
  { time: '16:58', code: 'm2405', name: '豆粕', price: 3280, trend: '震荡', pressure: 3320, support: 3250, entry: null, exit: null, confidence: 55, reason: '等待突破', signal: '观望' },
  { time: '16:52', code: 'i2405', name: '铁矿石', price: 892, trend: '上升', pressure: 920, support: 875, entry: 890, exit: 940, confidence: 82, reason: '趋势延续', signal: '多' },
  { time: '16:45', code: 'j2405', name: '焦炭', price: 2180, trend: '下降', pressure: 2220, support: 2140, entry: 2185, exit: 2120, confidence: 71, reason: '破位下行', signal: '空' },
  { time: '16:38', code: 'au2406', name: '黄金', price: 485, trend: '上升', pressure: 492, support: 478, entry: 484, exit: 495, confidence: 85, reason: '避险情绪', signal: '多' },
  { time: '16:32', code: 'ag2406', name: '白银', price: 5820, trend: '震荡', pressure: 5900, support: 5750, entry: null, exit: null, confidence: 52, reason: '区间整理', signal: '观望' },
  { time: '16:25', code: 'cu2405', name: '沪铜', price: 76500, trend: '上升', pressure: 77200, support: 75800, entry: 76400, exit: 77500, confidence: 75, reason: '需求回暖', signal: '多' },
]

// Generate IC data for all 31 factors with varying intensities
const generateICData = () => {
  return allFactorNames.map(name => ({
    factor: name,
    values: Array.from({ length: 30 }, () => (Math.random() - 0.5) * 0.4),
    avgIC: (Math.random() - 0.3) * 0.15,
    stdIC: Math.random() * 0.08 + 0.02,
    ir: (Math.random() * 2.5 + 0.5).toFixed(2),
    winRate: (Math.random() * 20 + 50).toFixed(1),
  }))
}

// IR ranking data
const irRankingData = [
  { factor: '价格动量', ir: 2.85, winRate: 68.5, calls: 156 },
  { factor: '相对强弱', ir: 2.42, winRate: 65.2, calls: 142 },
  { factor: '布林带', ir: 2.18, winRate: 62.8, calls: 128 },
  { factor: '放量', ir: 1.95, winRate: 61.5, calls: 98 },
  { factor: '趋势强度', ir: 1.78, winRate: 58.9, calls: 112 },
  { factor: 'MACD', ir: 1.52, winRate: 56.2, calls: 135 },
  { factor: '均值回复', ir: 1.35, winRate: 54.8, calls: 89 },
  { factor: 'ATR突破', ir: 1.12, winRate: 52.5, calls: 76 },
  { factor: '量价背离', ir: 0.95, winRate: 51.2, calls: 68 },
  { factor: 'KDJ', ir: 0.82, winRate: 49.8, calls: 145 },
]

// Confidence ranking data
const confidenceRanking = [
  { rank: 1, name: '动量突破策略', confidence: 92, expectedReturn: 3.2, risk: '低' },
  { rank: 2, name: '均线交叉策略', confidence: 88, expectedReturn: 2.8, risk: '低' },
  { rank: 3, name: '布林带反转', confidence: 85, expectedReturn: 2.5, risk: '中' },
  { rank: 4, name: '量价配合策略', confidence: 82, expectedReturn: 2.2, risk: '中' },
  { rank: 5, name: 'RSI超卖反弹', confidence: 78, expectedReturn: 1.9, risk: '中' },
  { rank: 6, name: '通道突破策略', confidence: 75, expectedReturn: 1.8, risk: '中' },
  { rank: 7, name: '趋势跟踪策略', confidence: 72, expectedReturn: 1.6, risk: '高' },
  { rank: 8, name: '震荡区间策略', confidence: 68, expectedReturn: 1.4, risk: '中' },
  { rank: 9, name: '套利策略', confidence: 65, expectedReturn: 1.2, risk: '低' },
  { rank: 10, name: '事件驱动策略', confidence: 62, expectedReturn: 1.0, risk: '高' },
]

// Factor contribution pie data (5 categories)
const factorContribution = [
  { name: '动量因子', value: 35, color: '#3b82f6' },
  { name: '均值回归', value: 25, color: '#8b5cf6' },
  { name: '成交量', value: 20, color: '#f59e0b' },
  { name: '突破因子', value: 12, color: '#22c55e' },
  { name: '波动率', value: 8, color: '#ef4444' },
]

// Complete 31 factor contribution (sorted by contribution descending)
const allFactorContributions = [
  // 动量类 (8 个) - 总贡献 35%
  { name: '价格动量', contribution: 12.5, category: '动量类', ir: 2.85 },
  { name: '相对强弱', contribution: 10.8, category: '动量类', ir: 2.42 },
  { name: '趋势强度', contribution: 7.8, category: '动量类', ir: 1.78 },
  { name: '动量突破', contribution: 6.2, category: '动量类', ir: 1.52 },
  { name: 'MACD', contribution: 5.5, category: '动量类', ir: 1.35 },
  { name: 'RSI', contribution: 4.8, category: '动量类', ir: 1.22 },
  { name: 'KDJ', contribution: 3.9, category: '动量类', ir: 1.08 },
  { name: 'CCI', contribution: 3.5, category: '动量类', ir: 0.95 },
  // 均值回归类 (6 个) - 总贡献 25%
  { name: '布林带', contribution: 9.2, category: '均值回归', ir: 2.18 },
  { name: '均值回复', contribution: 7.2, category: '均值回归', ir: 1.65 },
  { name: '乖离率', contribution: 4.5, category: '均值回归', ir: 1.28 },
  { name: 'Z-Score', contribution: 3.8, category: '均值回归', ir: 1.15 },
  { name: '百分位', contribution: 2.8, category: '均值回归', ir: 0.98 },
  { name: '标准差', contribution: 2.5, category: '均值回归', ir: 0.85 },
  // 成交量类 (6 个) - 总贡献 20%
  { name: '放量', contribution: 8.5, category: '成交量', ir: 1.95 },
  { name: '缩量', contribution: 6.1, category: '成交量', ir: 1.45 },
  { name: '量价背离', contribution: 3.8, category: '成交量', ir: 1.12 },
  { name: 'OBV', contribution: 2.9, category: '成交量', ir: 0.95 },
  { name: 'VWAP', contribution: 2.2, category: '成交量', ir: 0.82 },
  { name: '量比', contribution: 1.5, category: '成交量', ir: 0.68 },
  // 突破类 (5 个) - 总贡献 12%
  { name: '通道突破', contribution: 6.5, category: '突破类', ir: 1.52 },
  { name: '高低点突破', contribution: 4.2, category: '突破类', ir: 1.25 },
  { name: '唐奇安通道', contribution: 3.5, category: '突破类', ir: 1.08 },
  { name: 'ATR突破', contribution: 2.8, category: '突破类', ir: 0.92 },
  { name: '区间突破', contribution: 2.0, category: '突破类', ir: 0.75 },
  // 波动率类 (6 个) - 总贡献 8%
  { name: 'ATR', contribution: 3.2, category: '波动率', ir: 1.12 },
  { name: '历史波动率', contribution: 2.5, category: '波动率', ir: 0.95 },
  { name: '隐含波动率', contribution: 2.0, category: '波动率', ir: 0.82 },
  { name: '振幅', contribution: 1.8, category: '波动率', ir: 0.75 },
  { name: 'VIX', contribution: 1.2, category: '波动率', ir: 0.58 },
  { name: 'Parkinson', contribution: 0.8, category: '波动率', ir: 0.42 },
].sort((a, b) => b.contribution - a.contribution).map((f, i) => ({ ...f, rank: i + 1 }))

// Category to factors mapping for drilldown
const categoryFactors: Record<string, typeof allFactorContributions> = {
  '动量因子': allFactorContributions.filter(f => f.category === '动量类'),
  '均值回归': allFactorContributions.filter(f => f.category === '均值回归'),
  '成交量': allFactorContributions.filter(f => f.category === '成交量'),
  '突破因子': allFactorContributions.filter(f => f.category === '突破类'),
  '波动率': allFactorContributions.filter(f => f.category === '波动率'),
}

// Backtest comparison data
const backtestData = Array.from({ length: 90 }, (_, i) => {
  const date = new Date()
  date.setDate(date.getDate() - (89 - i))
  return {
    date: `${date.getMonth() + 1}/${date.getDate()}`,
    live: Math.round(10000 + i * 120 + Math.sin(i * 0.2) * 1500 + Math.random() * 500),
    backtest: Math.round(10000 + i * 135 + Math.sin(i * 0.2) * 1200 + Math.random() * 300),
  }
})

const comparisonMetrics = [
  { metric: '交易次数', live: '125 笔', backtest: '156 笔', deviation: '-31 笔', negGood: false },
  { metric: '胜率',    live: '58.5%',  backtest: '62.0%',  deviation: '-3.5%',  negGood: false },
  { metric: '盈亏比',  live: '1.8',    backtest: '2.1',    deviation: '-0.3',   negGood: false },
  { metric: '最大回撤',live: '-8.2%',  backtest: '-6.5%',  deviation: '-1.7%',  negGood: true  },
  { metric: '夏普比率',live: '2.1',    backtest: '2.5',    deviation: '-0.4',   negGood: false },
  { metric: '年化收益',live: '+42.3%', backtest: '+51.8%', deviation: '-9.5%',  negGood: false },
  { metric: '盈利因子',live: '1.85',   backtest: '2.12',   deviation: '-0.27',  negGood: false },
]

// Futures varieties for backtest
const futuresVarieties = [
  { id: 'rb2405', name: '螺纹钢', checked: true },
  { id: 'hc2405', name: '热卷', checked: true },
  { id: 'i2405', name: '铁矿石', checked: false },
  { id: 'j2405', name: '焦炭', checked: false },
  { id: 'm2405', name: '豆粕', checked: false },
  { id: 'au2406', name: '黄金', checked: false },
  { id: 'ag2406', name: '白银', checked: false },
  { id: 'cu2405', name: '沪铜', checked: false },
]

export function StrategyFutures({ onBack }: StrategyFuturesProps) {
  const { toast } = useToast()
  const [factors, setFactors] = useState(factorCategories)
  const [selectedVariety, setSelectedVariety] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showResult, setShowResult] = useState(false)
  const [signalFilter, setSignalFilter] = useState({ variety: '全部', direction: '全部', confidence: '全部' })
  const [selectedICFactor, setSelectedICFactor] = useState<string | null>(null)
  const [contributionView, setContributionView] = useState<'summary' | 'detail' | 'category'>('summary')
  const [drilldownCategory, setDrilldownCategory] = useState<string | null>(null)

  // CSV Export helper
  const exportCSV = (data: Record<string, unknown>[], filename: string) => {
    if (data.length === 0) {
      toast({ title: "导出失败", description: "没有数据可导出", variant: "destructive" })
      return
    }
    const headers = Object.keys(data[0]).join(',')
    const rows = data.map(row => Object.values(row).join(','))
    const csv = '\uFEFF' + [headers, ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
    toast({ title: "导出成功", description: `已导出 ${data.length} 条记录` })
  }

  const exportSignals = () => {
    const data = signalData.map(s => ({
      '时间': s.time,
      '代码': s.code,
      '名称': s.name,
      '现价': s.price,
      '趋势': s.trend,
      '压力位': s.pressure,
      '支撑位': s.support,
      '建议入场': s.entry || '-',
      '建议出场': s.exit || '-',
      '置信度': `${s.confidence}%`,
      '推荐理由': s.reason,
      '信号': s.signal
    }))
    exportCSV(data, '期货策略信号')
  }

  const exportFactorContribution = () => {
    const data = allFactorContributions.map(f => ({
      '排名': f.rank,
      '因子名称': f.name,
      '贡献度': `${f.contribution}%`,
      '所属类别': f.category,
      'IR比率': f.ir
    }))
    exportCSV(data, '因子贡献度')
  }

  const exportBacktest = () => {
    const data = comparisonMetrics.map(m => ({
      '指标': m.metric,
      '实盘': m.live,
      '回测': m.backtest,
      '偏离': m.deviation
    }))
    exportCSV(data, '回测报告')
  }
  
  // Backtest state
  const [backtestStartDate, setBacktestStartDate] = useState('2025-01-01')
  const [backtestEndDate, setBacktestEndDate] = useState('2025-03-21')
  const [backtestFactors, setBacktestFactors] = useState(factorCategories.map(c => ({ ...c, factors: c.factors.map(f => ({ ...f, checked: false })) })))
  const [backtestVarieties, setBacktestVarieties] = useState(futuresVarieties)
  const [backtestParams, setBacktestParams] = useState({ capital: 500000, maxPosition: 20, stopLoss: -5, takeProfit: 10, fee: 1 })
  const [showBacktestResult, setShowBacktestResult] = useState(false)

  const selectedCount = useMemo(() => 
    factors.reduce((acc, cat) => acc + cat.factors.filter(f => f.checked).length, 0)
  , [factors])

  const backtestSelectedFactorCount = useMemo(() =>
    backtestFactors.reduce((acc, cat) => acc + cat.factors.filter(f => f.checked).length, 0)
  , [backtestFactors])

  const backtestSelectedVarietyCount = useMemo(() =>
    backtestVarieties.filter(v => v.checked).length
  , [backtestVarieties])

  const toggleFactor = (catIndex: number, factorIndex: number) => {
    setFactors(prev => {
      const newFactors = [...prev]
      newFactors[catIndex] = {
        ...newFactors[catIndex],
        factors: newFactors[catIndex].factors.map((f, i) => 
          i === factorIndex ? { ...f, checked: !f.checked } : f
        )
      }
      return newFactors
    })
  }

  const toggleBacktestFactor = (catIndex: number, factorIndex: number) => {
    setBacktestFactors(prev => {
      const newFactors = [...prev]
      newFactors[catIndex] = {
        ...newFactors[catIndex],
        factors: newFactors[catIndex].factors.map((f, i) => 
          i === factorIndex ? { ...f, checked: !f.checked } : f
        )
      }
      return newFactors
    })
  }

  const toggleBacktestVariety = (index: number) => {
    setBacktestVarieties(prev => prev.map((v, i) => i === index ? { ...v, checked: !v.checked } : v))
  }

  const runCalculation = () => {
    setShowResult(true)
  }

  const resetCalculation = () => {
    setShowResult(false)
    setSelectedVariety('')
  }

  const runBacktest = () => {
    setShowBacktestResult(true)
  }

  const resetBacktest = () => {
    setShowBacktestResult(false)
    setBacktestFactors(factorCategories.map(c => ({ ...c, factors: c.factors.map(f => ({ ...f, checked: false })) })))
    setBacktestVarieties(futuresVarieties.map(v => ({ ...v, checked: false })))
  }

  const setQuickDate = (range: string) => {
    const end = new Date()
    const start = new Date()
    switch (range) {
      case '1m': start.setMonth(start.getMonth() - 1); break
      case '3m': start.setMonth(start.getMonth() - 3); break
      case '6m': start.setMonth(start.getMonth() - 6); break
      case '1y': start.setFullYear(start.getFullYear() - 1); break
      case 'all': start.setFullYear(2020, 0, 1); break
    }
    setBacktestStartDate(start.toISOString().split('T')[0])
    setBacktestEndDate(end.toISOString().split('T')[0])
  }

  const icData = useMemo(() => generateICData(), [])

  const filteredSignals = signalData.filter(s => {
    if (signalFilter.direction !== '全部' && s.signal !== signalFilter.direction) return false
    if (signalFilter.confidence === '>80%' && s.confidence <= 80) return false
    if (signalFilter.confidence === '70-80%' && (s.confidence < 70 || s.confidence > 80)) return false
    if (signalFilter.confidence === '<70%' && s.confidence >= 70) return false
    return true
  })

  // Get IC color based on value - varying opacity
  const getICColor = (value: number) => {
    const absValue = Math.abs(value)
    const opacity = Math.min(absValue * 5, 1) // Scale opacity: 0.2 IC = full opacity
    if (value > 0) {
      return `rgba(239, 68, 68, ${0.2 + opacity * 0.8})` // Red for positive
    } else {
      return `rgba(34, 197, 94, ${0.2 + opacity * 0.8})` // Green for negative
    }
  }

  return (
    <div className="p-6 space-y-6 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-muted-foreground" />
          </button>
          <div>
            <h1 className="text-xl font-semibold text-foreground">策略信号 - 中国期货</h1>
            <p className="text-xs text-muted-foreground mt-0.5">手动因子测算、信号生成与回测分析</p>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button className="flex items-center gap-2">
              <FileDown className="w-4 h-4" />
              导出报表
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={exportSignals}>
              <Download className="w-4 h-4 mr-2" />
              导出策略信号
            </DropdownMenuItem>
            <DropdownMenuItem onClick={exportFactorContribution}>
              <Download className="w-4 h-4 mr-2" />
              导出因子贡献度
            </DropdownMenuItem>
            <DropdownMenuItem onClick={exportBacktest}>
              <Download className="w-4 h-4 mr-2" />
              导出回测报告
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Row 1: KPI Cards - 2行 x 4列 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-3"
      >
        {[
          { label: '今日信号总数', value: kpiData.todaySignals, icon: Activity },
          { label: '多头信号', value: kpiData.longSignals, positive: true, icon: TrendingUp },
          { label: '空头信号', value: kpiData.shortSignals, negative: true, icon: TrendingDown },
          { label: '中性信号', value: kpiData.neutralSignals, neutral: true, icon: Target },
          { label: '平均置信度', value: `${kpiData.avgConfidence}%`, icon: Percent },
          { label: '高置信度(>80%)', value: `${kpiData.highConfidence}个`, icon: Sparkles },
          { label: '预期收益', value: `+${kpiData.expectedReturn.toLocaleString()}`, positive: true, icon: Trophy },
          { label: '风险等级', value: kpiData.riskLevel, neutral: true, icon: AlertTriangle },
        ].map((kpi, i) => (
          <div key={i} className="card-surface p-4 flex flex-col items-center justify-center text-center min-h-[100px]">
            <div className="flex items-center gap-1.5 mb-2">
              <kpi.icon className={cn(
                'w-4 h-4',
                kpi.positive && 'text-red-500',
                kpi.negative && 'text-emerald-500',
                kpi.neutral && 'text-amber-500',
                !kpi.positive && !kpi.negative && !kpi.neutral && 'text-primary'
              )} />
              <span className="text-xs text-muted-foreground">{kpi.label}</span>
            </div>
            <p className={cn(
              'text-xl font-semibold font-mono',
              kpi.positive && 'text-red-600',
              kpi.negative && 'text-emerald-600',
              kpi.neutral && 'text-amber-600',
              !kpi.positive && !kpi.negative && !kpi.neutral && 'text-foreground'
            )}>
              {kpi.value}
            </p>
          </div>
        ))}
      </motion.div>

      {/* Row 2: Manual Factor Calculation Tool - NO SCROLLBAR */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card-surface p-5"
      >
        <div className="flex items-center gap-2 mb-4">
          <FlaskConical className="w-5 h-5 text-primary" />
          <h3 className="text-sm font-semibold text-foreground tracking-tight">手动因子测算（沙盒环境）</h3>
        </div>
        <div className="flex items-center gap-2 mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
          <Lightbulb className="w-4 h-4 text-amber-500 shrink-0" />
          <p className="text-xs text-amber-600 dark:text-amber-400">此处修改的参数仅本次测算使用，不会保存到系统配置</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Step 1: Select Factors - NO SCROLLBAR */}
          <div>
            <h4 className="text-xs font-medium text-muted-foreground mb-3">步骤 1: 选择因子（共31个）</h4>
            <div className="space-y-3">
              {factors.map((category, catIndex) => (
                <div key={category.name} className="p-3 bg-muted/30 rounded-lg">
                  <p className="text-[11px] font-medium text-muted-foreground mb-2">{category.name} ({category.factors.length}个)</p>
                  <div className="flex flex-wrap gap-2">
                    {category.factors.map((factor, factorIndex) => (
                      <button
                        key={factor.id}
                        onClick={() => toggleFactor(catIndex, factorIndex)}
                        className={cn(
                          'px-2.5 py-1 text-[11px] rounded-md border transition-colors',
                          factor.checked 
                            ? 'bg-primary text-primary-foreground border-primary' 
                            : 'bg-background border-border text-muted-foreground hover:border-primary/50'
                        )}
                      >
                        {factor.checked && <Check className="w-3 h-3 inline mr-1" />}
                        {factor.name}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-2">已选择：{selectedCount} 个因子</p>
          </div>

          {/* Step 2 & 3: Parameters & Variety */}
          <div className="space-y-4">
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-3">步骤 2: 设置参数</h4>
              <div className="space-y-3">
                <div className="p-3 bg-muted/30 rounded-lg">
                  <p className="text-[11px] font-medium text-foreground mb-2">动量因子</p>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="text-[10px] text-muted-foreground">回看周期</label>
                      <select className="w-full mt-1 px-2 py-1 text-xs bg-background border border-border rounded">
                        <option>20 天</option>
                        <option>10 天</option>
                        <option>30 天</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground">入场阈值</label>
                      <select className="w-full mt-1 px-2 py-1 text-xs bg-background border border-border rounded">
                        <option>0.5</option>
                        <option>0.3</option>
                        <option>0.7</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground">出场阈值</label>
                      <select className="w-full mt-1 px-2 py-1 text-xs bg-background border border-border rounded">
                        <option>0.3</option>
                        <option>0.2</option>
                        <option>0.5</option>
                      </select>
                    </div>
                  </div>
                </div>
                <div className="p-3 bg-muted/30 rounded-lg">
                  <p className="text-[11px] font-medium text-foreground mb-2">均值回归因子</p>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] text-muted-foreground">均值周期</label>
                      <select className="w-full mt-1 px-2 py-1 text-xs bg-background border border-border rounded">
                        <option>30 天</option>
                        <option>20 天</option>
                        <option>60 天</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground">标准差倍数</label>
                      <select className="w-full mt-1 px-2 py-1 text-xs bg-background border border-border rounded">
                        <option>2.0</option>
                        <option>1.5</option>
                        <option>2.5</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
              <button className="mt-2 text-xs text-primary hover:underline">恢复默认值</button>
            </div>

            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-3">步骤 3: 选择品种</h4>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="输入品种代码或名称（如 rb2405 螺纹钢）"
                  value={selectedVariety}
                  onChange={(e) => setSelectedVariety(e.target.value)}
                  className="w-full pl-9 pr-4 py-2.5 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>
              {selectedVariety && (
                <div className="mt-2 p-2 bg-muted/30 rounded-lg">
                  <div className="flex items-center justify-between p-2 hover:bg-muted rounded cursor-pointer">
                    <div>
                      <span className="text-xs font-mono font-medium">rb2405</span>
                      <span className="text-xs text-muted-foreground ml-2">螺纹钢 主力合约</span>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-mono">3,520</span>
                      <span className="text-xs text-red-500 ml-2">+2.5%</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Step 4: Run */}
            <div className="flex gap-3 pt-2">
              <button
                onClick={runCalculation}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
              >
                <Play className="w-4 h-4" />
                运行测算
              </button>
              <button
                onClick={resetCalculation}
                className="px-4 py-2.5 bg-muted text-muted-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Calculation Result */}
        {showResult && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-6 pt-6 border-t border-border"
          >
            <h4 className="text-sm font-semibold text-foreground mb-4">测算结果</h4>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-center">
                <p className="text-[10px] text-muted-foreground mb-1">信号方向</p>
                <p className="text-lg font-semibold text-red-600">多</p>
              </div>
              <div className="p-3 bg-muted/30 rounded-lg text-center">
                <p className="text-[10px] text-muted-foreground mb-1">置信度</p>
                <p className="text-lg font-semibold font-mono">78%</p>
              </div>
              <div className="p-3 bg-muted/30 rounded-lg text-center">
                <p className="text-[10px] text-muted-foreground mb-1">预期收益</p>
                <p className="text-lg font-semibold font-mono text-red-600">+2.4%</p>
              </div>
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-center">
                <p className="text-[10px] text-muted-foreground mb-1">风险等级</p>
                <p className="text-lg font-semibold text-amber-600">中等</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground mb-2">因子贡献度</p>
                <div className="space-y-2">
                  {[
                    { name: '动量因子', value: 85 },
                    { name: '均值回归', value: 45 },
                    { name: '突破因子', value: 62 },
                    { name: '成交量', value: 55 },
                  ].map((f) => (
                    <div key={f.name} className="flex items-center gap-2">
                      <span className="text-[11px] text-muted-foreground w-16">{f.name}</span>
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-primary rounded-full transition-all"
                          style={{ width: `${f.value}%` }}
                        />
                      </div>
                      <span className="text-[11px] font-mono w-8 text-right">{f.value}%</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">开仓建议</span>
                  <span className="font-mono">3,520 附近</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">止损位</span>
                  <span className="font-mono text-emerald-600">3,480</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">目标位</span>
                  <span className="font-mono text-red-600">3,580</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">持仓周期</span>
                  <span className="font-mono">3-5 个交易日</span>
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-4">
              <button className="px-3 py-1.5 text-xs bg-muted text-foreground rounded hover:bg-muted/80 transition-colors">
                导出结果
              </button>
              <button className="px-3 py-1.5 text-xs bg-muted text-foreground rounded hover:bg-muted/80 transition-colors">
                重新测算
              </button>
              <button className="px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors">
                加入跟踪
              </button>
            </div>
          </motion.div>
        )}
      </motion.div>

      {/* Row 3: IC Heatmap (31 factors) & IR Ranking */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* IC Heatmap - 31 factors with click details */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-3 card-surface p-5"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground tracking-tight">因子 IC 热力图（近30交易日）</h3>
            <select className="text-xs px-2 py-1 bg-muted border-0 rounded">
              <option>IC 降序</option>
              <option>IC 升序</option>
              <option>名称</option>
            </select>
          </div>
          <div className="overflow-x-auto">
            <div className="w-full">
              <div className="flex mb-1">
                <div className="w-20 shrink-0" />
                {Array.from({ length: 30 }, (_, i) => (
                  <div key={i} className="flex-1 text-[8px] text-muted-foreground text-center">
                    {i + 1}
                  </div>
                ))}
              </div>
              {icData.map((row) => (
                <div 
                  key={row.factor} 
                  className={cn(
                    "flex mb-0.5 cursor-pointer transition-opacity",
                    selectedICFactor && selectedICFactor !== row.factor && "opacity-40"
                  )}
                  onClick={() => setSelectedICFactor(selectedICFactor === row.factor ? null : row.factor)}
                >
                  <div className="w-20 shrink-0 text-[10px] text-muted-foreground truncate pr-1 hover:text-foreground">
                    {row.factor}
                  </div>
                  {row.values.map((v, i) => (
                    <div
                      key={i}
                      className="flex-1 h-5 rounded-sm mx-px cursor-pointer hover:ring-1 hover:ring-primary transition-colors"
                      style={{ backgroundColor: getICColor(v) }}
                      title={`IC: ${v.toFixed(3)}`}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>
          <div className="flex items-center justify-center gap-4 mt-3 text-[10px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 bg-emerald-500 rounded-sm" /> 负IC
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 bg-red-500 rounded-sm" /> 正IC
            </span>
          </div>

          {/* IC Detail Panel */}
          <AnimatePresence>
            {selectedICFactor && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4 pt-4 border-t border-border"
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-semibold text-foreground">因子详情：{selectedICFactor}</h4>
                  <button 
                    onClick={() => setSelectedICFactor(null)}
                    className="p-1 hover:bg-muted rounded"
                  >
                    <X className="w-3.5 h-3.5 text-muted-foreground" />
                  </button>
                </div>
                {(() => {
                  const data = icData.find(d => d.factor === selectedICFactor)
                  if (!data) return null
                  return (
                    <div className="grid grid-cols-4 gap-3">
                      <div className="p-2 bg-muted/30 rounded text-center">
                        <p className="text-[10px] text-muted-foreground">平均 IC</p>
                        <p className="text-sm font-mono font-semibold">{data.avgIC.toFixed(4)}</p>
                      </div>
                      <div className="p-2 bg-muted/30 rounded text-center">
                        <p className="text-[10px] text-muted-foreground">IC 标准差</p>
                        <p className="text-sm font-mono font-semibold">{data.stdIC.toFixed(4)}</p>
                      </div>
                      <div className="p-2 bg-muted/30 rounded text-center">
                        <p className="text-[10px] text-muted-foreground">IR 比率</p>
                        <p className="text-sm font-mono font-semibold">{data.ir}</p>
                      </div>
                      <div className="p-2 bg-muted/30 rounded text-center">
                        <p className="text-[10px] text-muted-foreground">胜率</p>
                        <p className="text-sm font-mono font-semibold">{data.winRate}%</p>
                      </div>
                    </div>
                  )
                })()}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* IR Ranking */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="card-surface p-5"
        >
          <h3 className="text-sm font-semibold text-foreground tracking-tight mb-4">因子 IR 比率排行（近30日）</h3>
          <div className="space-y-2">
            {irRankingData.map((item, i) => (
              <div key={item.factor} className="flex items-center gap-3 p-2 bg-muted/30 rounded-lg">
                <span className={cn(
                  'w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-medium',
                  i < 3 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                )}>
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-foreground truncate">{item.factor}</p>
                  <p className="text-[10px] text-muted-foreground">胜率 {item.winRate}% · {item.calls}次</p>
                </div>
                <span className={cn(
                  'text-sm font-mono font-semibold',
                  item.ir >= 2 ? 'text-emerald-600' : item.ir >= 1 ? 'text-amber-600' : 'text-red-600'
                )}>
                  {item.ir.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Row 4: Signal List */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card-surface p-5"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-foreground tracking-tight">策略信号列表</h3>
          <div className="flex items-center gap-2">
            <select 
              value={signalFilter.direction}
              onChange={(e) => setSignalFilter(p => ({ ...p, direction: e.target.value }))}
              className="text-xs px-2 py-1.5 bg-muted border-0 rounded"
            >
              <option value="全部">全部方向</option>
              <option value="多">多</option>
              <option value="空">空</option>
              <option value="观望">观望</option>
            </select>
            <select
              value={signalFilter.confidence}
              onChange={(e) => setSignalFilter(p => ({ ...p, confidence: e.target.value }))}
              className="text-xs px-2 py-1.5 bg-muted border-0 rounded"
            >
              <option value="全部">全部置信度</option>
              <option value=">80%">{'>'}80%</option>
              <option value="70-80%">70-80%</option>
              <option value="<70%">{'<'}70%</option>
            </select>
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <input
                type="text"
                placeholder="搜索..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-7 pr-3 py-1.5 text-xs bg-muted border-0 rounded w-32 focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <button className="flex items-center gap-1 px-2 py-1.5 text-xs bg-muted rounded hover:bg-muted/80 transition-colors">
              <Download className="w-3.5 h-3.5" />
              导出
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs min-w-[1100px]">
            <thead>
              <tr className="border-b border-border">
                <th className="py-2 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">时间</th>
                <th className="py-2 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">代码</th>
                <th className="py-2 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">名称</th>
                <th className="py-2 px-2 text-right font-medium text-muted-foreground whitespace-nowrap">当前价</th>
                <th className="py-2 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">趋势</th>
                <th className="py-2 px-2 text-right font-medium text-muted-foreground whitespace-nowrap">压力位</th>
                <th className="py-2 px-2 text-right font-medium text-muted-foreground whitespace-nowrap">支撑位</th>
                <th className="py-2 px-2 text-right font-medium text-muted-foreground whitespace-nowrap">开仓价</th>
                <th className="py-2 px-2 text-right font-medium text-muted-foreground whitespace-nowrap">平仓价</th>
                <th className="py-2 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">置信度</th>
                <th className="py-2 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">推荐理由</th>
                <th className="py-2 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredSignals.map((signal, i) => (
                <tr key={i} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                  <td className="py-3 px-2 font-mono text-muted-foreground whitespace-nowrap">{signal.time}</td>
                  <td className="py-3 px-2 font-mono font-medium text-primary cursor-pointer hover:underline whitespace-nowrap">{signal.code}</td>
                  <td className="py-3 px-2 whitespace-nowrap">{signal.name}</td>
                  <td className="py-3 px-2 text-right font-mono whitespace-nowrap">{signal.price.toLocaleString()}</td>
                  <td className="py-3 px-2 text-center whitespace-nowrap">
                    <span className={cn(
                      'px-1.5 py-0.5 rounded text-[10px]',
                      signal.trend === '上升' && 'bg-red-500/10 text-red-600',
                      signal.trend === '下降' && 'bg-emerald-500/10 text-emerald-600',
                      signal.trend === '震荡' && 'bg-amber-500/10 text-amber-600'
                    )}>
                      {signal.trend}
                    </span>
                  </td>
                  <td className="py-3 px-2 text-right font-mono text-muted-foreground whitespace-nowrap">{signal.pressure}</td>
                  <td className="py-3 px-2 text-right font-mono text-muted-foreground whitespace-nowrap">{signal.support}</td>
                  <td className="py-3 px-2 text-right font-mono whitespace-nowrap">{signal.entry ?? '-'}</td>
                  <td className="py-3 px-2 text-right font-mono whitespace-nowrap">{signal.exit ?? '-'}</td>
                  <td className="py-3 px-2 whitespace-nowrap">
                    <div className="flex items-center gap-1.5 justify-center">
                      <div className="w-12 h-1.5 bg-muted rounded-full overflow-hidden">
                        <div 
                          className={cn(
                            'h-full rounded-full',
                            signal.confidence >= 80 ? 'bg-emerald-500' : signal.confidence >= 70 ? 'bg-amber-500' : 'bg-red-500'
                          )}
                          style={{ width: `${signal.confidence}%` }}
                        />
                      </div>
                      <span className="text-[10px] font-mono">{signal.confidence}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-muted-foreground whitespace-nowrap">{signal.reason}</td>
                  <td className="py-3 px-2 text-center whitespace-nowrap">
                    <button className="px-2 py-1 text-[10px] bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors">
                      查看
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Row 5: Confidence Ranking & Factor Contribution Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: Confidence Ranking */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="card-surface p-5 flex flex-col"
        >
          <h3 className="text-sm font-semibold text-foreground tracking-tight mb-4">策略置信度排名 Top10</h3>
          <div className="space-y-2 flex-1">
            {confidenceRanking.map((item) => (
              <div key={item.rank} className="flex items-center gap-3 p-2 bg-muted/30 rounded-lg">
                <span className={cn(
                  'w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-semibold',
                  item.rank === 1 && 'bg-amber-400 text-amber-900',
                  item.rank === 2 && 'bg-gray-300 text-gray-700',
                  item.rank === 3 && 'bg-amber-600 text-amber-100',
                  item.rank > 3 && 'bg-muted text-muted-foreground'
                )}>
                  {item.rank}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-foreground truncate">{item.name}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-mono font-semibold">{item.confidence}%</p>
                  <p className="text-[10px] text-muted-foreground">+{item.expectedReturn}% · {item.risk}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Right: Factor Contribution Analysis - 3 View States */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card-surface p-5 flex flex-col"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground tracking-tight">因子贡献度分析</h3>
            {contributionView === 'summary' ? (
              <button 
                onClick={() => setContributionView('detail')}
                className="flex items-center gap-1 text-xs text-primary hover:underline"
              >
                查看全部
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button 
                onClick={() => {
                  setContributionView('summary')
                  setDrilldownCategory(null)
                }}
                className="flex items-center gap-1 text-xs text-primary hover:underline"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                返回汇总
              </button>
            )}
          </div>

          <AnimatePresence mode="wait">
            {/* View 1: Summary - Donut Chart with Category List */}
            {contributionView === 'summary' && (
              <motion.div
                key="summary"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="flex-1 flex flex-col"
              >
                <div className="flex items-center gap-6 flex-1">
                  <div className="w-36 h-36 shrink-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={factorContribution}
                          cx="50%"
                          cy="50%"
                          innerRadius={35}
                          outerRadius={58}
                          paddingAngle={2}
                          dataKey="value"
                          onClick={(_, index) => {
                            setDrilldownCategory(factorContribution[index].name)
                            setContributionView('category')
                          }}
                          style={{ cursor: 'pointer' }}
                        >
                          {factorContribution.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip 
                          formatter={(value: number) => [`${value}%`, '贡献度']}
                          contentStyle={{ 
                            backgroundColor: 'hsl(var(--card))', 
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '8px',
                            fontSize: '12px'
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex-1 space-y-2">
                    {factorContribution.map((item) => (
                      <button 
                        key={item.name} 
                        onClick={() => {
                          setDrilldownCategory(item.name)
                          setContributionView('category')
                        }}
                        className="flex items-center gap-2 w-full hover:bg-muted/30 rounded px-1 py-0.5 transition-colors"
                      >
                        <span 
                          className="w-3 h-3 rounded-sm shrink-0"
                          style={{ backgroundColor: item.color }}
                        />
                        <span className="text-xs text-muted-foreground flex-1 text-left">{item.name}</span>
                        <span className="text-xs font-mono font-medium">{item.value}%</span>
                      </button>
                    ))}
                  </div>
                </div>
                <p className="text-[10px] text-muted-foreground mt-3">点击类别查看该类别下的具体因子</p>
              </motion.div>
            )}

            {/* View 2: Detail - All 31 Factors Ranking */}
            {contributionView === 'detail' && (
              <motion.div
                key="detail"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="flex-1 flex flex-col"
              >
                <p className="text-xs text-muted-foreground mb-2">因子贡献度排行 Top31</p>
                <div className="space-y-1 flex-1 overflow-y-auto pr-1">
                  {allFactorContributions.map((item) => (
                    <div key={item.rank} className="flex items-center gap-2 p-1.5 bg-muted/30 rounded">
                      <span className={cn(
                        'w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-semibold shrink-0',
                        item.rank === 1 && 'bg-amber-400 text-amber-900',
                        item.rank === 2 && 'bg-gray-300 text-gray-700',
                        item.rank === 3 && 'bg-amber-600 text-amber-100',
                        item.rank > 3 && 'bg-muted text-muted-foreground'
                      )}>
                        {item.rank}
                      </span>
                      <span className="text-[11px] font-medium flex-1 truncate">{item.name}</span>
                      <span className="text-[10px] text-muted-foreground px-1.5 py-0.5 bg-muted/50 rounded">{item.category}</span>
                      <span className="text-[11px] font-mono w-10 text-right">{item.contribution}%</span>
                      <span className="text-[10px] font-mono text-muted-foreground w-12 text-right">IR:{item.ir}</span>
                    </div>
                  ))}
                </div>
                <button className="mt-2 text-xs text-primary hover:underline flex items-center gap-1 self-start">
                  <Download className="w-3 h-3" />
                  导出因子贡献报告
                </button>
              </motion.div>
            )}

            {/* View 3: Category Drilldown - Specific Category Factors */}
            {contributionView === 'category' && drilldownCategory && (
              <motion.div
                key="category"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="flex-1 flex flex-col"
              >
                <div className="flex items-center gap-2 mb-3">
                  <span 
                    className="w-3 h-3 rounded-sm"
                    style={{ backgroundColor: factorContribution.find(f => f.name === drilldownCategory)?.color }}
                  />
                  <p className="text-xs font-medium">{drilldownCategory}贡献度明细</p>
                  <span className="text-xs text-muted-foreground ml-auto">
                    总贡献：{factorContribution.find(f => f.name === drilldownCategory)?.value}%
                  </span>
                </div>
                <div className="space-y-2 flex-1">
                  {(categoryFactors[drilldownCategory] || []).map((item, idx) => (
                    <div key={item.name} className="flex items-center gap-2">
                      <span className="text-[10px] text-muted-foreground w-4">{idx + 1}</span>
                      <span className="text-xs font-medium w-20 truncate">{item.name}</span>
                      <div className="flex-1 h-2 bg-muted/50 rounded-full overflow-hidden">
                        <div 
                          className="h-full rounded-full transition-all"
                          style={{ 
                            width: `${(item.contribution / 15) * 100}%`,
                            backgroundColor: factorContribution.find(f => f.name === drilldownCategory)?.color
                          }}
                        />
                      </div>
                      <span className="text-[11px] font-mono w-12 text-right">{item.contribution}%</span>
                      <span className="text-[10px] font-mono text-muted-foreground w-12 text-right">IR:{item.ir}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Row 6: Manual Backtest Module */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
        className="card-surface p-5"
      >
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-primary" />
          <h3 className="text-sm font-semibold text-foreground tracking-tight">手动回测</h3>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Steps 1-4 */}
          <div className="space-y-4">
            {/* Step 1: Date Range */}
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">步骤 1: 选择回测区间</h4>
              <div className="flex gap-2 mb-2">
                <div className="flex-1">
                  <label className="text-[10px] text-muted-foreground">开始日期</label>
                  <input
                    type="date"
                    value={backtestStartDate}
                    onChange={(e) => setBacktestStartDate(e.target.value)}
                    className="w-full mt-1 px-2 py-1.5 text-xs bg-background border border-border rounded"
                  />
                </div>
                <div className="flex-1">
                  <label className="text-[10px] text-muted-foreground">结束日期</label>
                  <input
                    type="date"
                    value={backtestEndDate}
                    onChange={(e) => setBacktestEndDate(e.target.value)}
                    className="w-full mt-1 px-2 py-1.5 text-xs bg-background border border-border rounded"
                  />
                </div>
              </div>
              <div className="flex gap-1.5">
                {[
                  { label: '近 1 月', value: '1m' },
                  { label: '近 3 月', value: '3m' },
                  { label: '近 6 月', value: '6m' },
                  { label: '近 1 年', value: '1y' },
                  { label: '全部', value: 'all' },
                ].map((btn) => (
                  <button
                    key={btn.value}
                    onClick={() => setQuickDate(btn.value)}
                    className="px-2 py-1 text-[10px] bg-muted text-muted-foreground rounded hover:bg-muted/80 transition-colors"
                  >
                    {btn.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Step 2: Factor Selection */}
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">步骤 2: 选择因子组合</h4>
              <div className="space-y-2">
                {backtestFactors.map((category, catIndex) => (
                  <div key={category.name} className="flex flex-wrap gap-1.5">
                    {category.factors.map((factor, factorIndex) => (
                      <button
                        key={factor.id}
                        onClick={() => toggleBacktestFactor(catIndex, factorIndex)}
                        className={cn(
                          'px-2 py-0.5 text-[10px] rounded border transition-colors',
                          factor.checked 
                            ? 'bg-primary/10 text-primary border-primary' 
                            : 'bg-background border-border text-muted-foreground hover:border-primary/50'
                        )}
                      >
                        {factor.checked && <Check className="w-2.5 h-2.5 inline mr-0.5" />}
                        {factor.name}
                      </button>
                    ))}
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">已选择：{backtestSelectedFactorCount} 个因子</p>
            </div>

            {/* Step 3: Variety Selection */}
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">步骤 3: 选择品种</h4>
              <div className="flex flex-wrap gap-1.5">
                {backtestVarieties.map((variety, index) => (
                  <button
                    key={variety.id}
                    onClick={() => toggleBacktestVariety(index)}
                    className={cn(
                      'px-2 py-0.5 text-[10px] rounded border transition-colors',
                      variety.checked 
                        ? 'bg-primary/10 text-primary border-primary' 
                        : 'bg-background border-border text-muted-foreground hover:border-primary/50'
                    )}
                  >
                    {variety.checked && <Check className="w-2.5 h-2.5 inline mr-0.5" />}
                    {variety.id} {variety.name}
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">已选择：{backtestSelectedVarietyCount} 个品种</p>
            </div>
          </div>

          {/* Right: Step 4 & 5 */}
          <div className="space-y-4">
            {/* Step 4: Parameters */}
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">步骤 4: 设置参数</h4>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-muted-foreground">初始资金</label>
                  <input
                    type="number"
                    value={backtestParams.capital}
                    onChange={(e) => setBacktestParams(p => ({ ...p, capital: Number(e.target.value) }))}
                    className="w-full mt-1 px-2 py-1.5 text-xs bg-background border border-border rounded font-mono"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-muted-foreground">单笔最大仓位 (%)</label>
                  <input
                    type="number"
                    value={backtestParams.maxPosition}
                    onChange={(e) => setBacktestParams(p => ({ ...p, maxPosition: Number(e.target.value) }))}
                    className="w-full mt-1 px-2 py-1.5 text-xs bg-background border border-border rounded font-mono"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-muted-foreground">止损位 (%)</label>
                  <input
                    type="number"
                    value={backtestParams.stopLoss}
                    onChange={(e) => setBacktestParams(p => ({ ...p, stopLoss: Number(e.target.value) }))}
                    className="w-full mt-1 px-2 py-1.5 text-xs bg-background border border-border rounded font-mono"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-muted-foreground">止盈位 (%)</label>
                  <input
                    type="number"
                    value={backtestParams.takeProfit}
                    onChange={(e) => setBacktestParams(p => ({ ...p, takeProfit: Number(e.target.value) }))}
                    className="w-full mt-1 px-2 py-1.5 text-xs bg-background border border-border rounded font-mono"
                  />
                </div>
                <div className="col-span-2">
                  <label className="text-[10px] text-muted-foreground">交易成本（万分之）</label>
                  <input
                    type="number"
                    value={backtestParams.fee}
                    onChange={(e) => setBacktestParams(p => ({ ...p, fee: Number(e.target.value) }))}
                    className="w-full mt-1 px-2 py-1.5 text-xs bg-background border border-border rounded font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Step 5: Run */}
            <div className="flex gap-3">
              <button
                onClick={runBacktest}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
              >
                <Play className="w-4 h-4" />
                运行回测
              </button>
              <button
                onClick={resetBacktest}
                className="px-4 py-2.5 bg-muted text-muted-foreground rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
              >
                重置
              </button>
            </div>
          </div>
        </div>

        {/* Backtest Result */}
        <AnimatePresence>
          {showBacktestResult && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-6 pt-6 border-t border-border"
            >
              <h4 className="text-sm font-semibold text-foreground mb-4">回测结果</h4>
              
              {/* Core KPIs */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
                {[
                  { label: '总收益', value: '+18.5%', positive: true },
                  { label: '年化收益率', value: '+42.3%', positive: true },
                  { label: '夏普比率', value: '2.1' },
                  { label: '最大回撤', value: '-8.2%', negative: true },
                ].map((kpi, i) => (
                  <div key={i} className="p-3 bg-muted/30 rounded-lg text-center">
                    <p className="text-[10px] text-muted-foreground mb-1">{kpi.label}</p>
                    <p className={cn(
                      'text-lg font-semibold font-mono',
                      kpi.positive && 'text-red-600',
                      kpi.negative && 'text-emerald-600',
                      !kpi.positive && !kpi.negative && 'text-foreground'
                    )}>
                      {kpi.value}
                    </p>
                  </div>
                ))}
              </div>

              {/* Chart & Stats */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Equity Curve */}
                <div className="lg:col-span-2 h-[200px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={backtestData.slice(-60)}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis 
                        dataKey="date" 
                        tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                        tickLine={false}
                        axisLine={{ stroke: 'hsl(var(--border))' }}
                        interval={9}
                      />
                      <YAxis 
                        tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                        tickLine={false}
                        axisLine={{ stroke: 'hsl(var(--border))' }}
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
                        dataKey="live" 
                        stroke="#3b82f6" 
                        fill="#3b82f6"
                        fillOpacity={0.1}
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* Trade Stats */}
                <div className="space-y-2">
                  <h5 className="text-xs font-medium text-muted-foreground mb-2">交易统计</h5>
                  {[
                    { label: '总交易次数', value: '125' },
                    { label: '胜率', value: '58.5%' },
                    { label: '盈亏比', value: '1.8' },
                    { label: '平均盈利', value: '2,850' },
                    { label: '平均亏损', value: '-1,580' },
                    { label: '盈利交易数', value: '73' },
                    { label: '亏损交易数', value: '52' },
                  ].map((stat) => (
                    <div key={stat.label} className="flex justify-between text-xs">
                      <span className="text-muted-foreground">{stat.label}</span>
                      <span className="font-mono">{stat.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 mt-4">
                <button className="px-3 py-1.5 text-xs bg-muted text-foreground rounded hover:bg-muted/80 transition-colors">
                  <Download className="w-3.5 h-3.5 inline mr-1" />
                  导出回测报告
                </button>
                <button 
                  onClick={runBacktest}
                  className="px-3 py-1.5 text-xs bg-muted text-foreground rounded hover:bg-muted/80 transition-colors"
                >
                  重新回测
                </button>
                <button className="px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors">
                  保存策略
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Row 7: Live vs Backtest Signal Comparison */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="card-surface p-5 space-y-5"
      >
        <h3 className="text-sm font-semibold text-foreground tracking-tight">实盘信号 vs 回测信号</h3>

        {/* Filters & Quick Time Select */}
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3 p-3 bg-muted/20 rounded-lg border border-border/50">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground shrink-0 font-medium">策略</span>
              <select className="text-xs bg-background border border-border rounded px-2 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-primary">
                <option>均值回归策略</option>
                <option>动量突破策略</option>
                <option>布林带反转</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground shrink-0 font-medium">品种</span>
              <select className="text-xs bg-background border border-border rounded px-2 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-primary">
                <option>螺纹钢 rb</option>
                <option>热卷 hc</option>
                <option>全部</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground shrink-0 font-medium">时间</span>
              <select className="text-xs bg-background border border-border rounded px-2 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-primary">
                <option>近 6 月</option>
                <option>近 1 月</option>
                <option>近 3 月</option>
                <option>近 1 年</option>
                <option>全部</option>
              </select>
            </div>
            <button className="text-xs text-primary hover:underline ml-auto flex items-center gap-1">
              <Filter className="w-3 h-3" />
              查看使用的因子
            </button>
          </div>
        </div>

        {/* Factor Tags & Weight Selection */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <div className="flex flex-wrap items-center gap-2 p-3 bg-muted/20 rounded-lg border border-border/50">
            <span className="text-xs font-medium text-foreground shrink-0">使用的因子：</span>
            {['价格动量', '相对强弱', '布林带', '放量'].map((f) => (
              <span key={f} className="flex items-center gap-1 text-xs px-2 py-1 bg-blue-500/15 text-blue-500 rounded-full border border-blue-500/30">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                {f}
              </span>
            ))}
            <span className="text-xs text-muted-foreground">共 4 个因子</span>
          </div>
          <div className="flex items-center justify-end gap-2 p-3 bg-muted/20 rounded-lg border border-border/50">
            <span className="text-xs text-muted-foreground shrink-0">权重：</span>
            <select className="text-xs bg-background border border-border rounded px-2 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-primary">
              <option>IC 加权</option>
              <option>等权</option>
              <option>手动配置</option>
            </select>
          </div>
        </div>

        {/* Chart + Table */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-[240px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={backtestData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                  tickLine={false}
                  axisLine={{ stroke: 'hsl(var(--border))' }}
                  interval={14}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
                  tickLine={false}
                  axisLine={{ stroke: 'hsl(var(--border))' }}
                  tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }}
                  formatter={(value: number, name: string) => [
                    value.toLocaleString(),
                    name === 'live' ? '实盘信号' : '回测信号'
                  ]}
                />
                <Legend
                  formatter={(value) => value === 'live' ? '实盘信号' : '回测信号'}
                  wrapperStyle={{ fontSize: '12px' }}
                />
                <Line type="monotone" dataKey="live" stroke="#3b82f6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="backtest" stroke="#9ca3af" strokeWidth={2} strokeDasharray="5 5" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Comparison Table — 8 metrics with improved layout */}
          <div className="space-y-2 overflow-x-auto">
            <p className="text-xs font-medium text-foreground mb-2">指标对比</p>
            <table className="w-full text-xs min-w-[400px]">
              <thead>
                <tr className="border-b border-border">
                  <th className="py-2 text-left font-medium text-muted-foreground whitespace-nowrap">指标</th>
                  <th className="py-2 text-center font-medium text-muted-foreground whitespace-nowrap">实盘</th>
                  <th className="py-2 text-center font-medium text-muted-foreground whitespace-nowrap">回测</th>
                  <th className="py-2 text-center font-medium text-muted-foreground whitespace-nowrap">偏离度</th>
                </tr>
              </thead>
              <tbody>
                {comparisonMetrics.map((m) => (
                  <tr key={m.metric} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                    <td className="py-2.5 text-muted-foreground whitespace-nowrap">{m.metric}</td>
                    <td className="py-2.5 text-center font-mono font-medium whitespace-nowrap">{m.live}</td>
                    <td className="py-2.5 text-center font-mono font-medium whitespace-nowrap">{m.backtest}</td>
                    <td className={cn(
                      'py-2.5 text-center font-mono font-medium whitespace-nowrap',
                      m.deviation.startsWith('-') ? 'text-emerald-600' : 'text-red-600'
                    )}>
                      {m.deviation}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Sample Info & Deviation Analysis */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left: Sample Description */}
          <div className="p-3.5 bg-muted/20 rounded-lg border border-border/50">
            <p className="text-xs font-semibold text-foreground mb-2.5">样本说明</p>
            <div className="space-y-2 text-xs text-muted-foreground">
              <div className="flex items-start gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500 mt-1 shrink-0" />
                <span>实盘信号期间：2025-12-17 ~ 2026-03-21（95 个交易日）</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-2 h-2 rounded-full bg-gray-500 mt-1 shrink-0" />
                <span>回测信号期间：2025-01-01 ~ 2025-12-31（242 个交易日）</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-2 h-2 rounded-full bg-muted-foreground mt-1 shrink-0" />
                <span>覆盖品种：rb / hc / i / j / m / au / ag / cu（8 个主力合约）</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-2 h-2 rounded-full bg-muted-foreground mt-1 shrink-0" />
                <span>信号总数：实盘 125 个 / 回测 156 个</span>
              </div>
            </div>
          </div>

          {/* Right: Deviation Analysis */}
          <div className="p-3.5 bg-amber-50/50 dark:bg-amber-950/15 rounded-lg border border-amber-200/50 dark:border-amber-700/40">
            <p className="text-xs font-semibold text-foreground mb-2.5">偏离度分析 · 可能原因</p>
            <div className="space-y-1.5 text-xs">
              <div className="flex items-start gap-2 text-amber-700 dark:text-amber-500">
                <span className="shrink-0 mt-0.5">•</span>
                <span>实盘滑点：约 0.5–1 个跳动点</span>
              </div>
              <div className="flex items-start gap-2 text-amber-700 dark:text-amber-500">
                <span className="shrink-0 mt-0.5">���</span>
                <span>实盘手续费：万分之 1（回测已计入）</span>
              </div>
              <div className="flex items-start gap-2 text-amber-700 dark:text-amber-500">
                <span className="shrink-0 mt-0.5">•</span>
                <span>信号执行延迟：平均 2–3 秒</span>
              </div>
              <div className="flex items-start gap-2 text-amber-700 dark:text-amber-500">
                <span className="shrink-0 mt-0.5">•</span>
                <span>品种覆盖差异：实盘 8 个 vs 回测 12 个</span>
              </div>
              <div className="flex items-start gap-2 text-amber-700 dark:text-amber-500">
                <span className="shrink-0 mt-0.5">•</span>
                <span>市场环境变化：近期波动率有所上升</span>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
