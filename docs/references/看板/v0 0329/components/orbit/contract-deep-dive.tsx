"use client"

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  ArrowLeft, TrendingUp, TrendingDown, MoreVertical, 
  Plus, Zap, AlertCircle, Activity, Eye, ArrowUpRight, ArrowDownRight,
  Download, Play, Search, Newspaper, BarChart3, Wallet, Shield, Calculator,
  Layers, Star, Clock, ChevronRight, CheckCircle2
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useToast } from '@/hooks/use-toast'

interface ContractMetrics {
  currentPrice: number
  priceChange: number
  volume: number
  openInterest: number
  volumeRatio: number
  amplitude: number
  turnoverRate: number
  prevSettlement: number
}

interface TechIndicator {
  name: string
  value: number
  status: 'bullish' | 'neutral' | 'bearish'
}

interface TimelineEvent {
  id: string
  time: string
  title: string
  description: string
  impact: 'positive' | 'negative' | 'neutral'
}

interface RelatedVariety {
  code: string
  correlation: number
  priceDiff: number
  suggestion: string
}

interface MainContract {
  code: string
  type: 'near' | 'main' | 'far'
  volume: number
  label: string
  isCurrent?: boolean
}

interface FundamentalData {
  label: string
  value: string
  change: number
}

interface CapitalFlow {
  type: string
  amount: number
  direction: 'in' | 'out'
}

interface SignalHistory {
  time: string
  direction: 'long' | 'short' | 'neutral'
  confidence: number
  expectedReturn: number
}

interface RiskIndicator {
  label: string
  value: string
  level: 'low' | 'medium' | 'high'
  warning?: string
}

interface SectorItem {
  name: string
  change: number
  role: string
}

interface IndustryNews {
  id: number
  title: string
  source: string
  ts: number
}

interface ContractDeepDiveProps {
  contractCode: string
  contractName: string
  status: 'active' | 'main' | 'secondary'
  onBack: () => void
}

