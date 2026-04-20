'use client'

import { useState, useEffect, useCallback } from 'react'
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
  Send,
  Plus,
  Trash2,
  Pencil,
  ChevronDown,
  ChevronRight,
  Mail,
  MessageSquare,
} from 'lucide-react'
import {
  notificationApi,
  type ServiceNotifConfig,
  type NotificationRule,
} from '@/lib/api/settings'

type RuleType = NotificationRule['rule_type']
type RuleColor = NotificationRule['color']

// ── 颜色映射（与飞书 template 对齐）────────────────────────
const COLOR_CFG: Record<string, { label: string; hex: string; feishu: string }> = {
  red:       { label: '报警 P0', hex: '#c0392b', feishu: 'red' },
  orange:    { label: '报警 P1', hex: '#e67e22', feishu: 'orange' },
  yellow:    { label: '报警 P2', hex: '#f39c12', feishu: 'yellow' },
  grey:      { label: '交易',    hex: '#7f8c8d', feishu: 'grey' },
  blue:      { label: '资讯',    hex: '#2980b9', feishu: 'blue' },
  wathet:    { label: '新闻',    hex: '#5dade2', feishu: 'wathet' },
  turquoise: { label: '通知',    hex: '#1abc9c', feishu: 'turquoise' },
}

const RULE_TYPE_CFG: Record<string, { label: string; colorKey: string }> = {
  alarm_p0: { label: '🚨 报警 P0', colorKey: 'red' },
  alarm_p1: { label: '⚠️ 报警 P1', colorKey: 'orange' },
  alarm_p2: { label: '🔔 报警 P2', colorKey: 'yellow' },
  trade:    { label: '📊 交易回报', colorKey: 'grey' },
  info:     { label: '📈 资讯',    colorKey: 'blue' },
  news:     { label: '📰 新闻',    colorKey: 'wathet' },
  notify:   { label: '📣 通知',    colorKey: 'turquoise' },
}

const SERVICE_ORDER = ['sim-trading', 'data', 'decision', 'backtest']
const SERVICE_LABELS: Record<string, string> = {
  'sim-trading': '模拟交易',
  'data':        '数据服务',
  'decision':    '决策引擎',
  'backtest':    '回测系统',
}

// ── RuleDialog ────────────────────────────────────────────
interface RuleForm {
  name: string
  rule_type: RuleType
  color: RuleColor
  content_template: string
  enabled: boolean
}

const EMPTY_RULE: RuleForm = {
  name: '',
  rule_type: 'notify' as RuleType,
  color: 'turquoise' as RuleColor,
  content_template: '',
  enabled: true,
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
      setForm({ name: editing.name, rule_type: editing.rule_type, color: editing.color, content_template: editing.content_template, enabled: editing.enabled })
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
              <span className="text-xs text-muted-foreground">{COLOR_CFG[form.color]?.label} · feishu: <code className="text-xs">{form.color}</code></span>
            </div>
          </div>

          {/* 内容模板 */}
          <div className="space-y-1.5">
            <Label>内容模板 <span className="text-muted-foreground text-xs">（可选，支持 {`{变量}`}）</span></Label>
            <textarea
              placeholder="如：CTP 断线: {reason}"
              value={form.content_template}
              onChange={e => setForm(f => ({ ...f, content_template: e.target.value }))}
              rows={2}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground resize-none focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          {/* 启用 */}
          <div className="flex items-center justify-between rounded-md border border-input bg-muted/20 px-3 py-2">
            <Label className="text-sm">启用此规则</Label>
            <Switch checked={form.enabled} onCheckedChange={v => setForm(f => ({ ...f, enabled: v }))} />
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
  onConfigSaved: (service: string, updated: ServiceNotifConfig) => void
  onRuleAdded: (rule: NotificationRule) => void
  onRuleUpdated: (rule: NotificationRule) => void
  onRuleDeleted: (id: number) => void
}

