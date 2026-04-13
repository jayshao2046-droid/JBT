'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Shield,
  TrendingDown,
  BarChart3,
  AlertTriangle,
  Gauge,
  Activity,
  PieChart,
  Target,
  Zap,
  RefreshCw,
  Download,
  Settings,
  Clock,
  ChevronDown,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Wallet,
  Scale,
  Percent,
  DollarSign,
  Timer,
  Bell,
  Eye,
  X,
  Loader2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  ComposedChart,
  Bar,
  ReferenceLine,
} from 'recharts'

// KPI Data
const riskKPIs = {
  riskScore: { value: 72, max: 100, level: '中等风险' },
  positionUsage: { value: 65, status: 'safe' },
  var95: { value: -28500 },
  dayDrawdown: { value: -1.2 },
  maxDrawdown: { value: -8.2 },
  leverage: { value: 1.2 },
  liquidationCountdown: { value: null },
  pendingAlerts: { value: 3 },
}

// Risk trend data (7 days)
const riskTrendData = [
  { date: '03-15', score: 65 },
  { date: '03-16', score: 68 },
  { date: '03-17', score: 70 },
  { date: '03-18', score: 75 },
  { date: '03-19', score: 72 },
  { date: '03-20', score: 71 },
  { date: '03-21', score: 72 },
]

// Position distribution
const positionDistribution = [
  { name: '期货持仓', value: 280000, percent: 56, color: '#3b82f6' },
  { name: '股票持仓', value: 165000, percent: 33, color: '#22c55e' },
  { name: '现金', value: 55000, percent: 11, color: '#a855f7' },
]

// Concentration data
const concentrationData = [
  { symbol: 'rb2405', name: '螺纹钢', value: 85000, percent: 17 },
  { symbol: 'hc2405', name: '热卷', value: 65000, percent: 13 },
  { symbol: '600519', name: '贵州茅台', value: 65000, percent: 13 },
  { symbol: 'i2405', name: '铁矿石', value: 45000, percent: 9 },
  { symbol: 'other', name: '其他', value: 240000, percent: 48 },
]

// VaR trend data (30 days)
const varTrendData = Array.from({ length: 30 }, (_, i) => ({
  date: `${(i + 1).toString().padStart(2, '0')}`,
  var: -(Math.random() * 3 + 4).toFixed(1),
  threshold: -5,
}))

// VaR breakdown
const varBreakdown = [
  { symbol: 'rb2405', name: '螺纹钢', value: -8500, percent: 30 },
  { symbol: 'hc2405', name: '热卷', value: -6200, percent: 22 },
  { symbol: '600519', name: '贵州茅台', value: -5800, percent: 20 },
  { symbol: 'other', name: '其他', value: -8000, percent: 28 },
]

// Drawdown curve data
const drawdownData = Array.from({ length: 30 }, (_, i) => {
  const base = 1 + i * 0.003
  const noise = (Math.random() - 0.5) * 0.02
  return {
    date: `${(i + 1).toString().padStart(2, '0')}`,
    netValue: (base + noise).toFixed(4),
    drawdown: (-(Math.random() * 3)).toFixed(2),
  }
})

// Risk alerts
const riskAlerts = [
  { id: 1, time: '03-21 14:30', level: 'P1', type: 'VaR', content: 'VaR 超过 5% 阈值', current: '5.7%', threshold: '5%', status: 'pending' },
  { id: 2, time: '03-21 10:15', level: 'P2', type: '集中度', content: '关联品种接近上限', current: '28%', threshold: '30%', status: 'processing' },
  { id: 3, time: '03-20 16:45', level: 'P2', type: '回撤', content: '月回撤接近预警', current: '-7.5%', threshold: '-8%', status: 'resolved' },
]

// Section Header Component
function SectionHeader({ icon: Icon, title, description }: { icon: typeof Shield; title: string; description?: string }) {
  return (
    <div className="flex items-center gap-2.5 mb-4">
      <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
        <Icon className="w-4 h-4 text-primary" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        {description && <p className="text-[11px] text-muted-foreground">{description}</p>}
      </div>
    </div>
  )
}

