'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Bell,
  RefreshCw,
  Plus,
  Trash2,
  Pencil,
  ChevronDown,
  ChevronRight,
  Mail,
  MessageSquare,
  Clock,
  Zap,
  Calendar,
  TestTube2,
  Settings2,
} from 'lucide-react'
import {
  notificationApi,
  type ServiceNotifConfig,
  type NotificationRule,
} from '@/lib/api/settings'

type RuleType  = NotificationRule['rule_type']
type RuleColor = NotificationRule['color']

// ── 颜色配置（飞书 template 对齐）────────────────────────
const COLOR_CFG: Record<string, { label: string; hex: string }> = {
  red:       { label: '报警 P0', hex: '#c0392b' },
  orange:    { label: '报警 P1', hex: '#e67e22' },
  yellow:    { label: '报警 P2', hex: '#f39c12' },
  grey:      { label: '交易',   hex: '#7f8c8d' },
  blue:      { label: '资讯',   hex: '#2980b9' },
  wathet:    { label: '新闻',   hex: '#5dade2' },
  turquoise: { label: '通知',   hex: '#1abc9c' },
}

const RULE_TYPE_CFG: Record<string, { icon: string; label: string; colorKey: string }> = {
  alarm_p0: { icon: '🚨', label: '报警 P0', colorKey: 'red' },
  alarm_p1: { icon: '⚠️', label: '报警 P1', colorKey: 'orange' },
  alarm_p2: { icon: '🔔', label: '报警 P2', colorKey: 'yellow' },
  trade:    { icon: '📊', label: '交易回报', colorKey: 'grey' },
  info:     { icon: '📈', label: '资讯',    colorKey: 'blue' },
  news:     { icon: '📰', label: '新闻',    colorKey: 'wathet' },
  notify:   { icon: '📣', label: '通知',    colorKey: 'turquoise' },
}

const TRIGGER_TYPE_CFG: Record<string, { icon: React.ReactNode; label: string; desc: string }> = {
  realtime:      { icon: <Zap className="w-3 h-3" />,      label: '实时',   desc: '事件触发即时推送' },
  scheduled:     { icon: <Clock className="w-3 h-3" />,    label: '定时',   desc: '按指定时间点推送' },
  daily_summary: { icon: <Calendar className="w-3 h-3" />, label: '日报',   desc: '每日定时汇总推送' },
}

const SERVICE_ORDER = ['sim-trading', 'data', 'decision', 'backtest']
const SERVICE_LABELS: Record<string, string> = {
  'sim-trading': '模拟交易',
  'data':        '数据服务',
  'decision':    '决策引擎',
  'backtest':    '回测系统',
}

// ── RuleDialog（新建 / 编辑）────────────────────────────
type TriggerType = 'realtime' | 'scheduled' | 'daily_summary'

interface RuleForm {
  name: string
  rule_type: RuleType
  color: RuleColor
  content_template: string
  enabled: boolean
  feishu_enabled: boolean
  smtp_enabled: boolean
  trigger_type: TriggerType
  daily_limit: number
  time_window: string
  schedule_times: string
}

const EMPTY_RULE: RuleForm = {
  name: '',
  rule_type: 'notify' as RuleType,
  color: 'turquoise' as RuleColor,
  content_template: '',
  enabled: true,
  feishu_enabled: true,
  smtp_enabled: true,
  trigger_type: 'realtime',
  daily_limit: 0,
  time_window: '',
  schedule_times: '',
}

interface ConfigForm {
  feishu_webhook: string
  feishu_enabled: boolean
  smtp_host: string
  smtp_port: number
  smtp_username: string
  smtp_password: string
  smtp_to_addrs: string
  smtp_enabled: boolean
}

function toConfigForm(config: ServiceNotifConfig): ConfigForm {
  return {
    feishu_webhook: config.feishu_webhook,
    feishu_enabled: config.feishu_enabled,
    smtp_host: config.smtp_host,
    smtp_port: config.smtp_port,
    smtp_username: config.smtp_username,
    smtp_password: '',
    smtp_to_addrs: config.smtp_to_addrs,
    smtp_enabled: config.smtp_enabled,
  }
}

interface ConfigDialogProps {
  open: boolean
  config: ServiceNotifConfig
  onOpenChange: (v: boolean) => void
  onSave: (form: ConfigForm) => Promise<void>
  onTestFeishu: () => Promise<void>
  onTestSmtp: () => Promise<void>
}

