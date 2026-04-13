"use client"

import { useEffect, useState } from "react"
import { Activity, BarChart3, Clock, RefreshCw, Server } from "lucide-react"
import api from '@/src/utils/api'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import EmptyState from '@/components/ui/empty-state'

export default function IntelligencePage() {
  const [isLoading, setIsLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [strategies, setStrategies] = useState<any[]>([])
  const [results, setResults] = useState<any[]>([])
  const [systemStatus, setSystemStatus] = useState<any>({})

  const load = async () => {
    try { window.dispatchEvent(new CustomEvent('backtest:loading', { detail: true })) } catch (_) {}
    setIsLoading(true)
    setApiError(null)
    try {
      const [strategyRes, resultRes, systemRes] = await Promise.allSettled([
        api.getStrategies(),
        api.getResults(),
        api.getSystemStatus(),
      ])

      if (strategyRes.status === 'fulfilled') setStrategies(Array.isArray(strategyRes.value) ? strategyRes.value : [])
      if (resultRes.status === 'fulfilled') setResults(Array.isArray(resultRes.value) ? resultRes.value : [])
      if (systemRes.status === 'fulfilled') setSystemStatus(systemRes.value || {})

      if (strategyRes.status === 'rejected') {
        setApiError(api.friendlyError(strategyRes.reason))
      }

      const now = new Date()
      setLastUpdate(now)
      try { window.dispatchEvent(new CustomEvent('backtest:lastUpdate', { detail: now.toISOString() })) } catch (_) {}
    } catch (err) {
      setApiError(api.friendlyError(err))
    } finally {
      setIsLoading(false)
      try { window.dispatchEvent(new CustomEvent('backtest:loading', { detail: false })) } catch (_) {}
    }
  }

  useEffect(() => {
    load()
    const onRefresh = () => load()
    window.addEventListener('backtest:refresh', onRefresh)
    return () => window.removeEventListener('backtest:refresh', onRefresh)
  }, [])

  const running = results.filter((item: any) => ['running', 'submitted', 'pending'].includes(item.status)).length
  const completed = results.filter((item: any) => item.status === 'completed').length
  const failed = results.filter((item: any) => item.status === 'failed').length
  const latestResults = [...results].sort((a: any, b: any) => (b.submitted_at ?? 0) - (a.submitted_at ?? 0)).slice(0, 6)

  return (
    <div className="p-6 space-y-6">
      {apiError && <div className="text-sm text-red-400 bg-neutral-900 border border-red-800 p-3 rounded">API 错误：{apiError}</div>}

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wider">运行洞察</h1>
          <p className="text-sm text-neutral-400">查看策略数量、任务状态和当前系统资源</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={load}
            variant="outline"
            className="border-neutral-700 text-neutral-400 hover:bg-neutral-800"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      <div className="text-xs text-neutral-500 text-right">最后更新: {lastUpdate.toLocaleString("zh-CN")}</div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: '策略数量', value: strategies.length, icon: <BarChart3 className="w-8 h-8 text-orange-400" /> },
          { label: '运行中任务', value: running, icon: <Activity className="w-8 h-8 text-blue-400" /> },
          { label: '已完成任务', value: completed, icon: <Clock className="w-8 h-8 text-green-400" /> },
          { label: '失败任务', value: failed, icon: <Server className="w-8 h-8 text-red-400" /> },
        ].map((item) => (
          <Card key={item.label} className="bg-neutral-900 border-neutral-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-neutral-400 tracking-wider">{item.label}</p>
                  <p className="text-2xl font-bold text-white font-mono">{isLoading ? '--' : item.value}</p>
                </div>
                {item.icon}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">最近任务</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {latestResults.length > 0 ? latestResults.map((item: any, index: number) => (
              <div key={item.id ?? index} className="flex items-center justify-between rounded border border-neutral-800 bg-neutral-800/60 px-3 py-2">
                <div>
                  <p className="text-sm text-white font-mono">{item.strategy ?? item.payload?.strategy?.id ?? item.name ?? '--'}</p>
                  <p className="text-xs text-neutral-500">{item.submitted_at ? new Date(item.submitted_at * 1000).toLocaleString('zh-CN') : '--'}</p>
                </div>
                <span className="text-xs text-neutral-300">{item.status ?? '--'}</span>
              </div>
            )) : (
              <EmptyState title="暂无任务记录" description="执行回测后会在这里显示最近状态" icon="inbox" />
            )}
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-700">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-neutral-300 tracking-wider">系统资源</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            {[
              { label: 'CPU', value: systemStatus.cpu, unit: '%' },
              { label: '内存', value: systemStatus.memory, unit: '%' },
              { label: '磁盘', value: systemStatus.disk, unit: '%' },
              { label: '延迟', value: systemStatus.latency, unit: 'ms' },
            ].map((item) => (
              <div key={item.label} className="rounded border border-neutral-800 bg-neutral-800/60 p-3">
                <p className="text-xs text-neutral-400">{item.label}</p>
                <p className="mt-1 text-lg font-bold text-white font-mono">
                  {item.value != null ? `${Number(item.value).toFixed(1)}${item.unit}` : '--'}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}