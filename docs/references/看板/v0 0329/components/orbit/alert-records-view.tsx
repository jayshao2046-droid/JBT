"use client";

import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Bell,
  AlertTriangle,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Search,
  Filter,
  Download,
  RefreshCw,
  ChevronDown,
  Eye,
  ArrowUpCircle,
  Trash2,
  Settings,
  TrendingUp,
  BarChart3,
  PieChart,
  Calendar,
  Timer,
  Percent,
  Activity,
  Zap,
  FileDown,
  MessageSquare,
  Users,
  Phone,
  Mail,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Checkbox } from "@/components/ui/checkbox"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart as RePieChart,
  Pie,
  Legend,
} from 'recharts'

// KPI Data
const alertKPIs = {
  todayAlerts: 12,
  pending: 3,
  processing: 2,
  resolved: 7,
  falsePositiveRate: 2.5,
  avgResponseTime: 15,
}

// Alert level counts
const alertLevelCounts = {
  P0: 3,
  P1: 5,
  P2: 4,
}

// Alert records
const alertRecords = [
  { id: 'ALM20260321001', time: '03-21 14:30', level: 'P0', type: 'VaR', content: 'VaR 超阈值', symbol: '全部', current: '5.7%', threshold: '5%', source: '自动', status: 'pending' },
  { id: 'ALM20260321002', time: '03-21 10:15', level: 'P1', type: '仓位', content: '仓位超限', symbol: 'rb2405', current: '22%', threshold: '20%', source: '自动', status: 'processing' },
  { id: 'ALM20260321003', time: '03-21 09:30', level: 'P1', type: '杠杆', content: '杠杆接近预警', symbol: '全部', current: '1.45倍', threshold: '1.5倍', source: '自动', status: 'pending' },
  { id: 'ALM20260320001', time: '03-20 16:45', level: 'P2', type: '回撤', content: '回撤预警', symbol: '全部', current: '-7.5%', threshold: '-8%', source: '自动', status: 'resolved' },
  { id: 'ALM20260320002', time: '03-20 14:20', level: 'P1', type: '集中度', content: '品种集中度预警', symbol: 'rb系列', current: '28%', threshold: '30%', source: '自动', status: 'resolved' },
  { id: 'ALM20260320003', time: '03-20 11:10', level: 'P2', type: 'VaR', content: 'VaR 接近阈值', symbol: '全部', current: '4.8%', threshold: '5%', source: '自动', status: 'resolved' },
  { id: 'ALM20260319001', time: '03-19 15:30', level: 'P0', type: '回撤', content: '日回撤超限', symbol: '全部', current: '-3.2%', threshold: '-3%', source: '自动', status: 'resolved' },
  { id: 'ALM20260319002', time: '03-19 10:00', level: 'P2', type: '流动性', content: '流动性不足', symbol: 'i2405', current: '低', threshold: '中', source: '人工', status: 'ignored' },
]

// Alert trend data (30 days)
const alertTrendData = Array.from({ length: 30 }, (_, i) => ({
  date: `${(i + 1).toString().padStart(2, '0')}`,
  P0: Math.floor(Math.random() * 3),
  P1: Math.floor(Math.random() * 5),
  P2: Math.floor(Math.random() * 6),
}))

// Alert type distribution
const alertTypeDistribution = [
  { name: '仓位告警', value: 35, color: '#3b82f6' },
  { name: 'VaR 告警', value: 25, color: '#ef4444' },
  { name: '回撤告警', value: 20, color: '#f59e0b' },
  { name: '杠杆告警', value: 10, color: '#8b5cf6' },
  { name: '其他告警', value: 10, color: '#6b7280' },
]

// Alert config
const alertConfig = [
  {
    level: 'P0',
    name: '紧急告警',
    conditions: 'VaR>10% / 回撤>-10% / 杠杆>2.5倍',
    channels: ['飞书', '邮件'],
    frequency: '立即',
    escalation: '15分钟未处理自动升级',
  },
  {
    level: 'P1',
    name: '重要告警',
    conditions: 'VaR>7% / 回撤>-7% / 杠杆>2.0倍',
    channels: ['飞书', '邮件'],
    frequency: '每小时汇总',
    escalation: '1小时未处理升级为P0',
  },
  {
    level: 'P2',
    name: '提示告警',
    conditions: 'VaR>5% / 回撤>-5% / 杠杆>1.5倍',
    channels: ['飞书', '邮件'],
    frequency: '每日汇总',
    escalation: '24小时未处理升级为P1',
  },
]