function ConfigDialog({ open, config, onOpenChange, onSave, onTestFeishu, onTestSmtp }: ConfigDialogProps) {
  const [form, setForm] = useState<ConfigForm>(() => toConfigForm(config))
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState<'feishu' | 'smtp' | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setForm(toConfigForm(config))
    setError('')
  }, [config, open])

  const handleSave = async () => {
    setSaving(true)
    setError('')
    try {
      await onSave(form)
      onOpenChange(false)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const runTest = async (kind: 'feishu' | 'smtp') => {
    setTesting(kind)
    setError('')
    try {
      if (kind === 'feishu') await onTestFeishu()
      else await onTestSmtp()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setTesting(null)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings2 className="w-4 h-4 text-orange-500" />
            渠道配置 · {config.display_name}
          </DialogTitle>
          <DialogDescription>配置该服务的飞书 Webhook 与 SMTP，并可直接做服务级链路测试。</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-1">
          <div className="rounded-md border border-input bg-muted/10 p-3 space-y-3">
            <div className="flex items-center justify-between">
              <Label className="flex items-center gap-2"><MessageSquare className="w-4 h-4 text-[#1abc9c]" />飞书 Webhook</Label>
              <Switch checked={form.feishu_enabled} onCheckedChange={v => setForm(f => ({ ...f, feishu_enabled: v }))} />
            </div>
            <Input
              placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..."
              value={form.feishu_webhook}
              onChange={e => setForm(f => ({ ...f, feishu_webhook: e.target.value }))}
            />
            <div className="flex justify-end">
              <Button type="button" variant="outline" size="sm" onClick={() => runTest('feishu')} disabled={testing !== null}>
                {testing === 'feishu' ? '测试中...' : '测试飞书'}
              </Button>
            </div>
          </div>

          <div className="rounded-md border border-input bg-muted/10 p-3 space-y-3">
            <div className="flex items-center justify-between">
              <Label className="flex items-center gap-2"><Mail className="w-4 h-4 text-blue-400" />SMTP 邮件</Label>
              <Switch checked={form.smtp_enabled} onCheckedChange={v => setForm(f => ({ ...f, smtp_enabled: v }))} />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Input placeholder="smtp.example.com" value={form.smtp_host} onChange={e => setForm(f => ({ ...f, smtp_host: e.target.value }))} />
              <Input type="number" min={1} value={form.smtp_port} onChange={e => setForm(f => ({ ...f, smtp_port: parseInt(e.target.value) || 465 }))} />
            </div>
            <Input placeholder="SMTP 用户名 / 发件邮箱" value={form.smtp_username} onChange={e => setForm(f => ({ ...f, smtp_username: e.target.value }))} />
            <Input type="password" placeholder={config.smtp_password_set ? '留空表示保留现有密码' : 'SMTP 密码'} value={form.smtp_password} onChange={e => setForm(f => ({ ...f, smtp_password: e.target.value }))} />
            <Input placeholder="收件人，逗号分隔" value={form.smtp_to_addrs} onChange={e => setForm(f => ({ ...f, smtp_to_addrs: e.target.value }))} />
            <div className="flex justify-end">
              <Button type="button" variant="outline" size="sm" onClick={() => runTest('smtp')} disabled={testing !== null}>
                {testing === 'smtp' ? '测试中...' : '测试邮件'}
              </Button>
            </div>
          </div>

          {error && <p className="text-sm text-destructive rounded-md bg-destructive/10 px-3 py-2">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
          <Button onClick={handleSave} disabled={saving}>{saving ? '保存中...' : '保存配置'}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface RuleDialogProps {
  open: boolean
  service: string
  editing: NotificationRule | null
  onOpenChange: (v: boolean) => void
  onSave: (form: RuleForm) => Promise<void>
}

function RuleDialog({ open, service, editing, onOpenChange, onSave }: RuleDialogProps) {
  const [form, setForm] = useState<RuleForm>(EMPTY_RULE)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (editing) {
      setForm({
        name: editing.name, rule_type: editing.rule_type, color: editing.color,
        content_template: editing.content_template, enabled: editing.enabled,
        feishu_enabled: editing.feishu_enabled, smtp_enabled: editing.smtp_enabled,
        trigger_type: editing.trigger_type ?? 'realtime',
        daily_limit: editing.daily_limit ?? 0,
        time_window: editing.time_window ?? '',
        schedule_times: editing.schedule_times ?? '',
      })
    } else {
      setForm(EMPTY_RULE)
    }
    setError('')
  }, [editing, open])

  // 选择 rule_type 时自动推荐 color
  const handleTypeChange = (t: string) => {
    const suggested = (RULE_TYPE_CFG[t]?.colorKey ?? 'turquoise') as RuleColor
    setForm(f => ({ ...f, rule_type: t as RuleType, color: suggested }))
  }

  const handleSave = async () => {
    if (!form.name.trim()) { setError('请输入规则名称'); return }
    setSaving(true); setError('')
    try { await onSave(form); onOpenChange(false) }
    catch (e) { setError((e as Error).message) }
    finally { setSaving(false) }
  }

  const dotColor = COLOR_CFG[form.color]?.hex ?? '#1abc9c'

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-orange-500" />
            {editing ? '编辑通知规则' : `新增通知规则 · ${SERVICE_LABELS[service] ?? service}`}
          </DialogTitle>
          <DialogDescription>配置通知名称、类型和 card 颜色</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-1">
          {/* 规则名称 */}
          <div className="space-y-1.5">
            <Label>规则名称</Label>
            <Input
              placeholder="如：CTP 断线告警 / 日报汇总"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className="bg-background"
            />
          </div>

          {/* 通知类型 */}
          <div className="space-y-1.5">
            <Label>通知类型</Label>
            <select
              value={form.rule_type}
              onChange={e => handleTypeChange(e.target.value)}
              className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm text-foreground"
            >
              {Object.entries(RULE_TYPE_CFG).map(([k, v]) => (
                <option key={k} value={k}>{v.label}</option>
              ))}
            </select>
          </div>

          {/* Card 颜色 */}
          <div className="space-y-1.5">
            <Label>飞书 Card 颜色</Label>
            <div className="grid grid-cols-7 gap-1.5">
              {Object.entries(COLOR_CFG).map(([k, v]) => (
                <TooltipProvider key={k} delayDuration={200}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={() => setForm(f => ({ ...f, color: k as RuleColor }))}
                        className={`h-8 rounded-md border-2 transition-all ${form.color === k ? 'border-white scale-110 shadow-lg' : 'border-transparent opacity-70 hover:opacity-100'}`}
                        style={{ backgroundColor: v.hex }}
                        aria-label={v.label}
                      />
                    </TooltipTrigger>
                    <TooltipContent side="top" className="text-xs">{v.label}</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              ))}
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className="w-3 h-3 rounded-full border border-border" style={{ backgroundColor: dotColor }} />
              <span className="text-xs text-muted-foreground">
                {COLOR_CFG[form.color]?.label}
                <code className="ml-1 text-[10px] bg-muted px-1 py-0.5 rounded">{form.color}</code>
              </span>
            </div>
          </div>

          {/* 内容模板 */}
          <div className="space-y-1.5">
            <Label>
              内容模板
              <span className="ml-1 text-[10px] text-muted-foreground">（可选，支持 {`{变量}`} 占位符）</span>
            </Label>
            <textarea
              placeholder="如：CTP 断线: {reason}"
              value={form.content_template}
              onChange={e => setForm(f => ({ ...f, content_template: e.target.value }))}
              rows={2}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground resize-none focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          {/* 推送频率 / 调度 */}
          <div className="space-y-2">
            <Label>推送方式</Label>
            <div className="grid grid-cols-3 gap-1.5">
              {Object.entries(TRIGGER_TYPE_CFG).map(([k, v]) => (
                <button key={k} type="button"
                  onClick={() => setForm(f => ({ ...f, trigger_type: k as TriggerType }))}
                  className={`flex items-center gap-1.5 px-2.5 py-2 rounded-md border text-xs transition-all
                    ${form.trigger_type === k
                      ? 'border-primary bg-primary/10 text-primary font-medium'
                      : 'border-border bg-background text-muted-foreground hover:bg-muted/20'}`}
                >
                  {v.icon}{v.label}
                </button>
              ))}
            </div>
            <p className="text-[10px] text-muted-foreground">{TRIGGER_TYPE_CFG[form.trigger_type]?.desc}</p>

            {/* 条件字段 */}
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label className="text-xs">每日上限 <span className="text-muted-foreground">(0=不限)</span></Label>
                <Input type="number" min={0} value={form.daily_limit}
                  onChange={e => setForm(f => ({ ...f, daily_limit: parseInt(e.target.value) || 0 }))}
                  className="bg-background h-8 text-xs" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">推送时段</Label>
                <Input placeholder="09:00-15:15" value={form.time_window}
                  onChange={e => setForm(f => ({ ...f, time_window: e.target.value }))}
                  className="bg-background h-8 text-xs" />
              </div>
            </div>
            {(form.trigger_type === 'scheduled' || form.trigger_type === 'daily_summary') && (
              <div className="space-y-1">
                <Label className="text-xs">定时时间点 <span className="text-muted-foreground">(逗号分隔)</span></Label>
                <Input placeholder="09:30,12:00,15:30" value={form.schedule_times}
                  onChange={e => setForm(f => ({ ...f, schedule_times: e.target.value }))}
                  className="bg-background h-8 text-xs" />
              </div>
            )}
          </div>

          {/* 渠道与开关 */}
          <div className="rounded-md border border-input bg-muted/10 divide-y divide-border/50">
            <div className="flex items-center justify-between px-3 py-2">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-3.5 h-3.5 text-[#1abc9c]" />
                <span className="text-sm">飞书通知</span>
              </div>
              <Switch checked={form.feishu_enabled} onCheckedChange={v => setForm(f => ({ ...f, feishu_enabled: v }))} />
            </div>
            <div className="flex items-center justify-between px-3 py-2">
              <div className="flex items-center gap-2">
                <Mail className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-sm">邮件通知</span>
              </div>
              <Switch checked={form.smtp_enabled} onCheckedChange={v => setForm(f => ({ ...f, smtp_enabled: v }))} />
            </div>
            <div className="flex items-center justify-between px-3 py-2">
              <div className="flex items-center gap-2">
                <Bell className="w-3.5 h-3.5 text-orange-400" />
                <span className="text-sm">启用此规则</span>
              </div>
              <Switch checked={form.enabled} onCheckedChange={v => setForm(f => ({ ...f, enabled: v }))} />
            </div>
          </div>

          {error && <p className="text-sm text-destructive rounded-md bg-destructive/10 px-3 py-2">{error}</p>}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
          <Button onClick={handleSave} disabled={saving}>{saving ? '保存中...' : editing ? '保存修改' : '添加规则'}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── ServicePanel ──────────────────────────────────────────
interface ServicePanelProps {
  config: ServiceNotifConfig
  rules: NotificationRule[]
  onConfigUpdated: (config: ServiceNotifConfig) => void
  onRuleAdded: (rule: NotificationRule) => void
  onRuleUpdated: (rule: NotificationRule) => void
  onRuleDeleted: (id: number) => void
}

// ── RuleKpiCard（每条规则的 KPI 卡片）────────────────────
interface RuleKpiCardProps {
  rule: NotificationRule
  feishuReady: boolean
  smtpReady: boolean
  isSelected?: boolean
  onToggleSelect?: (rule: NotificationRule) => void
  onUpdated: (rule: NotificationRule) => void
  onDelete:  (rule: NotificationRule) => void
  onEdit:    (rule: NotificationRule) => void
  onTest:    (rule: NotificationRule) => Promise<void>
}

function RuleKpiCard({ rule, feishuReady, smtpReady, isSelected, onToggleSelect, onUpdated, onDelete, onEdit, onTest }: RuleKpiCardProps) {
  const [busy, setBusy] = useState<string | null>(null)
  const typeCfg = RULE_TYPE_CFG[rule.rule_type]
  const hex = COLOR_CFG[rule.color]?.hex ?? '#888'
  const feishuLive = rule.enabled && rule.feishu_enabled && feishuReady
  const smtpLive = rule.enabled && rule.smtp_enabled && smtpReady

  const patch = async (field: string, value: boolean, busyKey: string) => {
    if (busy) return
    setBusy(busyKey)
    const updated = { ...rule, [field]: value }
    onUpdated(updated)  // 乐观更新
    try {
      await notificationApi.updateRule(rule.id, {
        service: rule.service, name: rule.name, rule_type: rule.rule_type,
        color: rule.color, content_template: rule.content_template,
        enabled: updated.enabled, feishu_enabled: updated.feishu_enabled, smtp_enabled: updated.smtp_enabled,
        trigger_type: rule.trigger_type, daily_limit: rule.daily_limit,
        time_window: rule.time_window, schedule_times: rule.schedule_times,
      })
    } catch {
      onUpdated(rule)   // 失败回滚
    } finally {
      setBusy(null)
    }
  }

  const toggleEnabled = () => patch('enabled',       !rule.enabled,       'toggle')
  const toggleFeishu  = (e: React.MouseEvent) => { e.stopPropagation(); patch('feishu_enabled', !rule.feishu_enabled, 'feishu') }
  const toggleSmtp    = (e: React.MouseEvent) => { e.stopPropagation(); patch('smtp_enabled',   !rule.smtp_enabled,   'smtp') }

  return (
    <div
      className={`relative group rounded-xl border border-border overflow-hidden cursor-pointer transition-all duration-150
        ${rule.enabled ? 'bg-card hover:bg-muted/10 hover:border-border/80' : 'opacity-45 bg-muted/5 hover:opacity-70'}`}
      onClick={toggleEnabled}
      title={rule.enabled ? '点击关闭此通知' : '点击开启此通知'}
    >
      {/* 颜色条 + 复选框 */}
      <div className="absolute left-0 top-0 bottom-0 w-1 rounded-l-xl flex items-start" style={{ backgroundColor: hex }}>
        {onToggleSelect && (
          <div
            className="absolute -left-2 -top-2 w-5 h-5 rounded border-2 border-border bg-background flex items-center justify-center cursor-pointer hover:bg-muted transition-all"
            onClick={(e) => { e.stopPropagation(); onToggleSelect(rule) }}
            title="选择此规则用于批量操作"
          >
            {isSelected && (
              <span className="text-xs font-bold text-foreground">✓</span>
            )}
          </div>
        )}
      </div>

      {/* 操作按钮（hover 显示） */}
      <div
        className="absolute top-1.5 right-1.5 flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity z-10"
        onClick={e => e.stopPropagation()}
      >
        <Button variant="ghost" size="icon"
          className="h-5 w-5 rounded bg-background/80 hover:bg-muted"
          onClick={() => void onTest(rule)}
        ><TestTube2 className="w-2.5 h-2.5" /></Button>
        <Button variant="ghost" size="icon"
          className="h-5 w-5 rounded bg-background/80 hover:bg-muted"
          onClick={() => onEdit(rule)}
        ><Pencil className="w-2.5 h-2.5" /></Button>
        <Button variant="ghost" size="icon"
          className="h-5 w-5 rounded bg-background/80 hover:bg-destructive/10 text-destructive"
          onClick={() => onDelete(rule)}
        ><Trash2 className="w-2.5 h-2.5" /></Button>
      </div>

      <div className="pl-3 pr-2 pt-2.5 pb-2.5 space-y-2">
        {/* 标题行 */}
        <div className="flex items-start gap-1.5 min-w-0">
          <span className="text-base leading-none mt-0.5 shrink-0">{typeCfg?.icon ?? '📣'}</span>
          <div className="min-w-0 flex-1">
            <p className={`text-xs font-semibold leading-tight truncate ${rule.enabled ? 'text-foreground' : 'text-muted-foreground'}`}>
              {rule.name}
            </p>
            <p className="text-[10px] text-muted-foreground mt-0.5">{typeCfg?.label ?? rule.rule_type}</p>
          </div>
        </div>

        {/* 内容模板 */}
        {rule.content_template && (
          <p className="text-[10px] text-muted-foreground leading-snug line-clamp-2 bg-muted/20 rounded px-1.5 py-1 font-mono">
            {rule.content_template}
          </p>
        )}

        {/* 调度信息 */}
        <div className="flex flex-wrap items-center gap-1">
          {(() => {
            const tt = TRIGGER_TYPE_CFG[rule.trigger_type] ?? TRIGGER_TYPE_CFG.realtime
            return (
              <span className="inline-flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded-full border border-border bg-muted/20 text-muted-foreground">
                {tt.icon}{tt.label}
              </span>
            )
          })()}
          {rule.daily_limit > 0 && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full border border-border bg-muted/20 text-muted-foreground">
              {rule.daily_limit}次/天
            </span>
          )}
          {rule.time_window && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full border border-border bg-muted/20 text-muted-foreground">
              🕐 {rule.time_window}
            </span>
          )}
          {rule.schedule_times && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full border border-border bg-muted/20 text-muted-foreground">
              ⏰ {rule.schedule_times}
            </span>
          )}
        </div>

        {/* 渠道开关行 */}
        <div className="flex items-center gap-1.5 pt-0.5" onClick={e => e.stopPropagation()}>
          <TooltipProvider delayDuration={150}>
            <Tooltip>
              <TooltipTrigger asChild>
                <button type="button" onClick={toggleFeishu}
                  disabled={!rule.enabled || busy === 'feishu'}
                  className={`flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full border transition-all
                    ${feishuLive
                      ? 'border-[#1abc9c]/40 bg-[#1abc9c]/10 text-[#1abc9c] hover:bg-[#1abc9c]/20'
                      : 'border-border bg-muted/20 text-muted-foreground hover:bg-muted/40'}
                    disabled:cursor-not-allowed disabled:opacity-50`}
                >
                  <MessageSquare className="w-2.5 h-2.5" />飞书
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">
                {!rule.feishu_enabled
                  ? '飞书规则已关闭（点击开启）'
                  : !feishuReady
                    ? '飞书规则已开启，但服务端 Webhook 未配置'
                    : '飞书已开启（点击关闭）'}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider delayDuration={150}>
            <Tooltip>
              <TooltipTrigger asChild>
                <button type="button" onClick={toggleSmtp}
                  disabled={!rule.enabled || busy === 'smtp'}
                  className={`flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full border transition-all
                    ${smtpLive
                      ? 'border-blue-400/40 bg-blue-400/10 text-blue-400 hover:bg-blue-400/20'
                      : 'border-border bg-muted/20 text-muted-foreground hover:bg-muted/40'}
                    disabled:cursor-not-allowed disabled:opacity-50`}
                >
                  <Mail className="w-2.5 h-2.5" />邮件
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">
                {!rule.smtp_enabled
                  ? '邮件规则已关闭（点击开启）'
                  : !smtpReady
                    ? '邮件规则已开启，但服务端 SMTP 未配置'
                    : '邮件已开启（点击关闭）'}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <span className={`ml-auto text-[10px] font-medium ${rule.enabled ? 'text-green-400' : 'text-muted-foreground'}`}>
            {busy === 'toggle' ? '…' : rule.enabled ? '开启' : '关闭'}
          </span>
        </div>
      </div>
    </div>
  )
}

// ── ServicePanel ──────────────────────────────────────────
interface ServicePanelProps {
  config: ServiceNotifConfig
  rules: NotificationRule[]
  onRuleAdded:   (rule: NotificationRule) => void
  onRuleUpdated: (rule: NotificationRule) => void
  onRuleDeleted: (id: number) => void
}

function ServicePanel({ config, rules, onConfigUpdated, onRuleAdded, onRuleUpdated, onRuleDeleted }: ServicePanelProps) {
  const [expanded,    setExpanded]    = useState(true)
  const [ruleDialog,  setRuleDialog]  = useState(false)
  const [configDialog,setConfigDialog]= useState(false)
  const [editingRule, setEditingRule] = useState<NotificationRule | null>(null)
  const [deleteTarget,setDeleteTarget]= useState<NotificationRule | null>(null)
  const [selectedRuleIds, setSelectedRuleIds] = useState<Set<number>>(new Set())
  const [testingBatch, setTestingBatch] = useState(false)
  const [batchResults, setBatchResults] = useState<Record<number, { success: boolean; msg: string }> | null>(null)
  const [toast, setToast] = useState<{ type: 'ok' | 'err'; msg: string } | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  const showToast = (type: 'ok' | 'err', msg: string) => {
    clearTimeout(toastTimer.current)
    setToast({ type, msg })
    toastTimer.current = setTimeout(() => setToast(null), 2500)
  }

  const toggleRuleSelect = (rule: NotificationRule) => {
    setSelectedRuleIds(prev => {
      const next = new Set(prev)
      if (next.has(rule.id)) {
        next.delete(rule.id)
      } else {
        next.add(rule.id)
      }
      return next
    })
  }

  const handleBatchTest = async () => {
    if (selectedRuleIds.size === 0) {
      showToast('err', '请先选择要测试的规则')
      return
    }
    setTestingBatch(true)
    setBatchResults({})
    const results: Record<number, { success: boolean; msg: string }> = {}
    
    try {
      await Promise.all(
        Array.from(selectedRuleIds).map(async (ruleId) => {
          const rule = rules.find(r => r.id === ruleId)
          if (!rule) return
          try {
            const res = await notificationApi.testRule(ruleId)
            const parts: string[] = []
            if (res.results.feishu) parts.push(`飞书${res.results.feishu.success ? '✓' : '✗'}`)
            if (res.results.smtp) parts.push(`邮件${res.results.smtp.success ? '✓' : '✗'}`)
            results[ruleId] = {
              success: res.success,
              msg: parts.join(' ') || (res.success ? '成功' : '失败'),
            }
          } catch (e) {
            results[ruleId] = {
              success: false,
              msg: (e as Error).message || '测试失败',
            }
          }
        })
      )
    } finally {
      setTestingBatch(false)
      setBatchResults(results)
      const okCount = Object.values(results).filter(r => r.success).length
      const total = Object.keys(results).length
      showToast(okCount > 0 ? 'ok' : 'err', `批量测试完成: ${okCount}/${total} 成功`)
    }
  }

  const handleRuleSave = async (form: RuleForm) => {
    if (editingRule) {
      await notificationApi.updateRule(editingRule.id, { service: config.service, ...form })
      onRuleUpdated({ ...editingRule, ...form })
      showToast('ok', `「${form.name}」已更新`)
    } else {
      const res = await notificationApi.createRule({ service: config.service, ...form })
      onRuleAdded({ id: res.id, service: config.service, sort_order: 99, created_at: new Date().toISOString(), ...form })
      showToast('ok', `「${form.name}」已添加`)
    }
  }

  const handleDelete = async (rule: NotificationRule) => {
    await notificationApi.deleteRule(rule.id)
    onRuleDeleted(rule.id)
    setDeleteTarget(null)
    showToast('ok', `已删除「${rule.name}」`)
  }

  const handleConfigSave = async (form: ConfigForm) => {
    await notificationApi.updateConfig(config.service, form)
    onConfigUpdated({
      ...config,
      ...form,
      smtp_password_set: config.smtp_password_set || !!form.smtp_password,
      updated_at: new Date().toISOString(),
    })
    showToast('ok', `${config.display_name} 渠道配置已保存`)
  }

  const handleServiceFeishuTest = async () => {
    await notificationApi.testFeishu(config.service)
    showToast('ok', `${config.display_name} 飞书测试已发送`)
  }

  const handleServiceSmtpTest = async () => {
    await notificationApi.testSmtp(config.service)
    showToast('ok', `${config.display_name} 邮件测试已发送`)
  }

  const handleRuleTest = async (rule: NotificationRule) => {
    const res = await notificationApi.testRule(rule.id)
    const parts: string[] = []
    if (res.results.feishu) parts.push(`飞书${res.results.feishu.success ? '成功' : '失败'}`)
    if (res.results.smtp) parts.push(`邮件${res.results.smtp.success ? '成功' : '失败'}`)
    showToast(res.success ? 'ok' : 'err', `「${rule.name}」测试：${parts.join(' / ')}`)
  }

  const feishuActive = config.feishu_enabled && !!config.feishu_webhook
  const smtpActive   = config.smtp_enabled   && !!config.smtp_host
  const enabledCount = rules.filter(r => r.enabled).length

  return (
    <div className="rounded-xl border border-border overflow-hidden">
      {/* 服务标题行 */}
      <button type="button"
        className="w-full flex items-center gap-3 px-4 py-2.5 bg-muted/10 hover:bg-muted/20 transition-colors text-left"
        onClick={() => setExpanded(e => !e)}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className="text-sm font-semibold text-foreground">{SERVICE_LABELS[config.service] ?? config.service}</span>
          <span className="text-[10px] text-muted-foreground font-mono hidden sm:inline">{config.service}</span>
          <div className="flex items-center gap-1.5 ml-auto mr-1">
            <TooltipProvider delayDuration={200}><Tooltip>
              <TooltipTrigger asChild>
                <span className={`flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full
                  ${feishuActive ? 'bg-[#1abc9c]/10 text-[#1abc9c]' : 'bg-muted/30 text-muted-foreground'}`}>
                  <MessageSquare className="w-3 h-3" />飞书
                </span>
              </TooltipTrigger>
              <TooltipContent side="top" className="text-xs">{feishuActive ? '飞书已在后端配置' : '飞书未配置（服务端 .env）'}</TooltipContent>
            </Tooltip></TooltipProvider>
            <TooltipProvider delayDuration={200}><Tooltip>
              <TooltipTrigger asChild>
                <span className={`flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full
                  ${smtpActive ? 'bg-blue-400/10 text-blue-400' : 'bg-muted/30 text-muted-foreground'}`}>
                  <Mail className="w-3 h-3" />邮件
                </span>
              </TooltipTrigger>
              <TooltipContent side="top" className="text-xs">{smtpActive ? '邮件已在后端配置' : '邮件未配置（服务端 .env）'}</TooltipContent>
            </Tooltip></TooltipProvider>
            <Badge variant="outline" className="text-[10px] h-5 px-1.5">{enabledCount}/{rules.length}</Badge>
          </div>
        </div>
        <span
          role="button"
          tabIndex={0}
          className="inline-flex items-center h-7 px-2 text-xs mr-1 rounded-md hover:bg-muted/40"
          onClick={(e) => { e.stopPropagation(); setConfigDialog(true) }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              e.stopPropagation()
              setConfigDialog(true)
            }
          }}
        >
          <Settings2 className="w-3.5 h-3.5 mr-1" />渠道配置
        </span>
        {expanded ? <ChevronDown className="w-4 h-4 text-muted-foreground shrink-0" /> : <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />}
      </button>

      {/* 展开内容 */}
      {expanded && (
        <div className="px-4 py-3 border-t border-border/50 space-y-3">
          {toast && (
            <p className={`text-xs px-3 py-1.5 rounded-md ${toast.type === 'ok' ? 'bg-green-500/10 text-green-400' : 'bg-destructive/10 text-destructive'}`}>
              {toast.msg}
            </p>
          )}
          {rules.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-4">暂无通知规则，点击下方添加</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
              {rules.map(rule => (
                <RuleKpiCard key={rule.id} rule={rule}
                  feishuReady={feishuActive}
                  smtpReady={smtpActive}
                  isSelected={selectedRuleIds.has(rule.id)}
                  onToggleSelect={toggleRuleSelect}
                  onUpdated={onRuleUpdated}
                  onDelete={setDeleteTarget}
                  onEdit={r => { setEditingRule(r); setRuleDialog(true) }}
                  onTest={handleRuleTest}
                />
              ))}
            </div>
          )}
          {batchResults && Object.keys(batchResults).length > 0 && (
            <div className="rounded-md border border-border/50 bg-muted/5 p-2.5 space-y-1">
              <p className="text-xs font-semibold text-foreground mb-1">批量测试结果</p>
              {rules
                .filter(r => selectedRuleIds.has(r.id))
                .map(rule => {
                  const result = batchResults[rule.id]
                  return (
                    <div key={rule.id} className="flex items-center justify-between text-[10px] px-2 py-1 rounded bg-background/50">
                      <span className="text-muted-foreground truncate flex-1">{rule.name}</span>
                      <span className={result?.success ? 'text-green-400 font-medium' : 'text-destructive font-medium'}>
                        {result?.msg || '—'}
                      </span>
                    </div>
                  )
                })}
            </div>
          )}
          <div className="flex justify-between gap-2 pt-1">
            <div className="flex gap-1.5">
              {selectedRuleIds.size > 0 && (
                <>
                  <Button variant="outline" size="sm" className="h-7 text-xs gap-1"
                    onClick={() => setSelectedRuleIds(new Set())}
                    title="清除所有选择"
                  >
                    取消选择 ({selectedRuleIds.size})
                  </Button>
                  <Button size="sm" className="h-7 text-xs gap-1 bg-orange-600 hover:bg-orange-700"
                    onClick={handleBatchTest}
                    disabled={testingBatch}
                  >
                    {testingBatch ? '测试中…' : '🚀 批量测试'} ({selectedRuleIds.size})
                  </Button>
                </>
              )}
            </div>
            <Button variant="outline" size="sm" className="h-7 text-xs gap-1.5"
              onClick={() => { setEditingRule(null); setRuleDialog(true) }}
            >
              <Plus className="w-3 h-3" />添加通知规则
            </Button>
          </div>
        </div>
      )}

      <RuleDialog open={ruleDialog} service={config.service} editing={editingRule}
        onOpenChange={setRuleDialog} onSave={handleRuleSave} />

      <ConfigDialog
        open={configDialog}
        config={config}
        onOpenChange={setConfigDialog}
        onSave={handleConfigSave}
        onTestFeishu={handleServiceFeishuTest}
        onTestSmtp={handleServiceSmtpTest}
      />

      <Dialog open={!!deleteTarget} onOpenChange={v => !v && setDeleteTarget(null)}>
        <DialogContent className="sm:max-w-xs">
          <DialogHeader>
            <DialogTitle className="text-destructive">删除通知规则</DialogTitle>
            <DialogDescription>确定删除「{deleteTarget?.name}」？此操作不可撤销。</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>取消</Button>
            <Button variant="destructive" onClick={() => deleteTarget && handleDelete(deleteTarget)}>确认删除</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// ── NotificationsCard（主组件）────────────────────────────
export function NotificationsCard() {
  const [configs,  setConfigs]  = useState<ServiceNotifConfig[]>([])
  const [rules,    setRules]    = useState<NotificationRule[]>([])
  const [loading,  setLoading]  = useState(true)
  const [spinning, setSpinning] = useState(false)
  const [error,    setError]    = useState('')

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setSpinning(true)
    setError('')
    try {
      const [cfgs, rls] = await Promise.all([
        notificationApi.listConfigs(),
        notificationApi.listRules(),
      ])
      const sorted = SERVICE_ORDER
        .map(s => cfgs.find(c => c.service === s))
        .filter((c): c is ServiceNotifConfig => !!c)
      setConfigs(sorted)
      setRules(rls)
    } catch (e) {
      setError('加载失败: ' + (e as Error).message)
    } finally {
      setLoading(false)
      setSpinning(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const rulesFor = (service: string) =>
    rules.filter(r => r.service === service).sort((a, b) => a.sort_order - b.sort_order)

  if (loading) {
    return (
      <Card className="bg-transparent backdrop-blur-sm border-border">
        <CardContent className="py-10 text-center text-muted-foreground text-sm">加载中...</CardContent>
      </Card>
    )
  }

  return (
    <Card className="bg-transparent backdrop-blur-sm border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-foreground flex items-center gap-2 text-base">
              <Bell className="w-4 h-4 text-orange-500" />
              通知规则管理
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">
              点击卡片开启/关闭通知；点击
              <MessageSquare className="inline w-3 h-3 mx-0.5" />飞书 /
              <Mail className="inline w-3 h-3 mx-0.5" />邮件 标签独立控制渠道；右上角可配置渠道并逐条测试
            </p>
          </div>
          <Button variant="ghost" size="icon" className="h-7 w-7"
            onClick={() => load(true)} title="刷新">
            <RefreshCw className={`w-3.5 h-3.5 ${spinning ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-2.5">
        {error && (
          <p className="text-sm text-destructive rounded-md bg-destructive/10 px-3 py-2">{error}</p>
        )}
        {/* 颜色图例 */}
        <div className="flex flex-wrap gap-x-3 gap-y-1 pb-1 border-b border-border/50">
          {Object.entries(COLOR_CFG).map(([, v]) => (
            <span key={v.label} className="flex items-center gap-1 text-[10px] text-muted-foreground">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: v.hex }} />
              {v.label}
            </span>
          ))}
        </div>
        {configs.map(cfg => (
          <ServicePanel key={cfg.service} config={cfg} rules={rulesFor(cfg.service)}
            onConfigUpdated={config => setConfigs(prev => prev.map(c => c.service === config.service ? config : c))}
            onRuleAdded={rule  => setRules(prev => [...prev, rule])}
            onRuleUpdated={rule => setRules(prev => prev.map(r => r.id === rule.id ? rule : r))}
            onRuleDeleted={id  => setRules(prev => prev.filter(r => r.id !== id))}
          />
        ))}
      </CardContent>
    </Card>
  )
}
