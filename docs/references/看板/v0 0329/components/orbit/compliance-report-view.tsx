'use client'

import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { LineChart, Line, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import {
  FileText,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Calendar,
  Download,
  Upload,
  Eye,
  Edit,
  Send,
  FolderOpen,
  Shield,
  Users,
  Server,
  Briefcase,
  Wallet,
  Building,
  Award,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronRight,
  FileCheck,
  FileClock,
  FileWarning,
  FileUp,
  Loader2,
  TrendingUp,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { useToast } from "@/hooks/use-toast"
import { Progress } from "@/components/ui/progress"

// KPI Data
const complianceKPIs = {
  score: { value: 95, max: 100 },
  status: 'completed',
  nextReport: '2026-04-15',
  pendingTasks: 2,
}

// Compliance overview
const complianceChecks = [
  { id: 1, name: '交易员资质认证', status: 'completed', detail: '有效期：2026-12-31' },
  { id: 2, name: '系统压力测试报告', status: 'completed', detail: '最后测试：2026-03-01' },
  { id: 3, name: '风控制度文档', status: 'completed', detail: '版本：v2.5' },
  { id: 4, name: '投资者适当性管理', status: 'completed', detail: '覆盖率：100%' },
  { id: 5, name: '信息披露完整', status: 'completed', detail: '及时率：98%' },
  { id: 6, name: '季度自查报告', status: 'pending', detail: '截止日期：2026-03-31' },
  { id: 7, name: '年度审计报告', status: 'pending', detail: '截止日期：2026-06-30' },
]

const complianceRisks = [
  { id: 1, level: 'warning', content: '季度自查报告即将到期（还剩 10 天）' },
  { id: 2, level: 'info', content: '年度审计需提前准备材料' },
]

// Filing records
const filingRecords = [
  { id: 1, type: '程序化交易报备', date: '2026-03-15', agency: '中期协', status: 'completed', owner: '张三', nextDate: '2026-06-15' },
  { id: 2, type: '产品备案', date: '2026-02-01', agency: '基金业协会', status: 'completed', owner: '李四', nextDate: '2027-02-01' },
  { id: 3, type: '月度运行报告', date: '2026-03-01', agency: '证监会', status: 'completed', owner: '王五', nextDate: '2026-04-01' },
  { id: 4, type: '季度自查报告', date: '-', agency: '中期协', status: 'pending', owner: '张三', nextDate: '2026-03-31' },
  { id: 5, type: '年度审计报告', date: '-', agency: '会计师事务所', status: 'pending', owner: '李四', nextDate: '2026-06-30' },
]

// Compliance checklist categories
const checklistCategories = [
  {
    id: 'org',
    name: '组织管理',
    icon: Building,
    items: [
      { name: '公司治理结构完善', checked: true },
      { name: '内部控制制度健全', checked: true },
      { name: '风险管理组织架构明确', checked: true },
      { name: '岗位职责清晰', checked: true },
    ],
  },
  {
    id: 'hr',
    name: '人员管理',
    icon: Users,
    items: [
      { name: '交易员持证上岗', checked: true },
      { name: '风控员资质合格', checked: true },
      { name: '定期培训记录完整', checked: true },
      { name: '背景调查完成', checked: true },
    ],
  },
  {
    id: 'system',
    name: '系统管理',
    icon: Server,
    items: [
      { name: '交易系统稳定可靠', checked: true },
      { name: '风控系统独立有效', checked: true },
      { name: '数据备份完整', checked: true },
      { name: '灾备方案完善', checked: true },
    ],
  },
  {
    id: 'trading',
    name: '交易管理',
    icon: Briefcase,
    items: [
      { name: '交易指令规范', checked: true },
      { name: '异常交易监控', checked: true },
      { name: '交易记录完整', checked: true },
      { name: '禁止行为管控', checked: true },
    ],
  },
  {
    id: 'fund',
    name: '资金管理',
    icon: Wallet,
    items: [
      { name: '资金托管规范', checked: true },
      { name: '资金划转审批', checked: true },
      { name: '资金对账及时', checked: true },
      { name: '资金使用合规', checked: true },
    ],
  },
]

// Document categories
const documentCategories = [
  {
    id: 'policy',
    name: '制度文档',
    icon: FileText,
    documents: [
      { name: '风控制度手册 v2.5.pdf', size: '15MB' },
      { name: '交易管理制度 v1.8.pdf', size: '8MB' },
      { name: '合规管理办法 v2.0.pdf', size: '12MB' },
      { name: '应急预案 v1.5.pdf', size: '5MB' },
    ],
  },
  {
    id: 'template',
    name: '报备模板',
    icon: FolderOpen,
    documents: [
      { name: '程序化交易报备模板.docx', size: '2MB' },
      { name: '产品备案模板.docx', size: '3MB' },
      { name: '月度运行报告模板.xlsx', size: '1MB' },
      { name: '季度自查报告模板.docx', size: '2MB' },
    ],
  },
  {
    id: 'audit',
    name: '审计报告',
    icon: Award,
    documents: [
      { name: '2025年度审计报告.pdf', size: '25MB' },
      { name: '2025年Q4专项审计报告.pdf', size: '18MB' },
      { name: '系统压力测试报告.pdf', size: '10MB' },
    ],
  },
]

// Compliance score trend data
const complianceScoreTrend = [
  { date: '1月', score: 85 },
  { date: '2月', score: 87 },
  { date: '3月', score: 90 },
  { date: '4月', score: 92 },
  { date: '5月', score: 94 },
  { date: '6月', score: 95 },
]

// Filing deadline calendar for next 90 days
const filingCalendar = [
  { date: '03-31', type: '季度自查报告', status: 'pending', remaining: 10 },
  { date: '04-01', type: '月度运行报告', status: 'planned', remaining: 15 },
  { date: '04-15', type: '交易员证书年审', status: 'planned', remaining: 29 },
  { date: '05-15', type: '程序化交易报备', status: 'planned', remaining: 59 },
  { date: '06-30', type: '年度审计报告', status: 'pending', remaining: 105 },
]

// Section Header Component
function SectionHeader({ icon: Icon, title, description }: { icon: typeof FileText; title: string; description?: string }) {
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
  icon: typeof FileText
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

export function ComplianceReportView() {
  const { toast } = useToast()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [expandedCategories, setExpandedCategories] = useState<string[]>(['org', 'policy'])
  
  // Upload dialog state
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  
  // Submit dialog state
  const [showSubmitDialog, setShowSubmitDialog] = useState(false)
  const [selectedFiling, setSelectedFiling] = useState<typeof filingRecords[0] | null>(null)

  const toggleCategory = (id: string) => {
    setExpandedCategories(prev =>
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    )
  }

  // File upload handlers
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Check file type
      const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
      if (!allowedTypes.includes(file.type)) {
        toast({ title: "文件类型错误", description: "仅支持 PDF、DOCX、XLSX 格式", variant: "destructive" })
        return
      }
      // Check file size (50MB)
      if (file.size > 50 * 1024 * 1024) {
        toast({ title: "文件过大", description: "文件大小不能超过 50MB", variant: "destructive" })
        return
      }
      setSelectedFile(file)
      setShowUploadDialog(true)
    }
  }

  const handleUpload = () => {
    if (!selectedFile) return
    
    setIsUploading(true)
    setUploadProgress(0)
    
    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsUploading(false)
          setShowUploadDialog(false)
          setSelectedFile(null)
          toast({ title: "上传成功", description: `${selectedFile.name} 已成功上传` })
          return 100
        }
        return prev + 10
      })
    }, 150)
  }

  const triggerFileSelect = () => {
    fileInputRef.current?.click()
  }

  // Submit filing handlers
  const handleSubmitFiling = (filing: typeof filingRecords[0]) => {
    setSelectedFiling(filing)
    setShowSubmitDialog(true)
  }

  const confirmSubmit = () => {
    if (selectedFiling) {
      toast({ title: "提交成功", description: `${selectedFiling.type} 已成功提交至 ${selectedFiling.agency}` })
      setShowSubmitDialog(false)
      setSelectedFiling(null)
    }
  }

  return (
    <div className="space-y-4 p-1">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-foreground">合规报表</h1>
          <p className="text-xs text-muted-foreground">管理监管报备、合规检查和文档下载</p>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept=".pdf,.doc,.docx,.xls,.xlsx"
            className="hidden"
          />
          <Button variant="outline" size="sm" className="h-7 text-xs" onClick={triggerFileSelect}>
            <FileUp className="w-3 h-3 mr-1" />
            上传文档
          </Button>
          <Button variant="outline" size="sm" className="h-7 text-xs">
            <Download className="w-3 h-3 mr-1" />
            导出报表
          </Button>
        </div>
      </div>

      {/* Row 1: KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KPICard icon={Award} label="合规评分" value={`${complianceKPIs.score.value}`} subValue="/100" color="green" />
        <KPICard icon={FileCheck} label="报备状态" value="已完成" color="green" />
        <KPICard icon={Calendar} label="下次报备" value={complianceKPIs.nextReport} />
        <KPICard icon={FileClock} label="待办事项" value={complianceKPIs.pendingTasks} subValue="项" color="yellow" />
      </div>

      {/* Row 2: Compliance Overview */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card-surface p-4"
      >
        <SectionHeader icon={Shield} title="合规状态概览" description="整体合规检查状态" />
        <div className="space-y-4">
          {/* Overall status */}
          <div className="flex items-center gap-2 p-3 rounded-lg bg-#3FB950/10 border border-#3FB950/20">
            <CheckCircle2 className="w-5 h-5 text-#3FB950" />
            <span className="text-sm font-semibold text-emerald-600">整体合规状态：正常</span>
          </div>

          {/* Check items */}
          <div>
            <p className="text-[11px] text-muted-foreground mb-2">合规检查项：</p>
            <div className="space-y-1.5">
              {complianceChecks.map((check) => (
                <div key={check.id} className="flex items-center gap-2 text-[11px]">
                  {check.status === 'completed' ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950 shrink-0" />
                  ) : (
                    <XCircle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                  )}
                  <span className="text-foreground whitespace-nowrap">{check.name}</span>
                  <span className="text-muted-foreground whitespace-nowrap">（{check.detail}）</span>
                  {check.status === 'pending' && (
                    <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-500 text-[10px] font-medium whitespace-nowrap">待完成</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Risk points */}
          <div>
            <p className="text-[11px] text-muted-foreground mb-2">合规风险点：</p>
            <div className="space-y-1.5">
              {complianceRisks.map((risk) => (
                <div key={risk.id} className="flex items-center gap-2 text-[11px]">
                  {risk.level === 'warning' ? (
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                  ) : (
                    <Info className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                  )}
                  <span className={cn(
                    "whitespace-nowrap",
                    risk.level === 'warning' ? 'text-amber-600' : 'text-blue-600'
                  )}>
                    {risk.content}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Row 2.5: Compliance Score Trend Chart */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.12 }}
        className="card-surface p-4"
      >
        <SectionHeader icon={TrendingUp} title="合规评分趋势" description="过去 6 个月的合规评分演进" />
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={complianceScoreTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
              <XAxis dataKey="date" tick={{ fontSize: 9 }} stroke="hsl(var(--muted-foreground))" />
              <YAxis domain={[80, 100]} tick={{ fontSize: 9 }} stroke="hsl(var(--muted-foreground))" />
              <Tooltip 
                contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '11px' }}
                formatter={(value) => [`${value}/100`, '评分']}
              />
              <Line 
                type="monotone" 
                dataKey="score" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ fill: '#3b82f6', r: 4 }}
                activeDot={{ r: 6 }}
                name="合规评分"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Row 2.7: Filing Deadline Calendar */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.14 }}
        className="card-surface p-4"
      >
        <SectionHeader icon={Calendar} title="报备截止日期" description="未来 3 个月的关键报备日期" />
        <div className="space-y-2">
          {filingCalendar.map((filing, idx) => (
            <div 
              key={idx} 
              className={cn(
                "flex items-center justify-between p-2.5 rounded-lg border transition-colors",
                filing.status === 'pending' ? 'bg-amber-500/5 border-amber-500/20' : 'bg-muted/30 border-border/50'
              )}
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center text-xs font-bold text-primary">
                  {filing.remaining}
                </div>
                <div>
                  <p className="text-xs font-medium text-foreground">{filing.type}</p>
                  <p className="text-[10px] text-muted-foreground">{filing.date}</p>
                </div>
              </div>
              <span className={cn(
                "px-2 py-0.5 rounded text-[10px] font-medium",
                filing.status === 'pending' ? 'bg-amber-500/10 text-amber-600' : 'bg-#3FB950/10 text-emerald-600'
              )}>
                {filing.status === 'pending' ? '待完成' : '已规划'}
              </span>
            </div>
          ))}
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="card-surface p-4"
      >
        <SectionHeader icon={FileText} title="监管报备记录" description="各类监管报备状态跟踪" />
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">报备类型</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">报备日期</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">监管机构</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">状态</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">负责人</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">下次报备</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">操作</th>
              </tr>
            </thead>
            <tbody>
              {filingRecords.map((record, index) => (
                <tr key={record.id} className={cn("border-b border-border/50", index % 2 === 0 && "bg-muted/20")}>
                  <td className="py-2.5 px-2 text-foreground whitespace-nowrap">{record.type}</td>
                  <td className="py-2.5 px-2 font-mono text-foreground whitespace-nowrap">{record.date}</td>
                  <td className="py-2.5 px-2 text-foreground whitespace-nowrap">{record.agency}</td>
                  <td className="py-2.5 px-2 text-center">
                    <span className={cn(
                      "px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap",
                      record.status === 'completed' ? 'bg-#3FB950/10 text-#3FB950' : 'bg-amber-500/10 text-amber-500'
                    )}>
                      {record.status === 'completed' ? '已完成' : '待开始'}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-foreground whitespace-nowrap">{record.owner}</td>
                  <td className="py-2.5 px-2 font-mono text-foreground whitespace-nowrap">{record.nextDate}</td>
                  <td className="py-2.5 px-2 text-center">
                    <div className="flex items-center justify-center gap-1">
                      {record.status === 'completed' ? (
                        <>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]">
                            <Eye className="w-3 h-3 mr-1" />
                            查看
                          </Button>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]">
                            <Download className="w-3 h-3 mr-1" />
                            下载
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]">
                            <Edit className="w-3 h-3 mr-1" />
                            编辑
                          </Button>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]" onClick={() => handleSubmitFiling(record)}>
                            <Send className="w-3 h-3 mr-1" />
                            提交
                          </Button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Row 4: Compliance Checklist */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="card-surface p-4"
      >
        <SectionHeader icon={FileCheck} title="合规检查清单" description="各项合规检查完成状态" />
        <div className="space-y-2">
          {checklistCategories.map((category) => {
            const Icon = category.icon
            const isExpanded = expandedCategories.includes(category.id)
            const allChecked = category.items.every(item => item.checked)

            return (
              <div key={category.id} className="border border-border/50 rounded-lg overflow-hidden">
                <button
                  onClick={() => toggleCategory(category.id)}
                  className="w-full flex items-center justify-between p-3 bg-muted/20 hover:bg-muted/40 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 text-primary" />
                    <span className="text-[12px] font-semibold text-foreground">{category.name}</span>
                    {allChecked && <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950" />}
                  </div>
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  )}
                </button>
                {isExpanded && (
                  <div className="p-3 space-y-1.5">
                    {category.items.map((item, index) => (
                      <div key={index} className="flex items-center gap-2 text-[11px]">
                        {item.checked ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-#3FB950 shrink-0" />
                        ) : (
                          <XCircle className="w-3.5 h-3.5 text-#FF3B30 shrink-0" />
                        )}
                        <span className="text-foreground whitespace-nowrap">{item.name}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </motion.div>

      {/* Row 5: Document Download Center */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="card-surface p-4"
      >
        <SectionHeader icon={Download} title="文档下载中心" description="制度文档、报备模板和审计报告" />
        <div className="space-y-2">
          {documentCategories.map((category) => {
            const Icon = category.icon
            const isExpanded = expandedCategories.includes(category.id)

            return (
              <div key={category.id} className="border border-border/50 rounded-lg overflow-hidden">
                <button
                  onClick={() => toggleCategory(category.id)}
                  className="w-full flex items-center justify-between p-3 bg-muted/20 hover:bg-muted/40 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 text-primary" />
                    <span className="text-[12px] font-semibold text-foreground">{category.name}</span>
                    <span className="text-[10px] text-muted-foreground">({category.documents.length} 个文件)</span>
                  </div>
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  )}
                </button>
                {isExpanded && (
                  <div className="p-3 space-y-2">
                    {category.documents.map((doc, index) => (
                      <div key={index} className="flex items-center justify-between p-2 rounded bg-muted/30 hover:bg-muted/50 transition-colors">
                        <div className="flex items-center gap-2">
                          <FileText className="w-3.5 h-3.5 text-muted-foreground" />
                          <span className="text-[11px] text-foreground whitespace-nowrap">{doc.name}</span>
                          <span className="text-[10px] text-muted-foreground whitespace-nowrap">({doc.size})</span>
                        </div>
                        <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]">
                          <Download className="w-3 h-3 mr-1" />
                          下载
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </motion.div>

      {/* Row 6: Compliance Alerts */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card-surface p-4"
      >
        <SectionHeader icon={AlertTriangle} title="合规告警" description="待处理的合规提醒和告警" />
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">告警时间</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">告警类型</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">告警内容</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">截止日期</th>
                <th className="text-left py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">剩余天数</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">状态</th>
                <th className="text-center py-2 px-2 text-muted-foreground font-medium whitespace-nowrap">操作</th>
              </tr>
            </thead>
            <tbody>
              {complianceAlerts.map((alert, index) => (
                <tr key={alert.id} className={cn("border-b border-border/50", index % 2 === 0 && "bg-muted/20")}>
                  <td className="py-2.5 px-2 font-mono text-foreground whitespace-nowrap">{alert.time}</td>
                  <td className="py-2.5 px-2 text-foreground whitespace-nowrap">{alert.type}</td>
                  <td className="py-2.5 px-2 text-foreground whitespace-nowrap">{alert.content}</td>
                  <td className="py-2.5 px-2 font-mono text-foreground whitespace-nowrap">{alert.deadline}</td>
                  <td className="py-2.5 px-2 font-mono text-amber-500 whitespace-nowrap">{alert.remaining}</td>
                  <td className="py-2.5 px-2 text-center">
                    <span className={cn(
                      "px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap",
                      alert.status === 'pending' ? 'bg-#FF3B30/10 text-#FF3B30' : 'bg-blue-500/10 text-blue-500'
                    )}>
                      {alert.status === 'pending' ? '未处理' : '已计划'}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    <div className="flex items-center justify-center gap-1">
                      {alert.status === 'pending' ? (
                        <>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]">处理</Button>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]">延期</Button>
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

      {/* Upload Dialog */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileUp className="w-5 h-5 text-primary" />
              上传文档
            </DialogTitle>
            <DialogDescription>
              支持 PDF、DOCX、XLSX 格式，文件大小不超过 50MB
            </DialogDescription>
          </DialogHeader>
          
          {selectedFile && (
            <div className="py-4 space-y-4">
              <div className="p-4 bg-muted/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <FileText className="w-8 h-8 text-primary" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{selectedFile.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  {!isUploading && (
                    <Button variant="ghost" size="sm" onClick={() => setSelectedFile(null)}>
                      <XCircle className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>
              
              {isUploading && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">上传进度</span>
                    <span className="font-mono">{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} className="h-2" />
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowUploadDialog(false)
              setSelectedFile(null)
            }} disabled={isUploading}>
              取消
            </Button>
            <Button onClick={handleUpload} disabled={isUploading || !selectedFile}>
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                  上传中...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-1" />
                  确认上传
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Submit Filing Dialog */}
      <Dialog open={showSubmitDialog} onOpenChange={setShowSubmitDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Send className="w-5 h-5 text-primary" />
              确认提交报备
            </DialogTitle>
            <DialogDescription>
              请确认报备信息后提交
            </DialogDescription>
          </DialogHeader>
          
          {selectedFiling && (
            <div className="py-4 space-y-4">
              <div className="p-4 bg-muted/50 rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">报备类型</span>
                  <span className="text-sm font-medium">{selectedFiling.type}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">监管机构</span>
                  <span className="text-sm font-medium">{selectedFiling.agency}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">负责人</span>
                  <span className="text-sm font-medium">{selectedFiling.owner}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">截止日期</span>
                  <span className="text-sm font-mono text-amber-500">{selectedFiling.nextDate}</span>
                </div>
              </div>
              
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <p className="text-xs text-amber-600 flex items-center gap-2">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  提交后将无法修改，请确认信息无误
                </p>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              if (!isUploading) setShowUploadDialog(false)
            }} disabled={isUploading}>
              取消
            </Button>
            <Button onClick={handleUpload} disabled={isUploading} className="flex items-center gap-2">
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  上传中...
                </>
              ) : (
                <>
                  <FileUp className="w-4 h-4" />
                  确认上传
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
