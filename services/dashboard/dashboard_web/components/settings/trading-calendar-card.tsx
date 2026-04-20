'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  CalendarDays,
  Plus,
  Trash2,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Pencil,
} from 'lucide-react'
import { calendarApi, type CalendarEntry, type CalendarEntryType } from '@/lib/api/settings'

const TYPE_CFG: Record<CalendarEntryType, { label: string; color: string; badge: string }> = {
  holiday: {
    label: '休市/节假日',
    color: 'bg-red-500',
    badge: 'text-red-400 border-red-500/30 bg-red-500/5',
  },
  workday: {
    label: '补班交易日',
    color: 'bg-green-500',
    badge: 'text-green-400 border-green-500/30 bg-green-500/5',
  },
  early_close: {
    label: '提前收盘',
    color: 'bg-yellow-500',
    badge: 'text-yellow-400 border-yellow-500/30 bg-yellow-500/5',
  },
}

// 生成指定月的日历网格
function buildCalendarGrid(year: number, month: number, entries: CalendarEntry[]) {
  const entryMap = new Map(entries.map(e => [e.date, e]))
  const firstDay = new Date(year, month - 1, 1).getDay() // 0=Sun
  const daysInMonth = new Date(year, month, 0).getDate()
  // 调整为周一起
  const startOffset = (firstDay + 6) % 7
  const cells: Array<{ day: number | null; date: string | null; entry: CalendarEntry | null; isWeekend: boolean }> = []
  for (let i = 0; i < startOffset; i++) cells.push({ day: null, date: null, entry: null, isWeekend: false })
  for (let d = 1; d <= daysInMonth; d++) {
    const date = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const dow = new Date(year, month - 1, d).getDay()
    cells.push({ day: d, date, entry: entryMap.get(date) ?? null, isWeekend: dow === 0 || dow === 6 })
  }
  return cells
}

interface EntryFormState {
  date: string
  type: CalendarEntryType
  label: string
  note: string
}

const EMPTY_FORM: EntryFormState = { date: '', type: 'holiday', label: '', note: '' }

interface EntryDialogProps {
  open: boolean
  onOpenChange: (v: boolean) => void
  initial: EntryFormState
  editing: CalendarEntry | null
  onSave: (form: EntryFormState) => Promise<void>
}

