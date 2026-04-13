'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  ArrowLeft, TrendingUp, TrendingDown, MoreVertical, 
  Plus, Star, Building2, Users, Landmark, CreditCard, Download, AlertCircle
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'

interface StockMetrics {
  currentPrice: number
  priceChange: number
  amplitude: number
  totalMarketCap: number
  circulatingMarketCap: number
  pe: number
  pb: number
  dividendYield: number
}

interface FinancialData {
  revenue: number
  revenueGrowth: number
  netProfit: number
  profitGrowth: number
  roe: number
  grossMargin: number
  debtRatio: number
  cashFlow: number
}

interface ShareholderData {
  totalShares: number
  circulatingShares: number
  shareholderCount: number
  top10Ratio: number
  controllingHolder: string
  controllingRatio: number
}

interface InstitutionalHolding {
  name: string
  ratio: number
  change: number
}

interface MarginTrading {
  marginBalance: number
  shortBalance: number
  marginBuy: number
  shortSell: number
  collateralRatio: number
}

interface TimelineEvent {
  id: string
  time: string
  type: '公告' | '新闻' | '研报' | '财报'
  title: string
  source: string
  impact: 'positive' | 'negative' | 'neutral'
}

interface RelatedStock {
  code: string
  name: string
  price: number
  change: number
}

interface StockDeepDiveProps {
  stockCode?: string
  stockName?: string
  status?: 'trading' | 'closed' | 'suspended'
  onBack?: () => void
}

