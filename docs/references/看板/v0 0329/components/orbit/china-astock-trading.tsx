"use client";

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft, TrendingUp, TrendingDown, Download, Search,
  Filter, Plus, X, AlertTriangle, Eye, Edit2, Trash2,
  BarChart3, Target, Percent, Trophy, Clock, Wallet,
  PieChart, ChevronDown, CheckCircle2, XCircle, BookOpen, FileDown
} from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useToast } from "@/hooks/use-toast"
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, AreaChart, PieChart as RechartsPie, Pie, Cell, Legend
} from 'recharts'

interface ChinaAStockTradingProps {
  onBack: () => void
}

// Trading days per month
const TRADING_DAYS_PER_MONTH = [22, 20, 21, 22, 21, 22, 23, 22, 21, 23, 21, 22]
const MONTH_LABELS = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']

function generateCurveData(period: '本周' | '本月' | '本年' | '全部') {
  let manual = 165000
  let tracked = 0
  const data: { date: string; manual: number; tracked: number }[] = []

  if (period === '本周') {
    const days = ['周一','周二','周三','周四','周五','周六','周日']
    for (const day of days) {
      manual += (Math.random() - 0.45) * 3000
      tracked += (Math.random() - 0.4) * 0.4
      data.push({ date: day, manual: Math.round(manual), tracked: parseFloat((tracked + 3.2).toFixed(2)) })
    }
  } else if (period === '本月') {
    for (let d = 1; d <= 31; d++) {
      manual += (Math.random() - 0.45) * 2000
      tracked += (Math.random() - 0.4) * 0.3
      data.push({ date: `${d}日`, manual: Math.round(manual), tracked: parseFloat((tracked + 3.2).toFixed(2)) })
    }
  } else if (period === '本年') {
    for (let m = 1; m <= 12; m++) {
      manual += (Math.random() - 0.4) * 15000
      tracked += (Math.random() - 0.35) * 1.5
      data.push({ date: `${m}月`, manual: Math.round(manual), tracked: parseFloat((tracked + 3.2).toFixed(2)) })
    }
  } else {
    const now = new Date()
    for (let i = 90; i >= 0; i--) {
      const date = new Date(now)
      date.setDate(date.getDate() - i)
      manual += (Math.random() - 0.45) * 2500
      tracked += (Math.random() - 0.4) * 0.2
      data.push({
        date: `${date.getMonth() + 1}/${date.getDate()}`,
        manual: Math.round(manual),
        tracked: parseFloat((tracked + 3.2).toFixed(2)),
      })
    }
  }
  return data
}

function generateHeatmapData() {
  return MONTH_LABELS.map((month, mi) => ({
    month,
    days: Array.from({ length: TRADING_DAYS_PER_MONTH[mi] }, () => (Math.random() - 0.42) * 5000),
  }))
}

// Mock data
const manualHoldings = [
  { code: '600519', name: '贵州茅台', currentPrice: 1680, costPrice: 1650, qty: 100, pnl: 3000, pnlPct: 2.5, buyDate: '03-10', status: '跟踪中' as const },
  { code: '000858', name: '五粮液',   currentPrice: 168.5, costPrice: 165, qty: 100, pnl: 350, pnlPct: 2.1, buyDate: '03-12', status: '跟踪中' as const },
]

const trackedStocks = [
  { code: '600519', name: '贵州茅台', recPrice: 1650, currentPrice: 1680, pnlPct: 2.5, confidence: 85, recDate: '03-10', reason: '均线突破', status: '跟踪中' as const },
  { code: '000858', name: '五粮液',   recPrice: 165,  currentPrice: 168.5, pnlPct: 2.1, confidence: 78, recDate: '03-12', reason: '量价齐升', status: '跟踪中' as const },
  { code: '601318', name: '中国平安', recPrice: 48.5, currentPrice: 52.3, pnlPct: 7.8, confidence: 82, recDate: '03-05', reason: 'MACD金叉', status: '跟踪中' as const },
  { code: '600036', name: '招商银行', recPrice: 38.2, currentPrice: 37.5, pnlPct: -1.8, confidence: 71, recDate: '03-08', reason: '支撑位反弹', status: '跟踪中' as const },
  { code: '002475', name: '立讯精密', recPrice: 42.1, currentPrice: 45.6, pnlPct: 8.3, confidence: 88, recDate: '03-03', reason: '突破平台', status: '跟踪中' as const },
  { code: '300750', name: '宁德时代', recPrice: 215, currentPrice: 198, pnlPct: -7.9, confidence: 65, recDate: '02-28', reason: '超跌反弹', status: '跟踪中' as const },
  { code: '601899', name: '紫金矿业', recPrice: 16.8, currentPrice: 18.2, pnlPct: 8.3, confidence: 79, recDate: '03-01', reason: '黄金上涨驱动', status: '已止盈' as const },
  { code: '000725', name: '京东方A',  recPrice: 4.85, currentPrice: 4.62, pnlPct: -4.7, confidence: 60, recDate: '02-25', reason: '均值回归', status: '已止损' as const },
  { code: '600900', name: '长江电力', recPrice: 28.5, currentPrice: 29.8, pnlPct: 4.6, confidence: 83, recDate: '03-06', reason: '红利策略', status: '跟踪中' as const },
  { code: '601888', name: '中国中免', recPrice: 92,   currentPrice: 98.5, pnlPct: 7.1, confidence: 76, recDate: '03-04', reason: '消费复苏', status: '跟踪中' as const },
  { code: '600276', name: '恒瑞医药', recPrice: 56.3, currentPrice: 54.1, pnlPct: -3.9, confidence: 68, recDate: '03-02', reason: '创新药催化', status: '跟踪中' as const },
  { code: '000651', name: '格力电器', recPrice: 38.9, currentPrice: 41.2, pnlPct: 5.9, confidence: 74, recDate: '02-27', reason: '估值修复', status: '跟踪中' as const },
  { code: '600030', name: '中信证券', recPrice: 22.1, currentPrice: 23.5, pnlPct: 6.3, confidence: 77, recDate: '03-07', reason: '牛市布局', status: '跟踪中' as const },
  { code: '601166', name: '兴业银行', recPrice: 18.6, currentPrice: 18.1, pnlPct: -2.7, confidence: 63, recDate: '03-09', reason: '低估值配置', status: '跟踪中' as const },
  { code: '002594', name: '比亚迪',   recPrice: 285,  currentPrice: 298, pnlPct: 4.6, confidence: 81, recDate: '03-11', reason: '销量创新高', status: '跟踪中' as const },
]