function EntryDialog({ open, onOpenChange, initial, editing, onSave }: EntryDialogProps) {
  const [form, setForm] = useState<EntryFormState>(initial)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { setForm(initial); setError('') }, [initial, open])

  const handleSave = async () => {
    if (!form.date) { setError('请选择日期'); return }
    if (!form.label.trim()) { setError('请填写名称'); return }
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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CalendarDays className="w-5 h-5 text-orange-500" />
            {editing ? '编辑日历条目' : '添加日历条目'}
          </DialogTitle>
          <DialogDescription>标记节假日、补班日或提前收盘日</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-1.5">
            <Label>日期</Label>
            <Input
              type="date"
              value={form.date}
              onChange={e => setForm(f => ({ ...f, date: e.target.value }))}
              className="bg-background"
            />
          </div>
          <div className="space-y-1.5">
            <Label>类型</Label>
            <select
              value={form.type}
              onChange={e => setForm(f => ({ ...f, type: e.target.value as CalendarEntryType }))}
              className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm text-foreground"
            >
              {Object.entries(TYPE_CFG).map(([k, v]) => (
                <option key={k} value={k}>{v.label}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label>名称（如：春节、劳动节补班）</Label>
            <Input
              placeholder="输入名称"
              value={form.label}
              onChange={e => setForm(f => ({ ...f, label: e.target.value }))}
              className="bg-background"
            />
          </div>
          <div className="space-y-1.5">
            <Label>备注（可选）</Label>
            <Input
              placeholder="额外说明"
              value={form.note}
              onChange={e => setForm(f => ({ ...f, note: e.target.value }))}
              className="bg-background"
            />
          </div>
          {error && (
            <p className="text-sm text-destructive rounded-md bg-destructive/10 px-3 py-2">{error}</p>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? '保存中...' : editing ? '保存修改' : '添加'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function TradingCalendarCard() {
  const today = new Date()
  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [entries, setEntries] = useState<CalendarEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogInitial, setDialogInitial] = useState<EntryFormState>(EMPTY_FORM)
  const [editingEntry, setEditingEntry] = useState<CalendarEntry | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<CalendarEntry | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await calendarApi.list(year)
      setEntries(data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [year])

  useEffect(() => { load() }, [load])

  const prevMonth = () => {
    if (month === 1) { setYear(y => y - 1); setMonth(12) }
    else setMonth(m => m - 1)
  }
  const nextMonth = () => {
    if (month === 12) { setYear(y => y + 1); setMonth(1) }
    else setMonth(m => m + 1)
  }

  const openAdd = (date?: string) => {
    setEditingEntry(null)
    setDialogInitial({ ...EMPTY_FORM, date: date ?? '' })
    setDialogOpen(true)
  }

  const openEdit = (entry: CalendarEntry) => {
    setEditingEntry(entry)
    setDialogInitial({ date: entry.date, type: entry.type, label: entry.label, note: entry.note })
    setDialogOpen(true)
  }

  const handleSave = async (form: EntryFormState) => {
    if (editingEntry) {
      await calendarApi.update(editingEntry.id, form)
      setEntries(prev => prev.map(e => e.id === editingEntry.id ? { ...e, ...form } : e))
    } else {
      const newEntry = await calendarApi.add(form)
      setEntries(prev => [...prev, newEntry].sort((a, b) => a.date.localeCompare(b.date)))
    }
  }

  const handleDelete = async (entry: CalendarEntry) => {
    await calendarApi.remove(entry.id)
    setEntries(prev => prev.filter(e => e.id !== entry.id))
    setDeleteConfirm(null)
  }

  const grid = buildCalendarGrid(year, month, entries)
  const weekdays = ['一', '二', '三', '四', '五', '六', '日']
  const monthEntries = entries.filter(e => e.date.startsWith(`${year}-${String(month).padStart(2, '0')}`))
    .sort((a, b) => a.date.localeCompare(b.date))

  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

  return (
    <>
      <Card className="bg-transparent backdrop-blur-sm border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-foreground flex items-center gap-2">
                <CalendarDays className="w-5 h-5 text-orange-500" />
                交易日历
              </CardTitle>
              <CardDescription>管理节假日、补班日和提前收盘日</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" onClick={load} disabled={loading} title="刷新">
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
              <Button size="sm" className="gap-1" onClick={() => openAdd()}>
                <Plus className="w-4 h-4" />
                添加
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 月份导航 */}
          <div className="flex items-center justify-between">
            <Button variant="ghost" size="icon" onClick={prevMonth}><ChevronLeft className="w-4 h-4" /></Button>
            <span className="font-semibold text-foreground">{year} 年 {month} 月</span>
            <Button variant="ghost" size="icon" onClick={nextMonth}><ChevronRight className="w-4 h-4" /></Button>
          </div>

          {/* 图例 */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            {Object.entries(TYPE_CFG).map(([k, v]) => (
              <span key={k} className="flex items-center gap-1">
                <span className={`w-2 h-2 rounded-full ${v.color}`} />{v.label}
              </span>
            ))}
          </div>

          {/* 日历网格 */}
          <div className="rounded-xl border border-border overflow-hidden">
            {/* 周标题 */}
            <div className="grid grid-cols-7 bg-muted/30">
              {weekdays.map(d => (
                <div key={d} className={`text-center text-xs py-2 font-medium ${d === '六' || d === '日' ? 'text-muted-foreground/60' : 'text-muted-foreground'}`}>
                  {d}
                </div>
              ))}
            </div>
            {/* 日格 */}
            <div className="grid grid-cols-7 divide-x divide-y divide-border/30">
              {grid.map((cell, i) => {
                if (!cell.day) {
                  return <div key={`empty-${i}`} className="aspect-square bg-muted/10" />
                }
                const isToday = cell.date === todayStr
                const entry = cell.entry
                const dotColor = entry ? TYPE_CFG[entry.type as CalendarEntryType]?.color : null

                return (
                  <div
                    key={cell.date}
                    className={`aspect-square flex flex-col items-center justify-center relative cursor-pointer hover:bg-muted/30 transition-colors group
                      ${cell.isWeekend ? 'bg-muted/10' : ''}
                      ${entry?.type === 'holiday' ? 'bg-red-500/5' : ''}
                      ${entry?.type === 'workday' ? 'bg-green-500/5' : ''}
                      ${entry?.type === 'early_close' ? 'bg-yellow-500/5' : ''}
                    `}
                    onClick={() => entry ? openEdit(entry) : openAdd(cell.date!)}
                    title={entry ? `${entry.label}（${TYPE_CFG[entry.type as CalendarEntryType]?.label}）` : '点击添加'}
                  >
                    <span className={`text-xs font-medium
                      ${isToday ? 'text-orange-400 font-bold' : cell.isWeekend ? 'text-muted-foreground/60' : 'text-foreground'}
                    `}>
                      {cell.day}
                    </span>
                    {isToday && (
                      <span className="absolute bottom-0.5 w-1 h-1 rounded-full bg-orange-400" />
                    )}
                    {dotColor && (
                      <span className={`absolute top-0.5 right-0.5 w-1.5 h-1.5 rounded-full ${dotColor}`} />
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* 本月条目列表 */}
          {monthEntries.length > 0 ? (
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground font-medium">{year} 年 {month} 月条目 ({monthEntries.length} 条)</p>
              <div className="rounded-lg border border-border divide-y divide-border/50">
                {monthEntries.map(entry => (
                  <div key={entry.id} className="flex items-center justify-between px-3 py-2 group hover:bg-muted/20">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-mono text-muted-foreground w-10 shrink-0">
                        {entry.date.slice(8)}日
                      </span>
                      <Badge variant="outline" className={`text-xs shrink-0 ${TYPE_CFG[entry.type as CalendarEntryType]?.badge}`}>
                        {TYPE_CFG[entry.type as CalendarEntryType]?.label}
                      </Badge>
                      <span className="text-sm text-foreground">{entry.label}</span>
                      {entry.note && (
                        <span className="text-xs text-muted-foreground truncate max-w-[120px]">{entry.note}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(entry)}>
                        <Pencil className="w-3.5 h-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-destructive hover:text-destructive"
                        onClick={() => setDeleteConfirm(entry)}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">
              本月无特殊日历条目，点击日期格可快速添加
            </p>
          )}
        </CardContent>
      </Card>

      <EntryDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        initial={dialogInitial}
        editing={editingEntry}
        onSave={handleSave}
      />

      {/* 删除确认 */}
      <Dialog open={!!deleteConfirm} onOpenChange={v => !v && setDeleteConfirm(null)}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-destructive">删除日历条目</DialogTitle>
            <DialogDescription>
              确定删除「{deleteConfirm?.label}」（{deleteConfirm?.date}）？
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirm(null)}>取消</Button>
            <Button variant="destructive" onClick={() => deleteConfirm && handleDelete(deleteConfirm)}>
              确认删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