// Section Header Component
function SectionHeader({ icon: Icon, title, description }: { icon: typeof Bell; title: string; description?: string }) {
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
function KPICard({ icon: Icon, label, value, subValue, color = 'default' }: {
  icon: typeof Bell
  label: string
  value: string | number
  subValue?: string
  color?: 'default' | 'green' | 'yellow' | 'red' | 'blue'
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

export function AlertRecordsView() {
  const { toast } = useToast()
  const [levelFilter, setLevelFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [timeRange, setTimeRange] = useState('today')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedAlerts, setSelectedAlerts] = useState<string[]>([])
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(20)
  
  // Dialog states
  const [showProcessDialog, setShowProcessDialog] = useState(false)
  const [showUpgradeDialog, setShowUpgradeDialog] = useState(false)
  const [selectedAlert, setSelectedAlert] = useState<typeof alertRecords[0] | null>(null)
  const [processMethod, setProcessMethod] = useState('')
  const [upgrading, setUpgrading] = useState(false)
  const [processNote, setProcessNote] = useState('')
  const [notifyUsers, setNotifyUsers] = useState(false)

  // 告警处理日志
  interface AlertLog {
    alertId: string
    processedAt: string
    processedBy: string
    method: string
    note: string
    notifiedUsers: string[]
  }
  
  const saveAlertLog = (log: AlertLog) => {
    const logs = JSON.parse(localStorage.getItem('alertLogs') || '[]')
    logs.push(log)
    localStorage.setItem('alertLogs', JSON.stringify(logs))
  }

  const toggleSelectAlert = (id: string) => {
    setSelectedAlerts(prev =>
      prev.includes(id) ? prev.filter(a => a !== id) : [...prev, id]
    )
  }

  const toggleSelectAll = () => {
    if (selectedAlerts.length === alertRecords.length) {
      setSelectedAlerts([])
    } else {
      setSelectedAlerts(alertRecords.map(a => a.id))
    }
  }

  const filteredAlerts = alertRecords.filter(alert => {
    if (levelFilter !== 'all' && alert.level !== levelFilter) return false
    if (typeFilter !== 'all' && alert.type !== typeFilter) return false
    if (statusFilter !== 'all' && alert.status !== statusFilter) return false
    if (searchQuery && !alert.content.includes(searchQuery) && !alert.symbol.includes(searchQuery)) return false
    return true
  })

  // 分页逻辑
  const totalPages = Math.ceil(filteredAlerts.length / itemsPerPage)
  const paginatedAlerts = filteredAlerts.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  // CSV Export
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

  const exportAlerts = () => {
    const data = filteredAlerts.map(a => ({
      '告警ID': a.id,
      '时间': a.time,
      '级别': a.level,
      '类型': a.type,
      '内容': a.content,
      '品种': a.symbol,
      '当前值': a.current,
      '阈值': a.threshold,
      '来源': a.source,
      '状态': a.status === 'pending' ? '未处理' : a.status === 'processing' ? '处理中' : a.status === 'resolved' ? '已解决' : '已忽略'
    }))
    exportCSV(data, '告警记录')
  }

  const exportSelectedAlerts = () => {
    const selected = alertRecords.filter(a => selectedAlerts.includes(a.id))
    const data = selected.map(a => ({
      '告警ID': a.id,
      '时间': a.time,
      '级别': a.level,
      '类型': a.type,
      '内容': a.content,
      '品种': a.symbol,
      '当前值': a.current,
      '阈值': a.threshold,
      '来源': a.source,
      '状态': a.status === 'pending' ? '未处理' : a.status === 'processing' ? '处理中' : a.status === 'resolved' ? '已解决' : '已忽略'
    }))
    exportCSV(data, '选中告警')
  }

  // Alert handling
  const handleProcess = (alert: typeof alertRecords[0]) => {
    setSelectedAlert(alert)
    setProcessMethod('')
    setProcessNote('')
    setNotifyUsers(false)
    setShowProcessDialog(true)
  }

  const confirmProcess = () => {
    if (!processMethod) {
      toast({ title: "请选择处理方式", variant: "destructive" })
      return
    }
    
    if (selectedAlert) {
      // 保存处理日志
      const log: AlertLog = {
        alertId: selectedAlert.id,
        processedAt: new Date().toISOString(),
        processedBy: '当前用户',
        method: processMethod,
        note: processNote,
        notifiedUsers: notifyUsers ? ['系统管理员', '风控员'] : []
      }
      saveAlertLog(log)
    }
    
    toast({ title: "处理成功", description: `告警 ${selectedAlert?.id} 已标记为已处理` })
    setShowProcessDialog(false)
    setSelectedAlert(null)
  }

  const handleUpgrade = (alert: typeof alertRecords[0]) => {
    setSelectedAlert(alert)
    setShowUpgradeDialog(true)
  }

  const confirmUpgrade = async () => {
    if (!selectedAlert) return
    setUpgrading(true)
    
    // Simulate sending notifications
    await new Promise(r => setTimeout(r, 1000))
    
    const oldLevel = selectedAlert.level
    const newLevel = oldLevel === 'P1' ? 'P0' : oldLevel === 'P2' ? 'P1' : oldLevel
    
    // Notification logic based on upgrade type
    let notificationSent = ''
    if (oldLevel === 'P1' && newLevel === 'P0') {
      // P1 -> P0: Send SMS + Phone
      notificationSent = '已发送短信和电话通知'
    } else if (oldLevel === 'P2' && newLevel === 'P1') {
      // P2 -> P1: Send Email
      notificationSent = '已发送邮件通知'
    }
    
    setUpgrading(false)
    setShowUpgradeDialog(false)
    
    toast({ 
      title: "升级成功", 
      description: `告警已从 ${oldLevel} 升级为 ${newLevel}，${notificationSent}` 
    })
    setSelectedAlert(null)
  }

  const handleIgnore = (alert: typeof alertRecords[0]) => {
    toast({ title: "已忽略", description: `告警 ${alert.id} 已标记为误��` })
  }

  const handleBatchProcess = () => {
    if (selectedAlerts.length === 0) {
      toast({ title: "请先选择告警", variant: "destructive" })
      return
    }
    toast({ title: "批量处理成功", description: `已处理 ${selectedAlerts.length} 条告警` })
    setSelectedAlerts([])
  }

  return (
    <div className="space-y-4 p-1">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-foreground">告警记录</h1>
          <p className="text-xs text-muted-foreground">管理和处理风险告警，追踪告警处理流程</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="h-7 text-xs">
            <RefreshCw className="w-3 h-3 mr-1" />
            刷新
          </Button>
          <Button variant="outline" size="sm" className="h-7 text-xs" onClick={exportAlerts}>
            <FileDown className="w-3 h-3 mr-1" />
            导出
          </Button>
        </div>
      </div>

      {/* Row 1: KPI Cards */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
        <KPICard icon={Bell} label="今日告警" value={alertKPIs.todayAlerts} subValue="条" />
        <KPICard icon={AlertCircle} label="未处理" value={alertKPIs.pending} subValue="条" color="red" />
        <KPICard icon={Clock} label="处理中" value={alertKPIs.processing} subValue="条" color="yellow" />
        <KPICard icon={CheckCircle2} label="已处理" value={alertKPIs.resolved} subValue="条" color="green" />
        <KPICard icon={Percent} label="误报率" value={alertKPIs.falsePositiveRate} subValue="%" color="blue" />
        <KPICard icon={Timer} label="平均响应" value={alertKPIs.avgResponseTime} subValue="分钟" />
      </div>

      {/* Row 2: Filters */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card-surface p-4"
      >
        <SectionHeader icon={Filter} title="告警级别筛选" description="快速筛选和搜索告警" />
        <div className="space-y-3">
          {/* Level quick filters */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setLevelFilter('all')}
              className={cn(
                "px-3 py-1.5 rounded-md text-[11px] font-medium transition-colors whitespace-nowrap",
                levelFilter === 'all' ? "bg-primary text-primary-foreground" : "bg-muted/50 text-muted-foreground hover:bg-muted"
              )}
            >
              全部
            </button>
            <button
              onClick={() => setLevelFilter('P0')}
              className={cn(
                "px-3 py-1.5 rounded-md text-[11px] font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap",
                levelFilter === 'P0' ? "bg-#FF3B30 text-white" : "bg-#FF3B30/10 text-#FF3B30 hover:bg-#FF3B30/20"
              )}
            >
              P0 紧急 <span className="px-1.5 py-0.5 rounded bg-white/20 text-[10px]">{alertLevelCounts.P0}</span>
            </button>
            <button
              onClick={() => setLevelFilter('P1')}
              className={cn(
                "px-3 py-1.5 rounded-md text-[11px] font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap",
                levelFilter === 'P1' ? "bg-amber-500 text-white" : "bg-amber-500/10 text-amber-500 hover:bg-amber-500/20"
              )}
            >
              P1 重要 <span className="px-1.5 py-0.5 rounded bg-white/20 text-[10px]">{alertLevelCounts.P1}</span>
            </button>
            <button
              onClick={() => setLevelFilter('P2')}
              className={cn(
                "px-3 py-1.5 rounded-md text-[11px] font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap",
                levelFilter === 'P2' ? "bg-blue-500 text-white" : "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20"
              )}
            >
              P2 提示 <span className="px-1.5 py-0.5 rounded bg-white/20 text-[10px]">{alertLevelCounts.P2}</span>
            </button>
          </div>

          {/* Other filters */}
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-muted-foreground whitespace-nowrap">按类型：</span>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-24 h-7 text-[11px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="仓位">仓位</SelectItem>
                  <SelectItem value="VaR">VaR</SelectItem>
                  <SelectItem value="回撤">回撤</SelectItem>
                  <SelectItem value="杠杆">杠杆</SelectItem>
                  <SelectItem value="集中度">集中度</SelectItem>
                  <SelectItem value="流动性">流动性</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-muted-foreground whitespace-nowrap">按状态：</span>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-24 h-7 text-[11px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="pending">未处理</SelectItem>
                  <SelectItem value="processing">处理中</SelectItem>
                  <SelectItem value="resolved">已解决</SelectItem>
                  <SelectItem value="ignored">已忽略</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[11px] text-muted-foreground whitespace-nowrap">时间：</span>
              {['today', 'week', 'month', 'custom'].map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={cn(
                    "px-2 py-1 text-[10px] rounded transition-colors whitespace-nowrap",
                    timeRange === range ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-secondary"
                  )}
                >
                  {range === 'today' ? '今日' : range === 'week' ? '本周' : range === 'month' ? '本月' : '自定义'}
                </button>
              ))}
            </div>
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                <Input
                  placeholder="搜索告警内容..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 h-7 text-[11px]"
                />
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Row 3: Alert List */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="card-surface p-4"
      >
        <div className="flex items-center justify-between mb-4">
          <SectionHeader icon={Bell} title="告警记录列表" description={`共 ${filteredAlerts.length} 条记录`} />
          <div className="flex items-center gap-2">
            {selectedAlerts.length > 0 && (
              <>
                <Button variant="outline" size="sm" className="h-7 text-[10px]" onClick={handleBatchProcess}>
                  <CheckCircle2 className="w-3 h-3 mr-1" />
                  批量标记已处理 ({selectedAlerts.length})
                </Button>
                <Button variant="outline" size="sm" className="h-7 text-[10px]" onClick={exportSelectedAlerts}>
                  <FileDown className="w-3 h-3 mr-1" />
                  批量导出
                </Button>
              </>
            )}
          </div>
        </div>
        <div className="overflow-x-auto">
          {filteredAlerts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <AlertCircle className="w-8 h-8 text-muted-foreground/30 mb-3" />
              <p className="text-sm text-muted-foreground">暂无风险告警</p>
            </div>
          ) : (
            <>
            <table className="w-full text-[11px]">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2 px-2 w-8">
                  <Checkbox
                    checked={selectedAlerts.length === alertRecords.length}
                    onCheckedChange={toggleSelectAll}
                  />
                </th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">告警时间</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">级别</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">告警类型</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">告警内容</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">相关品种</th>
                <th className="text-right py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">当前值</th>
                <th className="text-right py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">阈值</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">发现渠道</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">状态</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">操作</th>
              </tr>
            </thead>
            <tbody>
                {paginatedAlerts.map((alert, index) => (
                <tr key={alert.id} className={cn("border-b border-border/50", index % 2 === 0 && "bg-muted/20")}>
                  <td className="py-2.5 px-2">
                    <Checkbox
                      checked={selectedAlerts.includes(alert.id)}
                      onCheckedChange={() => toggleSelectAlert(alert.id)}
                    />
                  </td>
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
                  <td className="py-2.5 px-2 font-mono text-primary whitespace-nowrap">{alert.symbol}</td>
                  <td className="py-2.5 px-2 text-right font-mono text-#FF3B30 whitespace-nowrap">{alert.current}</td>
                  <td className="py-2.5 px-2 text-right font-mono text-muted-foreground whitespace-nowrap">{alert.threshold}</td>
                  <td className="py-2.5 px-2 text-center text-muted-foreground whitespace-nowrap">{alert.source}</td>
                  <td className="py-2.5 px-2 text-center">
                    <span className={cn(
                      "px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap",
                      alert.status === 'pending' ? 'bg-#FF3B30/10 text-#FF3B30' :
                      alert.status === 'processing' ? 'bg-amber-500/10 text-amber-500' :
                      alert.status === 'resolved' ? 'bg-#3FB950/10 text-#3FB950' :
                      'bg-gray-500/10 text-gray-500'
                    )}>
                      {alert.status === 'pending' ? '未处理' : alert.status === 'processing' ? '处理中' : alert.status === 'resolved' ? '已解决' : '已忽略'}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    <div className="flex items-center justify-center gap-1">
                      {alert.status === 'pending' || alert.status === 'processing' ? (
                        <>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]" onClick={() => handleProcess(alert)}>��理</Button>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]" onClick={() => handleUpgrade(alert)}>升级</Button>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]" onClick={() => handleIgnore(alert)}>忽略</Button>
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
            {/* 分页器 */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4 px-4 py-2 border-t border-border/30 bg-muted/20">
                <span className="text-xs text-muted-foreground">
                  第 {currentPage} / {totalPages} 页，共 {filteredAlerts.length} 条
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 text-xs bg-muted hover:bg-muted/80 disabled:opacity-50 rounded transition-colors"
                  >
                    上一页
                  </button>
                  <button
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 text-xs bg-muted hover:bg-muted/80 disabled:opacity-50 rounded transition-colors"
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

      {/* Row 4: Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Alert Trend */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card-surface p-4"
        >
          <SectionHeader icon={BarChart3} title="近 30 日告警趋势" description="按级别分组的告警数量" />
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={alertTrendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                <XAxis dataKey="date" tick={{ fontSize: 9 }} stroke="hsl(var(--muted-foreground))" />
                <YAxis tick={{ fontSize: 9 }} stroke="hsl(var(--muted-foreground))" />
                <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '11px' }} />
                <Bar dataKey="P0" stackId="a" fill="#ef4444" name="P0 紧急" />
                <Bar dataKey="P1" stackId="a" fill="#f59e0b" name="P1 重要" />
                <Bar dataKey="P2" stackId="a" fill="#3b82f6" name="P2 提示" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Alert Type Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="card-surface p-4"
        >
          <SectionHeader icon={PieChart} title="告警类型分布" description="各类型告警占比" />
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <RePieChart>
                <Pie
                  data={alertTypeDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={70}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, value }) => `${name} ${value}%`}
                  labelLine={{ stroke: 'hsl(var(--muted-foreground))', strokeWidth: 1 }}
                >
                  {alertTypeDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '11px' }} />
              </RePieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Row 5: Alert Configuration */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card-surface p-4"
      >
        <SectionHeader icon={Settings} title="告警配置" description="各级别告警触发条件和通知设置" />
        <div className="space-y-3">
          {alertConfig.map((config) => (
            <div
              key={config.level}
              className={cn(
                "p-3 rounded-lg border",
                config.level === 'P0' ? 'bg-#FF3B30/5 border-#FF3B30/20' :
                config.level === 'P1' ? 'bg-amber-500/5 border-amber-500/20' :
                'bg-blue-500/5 border-blue-500/20'
              )}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className={cn(
                  "px-2 py-0.5 rounded text-[11px] font-bold",
                  config.level === 'P0' ? 'bg-#FF3B30 text-white' :
                  config.level === 'P1' ? 'bg-amber-500 text-white' :
                  'bg-blue-500 text-white'
                )}>
                  {config.level}
                </span>
                <span className="text-sm font-semibold text-foreground">{config.name}配置</span>
              </div>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-[11px]">
                <div>
                  <span className="text-muted-foreground">触发条件：</span>
                  <span className="text-foreground whitespace-nowrap">{config.conditions}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">通知渠道：</span>
                  <span className="text-foreground whitespace-nowrap">{config.channels.join(' + ')}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">通知频率：</span>
                  <span className="text-foreground whitespace-nowrap">{config.frequency}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">升级机制：</span>
                  <span className="text-foreground whitespace-nowrap">{config.escalation}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Process Alert Dialog */}
      <Dialog open={showProcessDialog} onOpenChange={setShowProcessDialog}>
        <DialogContent className="sm:max-w-[550px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-primary" />
              处理告警
            </DialogTitle>
            <DialogDescription>
              请确认告警详情并选择处理方式
            </DialogDescription>
          </DialogHeader>
          
          {selectedAlert && (
            <div className="space-y-4 py-4">
              {/* Alert Details */}
              <div className="p-4 bg-muted/50 rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">告警ID</span>
                  <span className="text-xs font-mono font-semibold">{selectedAlert.id}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">告警时间</span>
                  <span className="text-xs font-mono">{selectedAlert.time}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">告警级别</span>
                  <span className={cn(
                    "px-2 py-0.5 rounded text-[10px] font-medium",
                    selectedAlert.level === 'P0' ? 'bg-#FF3B30/10 text-#FF3B30' :
                    selectedAlert.level === 'P1' ? 'bg-amber-500/10 text-amber-500' :
                    'bg-blue-500/10 text-blue-500'
                  )}>
                    {selectedAlert.level}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">告警内容</span>
                  <span className="text-xs font-medium">{selectedAlert.content}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">当前值 / 阈值</span>
                  <span className="text-xs font-mono">
                    <span className="text-#FF3B30">{selectedAlert.current}</span>
                    <span className="text-muted-foreground mx-1">/</span>
                    <span>{selectedAlert.threshold}</span>
                  </span>
                </div>
              </div>

              {/* Impact Assessment */}
              <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <p className="text-xs font-medium text-amber-600 mb-2">影响评估</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div><span className="text-muted-foreground">影响账户：</span>主账户</div>
                  <div><span className="text-muted-foreground">影响品种：</span>{selectedAlert.symbol}</div>
                  <div><span className="text-muted-foreground">潜在损失：</span>约 ¥5,000</div>
                  <div><span className="text-muted-foreground">建议操作：</span>立即处理</div>
                </div>
              </div>

              {/* Process Method */}
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">处理方式</p>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: 'reduce', label: '降低仓位', icon: TrendingDown },
                    { id: 'hedge', label: '对冲操作', icon: Activity },
                    { id: 'margin', label: '追加保证金', icon: Zap },
                    { id: 'other', label: '其他操作', icon: Settings },
                  ].map((method) => (
                    <button
                      key={method.id}
                      onClick={() => setProcessMethod(method.id)}
                      className={cn(
                        "flex items-center gap-2 p-3 rounded-lg border text-xs transition-colors",
                        processMethod === method.id 
                          ? "border-primary bg-primary/10 text-primary" 
                          : "border-border hover:bg-muted/50"
                      )}
                    >
                      <method.icon className="w-4 h-4" />
                      {method.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Process Note */}
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">处理说明</p>
                <Textarea
                  placeholder="请输入处理说明..."
                  value={processNote}
                  onChange={(e) => setProcessNote(e.target.value)}
                  className="h-20 text-xs"
                />
              </div>

              {/* Notify Users */}
              <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-muted-foreground" />
                  <span className="text-xs">通知相关人员</span>
                </div>
                <div className="flex items-center gap-3">
                  <button 
                    onClick={() => setNotifyUsers(!notifyUsers)}
                    className={cn(
                      "flex items-center gap-1 px-2 py-1 rounded text-[10px] transition-colors",
                      notifyUsers ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                    )}
                  >
                    <Mail className="w-3 h-3" />
                    邮件
                  </button>
                  <button 
                    onClick={() => setNotifyUsers(!notifyUsers)}
                    className={cn(
                      "flex items-center gap-1 px-2 py-1 rounded text-[10px] transition-colors",
                      notifyUsers ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                    )}
                  >
                    <Phone className="w-3 h-3" />
                    电话
                  </button>
                </div>
              </div>
            </div>
          )}

          <DialogFooter className="flex gap-2">
            <Button variant="outline" onClick={() => setShowProcessDialog(false)}>取消</Button>
            <Button variant="outline" onClick={() => {
              handleUpgrade(selectedAlert)
              setShowProcessDialog(false)
            }}>
              <ArrowUpCircle className="w-4 h-4 mr-1" />
              升级告警
            </Button>
            <Button variant="outline" onClick={() => {
              toast({ title: "已标记", description: "告警已标记为误报" })
              setShowProcessDialog(false)
            }}>
              标记误报
            </Button>
            <Button onClick={confirmProcess}>
              <CheckCircle2 className="w-4 h-4 mr-1" />
              确认处理
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upgrade Confirmation Dialog */}
      <Dialog open={showUpgradeDialog} onOpenChange={setShowUpgradeDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-600">
              <AlertTriangle className="w-5 h-5" />
              确认升级告警
            </DialogTitle>
            <DialogDescription>
              升级后将立即发送通知到所有已配置的渠道
            </DialogDescription>
          </DialogHeader>

          {selectedAlert && (
            <div className="space-y-4 py-4">
              {/* Current Level */}
              <div className="p-3 bg-muted/50 rounded-lg">
                <p className="text-xs text-muted-foreground mb-2">当前级别</p>
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "px-3 py-1 rounded text-sm font-semibold",
                    selectedAlert.level === 'P0' ? 'bg-#FF3B30 text-white' :
                    selectedAlert.level === 'P1' ? 'bg-amber-500 text-white' :
                    'bg-blue-500 text-white'
                  )}>
                    {selectedAlert.level}
                  </span>
                  <span className="text-xs text-muted-foreground">{selectedAlert.content}</span>
                </div>
              </div>

              {/* Upgrade Direction */}
              <div className="flex items-center justify-center">
                <div className="h-px flex-1 bg-border"></div>
                <ArrowDown className="w-5 h-5 text-amber-600 mx-2" />
                <div className="h-px flex-1 bg-border"></div>
              </div>

              {/* New Level */}
              <div className="p-3 bg-#FF3B30/10 border border-#FF3B30/20 rounded-lg">
                <p className="text-xs text-muted-foreground mb-2">升级后级别</p>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded text-sm font-semibold bg-#FF3B30 text-white">
                    {selectedAlert.level === 'P1' ? 'P0' : selectedAlert.level === 'P2' ? 'P1' : selectedAlert.level}
                  </span>
                  <span className="text-xs text-red-600 font-medium">更高优先级</span>
                </div>
              </div>

              {/* Notification Channels */}
              <div className="p-3 bg-muted/50 rounded-lg">
                <p className="text-xs text-muted-foreground mb-2">将发送通知到</p>
                <div className="flex flex-wrap gap-2">
                  {selectedAlert.level === 'P1' && (
                    <>
                      <span className="px-2 py-1 rounded text-xs bg-#FF3B30/10 text-red-600 font-medium flex items-center gap-1">
                        <Phone className="w-3 h-3" /> 电话通知
                      </span>
                      <span className="px-2 py-1 rounded text-xs bg-#FF3B30/10 text-red-600 font-medium flex items-center gap-1">
                        <MessageSquare className="w-3 h-3" /> 短信通知
                      </span>
                    </>
                  )}
                  {selectedAlert.level === 'P2' && (
                    <span className="px-2 py-1 rounded text-xs bg-amber-500/10 text-amber-600 font-medium flex items-center gap-1">
                      <Mail className="w-3 h-3" /> 邮件通知
                    </span>
                  )}
                </div>
              </div>

              {/* Warning */}
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <p className="text-xs text-amber-600 font-medium">
                  此操作将立即发送通知，确保确实需要升级此告警
                </p>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUpgradeDialog(false)}>取消</Button>
            <Button 
              onClick={confirmUpgrade} 
              disabled={upgrading}
              className="bg-amber-600 hover:bg-amber-700"
            >
              {upgrading ? (
                <>
                  <Spinner className="w-4 h-4 mr-2" />
                  升级中...
                </>
              ) : (
                <>
                  <ArrowUpCircle className="w-4 h-4 mr-2" />
                  确认升级
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
