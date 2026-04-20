'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Clock, Save, RefreshCw, Moon, Sun, Sunset } from 'lucide-react'
import { tradingSessionsApi, tradingConfigApi, type TradingSession } from '@/lib/api/settings'

const SESSION_ICONS: Record<string, React.ReactNode> = {
  night: <Moon className="w-4 h-4 text-blue-400" />,
  morning: <Sun className="w-4 h-4 text-yellow-400" />,
  afternoon: <Sunset className="w-4 h-4 text-orange-400" />,
}

const SESSION_COLORS: Record<string, string> = {
  night: 'border-blue-500/30 bg-blue-500/5',
  morning: 'border-yellow-500/30 bg-yellow-500/5',
  afternoon: 'border-orange-500/30 bg-orange-500/5',
}

interface GlobalConfig {
  auto_trading_enabled: boolean
  pre_market_enabled: boolean
  post_market_enabled: boolean
  pre_market_minutes: number
  timezone: string
}

const DEFAULT_CONFIG: GlobalConfig = {
  auto_trading_enabled: true,
  pre_market_enabled: true,
  post_market_enabled: true,
  pre_market_minutes: 30,
  timezone: 'Asia/Shanghai',
}

export function TradingSessionsCard() {
  const [sessions, setSessions] = useState<TradingSession[]>([])
  const [config, setConfig] = useState<GlobalConfig>(DEFAULT_CONFIG)
  const [editMap, setEditMap] = useState<Record<number, Partial<TradingSession>>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<Record<string | number, boolean>>({})
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [sess, cfg] = await Promise.all([
        tradingSessionsApi.list(),
        tradingConfigApi.get(),
      ])
      setSessions(sess)
      setConfig({
        auto_trading_enabled: cfg.auto_trading_enabled === 'true',
        pre_market_enabled: cfg.pre_market_enabled === 'true',
        post_market_enabled: cfg.post_market_enabled === 'true',
        pre_market_minutes: parseInt(cfg.pre_market_minutes ?? '30', 10),
        timezone: cfg.timezone ?? 'Asia/Shanghai',
      })
    } catch (e) {
      setMessage({ type: 'error', text: '加载失败: ' + (e as Error).message })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const getEdit = (s: TradingSession) => ({ ...s, ...editMap[s.id] })

  const patch = (id: number, field: keyof TradingSession, value: unknown) => {
    setEditMap(prev => ({ ...prev, [id]: { ...(prev[id] ?? {}), [field]: value } }))
  }

  const saveSession = async (s: TradingSession) => {
    const edited = getEdit(s)
    setSaving(prev => ({ ...prev, [s.id]: true }))
    try {
      await tradingSessionsApi.update(s.id, {
        label: edited.label,
        enabled: edited.enabled,
        start_time: edited.start_time,
        end_time: edited.end_time,
      })
      setSessions(prev => prev.map(x => x.id === s.id ? { ...x, ...editMap[x.id] } : x))
      setEditMap(prev => { const n = { ...prev }; delete n[s.id]; return n })
      showMsg('success', `「${edited.label}」已保存`)
    } catch (e) {
      showMsg('error', '保存失败: ' + (e as Error).message)
    } finally {
      setSaving(prev => ({ ...prev, [s.id]: false }))
    }
  }

  const saveConfig = async () => {
    setSaving(prev => ({ ...prev, config: true }))
    try {
      await tradingConfigApi.update({
        auto_trading_enabled: config.auto_trading_enabled,
        pre_market_enabled: config.pre_market_enabled,
        post_market_enabled: config.post_market_enabled,
        pre_market_minutes: config.pre_market_minutes,
        timezone: config.timezone,
      })
      showMsg('success', '全局配置已保存')
    } catch (e) {
      showMsg('error', '保存失败: ' + (e as Error).message)
    } finally {
      setSaving(prev => ({ ...prev, config: false }))
    }
  }

  const showMsg = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 3000)
  }

  const isDirty = (s: TradingSession) => !!editMap[s.id] && Object.keys(editMap[s.id]).length > 0

  if (loading) {
    return (
      <Card className="bg-transparent backdrop-blur-sm border-border">
        <CardContent className="py-8 text-center text-muted-foreground text-sm">加载中...</CardContent>
      </Card>
    )
  }

  return (
    <>
      {/* 三时段配置 */}
      <Card className="bg-transparent backdrop-blur-sm border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-foreground flex items-center gap-2">
                <Clock className="w-5 h-5 text-orange-500" />
                期货交易时段
              </CardTitle>
              <CardDescription className="text-muted-foreground">
                配置夜盘 / 上午盘 / 下午盘的开收盘时间与启用状态
              </CardDescription>
            </div>
            <Button variant="ghost" size="icon" onClick={load} title="刷新">
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {sessions.map(s => {
            const ed = getEdit(s)
            const dirty = isDirty(s)
            return (
              <div
                key={s.id}
                className={`rounded-xl border p-4 space-y-4 transition-colors ${SESSION_COLORS[s.name] ?? 'border-border bg-muted/10'}`}
              >
                {/* 头部：图标 + 名称 + 状态 + 开关 */}
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-background border border-border flex items-center justify-center shrink-0">
                    {SESSION_ICONS[s.name] ?? <Clock className="w-4 h-4" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <Input
                        value={ed.label}
                        onChange={e => patch(s.id, 'label', e.target.value)}
                        className="h-7 w-28 text-sm font-medium bg-background"
                      />
                      <Badge
                        variant="outline"
                        className={ed.enabled
                          ? 'text-green-400 border-green-500/30'
                          : 'text-neutral-500 border-neutral-500/30'}
                      >
                        {ed.enabled ? '启用' : '停用'}
                      </Badge>
                      {dirty && (
                        <Badge variant="outline" className="text-orange-400 border-orange-500/30 text-[10px]">
                          未保存
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {ed.start_time} — {ed.end_time}
                    </p>
                  </div>
                  <Switch
                    checked={ed.enabled}
                    onCheckedChange={v => patch(s.id, 'enabled', v)}
                  />
                </div>

                {/* 时间编辑 */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">开盘时间</Label>
                    <Input
                      type="time"
                      value={ed.start_time}
                      onChange={e => patch(s.id, 'start_time', e.target.value)}
                      className="h-8 bg-background text-sm"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">收盘时间</Label>
                    <Input
                      type="time"
                      value={ed.end_time}
                      onChange={e => patch(s.id, 'end_time', e.target.value)}
                      className="h-8 bg-background text-sm"
                    />
                  </div>
                </div>

                {/* 保存按钮（仅有改动才激活） */}
                <div className="flex justify-end">
                  <Button
                    size="sm"
                    className="h-7 text-xs gap-1"
                    disabled={!dirty || saving[s.id]}
                    onClick={() => saveSession(s)}
                  >
                    <Save className="w-3 h-3" />
                    {saving[s.id] ? '保存中...' : '保存此时段'}
                  </Button>
                </div>
              </div>
            )
          })}
        </CardContent>
      </Card>

      {/* 全局交易控制 */}
      <Card className="bg-transparent backdrop-blur-sm border-border">
        <CardHeader>
          <CardTitle className="text-foreground text-base">全局交易控制</CardTitle>
          <CardDescription>自动交易、盘前盘后时间与时区</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            {
              key: 'auto_trading_enabled' as const,
              label: '启用自动交易',
              desc: '在启用的时段内自动触发开仓/平仓',
            },
            {
              key: 'pre_market_enabled' as const,
              label: '盘前准备',
              desc: '开盘前提前启动系统连接 CTP',
            },
            {
              key: 'post_market_enabled' as const,
              label: '盘后清算',
              desc: '收盘后自动执行清算和报告',
            },
          ].map(({ key, label, desc }) => (
            <div key={key} className="flex items-center justify-between">
              <div>
                <Label className="text-foreground">{label}</Label>
                <p className="text-sm text-muted-foreground">{desc}</p>
              </div>
              <Switch
                checked={config[key]}
                onCheckedChange={v => setConfig(c => ({ ...c, [key]: v }))}
              />
            </div>
          ))}

          <div className="grid grid-cols-2 gap-4 pt-2">
            <div className="space-y-1.5">
              <Label className="text-sm text-foreground">盘前准备时间（分钟）</Label>
              <Input
                type="number"
                min={5}
                max={120}
                value={config.pre_market_minutes}
                onChange={e => setConfig(c => ({ ...c, pre_market_minutes: parseInt(e.target.value, 10) || 30 }))}
                className="h-8 bg-background"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm text-foreground">时区</Label>
              <select
                value={config.timezone}
                onChange={e => setConfig(c => ({ ...c, timezone: e.target.value }))}
                className="w-full h-8 rounded-md border border-input bg-background px-3 text-sm text-foreground"
              >
                <option value="Asia/Shanghai">Asia/Shanghai（北京时间）</option>
                <option value="UTC">UTC</option>
                <option value="America/New_York">America/New_York</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            {message && (
              <p className={`text-sm ${message.type === 'success' ? 'text-green-400' : 'text-destructive'}`}>
                {message.text}
              </p>
            )}
            <Button
              className="ml-auto gap-1.5"
              onClick={saveConfig}
              disabled={saving['config']}
            >
              <Save className="w-4 h-4" />
              {saving['config'] ? '保存中...' : '保存全局配置'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </>
  )
}
