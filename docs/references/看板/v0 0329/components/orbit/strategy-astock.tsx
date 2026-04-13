'use client'
// Strategy A-Stock Management - Build 2026-03-17
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
  ResponsiveContainer, Legend, PieChart, Pie, Cell
} from 'recharts'

interface StrategyAStockProps {
  onBack: () => void
}

// KPI data for A-Stock
const kpiData = {
  todaySignals: 28,
  strongBuy: 6,
  normalBuy: 12,
  watchList: 10,
  avgConfidence: 68,
  highConfidence: 5,
  expectedReturn: 18500,
  riskLevel: '中等',
}

// A-Stock specific factors (31 factors in 5 categories)
const factorCategories = [
  {
    name: '基本面类',
    factors: [
      { id: 'pe_ratio', name: 'PE估值', checked: true },
      { id: 'pb_ratio', name: 'PB估值', checked: false },
      { id: 'roe', name: 'ROE', checked: true },
      { id: 'revenue_growth', name: '营收增速', checked: false },
      { id: 'profit_growth', name: '利润增速', checked: false },
      { id: 'dividend_yield', name: '股息率', checked: false },
    ]
  },
  {
    name: '技术面类',
    factors: [
      { id: 'ma_cross', name: '均线交叉', checked: true },
      { id: 'macd', name: 'MACD', checked: false },
      { id: 'kdj', name: 'KDJ', checked: false },
      { id: 'rsi', name: 'RSI', checked: false },
      { id: 'bollinger', name: '布林带', checked: true },
      { id: 'trend', name: '趋势强度', checked: false },
      { id: 'support_resist', name: '支撑阻力', checked: false },
    ]
  },
  {
    name: '资金面类',
    factors: [
      { id: 'north_flow', name: '北向资金', checked: true },
      { id: 'main_force', name: '主力资金', checked: false },
      { id: 'financing', name: '融资余额', checked: false },
      { id: 'institution', name: '机构持仓', checked: false },
      { id: 'block_trade', name: '大宗交易', checked: false },
      { id: 'fund_flow', name: '资金流向', checked: false },
    ]
  },
  {
    name: '情绪面类',
    factors: [
      { id: 'market_sentiment', name: '市场情绪', checked: false },
      { id: 'turnover_rate', name: '换手率', checked: true },
      { id: 'volume_ratio', name: '量比', checked: false },
      { id: 'limit_up', name: '涨停板', checked: false },
      { id: 'dragon_tiger', name: '龙虎榜', checked: false },
      { id: 'hot_topic', name: '热点题材', checked: false },
    ]
  },
  {
    name: '量价类',
    factors: [
      { id: 'volume_price', name: '量价配合', checked: true },
      { id: 'volume_breakout', name: '放量突破', checked: false },
      { id: 'shrink_volume', name: '缩量整理', checked: false },
      { id: 'price_momentum', name: '价格动量', checked: false },
      { id: 'relative_strength', name: '相对强弱', checked: false },
      { id: 'gap', name: '跳空缺口', checked: false },
    ]
  },
]

// All 31 factor names for IC heatmap
const allFactorNames = [
  'PE估值', 'PB估值', 'ROE', '营收增速', '利润增速', '股息率',
  '均线交叉', 'MACD', 'KDJ', 'RSI', '布林带', '趋势强度', '支撑阻力',
  '北向资金', '主力资金', '融资余额', '机构持仓', '大宗交易', '资金流向',
  '市场情绪', '换手率', '量比', '涨停板', '龙虎榜', '热点题材',
  '量价配合', '放量突破', '缩量整理', '价格动量', '相对强弱', '跳空缺口'
]

// Signal list data for A-Stock
const signalData = [
  { time: '14:55', code: '600519', name: '贵州茅台', price: 1688.50, trend: '上升', pressure: 1720, support: 1650, entry: 1685, exit: 1750, confidence: 85, reason: '北向资金流入+均线多头', signal: '强烈推荐', sector: '白酒' },
  { time: '14:52', code: '000858', name: '五粮液', price: 142.30, trend: '震荡', pressure: 148, support: 138, entry: 141, exit: 152, confidence: 72, reason: '量价配合', signal: '一般推荐', sector: '白酒' },
  { time: '14:48', code: '300750', name: '宁德时代', price: 185.60, trend: '下降', pressure: 192, support: 178, entry: null, exit: null, confidence: 55, reason: '等待企稳', signal: '观望', sector: '新能源' },
  { time: '14:42', code: '601318', name: '中国平安', price: 42.85, trend: '上升', pressure: 45, support: 41, entry: 42.5, exit: 46, confidence: 78, reason: '估值修复', signal: '一般推荐', sector: '保险' },
  { time: '14:35', code: '000001', name: '平安银行', price: 11.25, trend: '震荡', pressure: 11.8, support: 10.8, entry: 11.2, exit: 12.2, confidence: 65, reason: '银行板块联动', signal: '一般推荐', sector: '银行' },
  { time: '14:28', code: '002475', name: '立讯精密', price: 32.15, trend: '上升', pressure: 34, support: 30.5, entry: 32, exit: 35, confidence: 82, reason: '苹果产业链', signal: '强烈推荐', sector: '消费电子' },
  { time: '14:22', code: '600036', name: '招商银行', price: 32.80, trend: '上升', pressure: 34.5, support: 31.5, entry: 32.5, exit: 35.5, confidence: 75, reason: '业绩超预期', signal: '一般推荐', sector: '银行' },
  { time: '14:15', code: '601899', name: '紫金矿业', price: 15.65, trend: '震荡', pressure: 16.5, support: 15, entry: null, exit: null, confidence: 52, reason: '金价波动', signal: '观望', sector: '有色金属' },
]

// Generate IC data for all 31 factors
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
  { factor: '北向资金', ir: 2.92, winRate: 69.5, calls: 168 },
  { factor: 'ROE', ir: 2.65, winRate: 66.8, calls: 145 },
  { factor: '均线交叉', ir: 2.38, winRate: 64.2, calls: 156 },
  { factor: '量价配合', ir: 2.12, winRate: 62.5, calls: 132 },
  { factor: '布林带', ir: 1.95, winRate: 60.8, calls: 118 },
  { factor: 'PE估值', ir: 1.78, winRate: 58.5, calls: 142 },
  { factor: '换手率', ir: 1.52, winRate: 56.2, calls: 98 },
  { factor: '主力资金', ir: 1.35, winRate: 54.8, calls: 112 },
  { factor: 'MACD', ir: 1.18, winRate: 52.5, calls: 135 },
  { factor: '趋势强度', ir: 0.95, winRate: 50.2, calls: 88 },
]