export function StockDeepDive({ 
  stockCode = '600519', 
  stockName = '贵州茅台',
  status = 'trading',
  onBack 
}: StockDeepDiveProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [showMenu, setShowMenu] = useState(false)
  const [activeTab, setActiveTab] = useState<'全部' | '新闻' | '公告' | '研报' | '财报'>('全部')
  const [isWatchlisted, setIsWatchlisted] = useState(false)
  const [showExportMenu, setShowExportMenu] = useState(false)
  const { toast } = useToast()

  // Mock data
  const metrics: StockMetrics = {
    currentPrice: 1680,
    priceChange: 2.5,
    amplitude: 3.8,
    totalMarketCap: 21100,
    circulatingMarketCap: 21100,
    pe: 28.5,
    pb: 5.2,
    dividendYield: 1.8,
  }

  const financialData: FinancialData = {
    revenue: 1250,
    revenueGrowth: 18,
    netProfit: 620,
    profitGrowth: 20,
    roe: 28.5,
    grossMargin: 92.3,
    debtRatio: 15.2,
    cashFlow: 580,
  }

  const shareholderData: ShareholderData = {
    totalShares: 12.5,
    circulatingShares: 12.5,
    shareholderCount: 15.8,
    top10Ratio: 65.2,
    controllingHolder: '贵州茅台集团',
    controllingRatio: 58,
  }

  const institutionalHoldings: InstitutionalHolding[] = [
    { name: '基金持仓', ratio: 35.2, change: 2.1 },
    { name: '社保持仓', ratio: 5.8, change: 0.3 },
    { name: 'QFII持仓', ratio: 8.5, change: -0.5 },
    { name: '险资持仓', ratio: 3.2, change: 0.2 },
    { name: '北向资金', ratio: 12.5, change: 1.2 },
  ]

  const marginTrading: MarginTrading = {
    marginBalance: 125,
    shortBalance: 3.5,
    marginBuy: 8.5,
    shortSell: 125,
    collateralRatio: 285,
  }

  // 扩展到 20 条时间线事件
  const timelineEvents: TimelineEvent[] = [
    { id: '1', time: '14:30', type: '公告', title: '三季度财报发布', source: '上交所', impact: 'positive' },
    { id: '2', time: '10:00', type: '新闻', title: '白酒行业复苏', source: '财联社', impact: 'positive' },
    { id: '3', time: '09:00', type: '研报', title: '目标价1,800', source: '中信证券', impact: 'positive' },
    { id: '4', time: '2026-03-16', type: '财报', title: '年度报告发布', source: '巨潮资讯', impact: 'positive' },
    { id: '5', time: '2026-03-15', type: '公告', title: '分红预案公告', source: '上交所', impact: 'positive' },
    { id: '6', time: '2026-03-14', type: '新闻', title: '销售业绩创新高', source: '证券时报', impact: 'positive' },
    { id: '7', time: '2026-03-13', type: '研报', title: '评级上调至买入', source: '海通证券', impact: 'positive' },
    { id: '8', time: '2026-03-12', type: '公告', title: '高管增持计划', source: '上交所', impact: 'positive' },
    { id: '9', time: '2026-03-11', type: '新闻', title: '市场份额扩大', source: '新浪财经', impact: 'positive' },
    { id: '10', time: '2026-03-10', type: '财报', title: '季度报告发布', source: '巨潮资讯', impact: 'positive' },
    { id: '11', time: '2026-03-09', type: '研报', title: '维持增持评级', source: '国泰君安', impact: 'neutral' },
    { id: '12', time: '2026-03-08', type: '公告', title: '员工持股计划', source: '上交所', impact: 'positive' },
    { id: '13', time: '2026-03-07', type: '新闻', title: '国际化步伐加快', source: '财经网', impact: 'positive' },
    { id: '14', time: '2026-03-06', type: '研报', title: '产业链景气向上', source: '中金公司', impact: 'positive' },
    { id: '15', time: '2026-03-05', type: '公告', title: '重要客户签约', source: '上交所', impact: 'positive' },
    { id: '16', time: '2026-03-04', type: '财报', title: '中报发布', source: '巨潮资讯', impact: 'positive' },
    { id: '17', time: '2026-03-03', type: '新闻', title: '研发投入增加', source: '和讯网', impact: 'positive' },
    { id: '18', time: '2026-03-02', type: '研报', title: '盈利预测上调', source: '招商证券', impact: 'positive' },
    { id: '19', time: '2026-03-01', type: '公告', title: '董事会决议公告', source: '上交所', impact: 'neutral' },
    { id: '20', time: '2026-02-28', type: '新闻', title: '实现盈利创新高', source: '东方财富', impact: 'positive' },
  ]

  const relatedStocks: RelatedStock[] = [
    { code: '000858', name: '五粮液', price: 168.5, change: 3.2 },
    { code: '000568', name: '泸州老窖', price: 235.8, change: 2.8 },
    { code: '600809', name: '山西汾酒', price: 285.6, change: 1.5 },
  ]

  const sectorRanking: RelatedStock[] = [
    { code: '000858', name: '五粮液', price: 168.5, change: 3.2 },
    { code: '000568', name: '泸州老窖', price: 235.8, change: 2.8 },
    { code: '600809', name: '山西汾酒', price: 285.6, change: 1.5 },
    { code: '600519', name: '贵州茅台', price: 1680, change: 2.5 },
    { code: '002304', name: '洋河股份', price: 125.3, change: 1.2 },
  ]

  const isRising = metrics.priceChange >= 0

  useEffect(() => {
    setIsLoading(true)
    const timer = setTimeout(() => setIsLoading(false), 400)
    return () => clearTimeout(timer)
  }, [stockCode])

  const handleWatchlist = () => {
    setIsWatchlisted(!isWatchlisted)
    toast({
      title: isWatchlisted ? '已移除自选' : '已加入自选',
      description: `${stockCode} ${stockName}`,
    })
  }

  const handleExport = (type: 'financial' | 'institutional' | 'dragon-tiger') => {
    toast({
      title: '导出成功',
      description: `已导出${type === 'financial' ? '财务指标' : type === 'institutional' ? '机构持仓' : '龙虎榜数据'}到 CSV`,
    })
    setShowExportMenu(false)
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <motion.div
          className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        />
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      {/* Header */}
      <motion.div 
        className="flex items-start justify-between"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-start gap-4">
          <button
            onClick={() => onBack?.()}
            className="mt-1 p-1.5 rounded-md hover:bg-secondary/50 transition-colors text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-semibold text-foreground">
                {stockCode} {stockName}
              </h1>
              <span className={cn(
                'px-2 py-0.5 rounded text-xs font-medium transition-all',
                status === 'trading' && 'bg-[#3FB950]/10 text-[#3FB950]',
                status === 'closed' && 'bg-muted text-muted-foreground',
                status === 'suspended' && 'bg-[#FF3B30]/10 text-[#FF3B30]'
              )}>
                {status === 'trading' ? '交易中' : status === 'closed' ? '已收盘' : '停牌'}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
              <span className="px-1.5 py-0.5 bg-muted/50 rounded">白酒</span>
              <span className="px-1.5 py-0.5 bg-muted/50 rounded">消费</span>
              <span className="px-1.5 py-0.5 bg-muted/50 rounded">上证50</span>
              <span className="px-1.5 py-0.5 bg-muted/50 rounded">沪深300</span>
              <span className="ml-2">最后更新：实时</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={handleWatchlist}
            className={cn(
              'flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
              isWatchlisted
                ? 'bg-primary text-primary-foreground'
                : 'text-primary bg-primary/10 hover:bg-primary/20'
            )}
          >
            <Star className={cn('w-3.5 h-3.5', isWatchlisted && 'fill-current')} />
            {isWatchlisted ? '已自选' : '加自选'}
          </button>
          
          {/* 导出菜单 */}
          <div className="relative">
            <button 
              onClick={() => setShowExportMenu(!showExportMenu)}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-muted-foreground bg-muted hover:bg-muted/80 rounded-md transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              导出
            </button>
            <AnimatePresence>
              {showExportMenu && (
                <motion.div
                  className="absolute right-0 top-full mt-1 bg-card border border-border rounded-md shadow-lg z-50"
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -5 }}
                >
                  <button
                    onClick={() => handleExport('financial')}
                    className="w-full text-left px-4 py-2 text-xs hover:bg-muted rounded-t-md transition-colors whitespace-nowrap"
                  >
                    导出财务指标
                  </button>
                  <button
                    onClick={() => handleExport('institutional')}
                    className="w-full text-left px-4 py-2 text-xs hover:bg-muted transition-colors whitespace-nowrap"
                  >
                    导出机构持仓
                  </button>
                  <button
                    onClick={() => handleExport('dragon-tiger')}
                    className="w-full text-left px-4 py-2 text-xs hover:bg-muted rounded-b-md transition-colors whitespace-nowrap"
                  >
                    导出龙虎榜
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          
          <button 
            onClick={() => setShowMenu(!showMenu)}
            className="p-1.5 rounded-md hover:bg-secondary/50 transition-colors text-muted-foreground"
          >
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </motion.div>

      {/* Row 1: 8 KPI Cards (2 rows x 4 cols) */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: '当前价', value: `¥${metrics.currentPrice.toLocaleString()}`, color: 'text-foreground' },
          { label: '涨跌幅', value: `${isRising ? '+' : ''}${metrics.priceChange}%`, color: isRising ? 'text-[#FF3B30]' : 'text-[#3FB950]' },
          { label: '振幅', value: `${metrics.amplitude}%`, color: 'text-foreground' },
          { label: '总市值', value: `¥${(metrics.totalMarketCap / 100).toFixed(2)}万亿`, color: 'text-foreground' },
          { label: '流通市值', value: `¥${(metrics.circulatingMarketCap / 100).toFixed(2)}万亿`, color: 'text-foreground' },
          { label: 'PE', value: metrics.pe.toFixed(1), color: 'text-foreground' },
          { label: 'PB', value: metrics.pb.toFixed(1), color: 'text-foreground' },
          { label: '股息率', value: `${metrics.dividendYield}%`, color: 'text-foreground' },
        ].map((item, i) => (
          <motion.div
            key={i}
            className="card-surface p-3 text-center"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03 }}
          >
            <p className="text-xs text-muted-foreground mb-1">{item.label}</p>
            <p className={cn('text-sm font-semibold font-mono', item.color)}>
              {item.value}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Row 2: Financial Data + Shareholder Structure */}
      <motion.div 
        className="grid grid-cols-2 gap-4"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        {/* Financial Data */}
        <div className="card-surface p-5">
          <div className="flex items-center gap-2 mb-4">
            <Landmark className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">核心财务指标</h3>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: '营业收入', value: `¥${financialData.revenue}亿`, change: `+${financialData.revenueGrowth}%` },
              { label: '净利润', value: `¥${financialData.netProfit}亿`, change: `+${financialData.profitGrowth}%` },
              { label: 'ROE', value: `${financialData.roe}%`, change: null },
              { label: '毛利率', value: `${financialData.grossMargin}%`, change: null },
              { label: '负债率', value: `${financialData.debtRatio}%`, change: null },
              { label: '经营现金流', value: `¥${financialData.cashFlow}亿`, change: null },
            ].map((item, i) => (
              <div key={i} className="p-2 bg-muted/30 rounded">
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <div className="flex items-baseline gap-1">
                  <p className="text-sm font-mono font-medium">{item.value}</p>
                  {item.change && (
                    <span className="text-xs text-[#FF3B30]">{item.change}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Shareholder Structure */}
        <div className="card-surface p-5">
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">股东结构</h3>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: '总股本', value: `${shareholderData.totalShares}亿股` },
              { label: '流通股', value: `${shareholderData.circulatingShares}亿股` },
              { label: '股东户数', value: `${shareholderData.shareholderCount}万户` },
              { label: '前十大持股', value: `${shareholderData.top10Ratio}%` },
            ].map((item, i) => (
              <div key={i} className="p-2 bg-muted/30 rounded">
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p className="text-sm font-mono font-medium">{item.value}</p>
              </div>
            ))}
          </div>
          <div className="mt-3 p-2 bg-primary/5 rounded border border-primary/10">
            <p className="text-xs text-muted-foreground">控股股东</p>
            <p className="text-sm font-medium">{shareholderData.controllingHolder} ({shareholderData.controllingRatio}%)</p>
          </div>
        </div>
      </motion.div>

      {/* Row 3: Institutional Holdings + Margin Trading */}
      <motion.div 
        className="grid grid-cols-2 gap-4"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
      >
        {/* Institutional Holdings */}
        <div className="card-surface p-5">
          <div className="flex items-center gap-2 mb-4">
            <Building2 className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">机构持仓</h3>
          </div>
          <div className="space-y-2">
            {institutionalHoldings.map((item, i) => (
              <div key={i} className="flex items-center justify-between p-2 bg-muted/30 rounded">
                <span className="text-xs text-muted-foreground">{item.name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono font-medium">{item.ratio}%</span>
                  <span className={cn(
                    'text-xs font-medium',
                    item.change >= 0 ? 'text-[#FF3B30]' : 'text-[#3FB950]'
                  )}>
                    {item.change >= 0 ? '+' : ''}{item.change}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Margin Trading */}
        <div className="card-surface p-5">
          <div className="flex items-center gap-2 mb-4">
            <CreditCard className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">融资融券</h3>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: '融资余额', value: `¥${marginTrading.marginBalance}亿` },
              { label: '融券余额', value: `¥${marginTrading.shortBalance}亿` },
              { label: '融资买入额', value: `¥${marginTrading.marginBuy}亿` },
              { label: '融券卖出量', value: `${marginTrading.shortSell}万股` },
            ].map((item, i) => (
              <div key={i} className="p-2 bg-muted/30 rounded">
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p className="text-sm font-mono font-medium">{item.value}</p>
              </div>
            ))}
          </div>
          <div className="mt-3 p-2 bg-[#3FB950]/10 rounded border border-[#3FB950]/20">
            <p className="text-xs text-muted-foreground">担保比例</p>
            <p className="text-sm font-mono font-medium text-[#3FB950]">{marginTrading.collateralRatio}%</p>
          </div>
        </div>
      </motion.div>

      {/* Row 4: Dragon Tiger List + Block Trade */}
      <motion.div 
        className="grid grid-cols-2 gap-4"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        {/* Dragon Tiger List */}
        <div className="card-surface p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground">龙虎榜（近5日）</h3>
            <span className="text-xs text-primary font-medium">净额: +¥2.5亿</span>
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-muted-foreground mb-1">买入营业部 Top5</p>
              <div className="space-y-1">
                {['中信证券上海分公司', '国泰君安总部', '华泰证券深圳'].map((name, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-1.5 bg-[#FF3B30]/5 rounded">
                    <span className="truncate flex-1">{name}</span>
                    <span className="font-mono text-[#FF3B30] ml-2">¥{(Math.random() * 2 + 0.5).toFixed(2)}亿</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">卖出营业部 Top5</p>
              <div className="space-y-1">
                {['招商证券深圳', '广发证券广州', '海通证券上海'].map((name, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-1.5 bg-[#3FB950]/5 rounded">
                    <span className="truncate flex-1">{name}</span>
                    <span className="font-mono text-[#3FB950] ml-2">¥{(Math.random() * 1.5 + 0.3).toFixed(2)}亿</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Block Trade */}
        <div className="card-surface p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">大宗交易</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs min-w-[300px]">
              <thead className="border-b border-border/50">
                <tr>
                  <th className="text-left py-2 font-medium text-muted-foreground whitespace-nowrap">日期</th>
                  <th className="text-left py-2 font-medium text-muted-foreground whitespace-nowrap">价格</th>
                  <th className="text-left py-2 font-medium text-muted-foreground whitespace-nowrap">溢价</th>
                  <th className="text-right py-2 font-medium text-muted-foreground whitespace-nowrap">成交额</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { date: '03-14', price: 1675, premium: -0.3, amount: 1.2 },
                  { date: '03-12', price: 1668, premium: 0.5, amount: 2.5 },
                  { date: '03-10', price: 1655, premium: -0.8, amount: 0.8 },
                ].map((trade, i) => (
                  <tr key={i} className="border-b border-border/30">
                    <td className="py-2 whitespace-nowrap">{trade.date}</td>
                    <td className="py-2 font-mono whitespace-nowrap">{trade.price}</td>
                    <td className={cn('py-2 whitespace-nowrap', trade.premium >= 0 ? 'text-[#FF3B30]' : 'text-[#3FB950]')}>
                      {trade.premium >= 0 ? '+' : ''}{trade.premium}%
                    </td>
                    <td className="py-2 text-right font-mono whitespace-nowrap">¥{trade.amount}亿</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </motion.div>

      {/* Row 5: Timeline (扩展到 20 条) */}
      <motion.div 
        className="card-surface p-5"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-foreground">时间线</h3>
          <button className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-primary bg-primary/10 hover:bg-primary/20 rounded-md transition-colors">
            <Plus className="w-3.5 h-3.5" />
            记录活动
          </button>
        </div>
        
        <div className="flex gap-2 mb-4">
          {(['全部', '新闻', '公告', '研报', '财报'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                'px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
                activeTab === tab 
                  ? 'bg-primary text-primary-foreground' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              )}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="space-y-2 max-h-80 overflow-y-auto">
          {timelineEvents.map((event) => (
            <div key={event.id} className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors cursor-pointer">
              <span className="text-xs text-muted-foreground w-16 flex-shrink-0">{event.time}</span>
              <span className={cn(
                'text-xs font-medium px-1.5 py-0.5 rounded flex-shrink-0',
                event.type === '公告' && 'bg-blue-100 text-blue-700',
                event.type === '新闻' && 'bg-amber-100 text-amber-700',
                event.type === '研报' && 'bg-purple-100 text-purple-700',
                event.type === '财报' && 'bg-[#3FB950]/10 text-[#3FB950]',
              )}>
                {event.type}
              </span>
              <span className="text-sm font-medium text-foreground flex-1 truncate">{event.title}</span>
              <span className="text-xs text-muted-foreground flex-shrink-0">{event.source}</span>
              <span className={cn(
                'text-xs font-medium px-1.5 py-0.5 rounded flex-shrink-0',
                event.impact === 'positive' && 'bg-[#FF3B30]/10 text-[#FF3B30]',
                event.impact === 'negative' && 'bg-[#3FB950]/10 text-[#3FB950]',
                event.impact === 'neutral' && 'bg-muted text-muted-foreground'
              )}>
                {event.impact === 'positive' ? '利好' : event.impact === 'negative' ? '利空' : '中性'}
              </span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Row 6: Related Stocks + Sector Ranking */}
      <motion.div 
        className="grid grid-cols-2 gap-4"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        {/* Related Stocks */}
        <div className="card-surface p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">相关股票</h3>
          <div className="space-y-2">
            {relatedStocks.map((stock, i) => (
              <div key={i} className="flex items-center justify-between p-2 bg-muted/30 rounded hover:bg-muted transition-colors cursor-pointer">
                <div>
                  <p className="text-xs font-mono">{stock.code}</p>
                  <p className="text-sm font-medium">{stock.name}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-mono">{stock.price.toFixed(2)}</p>
                  <p className={cn(
                    'text-xs font-medium',
                    stock.change >= 0 ? 'text-[#FF3B30]' : 'text-[#3FB950]'
                  )}>
                    {stock.change >= 0 ? '+' : ''}{stock.change}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sector Ranking */}
        <div className="card-surface p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground">同板块排行</h3>
            <span className="text-xs text-muted-foreground">白酒行业</span>
          </div>
          <div className="space-y-2">
            {sectorRanking.map((stock, i) => (
              <div key={i} className="flex items-center justify-between p-2 bg-muted/30 rounded hover:bg-muted transition-colors cursor-pointer">
                <div className="flex items-center gap-2">
                  <span className={cn(
                    'w-5 h-5 rounded flex items-center justify-center text-xs font-bold flex-shrink-0',
                    i === 0 && 'bg-[#FF3B30] text-white',
                    i === 1 && 'bg-[#FF8533] text-white',
                    i === 2 && 'bg-[#FFB84D] text-white',
                    i > 2 && 'bg-muted text-muted-foreground'
                  )}>
                    {i + 1}
                  </span>
                  <div>
                    <p className="text-xs font-mono">{stock.code}</p>
                    <p className="text-sm font-medium">{stock.name}</p>
                  </div>
                </div>
                <p className={cn(
                  'text-sm font-mono font-medium',
                  stock.change >= 0 ? 'text-[#FF3B30]' : 'text-[#3FB950]'
                )}>
                  {stock.change >= 0 ? '+' : ''}{stock.change}%
                </p>
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* 风险提示 */}
      <motion.div
        className="flex items-start gap-3 p-4 bg-amber-50 border-l-4 border-[#FF3B30] rounded"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
      >
        <AlertCircle className="w-5 h-5 text-[#FF3B30] flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-semibold text-[#FF3B30] mb-1">风险提示</p>
          <p className="text-xs text-amber-900">
            本页面所有数据仅供参考，不构成投资建议。股市有风险，投资需谨慎。
          </p>
        </div>
      </motion.div>
    </div>
  )
}