// KPI Card Component
function KPICard({ icon: Icon, label, value, subValue, color = 'default', trend }: {
  icon: typeof Shield
  label: string
  value: string | number
  subValue?: string
  color?: 'default' | 'green' | 'yellow' | 'red' | 'blue'
  trend?: 'up' | 'down'
}) {
  const colorClasses = {
    default: 'text-foreground',
    green: 'text-#3FB950',
    yellow: 'text-amber-500',
    red: 'text-#FF3B30',
    blue: 'text-blue-500',
  }

  return (
    <div className="card-surface p-3 flex flex-col items-center justify-center text-center min-h-[90px]">
      <Icon className="w-4 h-4 text-muted-foreground mb-1.5" />
      <p className="text-[10px] text-muted-foreground mb-1 whitespace-nowrap">{label}</p>
      <div className="flex items-baseline gap-1">
        <span className={cn("text-lg font-bold font-mono", colorClasses[color])}>{value}</span>
        {subValue && <span className="text-[10px] text-muted-foreground">{subValue}</span>}
      </div>
    </div>
  )
}

// Risk Gauge Component
function RiskGauge({ score, level }: { score: number; level: string }) {
  const getColor = (score: number) => {
    if (score <= 60) return '#22c55e'
    if (score <= 80) return '#f59e0b'
    return '#ef4444'
  }

  const rotation = (score / 100) * 180 - 90

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-48 h-24 overflow-hidden">
        {/* Background arc */}
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 200 100">
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#22c55e" />
              <stop offset="50%" stopColor="#f59e0b" />
              <stop offset="100%" stopColor="#ef4444" />
            </linearGradient>
          </defs>
          {/* Background track */}
          <path
            d="M 20 90 A 80 80 0 0 1 180 90"
            fill="none"
            stroke="currentColor"
            strokeWidth="12"
            className="text-muted/30"
          />
          {/* Colored arc */}
          <path
            d="M 20 90 A 80 80 0 0 1 180 90"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="12"
            strokeDasharray={`${(score / 100) * 251.2} 251.2`}
          />
        </svg>
        {/* Needle */}
        <div
          className="absolute bottom-0 left-1/2 w-1 h-16 origin-bottom transition-transform duration-500"
          style={{ transform: `translateX(-50%) rotate(${rotation}deg)` }}
        >
          <div className="w-full h-full bg-foreground rounded-full" />
        </div>
        {/* Center dot */}
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-foreground" />
      </div>
      <div className="text-center mt-2">
        <span className="text-3xl font-bold" style={{ color: getColor(score) }}>{score}</span>
        <span className="text-sm text-muted-foreground ml-1">/ 100</span>
      </div>
      <span className="text-xs text-muted-foreground mt-1">{level}</span>
    </div>
  )
}