// Confidence ranking data
const confidenceRanking = [
  { rank: 1, name: '北向资金跟踪', confidence: 90, expectedReturn: 3.5, risk: '低' },
  { rank: 2, name: '价值成长策略', confidence: 86, expectedReturn: 3.0, risk: '低' },
  { rank: 3, name: '技术突破策略', confidence: 82, expectedReturn: 2.6, risk: '中' },
  { rank: 4, name: '龙头股策略', confidence: 78, expectedReturn: 2.2, risk: '中' },
  { rank: 5, name: '板块轮动策略', confidence: 75, expectedReturn: 2.0, risk: '中' },
  { rank: 6, name: '低估值策略', confidence: 72, expectedReturn: 1.8, risk: '低' },
  { rank: 7, name: '高股息策略', confidence: 68, expectedReturn: 1.5, risk: '低' },
  { rank: 8, name: '趋势跟踪策略', confidence: 65, expectedReturn: 1.3, risk: '高' },
  { rank: 9, name: '事件驱动策略', confidence: 62, expectedReturn: 1.2, risk: '高' },
  { rank: 10, name: '量化多因子', confidence: 58, expectedReturn: 1.0, risk: '中' },
]

// Factor contribution pie data
const factorContribution = [
  { name: '基本面', value: 30, color: '#3b82f6' },
  { name: '技术面', value: 25, color: '#8b5cf6' },
  { name: '资金面', value: 22, color: '#f59e0b' },
  { name: '情绪面', value: 13, color: '#22c55e' },
  { name: '量价类', value: 10, color: '#ef4444' },
]

// Complete 31 factor contribution
const allFactorContributions = [
  { name: '北向资金', contribution: 12.5, category: '资金面', ir: 2.92 },
  { name: 'ROE', contribution: 11.2, category: '基本面', ir: 2.65 },
  { name: '均线交叉', contribution: 9.8, category: '技术面', ir: 2.38 },
  { name: '量价配合', contribution: 8.5, category: '量价类', ir: 2.12 },
  { name: '布林带', contribution: 7.2, category: '技术面', ir: 1.95 },
  { name: 'PE估值', contribution: 6.8, category: '基本面', ir: 1.78 },
  { name: '换手率', contribution: 5.5, category: '情绪面', ir: 1.52 },
  { name: '主力资金', contribution: 4.8, category: '资金面', ir: 1.35 },
  { name: 'MACD', contribution: 4.2, category: '技术面', ir: 1.18 },
  { name: '趋势强度', contribution: 3.8, category: '技术面', ir: 0.95 },
  { name: 'PB估值', contribution: 3.5, category: '基本面', ir: 0.88 },
  { name: '营收增速', contribution: 3.2, category: '基本面', ir: 0.82 },
  { name: '融资余额', contribution: 2.8, category: '资金面', ir: 0.78 },
  { name: 'KDJ', contribution: 2.5, category: '技术面', ir: 0.72 },
  { name: '量比', contribution: 2.2, category: '情绪面', ir: 0.68 },
  { name: '放量突破', contribution: 2.0, category: '量价类', ir: 0.65 },
  { name: 'RSI', contribution: 1.8, category: '技术面', ir: 0.62 },
  { name: '利润增速', contribution: 1.5, category: '基本面', ir: 0.58 },
  { name: '机构持仓', contribution: 1.2, category: '资金面', ir: 0.55 },
  { name: '市场情绪', contribution: 1.0, category: '情绪面', ir: 0.52 },
].sort((a, b) => b.contribution - a.contribution).map((f, i) => ({ ...f, rank: i + 1 }))

// Category to factors mapping for drilldown
const categoryFactors: Record<string, typeof allFactorContributions> = {
  '基本面': allFactorContributions.filter(f => f.category === '基本面'),
  '技术面': allFactorContributions.filter(f => f.category === '技术面'),
  '资金面': allFactorContributions.filter(f => f.category === '资金面'),
  '情绪面': allFactorContributions.filter(f => f.category === '情绪面'),
  '量价类': allFactorContributions.filter(f => f.category === '量价类'),
}

// Backtest comparison data
const backtestData = Array.from({ length: 90 }, (_, i) => {
  const date = new Date()
  date.setDate(date.getDate() - (89 - i))
  return {
    date: `${date.getMonth() + 1}/${date.getDate()}`,
    live: Math.round(10000 + i * 100 + Math.sin(i * 0.2) * 1200 + Math.random() * 400),
    backtest: Math.round(10000 + i * 115 + Math.sin(i * 0.2) * 1000 + Math.random() * 250),
  }
})

const comparisonMetrics = [
  { metric: '交易次数', live: '98 笔', backtest: '125 笔', deviation: '-27 笔' },
  { metric: '胜率', live: '55.2%', backtest: '59.8%', deviation: '-4.6%' },
  { metric: '盈亏比', live: '1.6', backtest: '1.9', deviation: '-0.3' },
  { metric: '最大回撤', live: '-12.5%', backtest: '-9.8%', deviation: '-2.7%' },
  { metric: '夏普比率', live: '1.8', backtest: '2.2', deviation: '-0.4' },
  { metric: '年化收益', live: '+32.5%', backtest: '+42.8%', deviation: '-10.3%' },
  { metric: '盈利因子', live: '1.62', backtest: '1.95', deviation: '-0.33' },
]

// A-Stock varieties
const stockVarieties = [
  { id: '600519', name: '贵州茅台', checked: true },
  { id: '000858', name: '五粮液', checked: false },
  { id: '300750', name: '宁德时代', checked: true },
  { id: '601318', name: '中国平安', checked: false },
  { id: '000001', name: '平安银行', checked: false },
  { id: '002475', name: '立讯精密', checked: false },
  { id: '600036', name: '招商银行', checked: false },
  { id: '601899', name: '紫金矿业', checked: false },
]

