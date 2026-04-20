'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Clock, Save, RefreshCw, Moon, Sun, Sunset } from 'lucide-react'
import { tradingSessionsApi, tradingConfigApi, simControlApi, type TradingSession } from '@/lib/api/settings'

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
  const [simConnected, setSimConnected] = useState<boolean | null>(null)
  const [origAutoTrading, setOrigAutoTrading] = useState<boolean>(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      // 并行加载：dashboard DB 配置 + 真实 sim-trading 状态
      const [sess, cfg, simState] = await Promise.all([
        tradingSessionsApi.list(),
        tradingConfigApi.get(),
        simControlApi.getState(),
      ])
      setSessions(sess)
      // auto_trading_enabled 优先读真实 sim-trading 状态
      const autoTrading = simState !== null
        ? simState.trading_enabled
        : (cfg.auto_trading_enabled === 'true')
      setSimConnected(simState !== null)
      setOrigAutoTrading(autoTrading)
      setConfig({
        auto_trading_enabled: autoTrading,
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
    await tradingSessionsApi.update(s.id, {
      label: edited.label,
      enabled: edited.enabled,
      start_time: edited.start_time,
      end_time: edited.end_time,
    })
    setSessions(prev => prev.map(x => x.id === s.id ? { ...x, ...editMap[x.id] } : x))
    setEditMap(prev => { const n = { ...prev }; delete n[s.id]; return n })
  }

  const saveAll = async () => {
    setSaving(prev => ({ ...prev, config: true }))
    try {
      // 保存所有有改动的时段
      const dirtyIds = Object.keys(editMap).map(Number)
      await Promise.all(dirtyIds.map(id => {
        const s = sessions.find(x => x.id === id)
        return s ? saveSession(s) : Promise.resolve()
      }))
      // 若 auto_trading_enabled 发生变化，调用真实 sim-trading API
      if (config.auto_trading_enabled !== origAutoTrading) {
        if (config.auto_trading_enabled) {
          await simControlApi.resume()
        } else {
          await simControlApi.pause('用户手动关闭自动交易')
        }
        setOrigAutoTrading(config.auto_trading_enabled)
      }
      // 同步保存 dashboard DB 配置
      await tradingConfigApi.update({
        auto_trading_enabled: config.auto_trading_enabled,
        pre_market_enabled: config.pre_market_enabled,
        post_market_enabled: config.post_market_enabled,
        pre_market_minutes: config.pre_market_minutes,
        timezone: config.timezone,
      })
      showMsg('success', '配置已保存')
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
      <Card className="bg-transparent backdrop-blur-sm border-border h-full">
        <CardContent className="py-8 text-center text-muted-foreground text-sm">加载中...</CardContent>
      </Card>
    )
  }

  return (
    <Card className="bg-transparent backdrop-blur-sm border-border h-full">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold text-foreground flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-orange-500" />
            交易控制
            {simConnected !== null && (
              <span className={`flex items-center gap-1 text-[10px] font-normal ml-1 ${simConnected ? 'text-green-400' : 'text-muted-foreground'}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${simConnected ? 'bg-green-400' : 'bg-muted-foreground'}`} />
                {simConnected ? 'Alienware 在线' : 'Alienware 离线'}
              </span>
            )}
          </CardTitle>
          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={load} title="刷新">
            <RefreshCw className="w-3 h-3" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">

        {/* 三时段紧凑行 */}
        <div className="space-y-1.5">
          {sessions.map(s => {
            const ed = getEdit(s)
            const dirty = isDirty(s)
            return (
              <div
                key={s.id}
                className={`rounded-lg border px-3 py-2 flex items-center gap-2 transition-colors ${SESSION_COLORS[s.name] ?? 'border-border bg-muted/10'}`}
              >
                {/* 图标 */}
                <div className="shrink-0">{SESSION_ICONS[s.name] ?? <Clock className="w-3.5 h-3.5" />}</div>

                {/* 名称 */}
                <Input
                  value={ed.label}
                  onChange={e => patch(s.id, 'label', e.target.value)}
                  className="h-6 w-16 text-xs font-medium bg-background px-1.5 shrink-0"
                />

                {/* 时间 */}
                <Input
                  type="time"
                  value={ed.start_time}
                  onChange={e => patch(s.id, 'start_time', e.target.value)}
                  className="h-6 w-20 text-xs bg-background px-1 shrink-0"
                />
                <span className="text-muted-foreground text-xs shrink-0">—</span>
                <Input
                  type="time"
                  value={ed.end_time}
                  onChange={e => patch(s.id, 'end_time', e.target.value)}
                  className="h-6 w-20 text-xs bg-background px-1 shrink-0"
                />

                {/* 开关 */}
                <Switch
                  checked={ed.enabled}
                  onCheckedChange={v => patch(s.id, 'enabled', v)}
                  className="shrink-0 scale-75 origin-right ml-auto"
                />

                {/* 有改动时显示橙点提示 */}
                {dirty && (
                  <span className="w-1.5 h-1.5 rounded-full bg-orange-400 shrink-0" title="有未保存改动" />
                )}
              </div>
            )
          })}
        </div>

        <div className="border-t border-border/50 pt-2 space-y-2">
          {/* 开关行 */}
          {[
            { key: 'auto_trading_enabled' as const, label: '自动交易', desc: '时段内自动触发开仓/平仓' },
            { key: 'pre_market_enabled' as const,   label: '盘前准备', desc: '开盘前提前连接 CTP' },
            { key: 'post_market_enabled' as const,  label: '盘后清算', desc: '收盘后自动执行清算' },
          ].map(({ key, label, desc }) => (
            <div key={key} className="flex items-center justify-between gap-2">
              <div className="min-w-0">
                <p className="text-xs font-medium text-foreground leading-tight">{label}</p>
                <p className="text-[11px] text-muted-foreground leading-tight">{desc}</p>
              </div>
              <Switch
                checked={config[key]}
                onCheckedChange={v => setConfig(c => ({ ...c, [key]: v }))}
                className="scale-75 origin-right shrink-0"
              />
            </div>
          ))}

          {/* 盘前分钟 + 时区 */}
          <div className="grid grid-cols-2 gap-2 pt-1">
            <div className="space-y-1">
              <Label className="text-[11px] text-muted-foreground">盘前分钟</Label>
              <Input
                type="number"
                min={5}
                max={120}
                value={config.pre_market_minutes}
                onChange={e => setConfig(c => ({ ...c, pre_market_minutes: parseInt(e.target.value, 10) || 30 }))}
                className="h-7 bg-background text-xs"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-[11px] text-muted-foreground">时区</Label>
              <select
                value={config.timezone}
                onChange={e => setConfig(c => ({ ...c, timezone: e.target.value }))}
                className="w-full h-7 rounded-md border border-input bg-background px-2 text-xs text-foreground"
              >
                <option value="Asia/Shanghai">北京时间</option>
                <option value="UTC">UTC</option>
                <option value="America/New_York">纽约时间</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1">
            {message && (
              <p className={`text-xs ${message.type === 'success' ? 'text-green-400' : 'text-destructive'}`}>
                {message.text}
              </p>
            )}
            <Button
              size="sm"
              className="ml-auto h-7 text-xs gap-1"
              onClick={saveAll}
              disabled={!!saving['config']}
            >
              <Save className="w-3 h-3" />
              {saving['config'] ? '保存中...' : '保存配置'}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