function ServicePanel({ config, rules, onConfigSaved, onRuleAdded, onRuleUpdated, onRuleDeleted }: ServicePanelProps) {
  const [expanded, setExpanded] = useState(false)
  const [form, setForm] = useState({
    feishu_webhook: config.feishu_webhook,
    feishu_enabled: config.feishu_enabled,
    smtp_host: config.smtp_host,
    smtp_port: config.smtp_port,
    smtp_username: config.smtp_username,
    smtp_password: '',
    smtp_to_addrs: config.smtp_to_addrs,
    smtp_enabled: config.smtp_enabled,
  })
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [ruleDialog, setRuleDialog] = useState(false)
  const [editingRule, setEditingRule] = useState<NotificationRule | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<NotificationRule | null>(null)

  const showMsg = (type: 'success' | 'error', text: string) => {
    setMsg({ type, text })
    setTimeout(() => setMsg(null), 3000)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await notificationApi.updateConfig(config.service, form)
      onConfigSaved(config.service, { ...config, ...form, smtp_password_set: !!form.smtp_password || config.smtp_password_set })
      showMsg('success', '配置已保存')
    } catch (e) { showMsg('error', '保存失败: ' + (e as Error).message) }
    finally { setSaving(false) }
  }

  const handleTestFeishu = async () => {
    if (!form.feishu_webhook) { showMsg('error', '请先填写 Webhook'); return }
    setTesting(true)
    try {
      const r = await notificationApi.testFeishu(config.service)
      showMsg(r.success ? 'success' : 'error', r.success ? '飞书测试消息发送成功' : '发送失败，请检查 Webhook')
    } catch (e) { showMsg('error', '测试失败: ' + (e as Error).message) }
    finally { setTesting(false) }
  }

  const handleRuleSave = async (form2: RuleForm) => {
    if (editingRule) {
      await notificationApi.updateRule(editingRule.id, { service: config.service, ...form2 })
      onRuleUpdated({ ...editingRule, ...form2 })
    } else {
      const res = await notificationApi.createRule({ service: config.service, ...form2 })
      onRuleAdded({ id: res.id, service: config.service, sort_order: 99, created_at: new Date().toISOString(), ...form2 })
    }
  }

  const handleDeleteRule = async (rule: NotificationRule) => {
    await notificationApi.deleteRule(rule.id)
    onRuleDeleted(rule.id)
    setDeleteConfirm(null)
  }

  const feishuActive = form.feishu_enabled && !!form.feishu_webhook
  const smtpActive   = form.smtp_enabled && !!form.smtp_host

  return (
    <div className="rounded-xl border border-border overflow-hidden">
      {/* 服务标题行 */}
      <button
        type="button"
        className="w-full flex items-center gap-3 px-4 py-3 bg-muted/10 hover:bg-muted/20 transition-colors text-left"
        onClick={() => setExpanded(e => !e)}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className="text-sm font-semibold text-foreground">
            {SERVICE_LABELS[config.service] ?? config.service}
          </span>
          <span className="text-xs text-muted-foreground font-mono">{config.service}</span>
          <div className="flex items-center gap-1.5 ml-auto mr-2">
            {/* 飞书指示 */}
            <TooltipProvider delayDuration={200}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className={`flex items-center gap-1 text-xs px-1.5 py-0.5 rounded-full ${feishuActive ? 'bg-turquoise-500/10 text-[#1abc9c]' : 'bg-muted/30 text-muted-foreground'}`}>
                    <MessageSquare className="w-3 h-3" />
                    飞书
                  </span>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">{feishuActive ? 'Webhook 已配置，通知开启' : 'Webhook 未配置或已关闭'}</TooltipContent>
              </Tooltip>
            </TooltipProvider>
            {/* 邮件指示 */}
            <TooltipProvider delayDuration={200}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className={`flex items-center gap-1 text-xs px-1.5 py-0.5 rounded-full ${smtpActive ? 'bg-blue-500/10 text-blue-400' : 'bg-muted/30 text-muted-foreground'}`}>
                    <Mail className="w-3 h-3" />
                    邮件
                  </span>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">{smtpActive ? 'SMTP 已配置，通知开启' : 'SMTP 未配置或已关闭'}</TooltipContent>
              </Tooltip>
            </TooltipProvider>
            {/* 规则数 */}
            <Badge variant="outline" className="text-[10px] h-5 px-1.5">
              {rules.filter(r => r.enabled).length}/{rules.length} 条规则
            </Badge>
          </div>
        </div>
        {expanded ? <ChevronDown className="w-4 h-4 text-muted-foreground shrink-0" /> : <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />}
      </button>

      {/* 展开内容 */}
      {expanded && (
        <div className="px-4 py-4 space-y-5 border-t border-border/50">
          {msg && (
            <p className={`text-xs px-3 py-2 rounded-md ${msg.type === 'success' ? 'bg-green-500/10 text-green-400' : 'bg-destructive/10 text-destructive'}`}>
              {msg.text}
            </p>
          )}

          {/* ── 飞书配置 ── */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-[#1abc9c]" />
                飞书 Webhook
              </p>
              <Switch
                checked={form.feishu_enabled}
                onCheckedChange={v => setForm(f => ({ ...f, feishu_enabled: v }))}
                className="scale-75 origin-right"
              />
            </div>
            <div className="flex gap-2">
              <Input
                placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..."
                value={form.feishu_webhook}
                onChange={e => setForm(f => ({ ...f, feishu_webhook: e.target.value }))}
                className="bg-background text-xs h-8 flex-1"
                disabled={!form.feishu_enabled}
              />
              <Button
                variant="outline"
                size="sm"
                className="h-8 px-2.5 gap-1 text-xs shrink-0"
                disabled={!form.feishu_webhook || testing}
                onClick={handleTestFeishu}
              >
                <Send className="w-3 h-3" />
                {testing ? '发送中…' : '测试'}
              </Button>
            </div>
          </div>

          {/* ── 邮件配置 ── */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-blue-400" />
                邮件 SMTP
              </p>
              <Switch
                checked={form.smtp_enabled}
                onCheckedChange={v => setForm(f => ({ ...f, smtp_enabled: v }))}
                className="scale-75 origin-right"
              />
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div className="col-span-2 space-y-1">
                <Label className="text-[10px] text-muted-foreground">SMTP 服务器</Label>
                <Input
                  placeholder="smtp.qq.com"
                  value={form.smtp_host}
                  onChange={e => setForm(f => ({ ...f, smtp_host: e.target.value }))}
                  className="bg-background text-xs h-8"
                  disabled={!form.smtp_enabled}
                />
              </div>
              <div className="space-y-1">
                <Label className="text-[10px] text-muted-foreground">端口</Label>
                <Input
                  type="number"
                  value={form.smtp_port}
                  onChange={e => setForm(f => ({ ...f, smtp_port: parseInt(e.target.value, 10) || 465 }))}
                  className="bg-background text-xs h-8"
                  disabled={!form.smtp_enabled}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label className="text-[10px] text-muted-foreground">用户名</Label>
                <Input
                  placeholder="xxx@qq.com"
                  value={form.smtp_username}
                  onChange={e => setForm(f => ({ ...f, smtp_username: e.target.value }))}
                  className="bg-background text-xs h-8"
                  disabled={!form.smtp_enabled}
                />
              </div>
              <div className="space-y-1">
                <Label className="text-[10px] text-muted-foreground">
                  密码{config.smtp_password_set ? ' (已设置)' : ''}
                </Label>
                <Input
                  type="password"
                  placeholder={config.smtp_password_set ? '留空保留原密码' : '输入授权码'}
                  value={form.smtp_password}
                  onChange={e => setForm(f => ({ ...f, smtp_password: e.target.value }))}
                  className="bg-background text-xs h-8"
                  disabled={!form.smtp_enabled}
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-[10px] text-muted-foreground">收件人（逗号分隔）</Label>
              <Input
                placeholder="a@example.com,b@example.com"
                value={form.smtp_to_addrs}
                onChange={e => setForm(f => ({ ...f, smtp_to_addrs: e.target.value }))}
                className="bg-background text-xs h-8"
                disabled={!form.smtp_enabled}
              />
            </div>
          </div>

          {/* 保存按钮 */}
          <div className="flex justify-end">
            <Button size="sm" className="h-7 text-xs gap-1" onClick={handleSave} disabled={saving}>
              {saving ? '保存中…' : '保存通知配置'}
            </Button>
          </div>

          {/* ── 通知规则 ── */}
          <div className="space-y-2 border-t border-border/50 pt-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Bell className="w-3.5 h-3.5 text-orange-400" />
                通知规则 <span className="text-muted-foreground font-normal">（{rules.length} 条）</span>
              </p>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-xs gap-1"
                onClick={() => { setEditingRule(null); setRuleDialog(true) }}
              >
                <Plus className="w-3 h-3" />
                添加
              </Button>
            </div>

            {rules.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-3">暂无通知规则，点击添加</p>
            ) : (
              <div className="rounded-lg border border-border divide-y divide-border/50">
                {rules.map(rule => (
                  <div key={rule.id} className="flex items-center gap-3 px-3 py-2 group hover:bg-muted/10">
                    {/* 颜色点 */}
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ backgroundColor: COLOR_CFG[rule.color]?.hex ?? '#888' }}
                    />
                    {/* 名称 + 类型 */}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-foreground truncate">{rule.name}</p>
                      <p className="text-[10px] text-muted-foreground">{RULE_TYPE_CFG[rule.rule_type]?.label ?? rule.rule_type}</p>
                    </div>
                    {/* 启用开关 */}
                    <Switch
                      checked={rule.enabled}
                      onCheckedChange={async v => {
                        await notificationApi.updateRule(rule.id, { ...rule, enabled: v })
                        onRuleUpdated({ ...rule, enabled: v })
                      }}
                      className="scale-75 origin-right shrink-0"
                    />
                    {/* 操作 */}
                    <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                      <Button
                        variant="ghost" size="icon" className="h-6 w-6"
                        onClick={() => { setEditingRule(rule); setRuleDialog(true) }}
                      >
                        <Pencil className="w-3 h-3" />
                      </Button>
                      <Button
                        variant="ghost" size="icon" className="h-6 w-6 text-destructive hover:text-destructive"
                        onClick={() => setDeleteConfirm(rule)}
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 规则弹窗 */}
      <RuleDialog
        open={ruleDialog}
        service={config.service}
        editing={editingRule}
        onOpenChange={setRuleDialog}
        onSave={handleRuleSave}
      />

      {/* 删除确认弹窗 */}
      <Dialog open={!!deleteConfirm} onOpenChange={v => !v && setDeleteConfirm(null)}>
        <DialogContent className="sm:max-w-xs">
          <DialogHeader>
            <DialogTitle className="text-destructive">删除通知规则</DialogTitle>
            <DialogDescription>确定删除「{deleteConfirm?.name}」？此操作不可撤销。</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirm(null)}>取消</Button>
            <Button variant="destructive" onClick={() => deleteConfirm && handleDeleteRule(deleteConfirm)}>确认删除</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// ── NotificationsCard（主组件）────────────────────────────
export function NotificationsCard() {
  const [configs, setConfigs] = useState<ServiceNotifConfig[]>([])
  const [rules, setRules] = useState<NotificationRule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [cfgs, rls] = await Promise.all([
        notificationApi.listConfigs(),
        notificationApi.listRules(),
      ])
      // 按固定服务顺序排序
      const sorted = SERVICE_ORDER
        .map(s => cfgs.find(c => c.service === s))
        .filter((c): c is ServiceNotifConfig => !!c)
      setConfigs(sorted)
      setRules(rls)
    } catch (e) {
      setError('加载失败: ' + (e as Error).message)
    } finally {
      setLoading(false)
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
              通知配置
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">
              各端飞书 Webhook & 邮件 SMTP 配置，以及通知规则管理
            </p>
          </div>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={load} title="刷新">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {error && (
          <p className="text-sm text-destructive rounded-md bg-destructive/10 px-3 py-2">{error}</p>
        )}

        {/* 颜色图例 */}
        <div className="flex flex-wrap gap-2 pb-1">
          {Object.entries(COLOR_CFG).map(([k, v]) => (
            <span key={k} className="flex items-center gap-1 text-[10px] text-muted-foreground">
              <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: v.hex }} />
              {v.label}
            </span>
          ))}
        </div>

        {/* 各服务面板 */}
        {configs.map(cfg => (
          <ServicePanel
            key={cfg.service}
            config={cfg}
            rules={rulesFor(cfg.service)}
            onConfigSaved={(service, updated) =>
              setConfigs(prev => prev.map(c => c.service === service ? updated : c))
            }
            onRuleAdded={rule => setRules(prev => [...prev, rule])}
            onRuleUpdated={rule => setRules(prev => prev.map(r => r.id === rule.id ? rule : r))}
            onRuleDeleted={id => setRules(prev => prev.filter(r => r.id !== id))}
          />
        ))}
      </CardContent>
    </Card>
  )
}