export function StrategyAStock({ onBack }: StrategyAStockProps) {
  const { toast } = useToast()
  const [factors, setFactors] = useState(factorCategories)
  const [selectedStock, setSelectedStock] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showResult, setShowResult] = useState(false)
  const [signalFilter, setSignalFilter] = useState({ sector: '全部', signal: '全部', confidence: '全部' })
  const [selectedICFactor, setSelectedICFactor] = useState<string | null>(null)
  const [contributionView, setContributionView] = useState<'summary' | 'detail' | 'category'>('summary')
  const [drilldownCategory, setDrilldownCategory] = useState<string | null>(null)
  
  // 加载和排序状态
  const [isTesting, setIsTesting] = useState(false)
  const [isBacktesting, setIsBacktesting] = useState(false)
  const [sortConfig, setSortConfig] = useState<{ column: string; direction: 'asc' | 'desc' } | null>(null)
  const [searchResults, setSearchResults] = useState<typeof stockVarieties>([])
  const [showSearchResults, setShowSearchResults] = useState(false)

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
      '信号': s.signal,
      '板块': s.sector
    }))
    exportCSV(data, '荐股信号')
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

  // 品种搜索处理
  const handleStockSearch = (query: string) => {
    if (!query.trim()) {
      setSearchResults([])
      setShowSearchResults(false)
      return
    }
    const results = stockVarieties.filter(s =>
      s.id.toLowerCase().includes(query.toLowerCase()) ||
      s.name.toLowerCase().includes(query.toLowerCase())
    )
    setSearchResults(results)
    setShowSearchResults(true)
  }

  // 信号列表排序处理
  const handleSort = (column: string) => {
    if (sortConfig?.column === column && sortConfig.direction === 'asc') {
      setSortConfig({ column, direction: 'desc' })
    } else {
      setSortConfig({ column, direction: 'asc' })
    }
  }

  // 获取排序后的信号列表
  const getSortedSignals = () => {
    let sorted = [...filteredSignals]
    if (!sortConfig) return sorted
    
    sorted.sort((a, b) => {
      let aVal: any = a[sortConfig.column as keyof typeof a]
      let bVal: any = b[sortConfig.column as keyof typeof b]
      
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal
      }
      return sortConfig.direction === 'asc' 
        ? String(aVal).localeCompare(String(bVal))
        : String(bVal).localeCompare(String(aVal))
    })
    return sorted
  }

  // 运行测算
  const runCalculation = async () => {
    setIsTesting(true)
    await new Promise(r => setTimeout(r, 1200))
    setIsTesting(false)
    setShowResult(true)
  }

  // 运行回测
  const runBacktest = async () => {
    setIsBacktesting(true)
    await new Promise(r => setTimeout(r, 1200))
    setIsBacktesting(false)
  }
  
  // Backtest state
  const [backtestStartDate, setBacktestStartDate] = useState('2025-01-01')
  const [backtestEndDate, setBacktestEndDate] = useState('2025-03-21')
  const [backtestFactors, setBacktestFactors] = useState(factorCategories.map(c => ({ ...c, factors: c.factors.map(f => ({ ...f, checked: false })) })))
  const [backtestStocks, setBacktestStocks] = useState(stockVarieties)
  const [backtestParams, setBacktestParams] = useState({ capital: 500000, maxPosition: 10, stopLoss: -8, takeProfit: 15, fee: 0.15 })
  const [showBacktestResult, setShowBacktestResult] = useState(false)

  const selectedCount = useMemo(() => 
    factors.reduce((acc, cat) => acc + cat.factors.filter(f => f.checked).length, 0)
  , [factors])

  const backtestSelectedFactorCount = useMemo(() =>
    backtestFactors.reduce((acc, cat) => acc + cat.factors.filter(f => f.checked).length, 0)
  , [backtestFactors])

  const backtestSelectedStockCount = useMemo(() =>
    backtestStocks.filter(v => v.checked).length
  , [backtestStocks])

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

  const toggleBacktestStock = (index: number) => {
    setBacktestStocks(prev => prev.map((v, i) => i === index ? { ...v, checked: !v.checked } : v))
  }

  const resetCalculation = () => {
    setShowResult(false)
    setSelectedStock('')
  }

  const resetBacktest = () => {
    setShowBacktestResult(false)
    setBacktestFactors(factorCategories.map(c => ({ ...c, factors: c.factors.map(f => ({ ...f, checked: false })) })))
    setBacktestStocks(stockVarieties.map(v => ({ ...v, checked: false })))
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
    if (signalFilter.signal !== '全部' && s.signal !== signalFilter.signal) return false
    if (signalFilter.sector !== '全部' && s.sector !== signalFilter.sector) return false
    if (signalFilter.confidence === '>80%' && s.confidence <= 80) return false
    if (signalFilter.confidence === '70-80%' && (s.confidence < 70 || s.confidence > 80)) return false
    if (signalFilter.confidence === '<70%' && s.confidence >= 70) return false
    return true
  })

  // Get IC color based on value
  const getICColor = (value: number) => {
    const absValue = Math.abs(value)
    const opacity = Math.min(absValue * 5, 1)
    if (value > 0) {
      return `rgba(239, 68, 68, ${0.2 + opacity * 0.8})`
    } else {
      return `rgba(34, 197, 94, ${0.2 + opacity * 0.8})`
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
            <h1 className="text-xl font-semibold text-foreground">策略信号 - 中国 A 股</h1>
            <p className="text-xs text-muted-foreground mt-0.5">手动因子测算、荐股信号与回测分析（T+1交易）</p>
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
              导出荐股信号
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
          { label: '今日荐股数', value: kpiData.todaySignals, icon: Activity },
          { label: '强烈推荐', value: kpiData.strongBuy, positive: true, icon: TrendingUp },
          { label: '一般推荐', value: kpiData.normalBuy, neutral: true, icon: Target },
          { label: '观望', value: kpiData.watchList, muted: true, icon: AlertTriangle },
          { label: '平均置信度', value: `${kpiData.avgConfidence}%`, icon: Percent },
          { label: '高置信度(>80%)', value: `${kpiData.highConfidence}个`, icon: Sparkles },
          { label: '预期收益', value: `+${kpiData.expectedReturn.toLocaleString()}`, positive: true, icon: Trophy },
          { label: '风险等级', value: kpiData.riskLevel, neutral: true, icon: AlertTriangle },
        ].map((kpi, i) => (
          <div key={i} className="card-surface p-4 flex flex-col items-center justify-center text-center min-h-[100px]">
            <div className="flex items-center gap-1.5 mb-2">
              <kpi.icon className={cn(
                'w-4 h-4',
                kpi.positive && 'text-#FF3B30',
                kpi.neutral && 'text-amber-500',
                kpi.muted && 'text-muted-foreground',
                !kpi.positive && !kpi.neutral && !kpi.muted && 'text-primary'
              )} />
              <span className="text-xs text-muted-foreground">{kpi.label}</span>
            </div>
            <p className={cn(
              'text-xl font-semibold font-mono',
              kpi.positive && 'text-#FF3B30',
              kpi.neutral && 'text-amber-600',
              kpi.muted && 'text-muted-foreground',
              !kpi.positive && !kpi.neutral && !kpi.muted && 'text-foreground'
            )}>
              {kpi.value}
            </p>
          </div>
        ))}
      </motion.div>

      {/* Row 2: Manual Factor Calculation */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card-surface p-5"
      >
        <div className="flex items-center gap-2 mb-4">
          <FlaskConical className="w-5 h-5 text-primary" />
          <h3 className="text-sm font-semibold text-foreground tracking-tight">手动因子测算（沙盒环境）</h3>
          
          {/* 沙盒环境提示 */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-3 p-4 bg-amber-500/10 border border-l-4 border-l-amber-500 border-amber-500/20 rounded-lg"
          >
            <div className="flex gap-3">
              <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
              <div className="flex-1 space-y-1">
                <p className="text-xs font-semibold text-amber-700 dark:text-amber-300">沙盒环境提示</p>
                <p className="text-xs text-amber-600 dark:text-amber-400 leading-relaxed">
                  此处修改的参数仅本次测算使用，不会保存到系统配置。退出页面后参数将重置，如需保存请前往设置页面。
                </p>
                <p className="text-xs text-amber-600 dark:text-amber-400 leading-relaxed pt-1 border-t border-amber-500/20">
                  注意：A 股为 T+1 交易制度，当日买入不可当日卖出。
                </p>
              </div>
            </div>
          </motion.div>
        </div>
        <div className="flex items-center gap-2 mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
          <Lightbulb className="w-4 h-4 text-amber-500 shrink-0" />
          <p className="text-xs text-amber-600 dark:text-amber-400">此处修改的参数仅本次测算使用，不会保存到系统配置。注意：A股为T+1交易</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Step 1: Select Factors */}
          <div>
            <h4 className="text-xs font-medium text-muted-foreground mb-3">步骤 1: 选择因子（共31个）</h4>
            <div className="space-y-3">
              {factors.map((category, catIndex) => (
                <div key={category.name} className="p-3 bg-muted/30 rounded-lg">
                  <p className="text-[11px] font-medium text-muted-foreground mb-2">{category.name} ({category.factors.length}个)</p>
                  <div className="flex flex-wrap gap-1.5">
                    {category.factors.map((factor, factorIndex) => (
                      <button
                        key={factor.id}
                        onClick={() => toggleFactor(catIndex, factorIndex)}
                        className={cn(
                          'px-2.5 py-1 rounded-full text-xs transition-all',
                          factor.checked 
                            ? 'bg-primary text-primary-foreground' 
                            : 'bg-muted/50 text-muted-foreground hover:bg-muted'
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

          {/* Step 2-3: Parameters & Stock Selection */}
          <div className="space-y-4">
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-3">步骤 2: 设置参数</h4>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-[11px] text-muted-foreground">回看周期</label>
                  <select className="w-full mt-1 px-2 py-1.5 text-xs bg-muted/50 border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary">
                    <option>20 天</option>
                    <option>60 天</option>
                    <option>120 天</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] text-muted-foreground">入场阈值</label>
                  <select className="w-full mt-1 px-2 py-1.5 text-xs bg-muted/50 border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary">
                    <option>0.5</option>
                    <option>0.6</option>
                    <option>0.7</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] text-muted-foreground">出场阈值</label>
                  <select className="w-full mt-1 px-2 py-1.5 text-xs bg-muted/50 border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary">
                    <option>0.3</option>
                    <option>0.2</option>
                    <option>0.1</option>
                  </select>
                </div>
              </div>
              <button className="text-xs text-primary hover:underline mt-2">恢复默认值</button>
            </div>

            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-3">步骤 3: 选择股票/板块</h4>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="输入股票代码或名称（如 600519 贵州茅台）"
                  value={selectedStock}
                  onChange={(e) => setSelectedStock(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 text-sm bg-muted/50 border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={runCalculation}
                disabled={selectedCount === 0}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="w-4 h-4" />
                运行测算
              </button>
            <button
              onClick={runCalculation}
              disabled={isTesting}
              className="flex items-center gap-2 px-4 py-2.5 bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-primary-foreground rounded-lg text-xs font-medium transition-colors"
            >
              {isTesting ? (
                <>
                  <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity }}>
                    <Play className="w-4 h-4" />
                  </motion.div>
                  测算中...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  运行测算
                </>
              )}
            </button>
            </div>

            {/* Result */}
            <AnimatePresence>
              {showResult && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="p-4 bg-primary/5 border border-primary/20 rounded-lg space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">测算结果</span>
                    <span className="text-xs px-2 py-0.5 bg-#FF3B30/10 text-#FF3B30 rounded">强烈推荐</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div><span className="text-muted-foreground">信号方向：</span><span className="text-#FF3B30 font-medium">买入</span></div>
                    <div><span className="text-muted-foreground">置信度：</span><span className="font-mono">82.5%</span></div>
                    <div><span className="text-muted-foreground">建议买入价：</span><span className="font-mono">1685.00</span></div>
                    <div><span className="text-muted-foreground">止损位：</span><span className="font-mono">1620.00</span></div>
                    <div><span className="text-muted-foreground">目标位：</span><span className="font-mono">1780.00</span></div>
                    <div><span className="text-muted-foreground">预期收益：</span><span className="text-#FF3B30 font-mono">+5.6%</span></div>
                  </div>
                  <div className="text-[11px] text-muted-foreground border-t border-border pt-2">
                    主要贡献因子：北向资金(35%) · ROE(28%) · 均线交叉(22%)
                  </div>
                  <div className="text-[10px] text-amber-600 bg-amber-500/10 px-2 py-1 rounded">
                    提示：A股T+1交易，建议次日开盘买入
                  </div>
                  <div className="flex gap-2 pt-2 border-t border-border/50">
                    <button 
                      onClick={() => toast({ title: "加入跟踪", description: `已将 ${selectedStock || '贵州茅台'} 添加到跟踪列表` })}
                      className="flex-1 text-xs px-3 py-1.5 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
                    >
                      加入跟踪
                    </button>
                    <button 
                      onClick={() => {
                        navigator.clipboard.writeText(`测算结果：${selectedStock || '贵州茅台'} 买入信号，置信度82.5%，目标位1780`)
                        toast({ title: "复制成功", description: "测算结果已复制到剪贴板" })
                      }}
                      className="flex-1 text-xs px-3 py-1.5 bg-muted/50 hover:bg-muted rounded transition-colors"
                    >
                      ���享结果
                    </button>
                    <button 
                      onClick={() => toast({ title: "保存成功", description: "测算参数已保存" })}
                      className="flex-1 text-xs px-3 py-1.5 bg-muted/50 hover:bg-muted rounded transition-colors"
                    >
                      保存测算
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>

      {/* Row 3: IC Heatmap & IR Ranking */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* IC Heatmap */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-3 card-surface p-5"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground tracking-tight">因子 IC 热力图（近30交易日）</h3>
            <select className="text-xs bg-muted/50 border border-border rounded px-2 py-1">
              <option>IC 降序</option>
              <option>IC 升序</option>
              <option>名称排序</option>
            </select>
          </div>
          <div className="overflow-x-auto">
            <div className="w-full">
              {/* Day headers */}
              <div className="flex items-center mb-1">
                <div className="w-20 shrink-0" />
                {Array.from({ length: 30 }, (_, i) => (
                  <div key={i} className="flex-1 text-center text-[9px] text-muted-foreground">{i + 1}</div>
                ))}
              </div>
              {/* Factor rows */}
              <div className="space-y-0.5">
                {icData.map((row) => (
                  <div 
                    key={row.factor} 
                    className={cn(
                      "flex items-center cursor-pointer hover:bg-muted/30 rounded transition-colors",
                      selectedICFactor === row.factor && "bg-muted/50"
                    )}
                    onClick={() => setSelectedICFactor(selectedICFactor === row.factor ? null : row.factor)}
                  >
                    <div className="w-20 shrink-0 text-[10px] text-muted-foreground truncate pr-2">{row.factor}</div>
                    {row.values.map((value, i) => (
                      <div
                        key={i}
                        className="flex-1 h-5 rounded-sm mx-px"
                        style={{ backgroundColor: getICColor(value) }}
                        title={`IC: ${value.toFixed(3)}`}
                      />
                    ))}
                  </div>
                ))}
              </div>
              {/* Legend */}
              <div className="flex items-center justify-center gap-6 mt-4 text-xs text-muted-foreground">
                <div className="flex items-center gap-1">
                  <span className="w-3 h-3 rounded-sm bg-#3FB950" />
                  <span>负IC</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-3 h-3 rounded-sm bg-#FF3B30" />
                  <span>正IC</span>
                </div>
              </div>
              {/* Selected factor details */}
              {selectedICFactor && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 p-3 bg-muted/30 rounded-lg"
                >
                  <p className="text-xs font-medium mb-2">{selectedICFactor} IC 统计</p>
                  <div className="grid grid-cols-4 gap-4 text-xs">
                    <div><span className="text-muted-foreground">平均IC：</span><span className="font-mono">{icData.find(d => d.factor === selectedICFactor)?.avgIC.toFixed(4)}</span></div>
                    <div><span className="text-muted-foreground">IC标准差：</span><span className="font-mono">{icData.find(d => d.factor === selectedICFactor)?.stdIC.toFixed(4)}</span></div>
                    <div><span className="text-muted-foreground">IR比率：</span><span className="font-mono">{icData.find(d => d.factor === selectedICFactor)?.ir}</span></div>
                    <div><span className="text-muted-foreground">胜率：</span><span className="font-mono">{icData.find(d => d.factor === selectedICFactor)?.winRate}%</span></div>
                  </div>
                </motion.div>
              )}
            </div>
          </div>
        </motion.div>

        {/* IR Ranking */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="lg:col-span-1 card-surface p-5"
        >
          <h3 className="text-sm font-semibold text-foreground tracking-tight mb-4">因子 IR 比率排行 Top10</h3>
          <div className="space-y-2">
            {irRankingData.map((item, i) => (
              <div key={item.factor} className="flex items-center gap-2 p-2 bg-muted/30 rounded">
                <span className={cn(
                  'w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-semibold',
                  i === 0 && 'bg-amber-400 text-amber-900',
                  i === 1 && 'bg-gray-300 text-gray-700',
                  i === 2 && 'bg-amber-600 text-amber-100',
                  i > 2 && 'bg-muted text-muted-foreground'
                )}>
                  {i + 1}
                </span>
                <span className="text-xs font-medium flex-1 truncate">{item.factor}</span>
                <span className="text-xs font-mono text-primary">{item.ir}</span>
                <span className="text-[10px] text-muted-foreground">{item.winRate}%</span>
                <span className="text-[10px] text-muted-foreground">{item.calls}次</span>
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
          <h3 className="text-sm font-semibold text-foreground tracking-tight">荐股信号列表</h3>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <input
                type="text"
                placeholder="搜索股票..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs bg-muted/50 border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary w-40"
              />
            </div>
            <select 
              value={signalFilter.sector}
              onChange={(e) => setSignalFilter({ ...signalFilter, sector: e.target.value })}
              className="text-xs bg-muted/50 border border-border rounded px-2 py-1.5"
            >
              <option value="全部">全部板块</option>
              <option value="白酒">白酒</option>
              <option value="新能源">新能源</option>
              <option value="银行">银行</option>
              <option value="保险">保险</option>
            </select>
            <select 
              value={signalFilter.signal}
              onChange={(e) => setSignalFilter({ ...signalFilter, signal: e.target.value })}
              className="text-xs bg-muted/50 border border-border rounded px-2 py-1.5"
            >
              <option value="全部">全部信号</option>
              <option value="强烈推荐">强烈推荐</option>
              <option value="一般推荐">一般推荐</option>
              <option value="观望">观望</option>
            </select>
            <select 
              value={signalFilter.confidence}
              onChange={(e) => setSignalFilter({ ...signalFilter, confidence: e.target.value })}
              className="text-xs bg-muted/50 border border-border rounded px-2 py-1.5"
            >
              <option value="全部">全部置信度</option>
              <option value=">80%">{'>'}80%</option>
              <option value="70-80%">70-80%</option>
              <option value="<70%">{'<'}70%</option>
            </select>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs min-w-[1200px]">
            <thead>
              <tr className="border-b border-border">
                <th className="py-2 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">时间</th>
                <th className="py-2 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">代码</th>
                <th className="py-2 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">名称</th>
                <th className="py-2 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">板块</th>
                <th className="py-2 px-2 text-right font-medium text-muted-foreground whitespace-nowrap">现价</th>
                <th className="py-2 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">趋势</th>
                <th className="py-2 px-2 text-right font-medium text-muted-foreground whitespace-nowrap">压力位</th>
                <th className="py-2 px-2 text-right font-medium text-muted-foreground whitespace-nowrap">支撑位</th>
                <th className="py-2 px-2 text-right font-medium text-muted-foreground whitespace-nowrap">建议买入</th>
                <th className="py-2 px-2 text-right font-medium text-muted-foreground whitespace-nowrap">目标价</th>
                <th className="py-2 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">置信度</th>
                <th className="py-2 px-2 text-left font-medium text-muted-foreground whitespace-nowrap">主要原因</th>
                <th className="py-2 px-2 text-center font-medium text-muted-foreground whitespace-nowrap">信号</th>
              </tr>
            </thead>
            <tbody>
              {filteredSignals.map((s, i) => (
                <tr key={i} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                  <td className="py-2.5 px-2 text-muted-foreground whitespace-nowrap">{s.time}</td>
                  <td className="py-2.5 px-2 font-mono whitespace-nowrap">{s.code}</td>
                  <td className="py-2.5 px-2 font-medium whitespace-nowrap">{s.name}</td>
                  <td className="py-2.5 px-2 text-muted-foreground whitespace-nowrap">{s.sector}</td>
                  <td className="py-2.5 px-2 text-right font-mono whitespace-nowrap">{s.price.toFixed(2)}</td>
                  <td className="py-2.5 px-2 text-center whitespace-nowrap">
                    <span className={cn(
                      'text-[10px] px-1.5 py-0.5 rounded',
                      s.trend === '上升' && 'bg-#FF3B30/10 text-#FF3B30',
                      s.trend === '下降' && 'bg-#3FB950/10 text-#3FB950',
                      s.trend === '震荡' && 'bg-amber-500/10 text-amber-600'
                    )}>
                      {s.trend}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-right font-mono text-muted-foreground whitespace-nowrap">{s.pressure}</td>
                  <td className="py-2.5 px-2 text-right font-mono text-muted-foreground whitespace-nowrap">{s.support}</td>
                  <td className="py-2.5 px-2 text-right font-mono whitespace-nowrap">{s.entry ?? '-'}</td>
                  <td className="py-2.5 px-2 text-right font-mono whitespace-nowrap">{s.exit ?? '-'}</td>
                  <td className="py-2.5 px-2 whitespace-nowrap">
                    <div className="flex items-center gap-1">
                      <div className="w-12 h-1.5 bg-muted rounded-full overflow-hidden">
                        <div 
                          className={cn(
                            'h-full rounded-full',
                            s.confidence >= 80 && 'bg-#FF3B30',
                            s.confidence >= 70 && s.confidence < 80 && 'bg-amber-500',
                            s.confidence < 70 && 'bg-gray-400'
                          )}
                          style={{ width: `${s.confidence}%` }}
                        />
                      </div>
                      <span className="font-mono text-[10px]">{s.confidence}%</span>
                    </div>
                  </td>
                  <td className="py-2.5 px-2 text-muted-foreground whitespace-nowrap">{s.reason}</td>
                  <td className="py-2.5 px-2 text-center whitespace-nowrap">
                    <span className={cn(
                      'text-[10px] px-2 py-0.5 rounded-full font-medium',
                      s.signal === '强烈推荐' && 'bg-#FF3B30/10 text-#FF3B30 border border-#FF3B30/20',
                      s.signal === '一般推荐' && 'bg-amber-500/10 text-amber-600 border border-amber-500/20',
                      s.signal === '观望' && 'bg-gray-500/10 text-gray-600 border border-gray-500/20'
                    )}>
                      {s.signal}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Row 5: Confidence Ranking & Factor Contribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Confidence Ranking */}
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

        {/* Factor Contribution */}
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

            {contributionView === 'detail' && (
              <motion.div
                key="detail"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="flex-1 flex flex-col"
              >
                <p className="text-xs text-muted-foreground mb-2">因子贡献度排行</p>
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

      {/* Row 6: Manual Backtest */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.55 }}
        className="card-surface p-5"
      >
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-primary" />
          <h3 className="text-sm font-semibold text-foreground tracking-tight">手动回测</h3>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Backtest Configuration */}
          <div className="space-y-4">
            {/* Step 1: Date Range */}
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">步骤 1: 选择回测区间</h4>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-muted-foreground">开始日期</label>
                  <input
                    type="date"
                    value={backtestStartDate}
                    onChange={(e) => setBacktestStartDate(e.target.value)}
                    className="w-full mt-1 px-2 py-1.5 text-xs bg-muted/50 border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-muted-foreground">结束日期</label>
                  <input
                    type="date"
                    value={backtestEndDate}
                    onChange={(e) => setBacktestEndDate(e.target.value)}
                    className="w-full mt-1 px-2 py-1.5 text-xs bg-muted/50 border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
              </div>
              <div className="flex gap-2 mt-2">
                {['1m', '3m', '6m', '1y', 'all'].map((range) => (
                  <button
                    key={range}
                    onClick={() => setQuickDate(range)}
                    className="px-2 py-1 text-xs bg-muted/50 hover:bg-muted rounded transition-colors"
                  >
                    {range === '1m' ? '近1月' : range === '3m' ? '近3月' : range === '6m' ? '近6月' : range === '1y' ? '近1年' : '全部'}
                  </button>
                ))}
              </div>
            </div>

            {/* Step 2: Select Factors */}
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">步骤 2: 选择因子组合</h4>
              <div className="space-y-2">
                {backtestFactors.map((category, catIndex) => (
                  <div key={category.name}>
                    <p className="text-[10px] text-muted-foreground mb-1">{category.name} ({category.factors.length}个)</p>
                    <div className="flex flex-wrap gap-1">
                      {category.factors.map((factor, factorIndex) => (
                        <button
                          key={factor.id}
                          onClick={() => toggleBacktestFactor(catIndex, factorIndex)}
                          className={cn(
                            'px-2 py-0.5 rounded text-[11px] transition-all',
                            factor.checked 
                              ? 'bg-primary text-primary-foreground' 
                              : 'bg-muted/50 text-muted-foreground hover:bg-muted'
                          )}
                        >
                          {factor.checked && <Check className="w-2.5 h-2.5 inline mr-0.5" />}
                          {factor.name}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">已选择：{backtestSelectedFactorCount} 个因子</p>
            </div>

            {/* Step 3: Select Stocks */}
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">步骤 3: 选择股票</h4>
              <div className="flex flex-wrap gap-1.5">
                {backtestStocks.map((stock, index) => (
                  <button
                    key={stock.id}
                    onClick={() => toggleBacktestStock(index)}
                    className={cn(
                      'px-2 py-1 rounded text-xs transition-all',
                      stock.checked 
                        ? 'bg-primary text-primary-foreground' 
                        : 'bg-muted/50 text-muted-foreground hover:bg-muted'
                    )}
                  >
                    {stock.checked && <Check className="w-3 h-3 inline mr-1" />}
                    {stock.id} {stock.name}
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">已选择：{backtestSelectedStockCount} 个股票</p>
            </div>
          </div>

          {/* Right: Parameters & Results */}
          <div className="space-y-4">
            {/* Step 4: Parameters */}
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">步骤 4: 设置参数</h4>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-muted-foreground">初始资金</label>
                  <input
                    type="number"
                    value={backtestParams.capital}
                    onChange={(e) => setBacktestParams({ ...backtestParams, capital: Number(e.target.value) })}
                    className="w-full mt-1 px-2 py-1.5 text-xs bg-muted/50 border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-muted-foreground">最大持仓(%)</label>
                  <input
                    type="number"
                    value={backtestParams.maxPosition}
                    onChange={(e) => setBacktestParams({ ...backtestParams, maxPosition: Number(e.target.value) })}
                    className="w-full mt-1 px-2 py-1.5 text-xs bg-muted/50 border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-muted-foreground">止损线(%)</label>
                  <input
                    type="number"
                    value={backtestParams.stopLoss}
                    onChange={(e) => setBacktestParams({ ...backtestParams, stopLoss: Number(e.target.value) })}
                    className="w-full mt-1 px-2 py-1.5 text-xs bg-muted/50 border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-muted-foreground">止盈线(%)</label>
                  <input
                    type="number"
                    value={backtestParams.takeProfit}
                    onChange={(e) => setBacktestParams({ ...backtestParams, takeProfit: Number(e.target.value) })}
                    className="w-full mt-1 px-2 py-1.5 text-xs bg-muted/50 border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
              </div>
            </div>

            {/* Step 5: Run */}
            <div className="flex gap-3">
              <button
                onClick={runBacktest}
                disabled={backtestSelectedFactorCount === 0 || backtestSelectedStockCount === 0}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="w-4 h-4" />
                运行回测
              </button>
            <button
              onClick={runBacktest}
              disabled={isBacktesting}
              className="flex items-center gap-2 px-4 py-2.5 bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-primary-foreground rounded-lg text-xs font-medium transition-colors"
            >
              {isBacktesting ? (
                <>
                  <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity }}>
                    <RotateCcw className="w-4 h-4" />
                  </motion.div>
                  回测中...
                </>
              ) : (
                <>
                  <RotateCcw className="w-4 h-4" />
                  运行回测
                </>
              )}
            </button>
            </div>

            {/* Backtest Results */}
            <AnimatePresence>
              {showBacktestResult && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-3"
                >
                  {/* KPI Grid */}
                  <div className="grid grid-cols-4 gap-2">
                    <div className="p-2 bg-muted/30 rounded text-center">
                      <p className="text-[10px] text-muted-foreground">年化收益</p>
                      <p className="text-sm font-mono font-semibold text-#FF3B30">+38.5%</p>
                    </div>
                    <div className="p-2 bg-muted/30 rounded text-center">
                      <p className="text-[10px] text-muted-foreground">最大回撤</p>
                      <p className="text-sm font-mono font-semibold text-#3FB950">-15.2%</p>
                    </div>
                    <div className="p-2 bg-muted/30 rounded text-center">
                      <p className="text-[10px] text-muted-foreground">夏普比率</p>
                      <p className="text-sm font-mono font-semibold">1.85</p>
                    </div>
                    <div className="p-2 bg-muted/30 rounded text-center">
                      <p className="text-[10px] text-muted-foreground">胜率</p>
                      <p className="text-sm font-mono font-semibold">58.2%</p>
                    </div>
                  </div>

                  {/* Trading Statistics Table */}
                  <div className="p-3 bg-muted/20 rounded-lg">
                    <p className="text-[10px] font-medium text-muted-foreground mb-2">交易统计</p>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px]">
                      <div className="flex justify-between"><span className="text-muted-foreground">交易次数</span><span className="font-mono">156 笔</span></div>
                      <div className="flex justify-between"><span className="text-muted-foreground">盈利次数</span><span className="font-mono text-#FF3B30">91 笔</span></div>
                      <div className="flex justify-between"><span className="text-muted-foreground">亏损次数</span><span className="font-mono text-#3FB950">65 笔</span></div>
                      <div className="flex justify-between"><span className="text-muted-foreground">盈亏比</span><span className="font-mono">1.72</span></div>
                      <div className="flex justify-between"><span className="text-muted-foreground">平均持仓</span><span className="font-mono">8.5 天</span></div>
                      <div className="flex justify-between"><span className="text-muted-foreground">最大连胜</span><span className="font-mono">7 次</span></div>
                    </div>
                  </div>

                  {/* Chart with max drawdown annotation */}
                  <div className="h-32 bg-muted/20 rounded-lg flex items-center justify-center relative">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={backtestData.slice(0, 30)}>
                        <Line type="monotone" dataKey="backtest" stroke="#3b82f6" strokeWidth={1.5} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                    <div className="absolute top-2 right-2 text-[9px] px-1.5 py-0.5 bg-#3FB950/20 text-#3FB950 rounded">
                      最大回撤: -15.2%
                    </div>
                  </div>

                  {/* Monthly PnL Heatmap */}
                  <div className="p-3 bg-muted/20 rounded-lg">
                    <p className="text-[10px] font-medium text-muted-foreground mb-2">月度盈亏热力图</p>
                    <div className="grid grid-cols-6 gap-1">
                      {['1月', '2月', '3月', '4月', '5月', '6月'].map((m, i) => {
                        const pnl = [5.2, -2.1, 8.5, 3.2, -1.5, 6.8][i]
                        return (
                          <div 
                            key={m} 
                            className={cn(
                              "p-1.5 rounded text-center",
                              pnl > 5 ? "bg-#FF3B30/30" : pnl > 0 ? "bg-#FF3B30/15" : pnl > -3 ? "bg-#3FB950/15" : "bg-#3FB950/30"
                            )}
                          >
                            <p className="text-[9px] text-muted-foreground">{m}</p>
                            <p className={cn("text-[10px] font-mono font-medium", pnl >= 0 ? "text-#FF3B30" : "text-#3FB950")}>
                              {pnl >= 0 ? '+' : ''}{pnl}%
                            </p>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <button 
                      onClick={exportBacktest}
                      className="flex-1 text-xs px-3 py-1.5 bg-muted/50 hover:bg-muted rounded transition-colors"
                    >
                      <Download className="w-3 h-3 inline mr-1" />
                      导出报告
                    </button>
                    <button 
                      onClick={() => toast({ title: "保存成功", description: "策略已保存到我的策略库" })}
                      className="flex-1 text-xs px-3 py-1.5 bg-primary/10 text-primary hover:bg-primary/20 rounded transition-colors"
                    >
                      保存策略
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>

      {/* Row 7: Live vs Backtest Comparison */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.55 }}
        className="card-surface p-5 space-y-5"
      >
        <h3 className="text-sm font-semibold text-foreground tracking-tight">实盘信号 vs 回测信号</h3>

        {/* Filters */}
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3 p-3 bg-muted/20 rounded-lg border border-border/50">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground shrink-0 font-medium">策略</span>
              <select className="text-xs bg-background border border-border rounded px-2 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-primary">
                <option>北向资金跟踪</option>
                <option>价值成长策略</option>
                <option>技术突破策略</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground shrink-0 font-medium">股票池</span>
              <select className="text-xs bg-background border border-border rounded px-2 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-primary">
                <option>沪深300</option>
                <option>中证500</option>
                <option>全市场</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground shrink-0 font-medium">时间</span>
              <select className="text-xs bg-background border border-border rounded px-2 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-primary">
                <option>近 6 月</option>
                <option>近 1 月</option>
                <option>近 3 月</option>
                <option>近 1 年</option>
              </select>
            </div>
            <button className="text-xs text-primary hover:underline ml-auto flex items-center gap-1">
              <Filter className="w-3 h-3" />
              查看使用的因子
            </button>
          </div>
        </div>

        {/* Factor Tags */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <div className="flex flex-wrap items-center gap-2 p-3 bg-muted/20 rounded-lg border border-border/50">
            <span className="text-xs font-medium text-foreground shrink-0">使用的因子：</span>
            {['北向资金', 'ROE', '均线交叉', '量价配合'].map((f) => (
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

          {/* Comparison Table */}
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
                      m.deviation.startsWith('-') ? 'text-#3FB950' : 'text-#FF3B30'
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
          <div className="p-3.5 bg-muted/20 rounded-lg border border-border/50">
            <p className="text-xs font-semibold text-foreground mb-2.5">样本说明</p>
            <div className="space-y-2 text-xs text-muted-foreground">
              <div className="flex items-start gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500 mt-1 shrink-0" />
                <span>实盘信号期间：2025-12-17 ~ 2026-03-21（65 个交易日）</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-2 h-2 rounded-full bg-gray-500 mt-1 shrink-0" />
                <span>回测信号期间：2025-01-01 ~ 2025-12-31（242 个交易日）</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-2 h-2 rounded-full bg-muted-foreground mt-1 shrink-0" />
                <span>覆盖股票：沪深300成分股（285 只）</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-2 h-2 rounded-full bg-muted-foreground mt-1 shrink-0" />
                <span>信号总数：实盘 98 个 / 回测 125 个</span>
              </div>
            </div>
          </div>

          <div className="p-3.5 bg-amber-50/50 dark:bg-amber-950/15 rounded-lg border border-amber-200/50 dark:border-amber-700/40">
            <p className="text-xs font-semibold text-foreground mb-2.5">偏离度分析 · 可能原因</p>
            <div className="space-y-1.5 text-xs">
              <div className="flex items-start gap-2 text-amber-700 dark:text-amber-500">
                <span className="shrink-0 mt-0.5">•</span>
                <span>T+1交易限制：无法当日止损</span>
              </div>
              <div className="flex items-start gap-2 text-amber-700 dark:text-amber-500">
                <span className="shrink-0 mt-0.5">•</span>
                <span>涨跌停限制：部分信号无法执行</span>
              </div>
              <div className="flex items-start gap-2 text-amber-700 dark:text-amber-500">
                <span className="shrink-0 mt-0.5">•</span>
                <span>交易成本：印花税+佣金约0.15%</span>
              </div>
              <div className="flex items-start gap-2 text-amber-700 dark:text-amber-500">
                <span className="shrink-0 mt-0.5">•</span>
                <span>市场情绪：近期波动率较回测期有所上升</span>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