export function RiskMonitorView() {
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [varMethod, setVarMethod] = useState('historical')
  const [varConfidence, setVarConfidence] = useState('95')
  const [drawdownRange, setDrawdownRange] = useState('1m')
  
  // 强平预警弹窗状态
  const [showLiquidationConfirm, setShowLiquidationConfirm] = useState(false)
  const [liquidationAction, setLiquidationAction] = useState<'reduce' | 'margin'>('reduce')
  const [liquidationRatio, setLiquidationRatio] = useState('30%')
  const [isProcessing, setIsProcessing] = useState(false)
  
  // 自动刷新计时器
  const [lastUpdateTime, setLastUpdateTime] = useState(new Date().toLocaleTimeString())
  const [isRefreshing, setIsRefreshing] = useState(false)

  const handleLiquidationAction = async (action: 'reduce' | 'margin') => {
    setLiquidationAction(action)
    setShowLiquidationConfirm(true)
  }

  const confirmLiquidationAction = async () => {
    setIsProcessing(true)
    await new Promise(r => setTimeout(r, 1200))
    setIsProcessing(false)
    setShowLiquidationConfirm(false)
  }

  const handleAutoRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => {
      setIsRefreshing(false)
      setLastUpdateTime(new Date().toLocaleTimeString())
    }, 800)
  }

  // 自动刷新效果
  useEffect(() => {
    if (!autoRefresh) return
    
    const interval = setInterval(() => {
      handleAutoRefresh()
    }, 30000) // 每30秒刷新一次
    
    return () => clearInterval(interval)
  }, [autoRefresh])

  return (
    <div className="space-y-4 p-1">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-foreground">风险监控</h1>
          <p className="text-xs text-muted-foreground">实时监控交易风险，管理仓位和风险敞口</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">自动刷新</span>
            <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} />
          </div>
          {lastUpdateTime && (
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              {isRefreshing ? (
                <>
                  <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity }}>
                    <RefreshCw className="w-3 h-3" />
                  </motion.div>
                  更新中...
                </>
              ) : (
                <>
                  <Clock className="w-3 h-3" />
                  最后更新: {lastUpdateTime}
                </>
              )}
            </span>
          )}
          <Button 
            variant="outline" 
            size="sm" 
            className="h-7 text-xs"
            onClick={handleAutoRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={cn("w-3 h-3 mr-1", isRefreshing && "animate-spin")} />
            刷新全部
          </Button>
          <Button variant="outline" size="sm" className="h-7 text-xs">
            <Download className="w-3 h-3 mr-1" />
            导出报告
          </Button>
        </div>
      </div>

      {/* Row 1: KPI Cards (8 items, 2 rows of 4) */}
      <div className="grid grid-cols-4 sm:grid-cols-8 gap-3">
        <KPICard icon={Shield} label="风险评分" value={`${riskKPIs.riskScore.value}`} subValue="/100" color={riskKPIs.riskScore.value <= 60 ? 'green' : riskKPIs.riskScore.value <= 80 ? 'yellow' : 'red'} />
        <KPICard icon={Percent} label="仓位使用率" value={`${riskKPIs.positionUsage.value}%`} color="green" />
        <KPICard icon={TrendingDown} label="VaR(95%)" value={`¥${Math.abs(riskKPIs.var95.value).toLocaleString()}`} color="red" />
        <KPICard icon={Activity} label="当日回撤" value={`${riskKPIs.dayDrawdown.value}%`} color="yellow" />
        <KPICard icon={BarChart3} label="最大回撤" value={`${riskKPIs.maxDrawdown.value}%`} color="red" />
        <KPICard icon={Scale} label="杠杆倍数" value={`${riskKPIs.leverage.value}`} subValue="倍" color="green" />
        <KPICard icon={Timer} label="强平倒计时" value={riskKPIs.liquidationCountdown.value ?? 'N/A'} color="green" />
        <KPICard icon={Bell} label="风险告警" value={riskKPIs.pendingAlerts.value} subValue="条待处理" color="yellow" />
      </div>

      {/* Row 2: Risk Dashboard */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card-surface p-4"
      >
        <SectionHeader icon={Gauge} title="整体风险仪表盘" description="综合风险评估与趋势" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Gauge */}
          <div className="flex flex-col items-center justify-center py-4">
            <div className="flex items-center gap-6 mb-4">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full bg-#3FB950" />
                <span className="text-[11px] text-muted-foreground">安全 (0-60)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full bg-amber-500" />
                <span className="text-[11px] text-muted-foreground">关注 (60-80)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full bg-#FF3B30" />
                <span className="text-[11px] text-muted-foreground">危险 (80-100)</span>
              </div>
            </div>
            <RiskGauge score={riskKPIs.riskScore.value} level={riskKPIs.riskScore.level} />
          </div>
          {/* Trend chart */}
          <div>
            <p className="text-[11px] text-muted-foreground mb-2">近 7 日风险评分变化</p>
            <div className="h-40">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={riskTrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
                  <YAxis domain={[50, 100]} tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
                  <Tooltip
                    contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '11px' }}
                  />
                  <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
                  <ReferenceLine y={60} stroke="#22c55e" strokeDasharray="3 3" />
                  <ReferenceLine y={80} stroke="#f59e0b" strokeDasharray="3 3" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Row 3: Position Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Position Usage */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="card-surface p-4"
        >
          <SectionHeader icon={Wallet} title="仓位使用分析" description="资金占用与分布" />
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3 text-center">
              <div>
                <p className="text-[10px] text-muted-foreground">总权益</p>
                <p className="text-sm font-bold text-foreground">¥500,000</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">可用资金</p>
                <p className="text-sm font-bold text-#3FB950">¥175,000</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">占用保证金</p>
                <p className="text-sm font-bold text-blue-500">¥325,000</p>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="text-muted-foreground">仓位使用率</span>
                <span className="font-mono text-foreground">65%</span>
              </div>
              <div className="h-2.5 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-#3FB950 to-blue-500 rounded-full" style={{ width: '65%' }} />
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-[11px] text-muted-foreground">仓位分布</p>
              {positionDistribution.map((item) => (
                <div key={item.name} className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: item.color }} />
                  <span className="text-[11px] text-foreground flex-1 whitespace-nowrap">{item.name}</span>
                  <span className="text-[11px] font-mono text-foreground whitespace-nowrap">¥{item.value.toLocaleString()}</span>
                  <span className="text-[10px] font-mono text-muted-foreground w-10 text-right whitespace-nowrap">{item.percent}%</span>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                className="flex-1 h-7 text-[11px]"
                onClick={() => handleLiquidationAction('reduce')}
              >
                降低仓位
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                className="flex-1 h-7 text-[11px]"
                onClick={() => handleLiquidationAction('margin')}
              >
                追加保证金
              </Button>
            </div>
          </div>
        </motion.div>

        {/* Concentration */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card-surface p-4"
        >
          <SectionHeader icon={PieChart} title="持仓集中度" description="品种分散度监控" />
          <div className="space-y-4">
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-#3FB950/10 border border-#3FB950/20">
              <span className="text-[11px] text-emerald-600">前三大持仓占比</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-emerald-600">45%</span>
                <CheckCircle2 className="w-4 h-4 text-#3FB950" />
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-[11px] text-muted-foreground">品种持仓分布</p>
              {concentrationData.map((item) => (
                <div key={item.symbol} className="flex items-center gap-2">
                  <span className="text-[11px] font-mono text-primary w-16 shrink-0 whitespace-nowrap">{item.symbol}</span>
                  <span className="text-[11px] text-foreground flex-1 whitespace-nowrap">{item.name}</span>
                  <span className="text-[11px] font-mono text-foreground whitespace-nowrap">¥{item.value.toLocaleString()}</span>
                  <span className="text-[10px] font-mono text-muted-foreground w-10 text-right whitespace-nowrap">{item.percent}%</span>
                </div>
              ))}
            </div>
            <div className="space-y-1.5">
              <p className="text-[11px] text-muted-foreground">集中度预警</p>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-muted-foreground whitespace-nowrap">单一品种上限：20%</span>
                <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950" />
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-muted-foreground whitespace-nowrap">单一板块上限：40%</span>
                <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950" />
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-muted-foreground whitespace-nowrap">关联品种上限：30%</span>
                <div className="flex items-center gap-1">
                  <span className="text-amber-500 font-mono whitespace-nowrap">28%</span>
                  <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Row 4: VaR Analysis */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="card-surface p-4"
      >
        <SectionHeader icon={TrendingDown} title="VaR 风险价值分析" description="在险价值计算与监控" />
        <div className="space-y-4">
          {/* Controls */}
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-muted-foreground whitespace-nowrap">计算方法：</span>
              <Select value={varMethod} onValueChange={setVarMethod}>
                <SelectTrigger className="w-32 h-7 text-[11px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="historical">历史模拟法</SelectItem>
                  <SelectItem value="parametric">参数法</SelectItem>
                  <SelectItem value="montecarlo">蒙特卡洛</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-muted-foreground whitespace-nowrap">置信水平：</span>
              <Select value={varConfidence} onValueChange={setVarConfidence}>
                <SelectTrigger className="w-20 h-7 text-[11px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="90">90%</SelectItem>
                  <SelectItem value="95">95%</SelectItem>
                  <SelectItem value="99">99%</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-muted-foreground whitespace-nowrap">持有期：</span>
              <Select defaultValue="1">
                <SelectTrigger className="w-20 h-7 text-[11px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 天</SelectItem>
                  <SelectItem value="5">5 天</SelectItem>
                  <SelectItem value="10">10 天</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* VaR Summary */}
          <div className="p-4 rounded-lg bg-#FF3B30/5 border border-#FF3B30/20">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-foreground">当前 VaR 值</span>
              <span className="text-xl font-bold text-#FF3B30">-¥28,500</span>
            </div>
            <p className="text-[11px] text-muted-foreground">
              占净值 <span className="text-#FF3B30 font-mono">5.7%</span> | 含义：在 95% 置信度下，未来 1 天最大可能损失不超过 ¥28,500
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* VaR Trend */}
            <div>
              <p className="text-[11px] text-muted-foreground mb-2">VaR 趋势（近 30 日）</p>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={varTrendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                    <XAxis dataKey="date" tick={{ fontSize: 9 }} stroke="hsl(var(--muted-foreground))" />
                    <YAxis domain={[-10, 0]} tick={{ fontSize: 9 }} stroke="hsl(var(--muted-foreground))" tickFormatter={(v) => `${v}%`} />
                    <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '11px' }} />
                    <ReferenceLine y={-5} stroke="#ef4444" strokeDasharray="3 3" label={{ value: '阈值', fontSize: 9, fill: '#ef4444' }} />
                    <Area type="monotone" dataKey="var" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* VaR Breakdown */}
            <div>
              <p className="text-[11px] text-muted-foreground mb-2">VaR 分解（按品种贡献）</p>
              <div className="space-y-2">
                {varBreakdown.map((item) => (
                  <div key={item.symbol} className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-primary w-16 shrink-0 whitespace-nowrap">{item.symbol}</span>
                    <span className="text-[11px] text-foreground flex-1 whitespace-nowrap">{item.name}</span>
                    <span className="text-[11px] font-mono text-#FF3B30 whitespace-nowrap">¥{Math.abs(item.value).toLocaleString()}</span>
                    <span className="text-[10px] font-mono text-muted-foreground w-10 text-right whitespace-nowrap">{item.percent}%</span>
                  </div>
                ))}
              </div>
              <div className="mt-4 p-3 rounded-lg bg-muted/30 border border-border/50">
                <p className="text-[11px] text-muted-foreground mb-2">VaR 预警阈值</p>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="w-2 h-2 rounded-full bg-#FF3B30 shrink-0" />
                    <span className="text-foreground whitespace-nowrap flex-1">P0 紧急</span>
                    <span className="font-mono text-muted-foreground whitespace-nowrap">{'>'}10% 净值</span>
                    <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950 shrink-0" />
                  </div>
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="w-2 h-2 rounded-full bg-amber-500 shrink-0" />
                    <span className="text-foreground whitespace-nowrap flex-1">P1 重要</span>
                    <span className="font-mono text-muted-foreground whitespace-nowrap">{'>'}7% 净值</span>
                    <AlertCircle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                  </div>
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0" />
                    <span className="text-foreground whitespace-nowrap flex-1">P2 提示</span>
                    <span className="font-mono text-muted-foreground whitespace-nowrap">{'>'}5% 净值</span>
                    <XCircle className="w-3.5 h-3.5 text-#FF3B30 shrink-0" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Row 5: Drawdown Monitoring */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Drawdown Analysis */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card-surface p-4"
        >
          <SectionHeader icon={TrendingDown} title="回撤监控" description="回撤状态与阈值" />
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 h-12 rounded-lg bg-#3FB950/10 border border-#3FB950/20">
              <span className="text-[11px] text-emerald-600 whitespace-nowrap">当前回撤</span>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-emerald-600">-1.2%</span>
                <CheckCircle2 className="w-4 h-4 text-#3FB950" />
              </div>
            </div>
            <div className="text-[11px] text-muted-foreground">
              最大回撤：<span className="text-#FF3B30 font-mono">-8.2%</span>（发生在 2026-02-15）
            </div>
            <div className="p-3 rounded-lg bg-muted/30 border border-border/50">
              <p className="text-[11px] text-muted-foreground mb-2">回撤阈值</p>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-[11px]">
                  <span className="text-foreground whitespace-nowrap flex-1">日回撤预警</span>
                  <span className="font-mono text-muted-foreground whitespace-nowrap">{'>-'}3%</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950 shrink-0" />
                </div>
                <div className="flex items-center gap-2 text-[11px]">
                  <span className="text-foreground whitespace-nowrap flex-1">周回撤预警</span>
                  <span className="font-mono text-muted-foreground whitespace-nowrap">{'>-'}5%</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950 shrink-0" />
                </div>
                <div className="flex items-center gap-2 text-[11px]">
                  <span className="text-foreground whitespace-nowrap flex-1">月回撤预警</span>
                  <span className="font-mono text-muted-foreground whitespace-nowrap">{'>-'}8%</span>
                  <AlertCircle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                </div>
                <div className="flex items-center gap-2 text-[11px]">
                  <span className="text-foreground whitespace-nowrap flex-1">年回撤预警</span>
                  <span className="font-mono text-muted-foreground whitespace-nowrap">{'>-'}15%</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950 shrink-0" />
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 text-center pt-2 border-t border-border/50">
              <div>
                <p className="text-[10px] text-muted-foreground">回撤恢复天数</p>
                <p className="text-sm font-bold text-foreground">12 天</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">历史最大回撤恢复</p>
                <p className="text-sm font-bold text-foreground">28 天</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Drawdown Curve */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="card-surface p-4"
        >
          <div className="flex items-center justify-between mb-4">
            <SectionHeader icon={Activity} title="净值与回撤曲线" />
            <div className="flex gap-1">
              {['1m', '3m', '6m', 'all'].map((range) => (
                <button
                  key={range}
                  onClick={() => setDrawdownRange(range)}
                  className={cn(
                    "px-2 py-1 text-[10px] rounded transition-colors whitespace-nowrap",
                    drawdownRange === range ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-secondary"
                  )}
                >
                  {range === '1m' ? '近1月' : range === '3m' ? '近3月' : range === '6m' ? '近6月' : '全部'}
                </button>
              ))}
            </div>
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={drawdownData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                <XAxis dataKey="date" tick={{ fontSize: 9 }} stroke="hsl(var(--muted-foreground))" />
                <YAxis yAxisId="left" tick={{ fontSize: 9 }} stroke="hsl(var(--muted-foreground))" domain={[0.95, 1.15]} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 9 }} stroke="hsl(var(--muted-foreground))" domain={[-10, 0]} />
                <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '11px' }} />
                <Area yAxisId="right" type="monotone" dataKey="drawdown" stroke="#ef4444" fill="#ef4444" fillOpacity={0.15} />
                <Line yAxisId="left" type="monotone" dataKey="netValue" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Row 6: Leverage & Liquidation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Leverage */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card-surface p-4"
        >
          <SectionHeader icon={Scale} title="杠杆监控" description="杠杆倍数与限制" />
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 h-12 rounded-lg bg-#3FB950/10 border border-#3FB950/20">
              <span className="text-[11px] text-emerald-600 whitespace-nowrap">当前杠杆</span>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-emerald-600">1.2 倍</span>
                <CheckCircle2 className="w-4 h-4 text-#3FB950" />
              </div>
            </div>
            <div className="space-y-2 text-[11px]">
              <p className="text-muted-foreground">杠杆计算</p>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-2 rounded bg-muted/30">
                  <p className="text-[10px] text-muted-foreground">总资产</p>
                  <p className="font-mono text-foreground">¥600,000</p>
                </div>
                <div className="p-2 rounded bg-muted/30">
                  <p className="text-[10px] text-muted-foreground">净资产</p>
                  <p className="font-mono text-foreground">¥500,000</p>
                </div>
                <div className="p-2 rounded bg-muted/30">
                  <p className="text-[10px] text-muted-foreground">杠杆倍数</p>
                  <p className="font-mono text-blue-500">1.2 倍</p>
                </div>
              </div>
            </div>
            <div className="p-3 rounded-lg bg-muted/30 border border-border/50">
              <p className="text-[11px] text-muted-foreground mb-2">杠杆阈值</p>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-[11px]">
                  <span className="w-2 h-2 rounded-full bg-amber-500 shrink-0" />
                  <span className="text-foreground whitespace-nowrap flex-1">预警线</span>
                  <span className="font-mono text-muted-foreground whitespace-nowrap">{'>'}1.5 倍</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950 shrink-0" />
                </div>
                <div className="flex items-center gap-2 text-[11px]">
                  <span className="w-2 h-2 rounded-full bg-orange-500 shrink-0" />
                  <span className="text-foreground whitespace-nowrap flex-1">警戒线</span>
                  <span className="font-mono text-muted-foreground whitespace-nowrap">{'>'}2.0 倍</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950 shrink-0" />
                </div>
                <div className="flex items-center gap-2 text-[11px]">
                  <span className="w-2 h-2 rounded-full bg-#FF3B30 shrink-0" />
                  <span className="text-foreground whitespace-nowrap flex-1">强平线</span>
                  <span className="font-mono text-muted-foreground whitespace-nowrap">{'>'}3.0 倍</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950 shrink-0" />
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Liquidation Warning */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45 }}
          className="card-surface p-4"
        >
          <SectionHeader icon={AlertTriangle} title="强平预警" description="强制平仓风险监控" />
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 h-12 rounded-lg bg-#3FB950/10 border border-#3FB950/20">
              <span className="text-[11px] text-emerald-600 whitespace-nowrap">强平状态</span>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-emerald-600">未触发</span>
                <CheckCircle2 className="w-4 h-4 text-#3FB950" />
              </div>
            </div>
            <div className="space-y-1.5">
              <p className="text-[11px] text-muted-foreground">强平条件检查</p>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-muted-foreground whitespace-nowrap">维持保证金充足率</span>
                <div className="flex items-center gap-1">
                  <span className="font-mono text-#3FB950 whitespace-nowrap">185%</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950" />
                </div>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-muted-foreground whitespace-nowrap">可用资金</span>
                <div className="flex items-center gap-1">
                  <span className="font-mono text-#3FB950 whitespace-nowrap">¥175,000</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950" />
                </div>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-muted-foreground whitespace-nowrap">风险度</span>
                <div className="flex items-center gap-1">
                  <span className="font-mono text-#3FB950 whitespace-nowrap">65%</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950" />
                </div>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-muted-foreground whitespace-nowrap">强平倒计时</span>
                <span className="font-mono text-muted-foreground whitespace-nowrap">N/A</span>
              </div>
            </div>
            <div className="p-3 rounded-lg bg-muted/30 border border-border/50">
              <p className="text-[11px] text-muted-foreground mb-2">强平预警线</p>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-[11px]">
                  <span className="w-2 h-2 rounded-full bg-amber-500 shrink-0" />
                  <span className="text-foreground whitespace-nowrap flex-1">一级预警</span>
                  <span className="font-mono text-muted-foreground whitespace-nowrap">风险度{'>'}80%</span>
                  <span className="font-mono text-#3FB950 whitespace-nowrap w-10 text-right">65%</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950 shrink-0" />
                </div>
                <div className="flex items-center gap-2 text-[11px]">
                  <span className="w-2 h-2 rounded-full bg-orange-500 shrink-0" />
                  <span className="text-foreground whitespace-nowrap flex-1">二级预警</span>
                  <span className="font-mono text-muted-foreground whitespace-nowrap">风险度{'>'}90%</span>
                  <span className="w-10" />
                  <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950 shrink-0" />
                </div>
                <div className="flex items-center gap-2 text-[11px]">
                  <span className="w-2 h-2 rounded-full bg-#FF3B30 shrink-0" />
                  <span className="text-foreground whitespace-nowrap flex-1">强平触发</span>
                  <span className="font-mono text-muted-foreground whitespace-nowrap">风险度{'>'}100%</span>
                  <span className="w-10" />
                  <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950 shrink-0" />
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="flex-1 h-7 text-[11px]">
                <DollarSign className="w-3 h-3 mr-1" />
                追加保证金
              </Button>
              <Button variant="outline" size="sm" className="flex-1 h-7 text-[11px]">
                <TrendingDown className="w-3 h-3 mr-1" />
                降低仓位
              </Button>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Row 7: Risk Alerts Table */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="card-surface p-4"
      >
        <SectionHeader icon={Bell} title="当前风险告警" description="待处理的风险告警列表" />
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">告警时间</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">级别</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">告警类型</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">告警内容</th>
                <th className="text-right py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">当前值</th>
                <th className="text-right py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">阈值</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">状态</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">操作</th>
              </tr>
            </thead>
            <tbody>
              {riskAlerts.map((alert, index) => (
                <tr key={alert.id} className={cn("border-b border-border/50", index % 2 === 0 && "bg-muted/20")}>
                  <td className="py-2.5 px-2 font-mono text-foreground whitespace-nowrap">{alert.time}</td>
                  <td className="py-2.5 px-2 text-center">
                    <span className={cn(
                      "px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap",
                      alert.level === 'P0' ? 'bg-#FF3B30/10 text-#FF3B30' :
                      alert.level === 'P1' ? 'bg-amber-500/10 text-amber-500' :
                      'bg-blue-500/10 text-blue-500'
                    )}>
                      {alert.level}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-foreground whitespace-nowrap">{alert.type}</td>
                  <td className="py-2.5 px-2 text-foreground whitespace-nowrap">{alert.content}</td>
                  <td className="py-2.5 px-2 text-right font-mono text-#FF3B30 whitespace-nowrap">{alert.current}</td>
                  <td className="py-2.5 px-2 text-right font-mono text-muted-foreground whitespace-nowrap">{alert.threshold}</td>
                  <td className="py-2.5 px-2 text-center">
                    <span className={cn(
                      "px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap",
                      alert.status === 'pending' ? 'bg-#FF3B30/10 text-#FF3B30' :
                      alert.status === 'processing' ? 'bg-amber-500/10 text-amber-500' :
                      'bg-#3FB950/10 text-#3FB950'
                    )}>
                      {alert.status === 'pending' ? '未处理' : alert.status === 'processing' ? '处理中' : '已解决'}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    <div className="flex items-center justify-center gap-1">
                      {alert.status !== 'resolved' ? (
                        <>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]">处理</Button>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]">忽略</Button>
                        </>
                      ) : (
                        <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]">
                          <Eye className="w-3 h-3 mr-1" />
                          查看
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* 强平预警二次确认弹窗 */}
      {showLiquidationConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <motion.div
            className="bg-card rounded-lg border border-border shadow-xl max-w-[560px] w-[90%]"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/30">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                <h2 className="text-sm font-semibold text-foreground">确认强平操作？</h2>
              </div>
              <button
                onClick={() => setShowLiquidationConfirm(false)}
                disabled={isProcessing}
                className="p-1 hover:bg-muted rounded transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content */}
            <div className="px-6 py-4 space-y-4">
              {/* Current Risk Status */}
              <div className="space-y-2 p-3 bg-muted/30 rounded-lg">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-muted-foreground">当前风险等级：</span>
                  <span className="font-semibold text-amber-500">中等风险 ({riskKPIs.riskScore.value} 分)</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-muted-foreground">仓位使用率：</span>
                  <span className="font-mono">{riskKPIs.positionUsage.value}%</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-muted-foreground">杠杆倍数：</span>
                  <span className="font-mono">{riskKPIs.leverage.value} 倍</span>
                </div>
              </div>

              {/* Operation Options */}
              <div className="space-y-3 p-3 bg-muted/20 rounded-lg">
                <div className="space-y-2">
                  <label className="text-xs font-medium text-foreground">操作类型：</label>
                  <select 
                    value={liquidationAction}
                    onChange={(e) => setLiquidationAction(e.target.value as 'reduce' | 'margin')}
                    className="w-full px-3 py-2 bg-muted border border-border rounded text-sm"
                  >
                    <option value="reduce">降低仓位</option>
                    <option value="margin">追加保证��</option>
                  </select>
                </div>
                {liquidationAction === 'reduce' && (
                  <div className="space-y-2">
                    <label className="text-xs font-medium text-foreground">平仓比例：</label>
                    <select 
                      value={liquidationRatio}
                      onChange={(e) => setLiquidationRatio(e.target.value)}
                      className="w-full px-3 py-2 bg-muted border border-border rounded text-sm"
                    >
                      <option value="10%">10%</option>
                      <option value="20%">20%</option>
                      <option value="30%">30%</option>
                      <option value="50%">50%</option>
                      <option value="100%">100% (全部平仓)</option>
                    </select>
                  </div>
                )}
              </div>

              {/* Warning */}
              <div className="p-3 bg-amber-500/10 border border-l-4 border-l-amber-500 border-amber-500/20 rounded">
                <p className="text-xs text-amber-700 dark:text-amber-300 font-medium">⚠️ 注意：此操作将立即执行，请确认</p>
              </div>
            </div>

            {/* Footer */}
            <div className="flex gap-3 px-6 py-4 border-t border-border/30 bg-muted/20">
              <button
                onClick={() => setShowLiquidationConfirm(false)}
                disabled={isProcessing}
                className="flex-1 px-4 py-2 text-sm font-medium text-foreground border border-border rounded-md hover:bg-muted transition-colors disabled:opacity-50"
              >
                取消
              </button>
              <button
                onClick={confirmLiquidationAction}
                disabled={isProcessing}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-amber-500 hover:bg-amber-500/90 rounded-md transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    处理中...
                  </>
                ) : (
                  '确认执行'
                )}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