export function ContractDeepDive({ 
  contractCode = 'rb2405', 
  contractName = '螺纹钢',
  status = 'main',
  onBack 
}: ContractDeepDiveProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [showMenu, setShowMenu] = useState(false)
  const [activeTab, setActiveTab] = useState<'全部' | '新闻' | '公告' | '研报'>('全部')
  const [selectedFactors, setSelectedFactors] = useState<string[]>(['动量突破'])
  const [calcParams, setCalcParams] = useState({
    holdDays: 5,
    stopLoss: -5,
    takeProfit: 10,
    positionRatio: 20,
  })
  const [calcResult, setCalcResult] = useState<{
    signal: 'long' | 'short' | 'neutral'
    confidence: number
    expectedReturn: number
    riskLevel: string
  } | null>(null)

  // 最后更新时间（模拟）
  const lastUpdateTime = '5 分钟前'

  // Mock data - KPI metrics (8 items)
  const metrics: ContractMetrics = {
    currentPrice: 3520,
    priceChange: 2.5,
    volume: 125000,
    openInterest: 285000,
    volumeRatio: 0.9,
    amplitude: 3.2,
    turnoverRate: 1.5,
    prevSettlement: 3480,
  }

  const techIndicators: TechIndicator[] = [
    { name: '趋势', value: 75, status: 'bullish' },
    { name: '动量', value: 68, status: 'bullish' },
    { name: '波动', value: 62, status: 'neutral' },
  ]

  const timelineEvents: TimelineEvent[] = [
    { id: '1', time: '14:30', title: '钢厂减产', description: '唐山地区钢厂限产30%', impact: 'positive' },
    { id: '2', time: '10:00', title: '库存数据', description: '社会库存环比下降2.1%', impact: 'neutral' },
    { id: '3', time: '09:00', title: '周度分析', description: '需求端持续疲软', impact: 'negative' },
  ]

  const relatedVarieties: RelatedVariety[] = [
    { code: 'hc2405', correlation: 85, priceDiff: 120, suggestion: '做多价差' },
    { code: 'rb2410', correlation: 92, priceDiff: 80, suggestion: '跨期套利' },
    { code: 'i2405', correlation: 78, priceDiff: 350, suggestion: '做多利润' },
  ]

  const mainContracts: MainContract[] = [
    { code: 'RB2401', type: 'near', volume: 45000, label: '近月合约' },
    { code: 'RB2405', type: 'main', volume: 125000, label: '主力合约', isCurrent: true },
    { code: 'RB2410', type: 'far', volume: 35000, label: '远月合约' },
  ]

  const fundamentalData: FundamentalData[] = [
    { label: '持仓量', value: '285,000 手', change: 5.2 },
    { label: '仓单数量', value: '12,500 吨', change: -2.1 },
    { label: '库存数据', value: '45,000 吨', change: 1.5 },
  ]

  const capitalFlows: CapitalFlow[] = [
    { type: '主力资金', amount: 2500, direction: 'in' },
    { type: '散户资金', amount: 800, direction: 'out' },
  ]

  const capitalFlowTrend = [30, 50, 70, 60, 90] // 近5日

  const orderDistribution = [
    { label: '大单', percent: 45 },
    { label: '中单', percent: 35 },
    { label: '小单', percent: 20 },
  ]

  const signalHistory: SignalHistory[] = [
    { time: '17:08', direction: 'long', confidence: 78, expectedReturn: 7000 },
    { time: '16:55', direction: 'short', confidence: 72, expectedReturn: 5200 },
    { time: '16:30', direction: 'neutral', confidence: 65, expectedReturn: 0 },
    { time: '15:45', direction: 'long', confidence: 81, expectedReturn: 8500 },
    { time: '15:20', direction: 'short', confidence: 69, expectedReturn: 4800 },
  ]

  const riskIndicators: RiskIndicator[] = [
    { label: 'VaR(95%)', value: '¥25,000', level: 'medium', warning: '中等风险' },
    { label: '强平价格', value: '¥3,280', level: 'high', warning: '警戒线' },
    { label: '保证金使用率', value: '78%', level: 'medium', warning: '警告' },
  ]

  const sectorItems: SectorItem[] = [
    { name: '螺纹钢', change: 2.5, role: '龙头' },
    { name: '热卷', change: 3.1, role: '跟涨' },
    { name: '铁矿石', change: 1.8, role: '跟涨' },
  ]

  const sectorCorrelations = [
    { pair: '螺纹 - 热卷', value: 0.92 },
    { pair: '螺纹 - 铁矿', value: 0.78 },
    { pair: '热卷 - 铁矿', value: 0.85 },
  ]

  const now = Date.now()
  const DAY = 86400000
  const industryNews: IndustryNews[] = [
    { id: 1, title: '唐山地区钢厂限产政策出台，产量预计下降30%', source: '钢铁资讯', ts: now - 1000 * 60 * 5 },
    { id: 2, title: '螺纹钢社会库存连续三周下降，去库速度加快', source: '我的钢铁', ts: now - 1000 * 60 * 20 },
    { id: 3, title: '基建项目开工率提升，钢材需求有望回暖', source: '期货日报', ts: now - 1000 * 60 * 45 },
    { id: 4, title: '铁矿石港口库存创近两年新低', source: '矿业周刊', ts: now - 1000 * 60 * 70 },
    { id: 5, title: '钢厂利润修复，开工率小幅回升', source: '钢联资讯', ts: now - 1000 * 60 * 100 },
    { id: 6, title: '焦炭第五轮提涨落地，成本支撑增强', source: '煤焦资讯', ts: now - 1000 * 60 * 130 },
    { id: 7, title: '房地产政策利好频出，市场信心修复', source: '财经日报', ts: now - 1000 * 60 * 180 },
    { id: 8, title: '废钢价格上涨，电炉成本抬升', source: '废钢资讯', ts: now - 1000 * 60 * 240 },
    { id: 9, title: '钢材出口订单增加，海外需求回暖', source: '国际钢铁', ts: now - 1000 * 60 * 300 },
    { id: 10, title: '环保限产力度加大，供给端收缩预期', source: '环保监测', ts: now - DAY * 0.3 },
    { id: 11, title: '下游需求端释放积极信号', source: '宏观经济', ts: now - DAY * 0.4 },
    { id: 12, title: '钢厂检修计划密集，短期供给偏紧', source: '钢联资讯', ts: now - DAY * 0.5 },
    { id: 13, title: '铁矿石发货量环比下降', source: '航运周刊', ts: now - DAY * 0.7 },
    { id: 14, title: '钢材期现价差收窄，基差修复', source: '期货日报', ts: now - DAY * 1 },
    { id: 15, title: '黑色系板块资金流入明显', source: '资金监测', ts: now - DAY * 1.2 },
    { id: 16, title: '钢厂原料库存偏低，补库需求旺盛', source: '钢联资讯', ts: now - DAY * 1.5 },
    { id: 17, title: '螺纹钢主力合约持仓量创新高', source: '中金所', ts: now - DAY * 2 },
    { id: 18, title: '钢材价格指数连续上涨', source: 'CRU', ts: now - DAY * 3 },
    { id: 19, title: '建材需求季节性回升', source: '建材资讯', ts: now - DAY * 4 },
    { id: 20, title: '钢厂盈利能力持续改善', source: '证券研报', ts: now - DAY * 5 },
  ]

  const factorOptions = ['动量突破', '均值回归', '布林带', 'MACD', 'RSI', '成交量']

  // Simulate loading
  useEffect(() => {
    setIsLoading(true)
    const timer = setTimeout(() => setIsLoading(false), 400)
    return () => clearTimeout(timer)
  }, [contractCode])

  const formatNewsTime = (ts: number): string => {
    const diff = now - ts
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return '刚刚'
    if (mins < 60) return `${mins}分钟前`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}小时前`
    const days = Math.floor(hrs / 24)
    return `${days}天前`
  }

  const handleRunCalc = () => {
    // Simulate calculation
    setCalcResult({
      signal: 'long',
      confidence: 75,
      expectedReturn: 8500,
      riskLevel: '中等',
    })
  }

  const overallScore = Math.round((techIndicators.reduce((sum, ind) => sum + ind.value, 0) / techIndicators.length))
  const isRising = metrics.priceChange >= 0

  if (isLoading) {
    return (
      <div className="p-6 space-y-6 overflow-y-auto h-full">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/3" />
          <div className="grid grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-20 bg-muted rounded" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <motion.div 
      className="p-6 space-y-5 overflow-y-auto h-full"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <motion.button
            onClick={() => {
              if (onBack) {
                onBack()
              }
            }}
            className="w-9 h-9 rounded-lg bg-muted border border-border/50 flex items-center justify-center text-muted-foreground hover:text-foreground hover:border-primary/30 transition-all"
            aria-label="返回"
            whileHover={{ x: -2 }}
            whileTap={{ scale: 0.95 }}
          >
            <ArrowLeft className="w-4 h-4" />
          </motion.button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold text-foreground tracking-tight">
                {contractCode.toUpperCase()}
              </h1>
              <span className={cn(
                'px-2 py-0.5 rounded text-xs font-medium',
                status === 'main' && 'bg-primary/10 text-primary',
                status === 'secondary' && 'bg-emerald-100 text-emerald-700',
                status === 'active' && 'bg-amber-100 text-amber-700'
              )}>
                {status === 'main' ? '主力合约' : status === 'secondary' ? '次主力' : '活跃'}
              </span>
              {metrics.priceChange > 2 && (
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-[#FF3B30]/10 text-[#FF3B30]">
                  高波动
                </span>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              {contractName} · 最后更新：5 分钟前
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="w-9 h-9 rounded-lg bg-muted border border-border/50 flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
            aria-label="更多操作"
          >
            <MoreVertical className="w-4 h-4" />
          </button>
          
          <AnimatePresence>
            {showMenu && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />
                <motion.div 
                  initial={{ opacity: 0, y: -8, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.95 }}
                  className="absolute right-0 top-full mt-1 w-40 bg-popover border border-border/50 rounded-lg shadow-lg z-20 py-1"
                >
                  <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted transition-colors">
                    <Plus className="w-4 h-4" />
                    添加到自选
                  </button>
                </motion.div>
              </>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* 三端状态栏 */}
      <div className="flex items-center justify-center gap-12 px-4 py-3 bg-secondary/20 rounded-lg border border-border/30">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-[#3FB950]" />
          <span className="text-[11px] font-medium text-foreground">数据端</span>
        </div>
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-[#3FB950]" />
          <span className="text-[11px] font-medium text-foreground">决策端</span>
        </div>
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-[#3FB950]" />
          <span className="text-[11px] font-medium text-foreground">交易端</span>
        </div>
      </div>

      {/* Row 1: KPI Cards (8 items, 2 rows of 4) */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: '当前价', value: `¥${metrics.currentPrice.toLocaleString()}`, color: 'text-foreground', icon: TrendingUp, iconColor: 'text-primary' },
          { label: '涨跌幅', value: `${isRising ? '+' : ''}${metrics.priceChange}%`, color: isRising ? 'text-[#FF3B30]' : 'text-[#3FB950]', icon: isRising ? TrendingUp : TrendingDown, iconColor: isRising ? 'text-[#FF3B30]' : 'text-[#3FB950]' },
          { label: '成交量', value: `${(metrics.volume / 1000).toFixed(0)}K`, color: 'text-foreground', icon: Activity, iconColor: 'text-muted-foreground' },
          { label: '持仓量', value: `${(metrics.openInterest / 1000).toFixed(0)}K`, color: 'text-foreground', icon: Eye, iconColor: 'text-muted-foreground' },
          { label: '量比', value: metrics.volumeRatio.toFixed(1), color: 'text-foreground', icon: Zap, iconColor: 'text-amber-500' },
          { label: '振幅', value: `${metrics.amplitude}%`, color: 'text-foreground', icon: Activity, iconColor: 'text-muted-foreground' },
          { label: '换手率', value: `${metrics.turnoverRate}%`, color: 'text-foreground', icon: BarChart3, iconColor: 'text-muted-foreground' },
          { label: '昨结算', value: `¥${metrics.prevSettlement.toLocaleString()}`, color: 'text-muted-foreground', icon: Clock, iconColor: 'text-muted-foreground' },
        ].map((item, i) => (
          <motion.div
            key={i}
            className="bg-card rounded-md p-3 text-center border border-border/30"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03 }}
          >
            <div className="flex items-center justify-center gap-1.5 mb-1.5">
              <item.icon className={cn('w-3.5 h-3.5', item.iconColor)} />
              <p className="text-xs text-muted-foreground">{item.label}</p>
            </div>
            <p className={cn('text-base font-semibold font-mono', item.color)}>
              {item.value}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Row 2: Technical Indicators + Timeline */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Technical Indicators Ring */}
        <motion.div 
          className="bg-card rounded-md p-4 border border-border/30"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <h3 className="text-sm font-medium text-foreground mb-3">技术指标评分</h3>
          
          <div className="flex flex-col items-center justify-center mb-4">
            <div className="relative w-24 h-24">
              <svg className="w-full h-full" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="42"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="6"
                  className="text-[#FF3B30]/20"
                />
                <motion.circle
                  cx="50"
                  cy="50"
                  r="42"
                  fill="none"
                  stroke="#FF3B30"
                  strokeWidth="6"
                  strokeLinecap="round"
                  transform="rotate(-90 50 50)"
                  initial={{ strokeDasharray: "0 264" }}
                  animate={{ strokeDasharray: `${(overallScore / 100) * 264} 264` }}
                  transition={{ duration: 1.2, ease: "easeOut", delay: 0.2 }}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <motion.span 
                  className="text-2xl font-bold text-foreground"
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5, delay: 0.5 }}
                >
                  {overallScore}
                </motion.span>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            {techIndicators.map((indicator, index) => (
              <motion.div 
                key={indicator.name}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.8 + index * 0.1 }}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-medium text-foreground">{indicator.name}</span>
                  <span className="text-[11px] text-muted-foreground">{indicator.value}%</span>
                </div>
                <div className="w-full h-1.5 bg-[#FF3B30]/10 rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full bg-[#FF3B30] rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${indicator.value}%` }}
                    transition={{ duration: 0.8, delay: 0.9 + index * 0.1, ease: "easeOut" }}
                  />
                </div>
              </motion.div>
            ))}
          </div>

          <div className="mt-3 p-2 bg-[#FF3B30]/10 border border-[#FF3B30]/20 rounded">
            <p className="text-[11px] font-medium text-[#FF3B30] text-center">多头信号</p>
          </div>
        </motion.div>

        {/* Timeline */}
        <motion.div 
          className="lg:col-span-2 bg-card rounded-md p-4 border border-border/30 flex flex-col"
          style={{ maxHeight: '320px' }}
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.15 }}
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-foreground">时间线</h3>
            <button className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-primary bg-primary/10 hover:bg-primary/20 rounded transition-colors">
              <Plus className="w-3 h-3" />
              记录活动
            </button>
          </div>
          
          <div className="flex gap-2 mb-3">
            {(['全部', '新闻', '公告', '研报'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  'px-2.5 py-1 text-xs font-medium rounded transition-colors',
                  activeTab === tab 
                    ? 'bg-primary text-primary-foreground' 
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                )}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="overflow-y-auto flex-1 -mr-2 pr-2">
            <div className="space-y-2">
              {timelineEvents.map((event) => (
                <div key={event.id} className="flex gap-2.5 p-2.5 bg-muted/50 rounded hover:bg-muted transition-colors cursor-pointer">
                  <div 
                    className={cn(
                      "w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0",
                      event.impact === 'positive' && 'bg-[#FF3B30]',
                      event.impact === 'negative' && 'bg-[#3FB950]',
                      event.impact === 'neutral' && 'bg-gray-400'
                    )}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[12px] font-medium text-foreground">{event.title}</span>
                      <span className={cn(
                        "text-[9px] font-medium px-1.5 py-0.5 rounded",
                        event.impact === 'positive' && 'bg-[#FF3B30]/10 text-[#FF3B30]',
                        event.impact === 'negative' && 'bg-[#3FB950]/10 text-[#3FB950]',
                        event.impact === 'neutral' && 'bg-muted text-muted-foreground'
                      )}>
                        {event.impact === 'positive' && '利好'}
                        {event.impact === 'negative' && '利空'}
                        {event.impact === 'neutral' && '中性'}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">{event.description}</p>
                    <p className="text-xs text-muted-foreground/60 mt-0.5">{event.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Row 3: Related Varieties + Main Contracts (50%/50%) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Related Varieties */}
        <motion.div 
          className="bg-card rounded-md p-4 border border-border/30"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-foreground">相关品种/套利机会</h3>
            <button className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-primary bg-primary/10 hover:bg-primary/20 rounded transition-colors">
              <Plus className="w-3 h-3" />
              新增机会
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead className="border-b border-border/50">
                <tr>
                  <th className="text-left py-2 px-2 font-medium text-muted-foreground">代码</th>
                  <th className="text-left py-2 px-2 font-medium text-muted-foreground">相关性</th>
                  <th className="text-left py-2 px-2 font-medium text-muted-foreground">价差</th>
                  <th className="text-left py-2 px-2 font-medium text-muted-foreground">建议</th>
                  <th className="text-center py-2 px-2 font-medium text-muted-foreground">操作</th>
                </tr>
              </thead>
              <tbody>
                {relatedVarieties.map((item, i) => (
                  <tr key={i} className="border-b border-border/30 hover:bg-secondary/30 transition-colors">
                    <td className="py-2 px-2 font-mono font-semibold">{item.code}</td>
                    <td className="py-2 px-2">{item.correlation}%</td>
                    <td className="py-2 px-2 font-mono">¥{item.priceDiff}</td>
                    <td className="py-2 px-2 text-foreground">{item.suggestion}</td>
                    <td className="py-2 px-2 text-center">
                      <button className="text-xs font-medium text-primary hover:text-primary/80 transition-colors">
                        查看
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Main Contracts */}
        <motion.div 
          className="bg-card rounded-md p-4 border border-border/30"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h3 className="text-sm font-medium text-foreground mb-3">主力合约切换</h3>

          <div className="grid grid-cols-3 gap-3">
            {mainContracts.map((contract, i) => (
              <div 
                key={i} 
                className={cn(
                  "p-3 rounded border transition-all cursor-pointer",
                  contract.isCurrent 
                    ? "bg-primary/10 border-primary/30" 
                    : "bg-muted/50 border-border/50 hover:border-primary/30"
                )}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-[12px] font-mono font-semibold text-foreground">{contract.code}</p>
                  {contract.isCurrent && <Star className="w-3.5 h-3.5 text-primary fill-primary" />}
                </div>
                <p className="text-xs text-muted-foreground mb-1">{contract.label}</p>
                <p className="text-xs text-muted-foreground mb-2">成交量 {(contract.volume / 1000).toFixed(0)}K</p>
                <button className={cn(
                  "w-full py-1.5 text-xs font-medium rounded transition-colors",
                  contract.isCurrent 
                    ? "bg-primary/20 text-primary cursor-default" 
                    : "bg-primary/10 text-primary hover:bg-primary/20"
                )}>
                  {contract.isCurrent ? '当前' : '切换'}
                </button>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Row 4: Fundamental Data + Capital Flow (50%/50%) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Fundamental Data */}
        <motion.div 
          className="bg-card rounded-md p-4 border border-border/30"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <h3 className="text-sm font-medium text-foreground mb-3">基本面数据</h3>

          <div className="grid grid-cols-3 gap-3 mb-3">
            {fundamentalData.map((item, i) => (
              <div key={i} className="p-3 bg-muted/50 rounded text-center">
                <p className="text-xs text-muted-foreground mb-1">{item.label}</p>
                <p className="text-sm font-semibold font-mono text-foreground mb-1">{item.value}</p>
                <div className={cn(
                  "flex items-center justify-center gap-0.5 text-xs font-medium",
                  item.change >= 0 ? "text-[#FF3B30]" : "text-[#3FB950]"
                )}>
                  {item.change >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                  {item.change >= 0 ? '+' : ''}{item.change}%
                </div>
              </div>
            ))}
          </div>

          <div className="p-2 bg-muted/30 rounded text-xs text-muted-foreground">
            注册仓单变化：<span className="font-medium text-foreground">+150 吨</span>（本周）
          </div>
        </motion.div>

        {/* Capital Flow */}
        <motion.div 
          className="bg-card rounded-md p-4 border border-border/30"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-foreground">资金流向</h3>
            <span className="text-xs text-muted-foreground">实时更新</span>
          </div>

          <div className="space-y-2 mb-3">
            {capitalFlows.map((flow, i) => (
              <div key={i} className="flex items-center justify-between">
                <span className="text-[11px] text-muted-foreground">{flow.type}</span>
                <div className={cn(
                  "flex items-center gap-1 text-[12px] font-semibold font-mono",
                  flow.direction === 'in' ? "text-[#FF3B30]" : "text-[#3FB950]"
                )}>
                  {flow.direction === 'in' ? '+' : '-'}¥{flow.amount.toLocaleString()} 万
                  {flow.direction === 'in' ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                </div>
              </div>
            ))}
          </div>

          {/* Mini bar chart */}
          <div className="p-2 bg-muted/30 rounded mb-3">
            <p className="text-xs text-muted-foreground mb-2">资金流向趋势（近 5 日）</p>
            <div className="flex items-end gap-1 h-8">
              {capitalFlowTrend.map((val, i) => (
                <div 
                  key={i} 
                  className="flex-1 bg-[#FF3B30] rounded-t"
                  style={{ height: `${(val / 100) * 100}%` }}
                />
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between text-xs">
            {orderDistribution.map((item, i) => (
              <span key={i} className="text-muted-foreground">
                {item.label}：<span className="font-medium text-foreground">{item.percent}%</span>
              </span>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Row 5: Strategy Signal History + Risk Indicators (50%/50%) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Strategy Signal History */}
        <motion.div 
          className="bg-card rounded-md p-4 border border-border/30"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-foreground">策略信号历史</h3>
            <button className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-primary bg-primary/10 hover:bg-primary/20 rounded transition-colors">
              <Download className="w-3 h-3" />
              导出 CSV
            </button>
          </div>

          <div className="overflow-x-auto mb-3">
            <table className="w-full text-[11px]">
              <thead className="border-b border-border/50">
                <tr>
                  <th className="text-left py-2 px-2 font-medium text-muted-foreground">时间</th>
                  <th className="text-left py-2 px-2 font-medium text-muted-foreground">方向</th>
                  <th className="text-left py-2 px-2 font-medium text-muted-foreground">置信度</th>
                  <th className="text-left py-2 px-2 font-medium text-muted-foreground">预期收益</th>
                  <th className="text-center py-2 px-2 font-medium text-muted-foreground">操作</th>
                </tr>
              </thead>
              <tbody>
                {signalHistory.map((signal, i) => (
                  <tr key={i} className="border-b border-border/30 hover:bg-secondary/30 transition-colors">
                    <td className="py-2 px-2 font-mono">{signal.time}</td>
                    <td className="py-2 px-2">
                      <span className={cn(
                        "text-xs font-medium px-1.5 py-0.5 rounded",
                        signal.direction === 'long' && 'bg-[#FF3B30]/10 text-[#FF3B30]',
                        signal.direction === 'short' && 'bg-[#3FB950]/10 text-[#3FB950]',
                        signal.direction === 'neutral' && 'bg-muted text-muted-foreground'
                      )}>
                        {signal.direction === 'long' ? '多' : signal.direction === 'short' ? '空' : '观望'}
                      </span>
                    </td>
                    <td className="py-2 px-2">{signal.confidence}%</td>
                    <td className="py-2 px-2 font-mono">
                      {signal.expectedReturn > 0 ? `+¥${signal.expectedReturn.toLocaleString()}` : '-'}
                    </td>
                    <td className="py-2 px-2 text-center">
                      {signal.direction !== 'neutral' && (
                        <button className="text-xs font-medium text-primary hover:text-primary/80 transition-colors">
                          跟投
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-2 bg-muted/30 rounded text-xs text-muted-foreground">
            近 30 日准确率：<span className="font-medium text-foreground">68.5%</span> (24/35)
          </div>
        </motion.div>

        {/* Risk Indicators */}
        <motion.div 
          className="bg-card rounded-md p-4 border border-border/30"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <h3 className="text-sm font-medium text-foreground mb-3">风险指标</h3>

          <div className="grid grid-cols-3 gap-3 mb-3">
            {riskIndicators.map((item, i) => (
              <div key={i} className="p-3 bg-muted/50 rounded text-center">
                <p className="text-xs text-muted-foreground mb-1">{item.label}</p>
                <p className="text-sm font-semibold font-mono text-foreground mb-1">{item.value}</p>
                <span className={cn(
                  "text-[9px] font-medium px-1.5 py-0.5 rounded",
                  item.level === 'low' && 'bg-[#3FB950]/10 text-[#3FB950]',
                  item.level === 'medium' && 'bg-amber-100 text-amber-700',
                  item.level === 'high' && 'bg-[#FF3B30]/10 text-[#FF3B30]'
                )}>
                  {item.warning}
                </span>
              </div>
            ))}
          </div>

          {/* Risk gauge */}
          <div className="p-3 bg-muted/30 rounded">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground">风险等级</span>
              <span className="text-[11px] font-medium text-amber-600">中等</span>
            </div>
            <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-[#3FB950] via-amber-500 to-[#FF3B30]"
                style={{ width: '100%' }}
              />
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-[9px] text-muted-foreground">低</span>
              <div 
                className="w-0 h-0 border-l-4 border-r-4 border-b-4 border-l-transparent border-r-transparent border-b-foreground"
                style={{ marginLeft: '55%' }}
              />
              <span className="text-[9px] text-muted-foreground">高</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Row 6: Manual Calculation Tool (100%) */}
      <motion.div 
        className="bg-card rounded-md p-4 border border-border/30"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
      >
        <div className="flex items-center gap-2 mb-3">
          <Calculator className="w-4 h-4 text-primary" />
          <h3 className="text-sm font-medium text-foreground">手动测算工具</h3>
        </div>

        {/* Factor selection */}
        <div className="mb-4">
          <p className="text-xs text-muted-foreground mb-2">因子选择：</p>
          <div className="flex flex-wrap gap-2">
            {factorOptions.map((factor) => (
              <button
                key={factor}
                onClick={() => {
                  if (selectedFactors.includes(factor)) {
                    setSelectedFactors(selectedFactors.filter(f => f !== factor))
                  } else {
                    setSelectedFactors([...selectedFactors, factor])
                  }
                }}
                className={cn(
                  "px-2.5 py-1 text-xs font-medium rounded transition-colors",
                  selectedFactors.includes(factor)
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                )}
              >
                {factor}
              </button>
            ))}
            <button className="px-2.5 py-1 text-xs font-medium text-primary bg-primary/10 hover:bg-primary/20 rounded transition-colors">
              + 添加
            </button>
          </div>
        </div>

        {/* Parameters */}
        <div className="p-3 bg-muted/30 rounded mb-4">
          <p className="text-xs text-muted-foreground mb-3">参数设置（沙盒环境，不影响系统）：</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">持仓周期（天）</label>
              <Input 
                type="number" 
                value={calcParams.holdDays} 
                onChange={(e) => setCalcParams({...calcParams, holdDays: parseInt(e.target.value) || 0})}
                className="h-8 text-[11px]"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">止损阈值（%）</label>
              <Input 
                type="number" 
                value={calcParams.stopLoss} 
                onChange={(e) => setCalcParams({...calcParams, stopLoss: parseInt(e.target.value) || 0})}
                className="h-8 text-[11px]"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">止盈阈值（%）</label>
              <Input 
                type="number" 
                value={calcParams.takeProfit} 
                onChange={(e) => setCalcParams({...calcParams, takeProfit: parseInt(e.target.value) || 0})}
                className="h-8 text-[11px]"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">仓位比例（%）</label>
              <Input 
                type="number" 
                value={calcParams.positionRatio} 
                onChange={(e) => setCalcParams({...calcParams, positionRatio: parseInt(e.target.value) || 0})}
                className="h-8 text-[11px]"
              />
            </div>
          </div>
        </div>

        {/* Search variety */}
        <div className="mb-4">
          <p className="text-xs text-muted-foreground mb-2">品种选择：</p>
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
            <Input placeholder="搜索品种..." className="h-8 text-[11px] pl-8" />
          </div>
        </div>

        {/* Run button */}
        <Button 
          onClick={handleRunCalc}
          className="w-full h-9 text-[12px]"
        >
          <Play className="w-3.5 h-3.5 mr-1.5" />
          运行测算
        </Button>

        {/* Result */}
        {calcResult && (
          <motion.div 
            className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <p className="text-xs text-muted-foreground mb-2">测算结果：</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <p className="text-xs text-muted-foreground">信号</p>
                <p className={cn(
                  "text-sm font-semibold",
                  calcResult.signal === 'long' ? 'text-[#FF3B30]' : calcResult.signal === 'short' ? 'text-[#3FB950]' : 'text-muted-foreground'
                )}>
                  {calcResult.signal === 'long' ? '做多' : calcResult.signal === 'short' ? '做空' : '观望'}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">置信度</p>
                <p className="text-sm font-semibold font-mono text-foreground">{calcResult.confidence}%</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">预期收益</p>
                <p className="text-sm font-semibold font-mono text-[#FF3B30]">+¥{calcResult.expectedReturn.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">风险等级</p>
                <p className="text-sm font-semibold text-amber-600">{calcResult.riskLevel}</p>
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>

      {/* Row 7: Sector Linkage (100%) */}
      <motion.div 
        className="bg-card rounded-md p-4 border border-border/30"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-medium text-foreground">板块联动 — 黑色金属</h3>
          </div>
          <div className="flex items-center gap-1 text-[12px] font-semibold text-[#FF3B30]">
            板块今日：+2.8%
            <ArrowUpRight className="w-3.5 h-3.5" />
          </div>
        </div>

        <div className="grid grid-cols-3 md:grid-cols-6 gap-3 mb-4">
          {sectorItems.map((item, i) => (
            <div key={i} className="p-3 bg-muted/50 rounded text-center">
              <p className="text-[11px] font-medium text-foreground mb-1">{item.name}</p>
              <p className={cn(
                "text-sm font-semibold font-mono",
                item.change >= 0 ? 'text-[#FF3B30]' : 'text-[#3FB950]'
              )}>
                {item.change >= 0 ? '+' : ''}{item.change}%
              </p>
              <span className={cn(
                "text-[9px] font-medium px-1.5 py-0.5 rounded mt-1 inline-block",
                item.role === '龙头' ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'
              )}>
                {item.role}
              </span>
            </div>
          ))}
        </div>

        <div className="p-2 bg-muted/30 rounded">
          <p className="text-xs text-muted-foreground mb-1">联动相关性：</p>
          <div className="flex flex-wrap gap-4">
            {sectorCorrelations.map((item, i) => (
              <span key={i} className="text-[11px] text-foreground">
                {item.pair}：<span className="font-mono font-medium">{item.value}</span>
              </span>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Row 8: Industry News (100%, 20 items with scroll) */}
      <motion.div 
        className="bg-card rounded-md p-4 border border-border/30"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Newspaper className="w-4 h-4 text-[#FF3B30]" />
            <h3 className="text-sm font-medium text-foreground">行业新闻</h3>
            <span className="text-xs text-muted-foreground/50">最新在顶部</span>
          </div>
          <span className="text-xs text-muted-foreground/50">{industryNews.length} 条</span>
        </div>

        <div className="max-h-[400px] overflow-y-auto space-y-0.5">
          {industryNews.map((news) => (
            <div key={news.id} className="py-2 px-2.5 hover:bg-secondary/30 rounded transition-colors cursor-pointer">
              <h4 className="text-[11px] font-medium text-foreground hover:text-primary transition-colors leading-snug">
                {news.title}
              </h4>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-muted-foreground/70 font-medium">{news.source}</span>
                <span className="text-xs text-muted-foreground/40">{formatNewsTime(news.ts)}</span>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  )
}