const historyRecords = [
  { time: '03-12 09:45', code: '000858', name: '五粮液',   source: '手动', costPrice: 165,   currentPrice: 168.5, pnlPct: 2.1,  result: '盈利' as const },
  { time: '03-10 10:20', code: '600519', name: '贵州茅台', source: '手动', costPrice: 1650,  currentPrice: 1680,  pnlPct: 2.5,  result: '盈利' as const },
  { time: '03-07 14:30', code: '600030', name: '中信证券', source: '策略', costPrice: 22.1,  currentPrice: 23.5,  pnlPct: 6.3,  result: '盈利' as const },
  { time: '03-05 11:00', code: '601318', name: '中国平安', source: '策略', costPrice: 48.5,  currentPrice: 52.3,  pnlPct: 7.8,  result: '盈利' as const },
  { time: '03-03 09:50', code: '002475', name: '立讯精密', source: '策略', costPrice: 42.1,  currentPrice: 45.6,  pnlPct: 8.3,  result: '盈利' as const },
  { time: '03-01 10:05', code: '601899', name: '紫金矿业', source: '策略', costPrice: 16.8,  currentPrice: 18.2,  pnlPct: 8.3,  result: '已止盈' as const },
  { time: '02-28 13:15', code: '300750', name: '宁德时代', source: '策略', costPrice: 215,   currentPrice: 198,   pnlPct: -7.9, result: '亏损' as const },
  { time: '02-25 14:00', code: '000725', name: '京东方A',  source: '策略', costPrice: 4.85,  currentPrice: 4.62,  pnlPct: -4.7, result: '已止损' as const },
]

const performanceMetrics = [
  { name: '胜率',       value: '65.2%', icon: Target,    negative: false },
  { name: '平均盈利',   value: '3,850', icon: TrendingUp, negative: false },
  { name: '平均亏损',   value: '-1,580', icon: TrendingDown, negative: true },
  { name: '盈利因子',   value: '2.4',   icon: BarChart3, negative: false },
  { name: '最大单笔盈利', value: '8,500', icon: Trophy,   negative: false },
  { name: '最大单笔亏损', value: '-3,200', icon: XCircle, negative: true },
  { name: '平均持仓周期', value: '12 天', icon: Clock,    negative: false },
  { name: '跟踪股票数', value: '17 只',  icon: Eye,      negative: false },
]

const sectorData = [
  { name: '白酒消费', value: 35, color: '#EF4444' },
  { name: '金融保险', value: 22, color: '#f97316' },
  { name: '新能源',   value: 18, color: '#22C55E' },
  { name: '医药生物', value: 12, color: '#3b82f6' },
  { name: '科技硬件', value: 8,  color: '#a855f7' },
  { name: '其他',     value: 5,  color: '#9ca3af' },
]

const topProfit = [
  { code: '002475', name: '立讯精密', pnlPct: 8.3 },
  { code: '601899', name: '紫金矿业', pnlPct: 8.3 },
  { code: '601318', name: '中国平安', pnlPct: 7.8 },
  { code: '601888', name: '中国中免', pnlPct: 7.1 },
  { code: '600030', name: '中信证券', pnlPct: 6.3 },
]

const topLoss = [
  { code: '300750', name: '宁德时代', pnlPct: -7.9 },
  { code: '000725', name: '京东方A',  pnlPct: -4.7 },
  { code: '600276', name: '恒瑞医药', pnlPct: -3.9 },
  { code: '000651', name: '格力电器', pnlPct: -2.7 },  // adjusted to loss for demo
  { code: '601166', name: '兴业银行', pnlPct: -2.7 },
]

// Strategy signals for import
const strategySignals = [
  { code: '600519', name: '贵州茅台', recPrice: 1680, confidence: 85, reason: '北向资金流入+均线多头' },
  { code: '000858', name: '五粮液', recPrice: 168, confidence: 78, reason: '量价配合' },
  { code: '601318', name: '中国平安', recPrice: 52, confidence: 82, reason: '估值修复' },
  { code: '002475', name: '立讯精密', recPrice: 45, confidence: 88, reason: '苹果产业链' },
  { code: '600036', name: '招商银行', recPrice: 37, confidence: 75, reason: '业绩超预期' },
]

export function ChinaAStockTrading({ onBack }: ChinaAStockTradingProps) {
  const { toast } = useToast()
  const [curvePeriod, setCurvePeriod] = useState<'本周' | '本月' | '本年' | '全部'>('本月')
  const [activeTab, setActiveTab] = useState<'manual' | 'tracked'>('manual')
  const [historyStatusFilter, setHistoryStatusFilter] = useState('全部')
  const [historySourceFilter, setHistorySourceFilter] = useState('全部')
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  
  // Dialog states
  const [showSellDialog, setShowSellDialog] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showImportDialog, setShowImportDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [selectedStock, setSelectedStock] = useState<typeof manualHoldings[0] | null>(null)
  const [selectedTracked, setSelectedTracked] = useState<typeof trackedStocks[0] | null>(null)
  const [selectedImports, setSelectedImports] = useState<string[]>([])
  
  // Loading states
  const [isSelling, setIsSelling] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  
  // Edit form state
  const [editForm, setEditForm] = useState({
    code: '',
    name: '',
    costPrice: '',
    qty: '',
    buyDate: '',
    takeProfitPct: '',
    stopLossPct: '',
    trackPrice: false,
    trackSignal: false,
    trackNews: false,
    remark: ''
  })

  const curveData = generateCurveData(curvePeriod)
  const heatmapData = generateHeatmapData()

  // Search filter for manual holdings and tracked stocks
  const filteredManualHoldings = useMemo(() => {
    if (!searchQuery.trim()) return manualHoldings
    const query = searchQuery.toLowerCase()
    return manualHoldings.filter(h => 
      h.code.toLowerCase().includes(query) || 
      h.name.toLowerCase().includes(query)
    )
  }, [searchQuery])

  const filteredTrackedStocks = useMemo(() => {
    if (!searchQuery.trim()) return trackedStocks
    const query = searchQuery.toLowerCase()
    return trackedStocks.filter(s => 
      s.code.toLowerCase().includes(query) || 
      s.name.toLowerCase().includes(query)
    )
  }, [searchQuery])

  const filteredHistory = historyRecords.filter(r => {
    const statusOk = historyStatusFilter === '全部' || r.result === historyStatusFilter
    const sourceOk = historySourceFilter === '全部' || r.source === historySourceFilter
    return statusOk && sourceOk
  })

  // CSV Export functions
  const exportCSV = (data: Record<string, unknown>[], filename: string) => {
    if (data.length === 0) {
      toast({ title: "导出失败", description: "没有数据可导出", variant: "destructive" })
      return
    }
    const headers = Object.keys(data[0]).join(',')
    const rows = data.map(row => Object.values(row).join(','))
    const csv = '\uFEFF' + [headers, ...rows].join('\n') // BOM for Chinese support
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
    toast({ title: "导出成功", description: `已导出 ${data.length} 条记录` })
  }

  const exportManualHoldings = () => {
    const data = manualHoldings.map(h => ({
      '代码': h.code,
      '名称': h.name,
      '当前价': h.currentPrice,
      '成本价': h.costPrice,
      '数量': h.qty,
      '浮动盈亏': h.pnl,
      '收益率': `${h.pnlPct}%`,
      '买入日期': h.buyDate,
      '状态': h.status
    }))
    exportCSV(data, '手动持仓')
  }

  const exportTrackedStocks = () => {
    const data = trackedStocks.map(s => ({
      '代码': s.code,
      '名称': s.name,
      '推荐价': s.recPrice,
      '当前价': s.currentPrice,
      '盈利率': `${s.pnlPct}%`,
      '置信度': `${s.confidence}%`,
      '推荐日期': s.recDate,
      '推荐理由': s.reason,
      '状态': s.status
    }))
    exportCSV(data, '跟踪股票')
  }

  const exportHistory = () => {
    const data = filteredHistory.map(h => ({
      '时间': h.time,
      '代码': h.code,
      '名称': h.name,
      '来源': h.source,
      '成本价': h.costPrice,
      '当前价': h.currentPrice,
      '收益率': `${h.pnlPct}%`,
      '结果': h.result
    }))
    exportCSV(data, '历史记录')
  }

  // Dialog handlers
  const handleMarkSell = (stock: typeof manualHoldings[0]) => {
    setSelectedStock(stock)
    setShowSellDialog(true)
  }

  const confirmSell = async () => {
    if (selectedStock) {
      setIsSelling(true)
      await new Promise(r => setTimeout(r, 800))
      setIsSelling(false)
      toast({ title: "卖出成功", description: `已卖出 ${selectedStock.name}` })
      setShowSellDialog(false)
      setSelectedStock(null)
    }
  }

  const handleDelete = (stock: typeof manualHoldings[0] | typeof trackedStocks[0], type: 'manual' | 'tracked') => {
    if (type === 'manual') {
      setSelectedStock(stock as typeof manualHoldings[0])
      setSelectedTracked(null)
    } else {
      setSelectedTracked(stock as typeof trackedStocks[0])
      setSelectedStock(null)
    }
    setShowDeleteDialog(true)
  }

  const confirmDelete = () => {
    const name = selectedStock?.name || selectedTracked?.name
    toast({ title: "删除成功", description: `已删除 ${name}` })
    setShowDeleteDialog(false)
    setSelectedStock(null)
    setSelectedTracked(null)
  }

  const handleImport = () => {
    setSelectedImports([])
    setShowImportDialog(true)
  }

  const handleEdit = (stock: typeof manualHoldings[0]) => {
    setSelectedStock(stock)
    setEditForm({
      code: stock.code,
      name: stock.name,
      costPrice: stock.costPrice.toString(),
      qty: stock.qty.toString(),
      buyDate: `2026-${stock.buyDate}`,
      takeProfitPct: '10',
      stopLossPct: '-5',
      trackPrice: true,
      trackSignal: true,
      trackNews: false,
      remark: ''
    })
    setShowEditDialog(true)
  }

  const confirmEdit = async () => {
    if (selectedStock) {
      setIsSaving(true)
      await new Promise(r => setTimeout(r, 800))
      setIsSaving(false)
      toast({ title: "保存成功", description: `已更新 ${selectedStock.name} 的信息` })
      setShowEditDialog(false)
      setSelectedStock(null)
    }
  }

  const toggleImportSelect = (code: string) => {
    setSelectedImports(prev => 
      prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code]
    )
  }

  const confirmImport = async () => {
    setIsImporting(true)
    await new Promise(r => setTimeout(r, 800))
    setIsImporting(false)
    toast({ title: "导入成功", description: `已添加 ${selectedImports.length} 只股票到跟踪列表` })
    setSelectedImports([])
    setShowImportDialog(false)
  }

  return (
    <div className="h-full overflow-y-auto bg-background">
      <div className="p-6 space-y-5 max-w-[1600px] mx-auto">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <button
              onClick={onBack}
              className="flex items-center justify-center w-8 h-8 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <h1 className="text-lg font-semibold text-foreground tracking-tight">交易记录 - 中国 A 股</h1>
              <p className="text-xs text-muted-foreground mt-0.5">荐股追踪、持仓记录、绩效数据</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Search box */}
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <input
                type="text"
                placeholder="搜索代码/名称..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 w-40 border border-border rounded-lg text-xs bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
            <button
              onClick={() => setShowAddDialog(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-xs font-medium hover:bg-primary/90 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              添加跟踪股票
            </button>
            <button 
              onClick={handleImport}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-border rounded-lg text-xs text-muted-foreground hover:bg-muted transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              从策略导入
            </button>
            <button 
              onClick={activeTab === 'manual' ? exportManualHoldings : exportTrackedStocks}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-border rounded-lg text-xs text-muted-foreground hover:bg-muted transition-colors"
            >
              <FileDown className="w-3.5 h-3.5" />
              导出报表
            </button>
          </div>
        </motion.div>

        {/* Risk Warning */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-start gap-3 px-4 py-3 bg-amber-500/8 border border-amber-500/20 rounded-xl"
        >
          <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
          <p className="text-xs text-amber-600 dark:text-amber-400 leading-relaxed">
            <span className="font-semibold">风险提示：</span>本页面所有股票仅为策略荐股参考，不构成投资建议。股市有风险，投资需谨慎。
          </p>
        </motion.div>

        {/* Row 1: KPI Cards */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-4 gap-3"
        >
          {/* Manual group */}
          <div className="col-span-4 grid grid-cols-4 gap-3">
            <div className="col-span-4">
              <p className="text-[10px] font-medium text-muted-foreground/60 uppercase tracking-widest mb-2">手动录入组（实际持仓）</p>
            </div>
            {[
              { label: '总投入',     value: '165,000', sub: null,      icon: Wallet,     positive: false },
              { label: '总浮盈',     value: '4,500',   sub: '+2.5%',   icon: TrendingUp, positive: true  },
              { label: '持仓数量',   value: '2 只',    sub: null,      icon: BookOpen,   positive: false },
              { label: '平均收益率', value: '+2.3%',   sub: null,      icon: Percent,    positive: true  },
            ].map((kpi, i) => (
              <div key={i} className="card-surface p-4 flex flex-col items-center justify-center text-center min-h-[90px]">
                <div className="flex items-center gap-1.5 mb-2">
                  <kpi.icon className={cn('w-3.5 h-3.5', kpi.positive ? 'text-#FF3B30' : 'text-primary')} />
                  <span className="text-xs text-muted-foreground">{kpi.label}</span>
                </div>
                <p className={cn('text-xl font-semibold font-mono', kpi.positive ? 'text-red-600' : 'text-foreground')}>{kpi.value}</p>
                {kpi.sub && <p className="text-xs font-mono mt-1 text-#FF3B30">{kpi.sub}</p>}
              </div>
            ))}
          </div>

          {/* Tracked group */}
          <div className="col-span-4 grid grid-cols-4 gap-3">
            <div className="col-span-4">
              <p className="text-[10px] font-medium text-muted-foreground/60 uppercase tracking-widest mb-2">按键追踪组（虚拟跟踪）</p>
            </div>
            {[
              { label: '跟踪中',   value: '15 只',  sub: null,    icon: Eye,        positive: false },
              { label: '平均盈利', value: '+3.2%',  sub: null,    icon: TrendingUp, positive: true  },
              { label: '胜率',     value: '65.2%',  sub: null,    icon: Target,     positive: false },
              { label: '最高盈利', value: '+8.5%',  sub: null,    icon: Trophy,     positive: true  },
            ].map((kpi, i) => (
              <div key={i} className="card-surface p-4 flex flex-col items-center justify-center text-center min-h-[90px]">
                <div className="flex items-center gap-1.5 mb-2">
                  <kpi.icon className={cn('w-3.5 h-3.5', kpi.positive ? 'text-#FF3B30' : 'text-primary')} />
                  <span className="text-xs text-muted-foreground">{kpi.label}</span>
                </div>
                <p className={cn('text-xl font-semibold font-mono', kpi.positive ? 'text-red-600' : 'text-foreground')}>{kpi.value}</p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Row 2: Curve Chart */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card-surface p-5"
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-foreground tracking-tight">跟踪收益曲线</h3>
              <p className="text-xs text-muted-foreground mt-1">蓝色：���动组合（元）· 红色：追踪平均（%）</p>
            </div>
            <div className="flex gap-1">
              {(['本周','本月','本年','全部'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setCurvePeriod(p)}
                  className={cn(
                    'px-2.5 py-1 text-xs font-medium rounded transition-colors',
                    curvePeriod === p ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                  )}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
          <div className="h-[220px]" key={curvePeriod}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={curveData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.1)" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#9ca3af' }} interval="preserveStartEnd" />
                <YAxis yAxisId="left" tick={{ fontSize: 10, fill: '#9ca3af' }} tickFormatter={(v) => `${(v/1000).toFixed(0)}K`} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10, fill: '#9ca3af' }} tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: 11 }}
                  formatter={(value: number, name: string) => [
                    name === 'manual' ? value.toLocaleString() : `${value}%`,
                    name === 'manual' ? '手动组合' : '追踪平均'
                  ]}
                />
                <Line yAxisId="left" type="monotone" dataKey="manual" stroke="#3b82f6" strokeWidth={1.5} dot={false} />
                <Line yAxisId="right" type="monotone" dataKey="tracked" stroke="#EF4444" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Row 3: Stock List with Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="card-surface"
        >
          {/* Tab header */}
          <div className="flex items-center justify-between px-5 pt-5 pb-0 border-b border-border/40">
            <div className="flex gap-0">
              {[
                { id: 'manual' as const, label: '手动录入' },
                { id: 'tracked' as const, label: '按键追踪' },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
                    activeTab === tab.id
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <AnimatePresence mode="wait">
            {activeTab === 'manual' ? (
              <motion.div key="manual" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="p-5">
                <div className="flex items-center gap-4 mb-4 text-xs text-muted-foreground">
                  <span>跟踪中: <span className="font-mono text-foreground">2 只</span></span>
                  <span>总浮盈: <span className="font-mono text-red-600">+4,500</span></span>
                  <span>平均收益率: <span className="font-mono text-red-600">+2.3%</span></span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs min-w-[900px]">
                    <thead>
                      <tr className="border-b border-border/30">
                        {['代码','名称','当前价','持仓成本','数量','浮动盈亏','收益率','买入日','状态','操作'].map(h => (
                          <th key={h} className="py-2 px-3 text-left text-muted-foreground font-medium whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {filteredManualHoldings.length === 0 ? (
                        <tr>
                          <td colSpan={11} className="py-8 text-center text-muted-foreground text-xs">
                            暂无持仓数据
                          </td>
                        </tr>
                      ) : filteredManualHoldings.map((row) => (
                        <tr key={row.code} className="border-b border-border/20 hover:bg-muted/20 transition-colors">
                          <td className="py-3 px-3 font-mono font-semibold text-primary cursor-pointer hover:underline whitespace-nowrap">{row.code}</td>
                          <td className="py-3 px-3 font-medium whitespace-nowrap">{row.name}</td>
                          <td className="py-3 px-3 font-mono whitespace-nowrap">{row.currentPrice.toLocaleString()}</td>
                          <td className="py-3 px-3 font-mono text-muted-foreground whitespace-nowrap">{row.costPrice.toLocaleString()}</td>
                          <td className="py-3 px-3 font-mono whitespace-nowrap">{row.qty}</td>
                          <td className={cn('py-3 px-3 font-mono font-medium whitespace-nowrap', row.pnl >= 0 ? 'text-red-600' : 'text-emerald-600')}>
                            {row.pnl >= 0 ? '+' : ''}{row.pnl.toLocaleString()}
                          </td>
                          <td className={cn('py-3 px-3 font-mono font-medium whitespace-nowrap', row.pnlPct >= 0 ? 'text-red-600' : 'text-emerald-600')}>
                            {row.pnlPct >= 0 ? '+' : ''}{row.pnlPct}%
                          </td>
                          <td className="py-3 px-3 text-muted-foreground whitespace-nowrap">{row.buyDate}</td>
                          <td className="py-3 px-3 whitespace-nowrap">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-500/10 text-blue-500">{row.status}</span>
                          </td>
                          <td className="py-3 px-3 whitespace-nowrap">
                            <div className="flex items-center gap-1.5">
                              <button onClick={() => handleEdit(row)} className="p-1 hover:bg-muted rounded text-muted-foreground hover:text-foreground transition-colors"><Edit2 className="w-3 h-3" /></button>
                              <button className="p-1 hover:bg-muted rounded text-muted-foreground hover:text-foreground transition-colors"><Eye className="w-3 h-3" /></button>
                              <button 
                                onClick={() => handleDelete(row, 'manual')}
                                className="p-1 hover:bg-muted rounded text-muted-foreground hover:text-#FF3B30 transition-colors"
                              >
                                <Trash2 className="w-3 h-3" />
                              </button>
                              <button 
                                onClick={() => handleMarkSell(row)}
                                className="px-2 py-0.5 text-[10px] bg-#FF3B30/10 text-red-600 rounded hover:bg-#FF3B30/20 transition-colors whitespace-nowrap"
                              >
                                标记卖出
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            ) : (
              <motion.div key="tracked" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="p-5">
                <div className="flex items-center gap-4 mb-4 text-xs text-muted-foreground">
                  <span>跟踪中: <span className="font-mono text-foreground">15 只</span></span>
                  <span>平均盈利: <span className="font-mono text-red-600">+3.2%</span></span>
                  <span>胜率: <span className="font-mono text-foreground">65.2%</span></span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs min-w-[1000px]">
                    <thead>
                      <tr className="border-b border-border/30">
                        {['代码','名称','推荐价','当前价','盈利%','置信度','推荐日','推荐理由','状态','操作'].map(h => (
                          <th key={h} className="py-2 px-3 text-left text-muted-foreground font-medium whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTrackedStocks.length === 0 ? (
                        <tr>
                          <td colSpan={10} className="py-8 text-center text-muted-foreground text-xs">
                            暂无跟踪数据
                          </td>
                        </tr>
                      ) : filteredTrackedStocks.map((row) => (
                        <tr key={row.code} className="border-b border-border/20 hover:bg-muted/20 transition-colors">
                          <td className="py-3 px-3 font-mono font-semibold text-primary cursor-pointer hover:underline whitespace-nowrap">{row.code}</td>
                          <td className="py-3 px-3 font-medium whitespace-nowrap">{row.name}</td>
                          <td className="py-3 px-3 font-mono text-muted-foreground whitespace-nowrap">{row.recPrice}</td>
                          <td className="py-3 px-3 font-mono whitespace-nowrap">{row.currentPrice}</td>
                          <td className={cn('py-3 px-3 font-mono font-medium whitespace-nowrap', row.pnlPct >= 0 ? 'text-red-600' : 'text-emerald-600')}>
                            {row.pnlPct >= 0 ? '+' : ''}{row.pnlPct}%
                          </td>
                          <td className="py-3 px-3 whitespace-nowrap">
                            <div className="flex items-center gap-2">
                              <div className="h-1 w-16 bg-muted rounded-full overflow-hidden">
                                <div className="h-full bg-primary rounded-full" style={{ width: `${row.confidence}%` }} />
                              </div>
                              <span className="font-mono text-muted-foreground">{row.confidence}%</span>
                            </div>
                          </td>
                          <td className="py-3 px-3 text-muted-foreground whitespace-nowrap">{row.recDate}</td>
                          <td className="py-3 px-3 text-muted-foreground whitespace-nowrap">{row.reason}</td>
                          <td className="py-3 px-3 whitespace-nowrap">
                            <span className={cn(
                              'px-2 py-0.5 rounded-full text-[10px] font-medium',
                              row.status === '跟踪中' && 'bg-blue-500/10 text-blue-500',
                              row.status === '已止盈' && 'bg-#FF3B30/10 text-#FF3B30',
                              row.status === '已止损' && 'bg-emerald-500/10 text-emerald-500',
                            )}>
                              {row.status}
                            </span>
                          </td>
                          <td className="py-3 px-3 whitespace-nowrap">
                            <div className="flex items-center gap-1.5">
                              <button className="p-1 hover:bg-muted rounded text-muted-foreground hover:text-foreground transition-colors"><Eye className="w-3 h-3" /></button>
                              <button 
                                onClick={() => handleDelete(row, 'tracked')}
                                className="p-1 hover:bg-muted rounded text-muted-foreground hover:text-#FF3B30 transition-colors"
                              >
                                <Trash2 className="w-3 h-3" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Row 4: History Records */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card-surface p-5"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground tracking-tight">荐股历史记录</h3>
            <div className="flex items-center gap-2">
              <div className="flex gap-1">
                {(['全部','盈利','亏损','已止盈','已止损'] as const).map(s => (
                  <button
                    key={s}
                    onClick={() => setHistoryStatusFilter(s)}
                    className={cn(
                      'px-2.5 py-1 text-[11px] rounded transition-colors font-medium',
                      historyStatusFilter === s ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                    )}
                  >
                    {s}
                  </button>
                ))}
              </div>
              <div className="w-px h-4 bg-border/50" />
              <div className="flex gap-1">
                {(['全部','手动','策略'] as const).map(s => (
                  <button
                    key={s}
                    onClick={() => setHistorySourceFilter(s)}
                    className={cn(
                      'px-2.5 py-1 text-[11px] rounded transition-colors font-medium',
                      historySourceFilter === s ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                    )}
                  >
                    {s}
                  </button>
                ))}
              </div>
              <button 
                onClick={exportHistory}
                className="flex items-center gap-1 px-2.5 py-1 border border-border rounded text-[11px] text-muted-foreground hover:bg-muted transition-colors"
              >
                <Download className="w-3 h-3" /> 导出 CSV
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs min-w-[900px]">
              <thead>
                <tr className="border-b border-border/30">
                  {['时间','代码','名称','来源','成本价/推荐价','当前价','收益率','结果','操作'].map(h => (
                    <th key={h} className="py-2 px-3 text-left text-muted-foreground font-medium whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredHistory.map((row, i) => (
                  <tr key={i} className="border-b border-border/20 hover:bg-muted/20 transition-colors">
                    <td className="py-3 px-3 text-muted-foreground whitespace-nowrap">{row.time}</td>
                    <td className="py-3 px-3 font-mono font-semibold text-primary cursor-pointer hover:underline whitespace-nowrap">{row.code}</td>
                    <td className="py-3 px-3 font-medium whitespace-nowrap">{row.name}</td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span className={cn(
                        'px-2 py-0.5 rounded-full text-[10px] font-medium',
                        row.source === '手动' ? 'bg-blue-500/10 text-blue-500' : 'bg-purple-500/10 text-purple-500'
                      )}>
                        {row.source}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-muted-foreground whitespace-nowrap">{row.costPrice}</td>
                    <td className="py-3 px-3 font-mono whitespace-nowrap">{row.currentPrice}</td>
                    <td className={cn('py-3 px-3 font-mono font-medium whitespace-nowrap', row.pnlPct >= 0 ? 'text-red-600' : 'text-emerald-600')}>
                      {row.pnlPct >= 0 ? '+' : ''}{row.pnlPct}%
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span className={cn(
                        'px-2 py-0.5 rounded-full text-[10px] font-medium',
                        row.result === '盈利' || row.result === '已止盈'   ? 'bg-#FF3B30/10 text-#FF3B30'     :
                        row.result === '亏损' || row.result === '已止损'   ? 'bg-emerald-500/10 text-emerald-500' : ''
                      )}>
                        {row.result}
                      </span>
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <button className="flex items-center gap-1 px-2 py-0.5 text-[11px] text-primary hover:bg-muted rounded transition-colors whitespace-nowrap">
                        <Eye className="w-3 h-3" /> 查看
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Row 5: Performance + Heatmap */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="grid grid-cols-2 gap-5"
        >
          {/* Performance metrics */}
          <div className="card-surface p-5">
            <h3 className="text-sm font-semibold text-foreground tracking-tight mb-4">绩效指标</h3>
            <div className="grid grid-cols-2 gap-3">
              {performanceMetrics.map((metric, i) => (
                <div key={i} className="p-3 bg-muted/30 rounded-lg flex flex-col items-center justify-center text-center">
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <metric.icon className={cn('w-3.5 h-3.5', metric.negative ? 'text-emerald-500' : 'text-primary')} />
                    <span className="text-[10px] text-muted-foreground">{metric.name}</span>
                  </div>
                  <p className={cn('text-lg font-semibold font-mono', metric.negative ? 'text-emerald-600' : 'text-foreground')}>
                    {metric.value}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Heatmap */}
          <div className="card-surface p-5">
            <h3 className="text-sm font-semibold text-foreground tracking-tight mb-4">月度盈亏热力图</h3>
            <div className="space-y-1.5 overflow-y-auto max-h-[320px] pr-1">
              {heatmapData.map(({ month, days }) => (
                <div key={month} className="flex items-center gap-2">
                  <span className="text-[10px] text-muted-foreground w-8 shrink-0">{month}</span>
                  <div className="flex gap-0.5 flex-1">
                    {days.map((value, i) => (
                      <div
                        key={i}
                        className={cn(
                          'flex-1 h-5 rounded-sm transition-colors cursor-pointer hover:ring-1 hover:ring-primary',
                          value > 3000  ? 'bg-#FF3B30' :
                          value > 1000  ? 'bg-red-400' :
                          value > 0     ? 'bg-red-300' :
                          value > -1000 ? 'bg-emerald-300' :
                          value > -3000 ? 'bg-emerald-400' :
                                          'bg-emerald-500'
                        )}
                        title={`${Math.round(value).toLocaleString()}`}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-center gap-4 mt-3 text-[10px] text-muted-foreground">
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-emerald-500 rounded-sm inline-block" /> 亏损</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-#FF3B30 rounded-sm inline-block" /> 盈利</span>
            </div>
          </div>
        </motion.div>

        {/* Row 6: Sector + Top Stocks */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="grid grid-cols-2 gap-5"
        >
          {/* Sector pie */}
          <div className="card-surface p-5">
            <h3 className="text-sm font-semibold text-foreground tracking-tight mb-4">行业分布</h3>
            <div className="h-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsPie>
                  <Pie
                    data={sectorData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, value }) => `${name} ${value}%`}
                    labelLine={false}
                  >
                    {sectorData.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: 11 }}
                    formatter={(value: number) => [`${value}%`, '占比']}
                  />
                </RechartsPie>
              </ResponsiveContainer>
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 justify-center">
              {sectorData.map((s) => (
                <span key={s.name} className="flex items-center gap-1 text-[10px] text-muted-foreground">
                  <span className="w-2 h-2 rounded-full inline-block" style={{ background: s.color }} />
                  {s.name}
                </span>
              ))}
            </div>
          </div>

          {/* Top stocks */}
          <div className="card-surface p-5">
            <h3 className="text-sm font-semibold text-foreground tracking-tight mb-4">个股收益排行</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[10px] font-medium text-muted-foreground mb-2">Top 5 盈利</p>
                <div className="space-y-2">
                  {topProfit.map((item, i) => (
                    <div key={item.code} className="flex items-center gap-2">
                      <span className="text-[10px] font-mono text-muted-foreground w-4">{i + 1}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-mono font-semibold text-foreground truncate">{item.code}</p>
                        <p className="text-[10px] text-muted-foreground truncate">{item.name}</p>
                      </div>
                      <span className="text-xs font-mono font-medium text-red-600">+{item.pnlPct}%</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-[10px] font-medium text-muted-foreground mb-2">Top 5 亏损</p>
                <div className="space-y-2">
                  {topLoss.map((item, i) => (
                    <div key={item.code} className="flex items-center gap-2">
                      <span className="text-[10px] font-mono text-muted-foreground w-4">{i + 1}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-mono font-semibold text-foreground truncate">{item.code}</p>
                        <p className="text-[10px] text-muted-foreground truncate">{item.name}</p>
                      </div>
                      <span className="text-xs font-mono font-medium text-emerald-600">{item.pnlPct}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </motion.div>

      </div>

      {/* Add Stock Dialog */}
      <AnimatePresence>
        {showAddDialog && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={(e) => e.target === e.currentTarget && setShowAddDialog(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-card border border-border rounded-2xl p-6 w-full max-w-[480px] shadow-xl"
            >
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h2 className="text-sm font-semibold text-foreground">手动录入股票</h2>
                  <p className="text-xs text-muted-foreground mt-0.5">记录实际持仓，追踪真实收益</p>
                </div>
                <button onClick={() => setShowAddDialog(false)} className="p-1.5 hover:bg-muted rounded-lg transition-colors text-muted-foreground">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Step 1: Search */}
                <div>
                  <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide block mb-1.5">步骤 1 · 搜索股票</label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="输入代码或名称..."
                      className="w-full pl-8 pr-3 py-2.5 bg-muted/40 border border-border rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-primary transition-shadow"
                    />
                  </div>
                  {searchQuery && (
                    <div className="mt-1 border border-border rounded-lg overflow-hidden">
                      <button className="w-full text-left px-3 py-2 text-xs hover:bg-muted/50 transition-colors flex items-center justify-between">
                        <span><span className="font-mono font-semibold text-foreground">600519</span> · 贵州茅台 · 白酒</span>
                        <span className="text-red-600 font-mono">1,680 +2.5%</span>
                      </button>
                    </div>
                  )}
                </div>

                {/* Step 2: Position info */}
                <div>
                  <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide block mb-1.5">步骤 2 · 填写持仓信息</label>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: '股票代码', placeholder: '600519', type: 'text' },
                      { label: '股票名称', placeholder: '贵州茅台', type: 'text' },
                      { label: '持仓成本 (元/股)', placeholder: '1,650', type: 'number' },
                      { label: '持仓数量 (股)', placeholder: '100', type: 'number' },
                    ].map(field => (
                      <div key={field.label}>
                        <label className="text-[10px] text-muted-foreground block mb-1">{field.label}</label>
                        <input
                          type={field.type}
                          placeholder={field.placeholder}
                          className="w-full px-3 py-2 bg-muted/40 border border-border rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-primary transition-shadow"
                        />
                      </div>
                    ))}
                    <div>
                      <label className="text-[10px] text-muted-foreground block mb-1">买入日期</label>
                      <input
                        type="date"
                        className="w-full px-3 py-2 bg-muted/40 border border-border rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-primary transition-shadow"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground block mb-1">投入金额（自动计算）</label>
                      <input
                        readOnly
                        placeholder="165,000"
                        className="w-full px-3 py-2 bg-muted/20 border border-border/50 rounded-lg text-xs text-muted-foreground cursor-not-allowed"
                      />
                    </div>
                  </div>
                </div>

                {/* Step 3: Tracking settings */}
                <div>
                  <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide block mb-1.5">步骤 3 · 跟踪设置</label>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[10px] text-muted-foreground block mb-1">止盈位 (%)</label>
                      <input type="number" placeholder="+10" className="w-full px-3 py-2 bg-muted/40 border border-border rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-primary transition-shadow" />
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground block mb-1">止损位 (%)</label>
                      <input type="number" placeholder="-5" className="w-full px-3 py-2 bg-muted/40 border border-border rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-primary transition-shadow" />
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button onClick={() => setShowAddDialog(false)} className="flex-1 py-2 border border-border rounded-lg text-xs font-medium text-muted-foreground hover:bg-muted transition-colors">
                  取消
                </button>
                <button onClick={() => setShowAddDialog(false)} className="flex-1 py-2 bg-primary text-primary-foreground rounded-lg text-xs font-medium hover:bg-primary/90 transition-colors">
                  确认添加
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sell Confirmation Dialog */}
      <Dialog open={showSellDialog} onOpenChange={setShowSellDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>确认标记卖出</DialogTitle>
            <DialogDescription>
              确认将以下股票标记为已卖出？
            </DialogDescription>
          </DialogHeader>
          {selectedStock && (
            <div className="space-y-3 py-4">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">股票代码</p>
                  <p className="font-mono font-semibold text-primary">{selectedStock.code}</p>
                </div>
                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">股票名称</p>
                  <p className="font-medium">{selectedStock.name}</p>
                </div>
                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">当前价</p>
                  <p className="font-mono">{selectedStock.currentPrice.toLocaleString()}</p>
                </div>
                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">成本价</p>
                  <p className="font-mono text-muted-foreground">{selectedStock.costPrice.toLocaleString()}</p>
                </div>
                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">浮动盈亏</p>
                  <p className={cn("font-mono font-medium", selectedStock.pnl >= 0 ? "text-red-600" : "text-emerald-600")}>
                    {selectedStock.pnl >= 0 ? '+' : ''}{selectedStock.pnl.toLocaleString()}
                  </p>
                </div>
                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">收益率</p>
                  <p className={cn("font-mono font-medium", selectedStock.pnlPct >= 0 ? "text-red-600" : "text-emerald-600")}>
                    {selectedStock.pnlPct >= 0 ? '+' : ''}{selectedStock.pnlPct}%
                  </p>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSellDialog(false)}>取消</Button>
            <Button variant="destructive" onClick={confirmSell} disabled={isSelling}>
              {isSelling ? <><Spinner className="w-4 h-4 mr-1" />处理中...</> : "确认标记为已卖出"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-#FF3B30" />
              确认删除
            </DialogTitle>
            <DialogDescription>
              确认删除 <span className="font-semibold text-foreground">{selectedStock?.name || selectedTracked?.name}</span>？
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="p-3 bg-#FF3B30/10 border border-#FF3B30/20 rounded-lg">
              <p className="text-xs text-red-600 flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5" />
                删除后无法恢复，请谨慎操作
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>取消</Button>
            <Button variant="destructive" onClick={confirmDelete}>确认删除</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Import from Strategy Dialog */}
      <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>从策略导入</DialogTitle>
            <DialogDescription>
              选择要导入到跟踪列表的策略荐股
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 max-h-[300px] overflow-y-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border">
                  <th className="py-2 px-2 text-left w-8"></th>
                  <th className="py-2 px-2 text-left text-muted-foreground">代码</th>
                  <th className="py-2 px-2 text-left text-muted-foreground">名称</th>
                  <th className="py-2 px-2 text-right text-muted-foreground">推荐价</th>
                  <th className="py-2 px-2 text-right text-muted-foreground">置信度</th>
                  <th className="py-2 px-2 text-left text-muted-foreground">推荐理由</th>
                </tr>
              </thead>
              <tbody>
                {strategySignals.map((signal) => (
                  <tr 
                    key={signal.code} 
                    className={cn(
                      "border-b border-border/50 cursor-pointer transition-colors",
                      selectedImports.includes(signal.code) ? "bg-primary/10" : "hover:bg-muted/50"
                    )}
                    onClick={() => toggleImportSelect(signal.code)}
                  >
                    <td className="py-2.5 px-2">
                      <input 
                        type="checkbox" 
                        checked={selectedImports.includes(signal.code)}
                        onChange={() => toggleImportSelect(signal.code)}
                        className="w-3.5 h-3.5 rounded border-border"
                      />
                    </td>
                    <td className="py-2.5 px-2 font-mono font-semibold text-primary">{signal.code}</td>
                    <td className="py-2.5 px-2 font-medium">{signal.name}</td>
                    <td className="py-2.5 px-2 text-right font-mono">{signal.recPrice}</td>
                    <td className="py-2.5 px-2 text-right">
                      <span className="px-1.5 py-0.5 rounded bg-primary/10 text-primary font-medium">{signal.confidence}%</span>
                    </td>
                    <td className="py-2.5 px-2 text-muted-foreground max-w-[150px] truncate" title={signal.reason}>{signal.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              已选择 <span className="font-semibold text-foreground">{selectedImports.length}</span> 只股票
            </p>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowImportDialog(false)}>取消</Button>
              <Button onClick={confirmImport} disabled={selectedImports.length === 0 || isImporting}>
                {isImporting ? <><Spinner className="w-4 h-4 mr-1" />导入中...</> : "确认导入"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Stock Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>编辑股票信息</DialogTitle>
            <DialogDescription>
              修改持仓信息和跟踪设置
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {/* Basic info */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-muted-foreground block mb-1">股票代���</label>
                <Input
                  value={editForm.code}
                  onChange={(e) => setEditForm(f => ({ ...f, code: e.target.value }))}
                  className="h-8 text-xs"
                  readOnly
                />
              </div>
              <div>
                <label className="text-[10px] text-muted-foreground block mb-1">股票名称</label>
                <Input
                  value={editForm.name}
                  onChange={(e) => setEditForm(f => ({ ...f, name: e.target.value }))}
                  className="h-8 text-xs"
                  readOnly
                />
              </div>
              <div>
                <label className="text-[10px] text-muted-foreground block mb-1">持仓成本 (元/股)</label>
                <Input
                  type="number"
                  value={editForm.costPrice}
                  onChange={(e) => setEditForm(f => ({ ...f, costPrice: e.target.value }))}
                  className="h-8 text-xs"
                />
              </div>
              <div>
                <label className="text-[10px] text-muted-foreground block mb-1">持仓数量 (股)</label>
                <Input
                  type="number"
                  value={editForm.qty}
                  onChange={(e) => setEditForm(f => ({ ...f, qty: e.target.value }))}
                  className="h-8 text-xs"
                />
              </div>
              <div>
                <label className="text-[10px] text-muted-foreground block mb-1">买入日期</label>
                <Input
                  type="date"
                  value={editForm.buyDate}
                  onChange={(e) => setEditForm(f => ({ ...f, buyDate: e.target.value }))}
                  className="h-8 text-xs"
                />
              </div>
            </div>

            {/* Stop settings */}
            <div>
              <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide block mb-2">止盈止损设置</label>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-muted-foreground block mb-1">止盈位 (%)</label>
                  <Input
                    type="number"
                    value={editForm.takeProfitPct}
                    onChange={(e) => setEditForm(f => ({ ...f, takeProfitPct: e.target.value }))}
                    placeholder="+10"
                    className="h-8 text-xs"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-muted-foreground block mb-1">止损位 (%)</label>
                  <Input
                    type="number"
                    value={editForm.stopLossPct}
                    onChange={(e) => setEditForm(f => ({ ...f, stopLossPct: e.target.value }))}
                    placeholder="-5"
                    className="h-8 text-xs"
                  />
                </div>
              </div>
            </div>

            {/* Track settings */}
            <div>
              <label className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide block mb-2">跟踪设置</label>
              <div className="flex flex-wrap gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editForm.trackPrice}
                    onChange={(e) => setEditForm(f => ({ ...f, trackPrice: e.target.checked }))}
                    className="w-3.5 h-3.5 rounded border-border"
                  />
                  <span className="text-xs text-foreground">价格到达提醒</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editForm.trackSignal}
                    onChange={(e) => setEditForm(f => ({ ...f, trackSignal: e.target.checked }))}
                    className="w-3.5 h-3.5 rounded border-border"
                  />
                  <span className="text-xs text-foreground">信号变化提醒</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editForm.trackNews}
                    onChange={(e) => setEditForm(f => ({ ...f, trackNews: e.target.checked }))}
                    className="w-3.5 h-3.5 rounded border-border"
                  />
                  <span className="text-xs text-foreground">公告新闻提醒</span>
                </label>
              </div>
            </div>

            {/* Remark */}
            <div>
              <label className="text-[10px] text-muted-foreground block mb-1">备注信息</label>
              <Input
                value={editForm.remark}
                onChange={(e) => setEditForm(f => ({ ...f, remark: e.target.value }))}
                placeholder="可选备注..."
                className="h-8 text-xs"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>取消</Button>
            <Button onClick={confirmEdit} disabled={isSaving}>
              {isSaving ? <><Spinner className="w-4 h-4 mr-1" />保存中...</> : "保存修改"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
